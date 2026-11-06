"""Repository operations behind ``mkdocs-note crypt``.

The click commands live in :mod:`mkdocs_note.cli`; this module contains the
testable behavior: discovering the repository and docs directory, installing
the git filter and hook, and reporting the state of encrypted notes in the
worktree, the index and ``HEAD``.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from mkdocs_note.utils.crypt import envelope, gitops, keys

ENVELOPE = "envelope"
PLAINTEXT = "plaintext"
CORRUPT = "corrupt"
MISSING = "not committed"
UNREADABLE = "unreadable"

HOOK_SIGNATURE = "-m mkdocs_note crypt check --staged"


class CryptCliError(RuntimeError):
	"""A crypt command cannot proceed (not a git repo, ephemeral Python, ...)."""


@dataclass(frozen=True)
class Repository:
	"""Resolved locations for one docs tree inside a git work tree."""

	project_root: Path
	repo_root: Path
	docs_dir: Path
	docs_rel: str
	attributes_file: Path
	attributes_pattern: str


@dataclass(frozen=True)
class NoteStatus:
	"""State of one flagged note in the worktree, index and HEAD."""

	rel: str
	key_field: str | None
	worktree: str
	index: str
	head: str
	errors: tuple[str, ...]

	@property
	def ok(self) -> bool:
		"""Return whether this note has no blocking problem."""
		return not self.errors


@dataclass(frozen=True)
class StatusReport:
	"""Result of ``mkdocs-note crypt status``."""

	commands: Mapping[str, str | None]
	required: bool
	attribute: str | None
	attribute_sample: str
	hook_installed: bool
	notes: tuple[NoteStatus, ...]
	problems: tuple[str, ...]

	@property
	def ok(self) -> bool:
		"""Return whether the repository is fully consistent."""
		return not self.problems


@dataclass(frozen=True)
class InstallReport:
	"""Result of ``mkdocs-note crypt init``."""

	commands: Mapping[str, str]
	attributes_changed: bool
	hook_status: str
	hook_path: Path
	hook_line: str
	plaintext_index: tuple[str, ...]


@dataclass(frozen=True)
class CheckReport:
	"""Result of ``mkdocs-note crypt check --staged``."""

	checked: tuple[str, ...]
	errors: tuple[str, ...]

	@property
	def ok(self) -> bool:
		"""Return whether every staged encrypted note is valid."""
		return not self.errors


@dataclass(frozen=True)
class UninstallReport:
	"""Result of ``mkdocs-note crypt uninstall``."""

	removed_keys: tuple[str, ...]
	hook_removed: bool
	hook_kept: bool


def make_repository(
	project_root: Path,
	docs_dir: Path | str | None = None,
) -> Repository:
	"""Resolve the repository, docs directory and attributes pattern.

	Args:
		project_root: Directory containing ``mkdocs.yml``.
		docs_dir: Docs directory; relative paths are resolved against
			``project_root``. Defaults to ``docs``.

	Raises:
		CryptCliError: when the docs directory is outside the git work tree.
	"""
	project_root = project_root.resolve()
	repo = gitops.repo_root(project_root)
	docs = Path(docs_dir) if docs_dir is not None else Path("docs")
	if not docs.is_absolute():
		docs = project_root / docs
	docs = docs.resolve()
	try:
		relative = docs.relative_to(repo)
	except ValueError as exc:
		raise CryptCliError(
			f"docs directory {docs} is outside the git repository {repo}"
		) from exc
	docs_rel = "" if relative == Path() else relative.as_posix()
	if docs_rel:
		pattern = f"/{docs_rel}/**/*.md filter={gitops.FILTER_NAME}"
	else:
		pattern = f"**/*.md filter={gitops.FILTER_NAME}"
	return Repository(
		project_root=project_root,
		repo_root=repo,
		docs_dir=docs,
		docs_rel=docs_rel,
		attributes_file=repo / ".gitattributes",
		attributes_pattern=pattern,
	)


def is_ephemeral_python(python: str) -> bool:
	"""Return whether *python* belongs to an ephemeral uvx/tool environment.

	A filter command that points into ``uvx``'s cache breaks as soon as that
	cache is cleaned, which would make ``git add`` fail in every clone.
	"""
	normalized = python.replace("\\", "/")
	return "/uv/archive-" in normalized or "/uv/tools/" in normalized


def filter_commands(python: str) -> dict[str, str]:
	"""Build the four ``filter.mkdocs-note.*`` config values.

	Forward slashes and double quotes keep the command valid in git's shell on
	Windows, where the interpreter path may contain spaces.
	"""
	executable = python.replace("\\", "/")
	base = f'"{executable}" -m mkdocs_note crypt'
	return {
		gitops.PROCESS_KEY: f"{base} filter-process",
		gitops.CLEAN_KEY: f"{base} clean",
		gitops.SMUDGE_KEY: f"{base} smudge",
		gitops.REQUIRED_KEY: "true",
	}


def _write_text(path: Path, text: str, mode: int | None = None) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(text, encoding="utf-8", newline="\n")
	if mode is not None:
		path.chmod(mode)


def _ensure_attributes(path: Path, pattern: str) -> bool:
	"""Add *pattern* to ``.gitattributes``; return whether the file changed."""
	existing = path.read_text(encoding="utf-8") if path.is_file() else ""
	if any(line.strip() == pattern for line in existing.splitlines()):
		return False
	if existing and not existing.endswith("\n"):
		existing += "\n"
	_write_text(path, existing + pattern + "\n")
	return True


def _hook_script(python: str) -> str:
	executable = python.replace("\\", "/")
	return (
		"#!/bin/sh\n"
		f"# Installed by `mkdocs-note crypt init`. Remove with "
		f"`mkdocs-note crypt uninstall`.\n"
		f'exec "{executable}" -m mkdocs_note crypt check --staged\n'
	)


def _key_field(meta: Mapping[str, Any]) -> str | None:
	"""Return the frontmatter field that holds this note's password."""
	try:
		return keys.resolve_password(meta).field
	except keys.PasswordError:
		return None


def _text_state(text: str) -> tuple[str, str | None]:
	"""Classify note text as envelope, plaintext or corrupt."""
	try:
		parsed = envelope.parse_envelope(text)
		if parsed is None:
			return PLAINTEXT, None
		envelope.decrypt_envelope(text)
	except keys.CryptoError as exc:
		return CORRUPT, str(exc)
	return ENVELOPE, None


def _blob_state(data: bytes | None) -> tuple[str, str | None]:
	"""Classify an index/HEAD blob."""
	if data is None:
		return MISSING, None
	try:
		text = data.decode("utf-8")
	except UnicodeDecodeError:
		return UNREADABLE, "not valid UTF-8"
	return _text_state(text)


def flagged_notes(repo: Repository) -> list[tuple[str, dict[str, Any], str]]:
	"""Return ``(rel, meta, text)`` for every note with ``encrypt: true``."""
	notes: list[tuple[str, dict[str, Any], str]] = []
	for path in sorted(repo.docs_dir.rglob("*.md")):
		try:
			raw = path.read_text(encoding="utf-8")
		except (OSError, UnicodeDecodeError):
			continue
		text = envelope.normalize_text(raw)
		split = envelope.split_frontmatter(text)
		if split is None or not keys.is_encrypted(split[2]):
			continue
		rel = gitops.repo_relative(repo.repo_root, path)
		notes.append((rel, split[2], text))
	return notes


def notes_with_plaintext_index(repo: Repository) -> list[str]:
	"""Return flagged notes whose staged copy is still plaintext."""
	result: list[str] = []
	for rel, _meta, _text in flagged_notes(repo):
		blob = gitops.blob_bytes(repo.repo_root, rel, ":")
		if blob is None:
			continue
		try:
			staged = blob.decode("utf-8")
		except UnicodeDecodeError:
			result.append(rel)
			continue
		if not envelope.looks_encrypted(staged):
			result.append(rel)
	return result


def install(repo: Repository, python: str) -> InstallReport:
	"""Configure the filter, ``.gitattributes`` and the pre-commit hook."""
	if is_ephemeral_python(python):
		raise CryptCliError(
			"refusing to configure a filter that points into an ephemeral uvx "
			"environment; install mkdocs-note in a project or user environment "
			"first"
		)
	if not Path(python).is_file():
		raise CryptCliError(f"interpreter does not exist: {python}")

	commands = filter_commands(python)
	try:
		for key, value in commands.items():
			gitops.config_set(repo.repo_root, key, value)
	except gitops.GitError as exc:
		raise CryptCliError(str(exc)) from exc

	attributes_changed = _ensure_attributes(
		repo.attributes_file, repo.attributes_pattern
	)

	hooks_dir = gitops.git_path(repo.repo_root, "hooks")
	hook_path = hooks_dir / "pre-commit"
	executable = python.replace("\\", "/")
	hook_line = f'"{executable}" -m mkdocs_note crypt check --staged'
	if hook_path.is_file():
		try:
			existing = hook_path.read_text(encoding="utf-8", errors="replace")
		except OSError:
			existing = ""
		hook_status = "present" if HOOK_SIGNATURE in existing else "existing"
	else:
		_write_text(hook_path, _hook_script(python), mode=0o755)
		hook_status = "installed"

	return InstallReport(
		commands=commands,
		attributes_changed=attributes_changed,
		hook_status=hook_status,
		hook_path=hook_path,
		hook_line=hook_line,
		plaintext_index=tuple(notes_with_plaintext_index(repo)),
	)


def status(repo: Repository) -> StatusReport:
	"""Inspect the filter configuration and every flagged note."""
	commands = {
		key: gitops.config_get(repo.repo_root, key) for key in gitops.FILTER_CONFIG_KEYS
	}
	required = commands.get(gitops.REQUIRED_KEY) == "true"
	hook_path = gitops.git_path(repo.repo_root, "hooks") / "pre-commit"
	try:
		hook_text = hook_path.read_text(encoding="utf-8", errors="replace")
	except OSError:
		hook_text = ""
	hook_installed = HOOK_SIGNATURE in hook_text

	notes: list[NoteStatus] = []
	for rel, meta, text in flagged_notes(repo):
		worktree, work_error = _text_state(text)
		index, index_error = _blob_state(gitops.blob_bytes(repo.repo_root, rel, ":"))
		head, head_error = _blob_state(gitops.blob_bytes(repo.repo_root, rel, "HEAD"))
		errors: list[str] = []
		if work_error:
			errors.append(f"worktree: {work_error}")
		if index in (PLAINTEXT, CORRUPT):
			detail = f" ({index_error})" if index_error else ""
			errors.append(
				f"index: {index}{detail}; re-add with 'git add --renormalize -- {rel}'"
			)
		if head in (PLAINTEXT, CORRUPT):
			detail = f" ({head_error})" if head_error else ""
			errors.append(
				f"HEAD: {head}{detail}; plaintext already committed, rewrite history "
				"if it matters"
			)
		notes.append(
			NoteStatus(
				rel=rel,
				key_field=_key_field(meta),
				worktree=worktree,
				index=index,
				head=head,
				errors=tuple(errors),
			)
		)

	problems: list[str] = []
	if commands.get(gitops.PROCESS_KEY) is None:
		problems.append(
			"filter.mkdocs-note.process is not configured; run 'mkdocs-note crypt init'"
		)
	if not required:
		problems.append(
			"filter.mkdocs-note.required is not true; a missing filter would "
			"silently store plaintext"
		)
	sample = (
		notes[0].rel
		if notes
		else (f"{repo.docs_rel}/index.md" if repo.docs_rel else "index.md")
	)
	attribute = gitops.check_attr(repo.repo_root, sample)
	if attribute != gitops.FILTER_NAME:
		problems.append(
			f".gitattributes does not set 'filter={gitops.FILTER_NAME}' for "
			f"{sample}; run 'mkdocs-note crypt init' and commit .gitattributes"
		)
	for note in notes:
		problems.extend(f"{note.rel}: {error}" for error in note.errors)

	return StatusReport(
		commands=commands,
		required=required,
		attribute=attribute,
		attribute_sample=sample,
		hook_installed=hook_installed,
		notes=tuple(notes),
		problems=tuple(problems),
	)


def check_staged(repo: Repository) -> CheckReport:
	"""Verify that staged encrypted notes are valid envelopes."""
	prefix = f"{repo.docs_rel}/" if repo.docs_rel else ""
	checked: list[str] = []
	errors: list[str] = []
	for rel in gitops.staged_paths(repo.repo_root):
		if not rel.endswith(".md"):
			continue
		if prefix and not rel.startswith(prefix):
			continue
		abs_path = repo.repo_root / rel
		try:
			raw = abs_path.read_text(encoding="utf-8")
		except (OSError, UnicodeDecodeError) as exc:
			errors.append(f"{rel}: cannot read the worktree copy ({exc})")
			checked.append(rel)
			continue
		split = envelope.split_frontmatter(envelope.normalize_text(raw))
		if split is None:
			continue
		meta = split[2]
		checked.append(rel)

		staged = gitops.blob_bytes(repo.repo_root, rel, ":")
		if staged is None:
			errors.append(f"{rel}: the staged copy is missing; re-add the file")
			continue
		try:
			staged_text = staged.decode("utf-8")
		except UnicodeDecodeError:
			errors.append(f"{rel}: the staged copy is not valid UTF-8")
			continue
		staged_encrypted = envelope.looks_encrypted(staged_text)

		if keys.is_encrypted(meta):
			try:
				keys.resolve_password(meta)
			except keys.PasswordError as exc:
				errors.append(f"{rel}: {exc}")
				continue
			if not staged_encrypted:
				errors.append(
					f"{rel}: staged as plaintext. Run 'mkdocs-note crypt init', "
					f"then 'git add --renormalize -- {rel}'."
				)
				continue
			try:
				envelope.decrypt_envelope(staged_text)
			except keys.CryptoError as exc:
				errors.append(
					f"{rel}: the staged envelope is corrupt or cannot be decrypted "
					f"({exc}); stage the whole file with 'git add -- {rel}'."
				)
		elif staged_encrypted:
			errors.append(
				f"{rel}: the staged copy is an envelope but the note no longer "
				f"has 'encrypt: true'; re-add it with 'git add -- {rel}'."
			)
	return CheckReport(checked=tuple(checked), errors=tuple(errors))


def uninstall(repo: Repository) -> UninstallReport:
	"""Remove the filter configuration and the hook installed by ``init``."""
	removed: list[str] = []
	for key in gitops.FILTER_CONFIG_KEYS:
		if gitops.config_unset(repo.repo_root, key):
			removed.append(key)

	hook_path = gitops.git_path(repo.repo_root, "hooks") / "pre-commit"
	hook_removed = False
	hook_kept = False
	if hook_path.is_file():
		try:
			text = hook_path.read_text(encoding="utf-8", errors="replace")
		except OSError:
			text = ""
		if HOOK_SIGNATURE in text:
			try:
				hook_path.unlink()
				hook_removed = True
			except OSError:
				hook_kept = True
		else:
			hook_kept = True

	return UninstallReport(
		removed_keys=tuple(removed),
		hook_removed=hook_removed,
		hook_kept=hook_kept,
	)


def python_executable() -> str:
	"""Return the interpreter that should host the filter commands."""
	return sys.executable
