"""Tests for the git clean/smudge filter and the crypt CLI helpers."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.crypt import envelope, gitfilter, gitops
from mkdocs_note.utils.crypt import cli as crypt_cli

PLAIN = (
	"---\n"
	"title: 测试笔记\n"
	"date: 2026-11-06 09:02:00\n"
	"permalink: 11408-resource\n"
	"publish: true\n"
	"encrypt: true\n"
	"---\n"
	"\n"
	"## 第一节\n"
	"\n"
	"这是一段需要加密的正文，包含独有的标记短语。\n"
)

RAW_PLAIN = b"no frontmatter\r\nkeep every byte\r\n"

SRC = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
GIT = shutil.which("git")


def _packet(data: bytes) -> bytes:
	return f"{len(data) + 4:04x}".encode("ascii") + data


def _flush() -> bytes:
	return b"0000"


def _client_handshake() -> bytes:
	return (
		_packet(b"git-filter-client\n")
		+ _packet(b"version=2\n")
		+ _flush()
		+ _packet(b"capability=clean\n")
		+ _packet(b"capability=smudge\n")
		+ _packet(b"capability=delay\n")
		+ _flush()
	)


def _request(command: str, data: bytes, pathname: str = "docs/note.md") -> bytes:
	return (
		_packet(f"command={command}\n".encode("ascii"))
		+ _packet(f"pathname={pathname}\n".encode("utf-8"))
		+ _flush()
		+ (_packet(data) if data else b"")
		+ _flush()
	)


def _read_packets(data: bytes) -> list[bytes | None]:
	reader = gitfilter.PacketReader(io.BytesIO(data))
	packets: list[bytes | None] = []
	while True:
		try:
			packets.append(reader.read_packet())
		except EOFError:
			return packets


class TestPacketProtocol(unittest.TestCase):
	def test_encode_and_decode_round_trip(self):
		payload = b"command=clean\n"
		stream = io.BytesIO(_packet(payload) + _flush())
		reader = gitfilter.PacketReader(stream)
		self.assertEqual(reader.read_packet(), payload)
		self.assertIsNone(reader.read_packet())

	def test_writer_round_trip(self):
		stream = io.BytesIO()
		writer = gitfilter.PacketWriter(stream)
		writer.write_packet(b"status=success")
		writer.write_flush()
		writer.flush()
		self.assertEqual(stream.getvalue(), _packet(b"status=success") + _flush())

	def test_writer_splits_large_content(self):
		stream = io.BytesIO()
		writer = gitfilter.PacketWriter(stream)
		data = b"x" * (gitfilter.MAX_PACKET_DATA + 10)
		writer.write_content(data)
		writer.write_flush()
		packets = _read_packets(stream.getvalue())
		self.assertEqual(b"".join(p for p in packets if p), data)
		self.assertEqual(sum(1 for p in packets if p), 2)

	def test_empty_content_is_a_single_flush(self):
		stream = io.BytesIO()
		writer = gitfilter.PacketWriter(stream)
		writer.write_content(b"")
		writer.write_flush()
		self.assertEqual(stream.getvalue(), _flush())

	def test_bad_header_raises(self):
		reader = gitfilter.PacketReader(io.BytesIO(b"zzzz"))
		with self.assertRaises(gitfilter.FilterProtocolError):
			reader.read_packet()

	def test_truncated_payload_raises(self):
		reader = gitfilter.PacketReader(io.BytesIO(b"0010abc"))
		with self.assertRaises(gitfilter.FilterProtocolError):
			reader.read_packet()


class TestFilterProcess(unittest.TestCase):
	def _serve(self, client_data: bytes) -> tuple[int, bytes, str]:
		stdout = io.BytesIO()
		stderr = io.StringIO()
		status = gitfilter.serve(
			gitfilter.PacketReader(io.BytesIO(client_data)),
			gitfilter.PacketWriter(stdout),
			stderr=stderr,
		)
		return status, stdout.getvalue(), stderr.getvalue()

	def test_clean_and_smudge_round_trip(self):
		data = PLAIN.encode("utf-8")
		client = (
			_client_handshake()
			+ _request("clean", data)
			+ _request("smudge", envelope.clean_bytes(data))
		)
		status, output, stderr = self._serve(client)
		self.assertEqual(status, 0)
		self.assertEqual(stderr, "")

		packets = _read_packets(output)
		self.assertEqual(
			packets[:6],
			[
				b"git-filter-server",
				b"version=2",
				None,
				b"capability=clean",
				b"capability=smudge",
				None,
			],
		)
		# clean: status, flush, content, flush, empty second status list
		cleaned = envelope.clean_bytes(data)
		self.assertEqual(packets[6:11], [b"status=success", None, cleaned, None, None])
		# smudge: the original plaintext comes back
		self.assertEqual(packets[11], b"status=success")
		self.assertEqual(packets[13], data)

	def test_clean_error_is_reported(self):
		unkeyed = PLAIN.replace("permalink: 11408-resource\n", "")
		status, output, _stderr = self._serve(
			_client_handshake() + _request("clean", unkeyed.encode("utf-8"))
		)
		self.assertEqual(status, 0)
		packets = _read_packets(output)
		self.assertEqual(packets[6], b"status=error")
		self.assertIn("requires a non-empty", packets[7].decode("utf-8"))

	def test_unknown_command_is_reported(self):
		status, output, _stderr = self._serve(
			_client_handshake() + _request("frobnicate", b"data")
		)
		self.assertEqual(status, 0)
		packets = _read_packets(output)
		self.assertEqual(packets[6], b"status=error")
		self.assertIn("unsupported filter command", packets[7].decode("utf-8"))

	def test_wrong_greeting_fails_handshake(self):
		status, _output, stderr = self._serve(_packet(b"not-git\n") + _flush())
		self.assertEqual(status, 1)
		self.assertIn("handshake failed", stderr)

	def test_handshake_without_capabilities_uses_all(self):
		client = _packet(b"git-filter-client\n") + _packet(b"version=2\n") + _flush()
		client += _flush()  # empty capability list
		client += _request("clean", PLAIN.encode("utf-8"))
		status, output, _stderr = self._serve(client)
		self.assertEqual(status, 0)
		packets = _read_packets(output)
		self.assertIn(b"capability=clean", packets)
		self.assertIn(b"capability=smudge", packets)


class TestSingleShot(unittest.TestCase):
	def test_clean(self):
		stdout = io.BytesIO()
		status = gitfilter.run_single(
			"clean",
			stdin=io.BytesIO(PLAIN.encode("utf-8")),
			stdout=stdout,
			stderr=io.StringIO(),
		)
		self.assertEqual(status, 0)
		self.assertEqual(stdout.getvalue(), envelope.clean_bytes(PLAIN.encode("utf-8")))

	def test_clean_error_exits_non_zero(self):
		stderr = io.StringIO()
		status = gitfilter.run_single(
			"clean",
			stdin=io.BytesIO(b"---\nencrypt: true\n---\nbody\n"),
			stdout=io.BytesIO(),
			stderr=stderr,
		)
		self.assertEqual(status, 1)
		self.assertIn("requires a non-empty", stderr.getvalue())

	def test_smudge_never_fails(self):
		garbage = b"---\nencrypt: true\n---\n<!-- mkdocs-note:encrypted v1 key=permalink\nAAAA\n-->\n"
		stdout = io.BytesIO()
		status = gitfilter.run_single(
			"smudge",
			stdin=io.BytesIO(garbage),
			stdout=stdout,
			stderr=io.StringIO(),
		)
		self.assertEqual(status, 0)
		self.assertEqual(stdout.getvalue(), garbage)


class TestRepositoryHelpers(unittest.TestCase):
	def test_filter_commands_use_forward_slashes(self):
		commands = crypt_cli.filter_commands(r"C:\Program Files\Python\python.exe")
		self.assertEqual(
			commands[gitops.PROCESS_KEY],
			'"C:/Program Files/Python/python.exe" -m mkdocs_note crypt filter-process',
		)
		self.assertEqual(commands[gitops.REQUIRED_KEY], "true")

	def test_ephemeral_uvx_detection(self):
		self.assertTrue(
			crypt_cli.is_ephemeral_python("/home/u/.cache/uv/archive-v0/abc/bin/python")
		)
		self.assertTrue(
			crypt_cli.is_ephemeral_python(
				"/home/u/.local/share/uv/tools/mkdocs-note/bin/python"
			)
		)
		self.assertFalse(
			crypt_cli.is_ephemeral_python("/home/u/project/.venv/bin/python")
		)


@unittest.skipUnless(GIT, "git is required")
class TestGitFilterIntegration(unittest.TestCase):
	def setUp(self):
		self.tmp = tempfile.TemporaryDirectory()
		self.addCleanup(self.tmp.cleanup)
		self.repo = Path(self.tmp.name) / "repo"
		(self.repo / "docs" / "note").mkdir(parents=True)
		(self.repo / "mkdocs.yml").write_text(
			"site_name: T\nplugins:\n  - mkdocs-note\n", encoding="utf-8"
		)
		(self.repo / "docs" / "index.md").write_text("# Home\n", encoding="utf-8")
		(self.repo / "docs" / "note" / "secret.md").write_text(PLAIN, encoding="utf-8")
		(self.repo / "docs" / "note" / "plain.md").write_bytes(RAW_PLAIN)
		self.env = {**os.environ, "PYTHONPATH": SRC}
		self._git("init", "-q")
		self._git("config", "user.email", "test@example.com")
		self._git("config", "user.name", "Tester")
		self.repository = crypt_cli.make_repository(self.repo, "docs")

	def _git(self, *args: str) -> subprocess.CompletedProcess:
		return subprocess.run(
			["git", "-c", "core.quotepath=false", *args],
			cwd=self.repo,
			env=self.env,
			capture_output=True,
			text=True,
			timeout=60,
			check=False,
		)

	def _git_bytes(self, *args: str) -> subprocess.CompletedProcess:
		return subprocess.run(
			["git", "-c", "core.quotepath=false", *args],
			cwd=self.repo,
			env=self.env,
			capture_output=True,
			text=False,
			timeout=60,
			check=False,
		)

	def _install(self) -> crypt_cli.InstallReport:
		return crypt_cli.install(self.repository, sys.executable)

	def _stage_and_commit(self) -> None:
		self._git("add", ".gitattributes", "mkdocs.yml", "docs")
		result = self._git("commit", "-qm", "notes", "--no-verify")
		self.assertEqual(result.returncode, 0, result.stderr)
		self.assertEqual(self._git("status", "--porcelain").stdout, "")

	def test_init_writes_attributes_config_and_hook(self):
		report = self._install()
		self.assertTrue(report.attributes_changed)
		self.assertIn(
			"/docs/**/*.md filter=mkdocs-note",
			(self.repo / ".gitattributes").read_text(encoding="utf-8"),
		)
		for key in gitops.FILTER_CONFIG_KEYS:
			self.assertIsNotNone(gitops.config_get(self.repo, key), key)
		self.assertEqual(report.hook_status, "installed")
		self.assertTrue(report.hook_path.is_file())
		self.assertIn(
			"mkdocs_note crypt check --staged",
			report.hook_path.read_text(encoding="utf-8"),
		)

		again = self._install()
		self.assertFalse(again.attributes_changed)
		self.assertEqual(again.hook_status, "present")

	def test_git_add_stores_envelope_and_keeps_worktree_plaintext(self):
		self._install()
		self._stage_and_commit()

		staged = self._git("show", ":docs/note/secret.md").stdout
		self.assertIn(envelope.MARKER, staged)
		self.assertNotIn("独有的标记短语", staged)
		self.assertIn("permalink: 11408-resource", staged)
		self.assertIn("## 第一节", self._read("docs/note/secret.md"))

		plain = self._git_bytes("show", ":docs/note/plain.md").stdout
		self.assertEqual(plain, RAW_PLAIN)

	def test_checkout_and_rename_round_trip(self):
		self._install()
		self._stage_and_commit()
		secret = self.repo / "docs" / "note" / "secret.md"
		secret.unlink()
		self.assertEqual(
			self._git("checkout", "--", "docs/note/secret.md").returncode, 0
		)
		self.assertIn("独有的标记短语", secret.read_text(encoding="utf-8"))

		moved = self._git("mv", "docs/note/secret.md", "docs/note/renamed.md")
		self.assertEqual(moved.returncode, 0, moved.stderr)
		self.assertIn(
			"R  docs/note/secret.md -> docs/note/renamed.md",
			self._git("status", "--short").stdout,
		)
		self.assertIn("独有", self._read("docs/note/renamed.md"))
		staged = self._git("show", ":docs/note/renamed.md").stdout
		self.assertIn(envelope.MARKER, staged)

	def test_status_is_clean_and_reports_envelopes(self):
		self._install()
		self._stage_and_commit()
		report = crypt_cli.status(self.repository)
		self.assertTrue(report.ok, report.problems)
		self.assertEqual(len(report.notes), 1)
		note = report.notes[0]
		self.assertEqual(note.key_field, "permalink")
		self.assertEqual(note.worktree, crypt_cli.PLAINTEXT)
		self.assertEqual(note.index, crypt_cli.ENVELOPE)
		self.assertEqual(note.head, crypt_cli.ENVELOPE)

	def test_plaintext_index_is_reported_by_status_and_check(self):
		self._install()
		self._stage_and_commit()
		plain_blob = self._git(
			"hash-object", "-w", "--no-filters", "docs/note/secret.md"
		).stdout.strip()
		self._git(
			"update-index", "--cacheinfo", f"100644,{plain_blob},docs/note/secret.md"
		)
		status = crypt_cli.status(self.repository)
		self.assertFalse(status.ok)
		self.assertTrue(
			any("index: plaintext" in problem for problem in status.problems)
		)
		checked = crypt_cli.check_staged(self.repository)
		self.assertFalse(checked.ok)
		self.assertTrue(any("staged as plaintext" in e for e in checked.errors))

	@unittest.skipUnless(os.name == "posix", "git hooks need a POSIX shell")
	def test_pre_commit_hook_blocks_plaintext(self):
		self._install()
		self._stage_and_commit()
		plain_blob = self._git(
			"hash-object", "-w", "--no-filters", "docs/note/secret.md"
		).stdout.strip()
		self._git(
			"update-index", "--cacheinfo", f"100644,{plain_blob},docs/note/secret.md"
		)
		result = self._git("commit", "-m", "blocked")
		self.assertNotEqual(result.returncode, 0)
		self.assertIn("staged as plaintext", result.stdout + result.stderr)
		self.assertIn("notes", self._git("log", "--format=%s").stdout)

	def test_check_staged_detects_corrupt_envelope(self):
		self._install()
		self._stage_and_commit()
		staged = self._git("show", ":docs/note/secret.md").stdout
		lines = staged.splitlines()
		for index, line in enumerate(lines):
			if len(line) > 40 and all(char.isalnum() or char in "+/=" for char in line):
				replacement = "B" if line[0] != "B" else "C"
				lines[index] = replacement + line[1:]
				break
		corrupt = "\n".join(lines) + "\n"
		corrupt_path = Path(self.tmp.name) / "corrupt.md"
		corrupt_path.write_text(corrupt, encoding="utf-8")
		blob = self._git(
			"hash-object", "-w", "--no-filters", str(corrupt_path)
		).stdout.strip()
		self._git("update-index", "--cacheinfo", f"100644,{blob},docs/note/secret.md")
		checked = crypt_cli.check_staged(self.repository)
		self.assertFalse(checked.ok)
		self.assertTrue(any("corrupt" in error for error in checked.errors))

	def test_missing_password_is_rejected_by_clean(self):
		self._install()
		unkeyed = PLAIN.replace("permalink: 11408-resource\n", "")
		(self.repo / "docs" / "note" / "secret.md").write_text(
			unkeyed, encoding="utf-8"
		)
		result = self._git("add", "docs/note/secret.md")
		self.assertNotEqual(result.returncode, 0)
		self.assertIn("requires a non-empty", result.stderr)

	def test_uninstall_removes_config_and_hook(self):
		self._install()
		report = crypt_cli.uninstall(self.repository)
		self.assertTrue(report.hook_removed)
		self.assertIn(gitops.PROCESS_KEY, report.removed_keys)
		for key in gitops.FILTER_CONFIG_KEYS:
			self.assertIsNone(gitops.config_get(self.repo, key), key)
		hook_path = gitops.git_path(self.repo, "hooks") / "pre-commit"
		self.assertFalse(hook_path.is_file())
		self.assertFalse(crypt_cli.status(self.repository).ok)

	def _read(self, relative: str) -> str:
		return (self.repo / relative).read_text(encoding="utf-8")


if __name__ == "__main__":
	unittest.main()
