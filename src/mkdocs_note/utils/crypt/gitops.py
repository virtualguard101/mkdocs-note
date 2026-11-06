"""Minimal git plumbing for the encryption filter and CLI.

Every helper runs git with ``core.quotepath=false`` so non-ASCII note paths
come back as raw UTF-8 instead of quoted octal escapes (the same reason the
3.4.2 link-preview fix sets it). None of the helpers assume that the calling
process' working directory is the repository root.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

FILTER_NAME = "mkdocs-note"
FILTER_KEY = f"filter.{FILTER_NAME}"
PROCESS_KEY = f"{FILTER_KEY}.process"
CLEAN_KEY = f"{FILTER_KEY}.clean"
SMUDGE_KEY = f"{FILTER_KEY}.smudge"
REQUIRED_KEY = f"{FILTER_KEY}.required"

FILTER_CONFIG_KEYS = (PROCESS_KEY, CLEAN_KEY, SMUDGE_KEY, REQUIRED_KEY)


class GitError(RuntimeError):
	"""A git command failed."""


def git_available() -> bool:
	"""Return whether a ``git`` executable is on PATH."""
	return shutil.which("git") is not None


def _run(
	cwd: Path | str,
	args: tuple[str, ...],
	*,
	text: bool,
	check: bool,
) -> subprocess.CompletedProcess:
	command = ["git", "-c", "core.quotepath=false", *args]
	try:
		result = subprocess.run(
			command,
			cwd=cwd,
			capture_output=True,
			text=text,
			check=False,
		)
	except OSError as exc:
		raise GitError(f"cannot run git: {exc}") from exc
	if check and result.returncode != 0:
		stderr = (
			result.stderr.strip()
			if text
			else result.stderr.decode("utf-8", "replace").strip()
		)
		raise GitError(f"git {' '.join(args)} failed ({result.returncode}): {stderr}")
	return result


def run_git(
	cwd: Path | str, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
	"""Run git with text output."""
	return _run(cwd, args, text=True, check=check)


def run_git_bytes(
	cwd: Path | str, *args: str, check: bool = True
) -> subprocess.CompletedProcess[bytes]:
	"""Run git with binary output (blobs must not be decoded)."""
	return _run(cwd, args, text=False, check=check)


def inside_work_tree(cwd: Path | str) -> bool:
	"""Return whether *cwd* is inside a git work tree."""
	if not git_available():
		return False
	result = run_git(cwd, "rev-parse", "--is-inside-work-tree", check=False)
	return result.returncode == 0 and result.stdout.strip() == "true"


def repo_root(cwd: Path | str) -> Path:
	"""Return the root of the work tree that contains *cwd*."""
	result = run_git(cwd, "rev-parse", "--show-toplevel", check=False)
	if result.returncode != 0 or not result.stdout.strip():
		raise GitError(f"not inside a git work tree: {cwd}")
	return Path(result.stdout.strip()).resolve()


def git_path(cwd: Path | str, name: str) -> Path:
	"""Resolve a path inside the git directory (``hooks``, ``info``, ...).

	Used instead of hardcoding ``.git`` so the helper also works in submodules
	and linked worktrees.
	"""
	result = run_git(cwd, "rev-parse", "--git-path", name)
	path = Path(result.stdout.strip())
	if not path.is_absolute():
		path = Path(cwd) / path
	return path


def config_get(cwd: Path | str, key: str) -> str | None:
	"""Return a git config value, or ``None`` when it is not set."""
	result = run_git(cwd, "config", "--get", key, check=False)
	if result.returncode != 0:
		return None
	value = result.stdout.strip()
	return value or None


def config_set(cwd: Path | str, key: str, value: str) -> None:
	"""Set a local git config value."""
	run_git(cwd, "config", key, value)


def config_unset(cwd: Path | str, key: str) -> bool:
	"""Unset every value of a git config key; return whether one was set."""
	result = run_git(cwd, "config", "--unset-all", key, check=False)
	return result.returncode == 0


def check_attr(cwd: Path | str, path: str, attr: str = "filter") -> str | None:
	"""Return the git attribute value for *path*, or ``None`` when unset.

	``path`` must be relative to the repository root.
	"""
	result = run_git(cwd, "check-attr", "-z", attr, "--", path, check=False)
	if result.returncode != 0:
		return None
	parts = result.stdout.split("\0")
	if len(parts) < 3:
		return None
	value = parts[2]
	if value in ("unspecified", "unset", ""):
		return None
	return value


def blob_bytes(cwd: Path | str, path: str, rev: str = ":") -> bytes | None:
	"""Read a blob from the index (``:``) or a ref (``HEAD``), or ``None``.

	``path`` must be relative to the repository root, with forward slashes.
	"""
	spec = f":{path}" if rev in ("", ":") else f"{rev}:{path}"
	result = run_git_bytes(cwd, "show", spec, check=False)
	if result.returncode != 0:
		return None
	return result.stdout


def staged_paths(cwd: Path | str) -> list[str]:
	"""Return repo-relative paths staged for the next commit."""
	result = run_git(cwd, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
	return [path for path in result.stdout.split("\0") if path]


def repo_relative(repo_root_path: Path, path: Path) -> str:
	"""Return *path* as a POSIX path relative to *repo_root_path*."""
	return path.resolve().relative_to(repo_root_path.resolve()).as_posix()
