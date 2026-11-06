"""Build-integration tests for encrypted pages.

Each test builds a tiny MkDocs site in a temporary directory. The notes live
under ``docs/notes`` (``notes_root``) so the plugin's note scanner validates
them; the site index and Material blog pages stay outside that directory.

CI is simulated by setting the ``CI`` environment variable, which switches
``encryption_config.strict`` to its fail-closed mode.
"""

from __future__ import annotations

import base64
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs.commands import build as mkdocs_build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort

from mkdocs_note.utils.crypt import envelope, keys, page

CANARY = "CANARY-SECRET-2026"
CANARY_TEXT = f"这一段独有标记 {CANARY} 只应存在于解密后的页面里。"

NOTE = (
	"---\n"
	"title: 保密笔记\n"
	"date: 2026-11-06 09:02:00\n"
	"permalink: 11408-resource\n"
	"publish: true\n"
	"encrypt: true\n"
	"---\n"
	"\n"
	"## 第一节\n"
	"\n"
	f"{CANARY_TEXT}\n"
	"\n"
	"## 第二节\n"
	"\n"
	"另一段内容，带有 `inline code` 与 [内部链接](../index.md)。\n"
)

OPEN_NOTE = (
	"---\n"
	"title: 公开笔记\n"
	"date: 2026-11-05 08:00:00\n"
	"permalink: open-note\n"
	"publish: true\n"
	"---\n"
	"\n"
	"## 公开内容\n"
	"\n"
	"这是一篇不需要加密的笔记。\n"
)

BASE_CONFIG = """\
site_name: Crypt Build Test
theme:
  name: material
plugins:
  - search
  - mkdocs-note:
      notes_root: docs/notes
      graph_config:
        enabled: true
        name: title
      preview_config:
        enabled: true
      encryption_config:
        kdf_iterations: 1000
"""

BLOG_CONFIG = """\
site_name: Crypt Blog Test
theme:
  name: material
plugins:
  - search
  - blog
  - mkdocs-note:
      notes_root: docs/notes
      encryption_config:
        kdf_iterations: 1000
"""

PAYLOAD_RE = re.compile(
	r'<script type="application/json" class="mkdocs-note-encrypted__payload">'
	r"(.*?)</script>",
	re.DOTALL,
)


class CryptBuildTestCase(unittest.TestCase):
	"""Base class that lays out and builds a throwaway MkDocs site."""

	def setUp(self):
		"""Create the site skeleton and enter its directory."""
		self._tmp = tempfile.TemporaryDirectory()
		self.addCleanup(self._tmp.cleanup)
		self.root = Path(self._tmp.name)
		self.docs = self.root / "docs"
		self.docs.mkdir()
		(self.docs / "index.md").write_text("# Home\n", encoding="utf-8")
		self._previous_cwd = os.getcwd()
		os.chdir(self.root)
		self.addCleanup(os.chdir, self._previous_cwd)

	def write_docs(self, rel: str, text: str) -> Path:
		"""Write a file below ``docs/`` and return its path."""
		path = self.docs / rel
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text(text, encoding="utf-8")
		return path

	def write_config(self, content: str = BASE_CONFIG) -> None:
		"""Write ``mkdocs.yml`` for the site."""
		(self.root / "mkdocs.yml").write_text(content, encoding="utf-8")

	def build(self) -> None:
		"""Load and build the site, raising whatever MkDocs raises."""
		config = load_config(config_file=str(self.root / "mkdocs.yml"))
		mkdocs_build.build(config)

	def site_texts(self) -> dict[str, str]:
		"""Return every built text file, keyed by its relative path."""
		site = self.root / "site"
		texts: dict[str, str] = {}
		for path in sorted(site.rglob("*")):
			if not path.is_file():
				continue
			try:
				texts[path.relative_to(site).as_posix()] = path.read_text(
					encoding="utf-8", errors="ignore"
				)
			except OSError:  # pragma: no cover - defensive
				continue
		return texts

	def page_html(self, rel: str) -> str:
		"""Return one built page's HTML."""
		return (self.root / "site" / rel).read_text(encoding="utf-8")

	def assert_no_canary(self) -> None:
		"""Fail when plaintext of the encrypted note reached any built file."""
		leaks = {
			name: text.count(CANARY)
			for name, text in self.site_texts().items()
			if CANARY in text
		}
		self.assertEqual(leaks, {}, f"plaintext leaked into {sorted(leaks)}")


class TestEncryptedBuild(CryptBuildTestCase):
	def test_envelope_page_yields_stub_and_payload(self):
		"""A CI build replaces the page with a stub plus an encrypted payload."""
		self.write_config()
		self.write_docs("notes/open.md", OPEN_NOTE)
		self.write_docs(
			"notes/secret.md",
			envelope.build_envelope(NOTE, "permalink", "11408-resource"),
		)

		with patch.dict(os.environ, {"CI": "1"}):
			self.build()

		html = self.page_html("notes/secret/index.html")
		self.assertIn("data-mkdocs-note-encrypted", html)
		self.assertIn("mkdocs-note-encrypted__payload", html)
		self.assertIn("保密笔记", html)
		self.assertNotIn(CANARY, html)

		match = PAYLOAD_RE.search(html)
		self.assertIsNotNone(match, "the encrypted payload is missing")
		payload = json.loads(match.group(1))
		self.assertEqual(payload["v"], 1)
		self.assertEqual(payload["iter"], 1000)
		self.assertTrue(payload["salt"])
		self.assertTrue(payload["iv"])
		self.assertTrue(payload["ct"])

		# The payload is a real AES-GCM ciphertext for this page and password.
		raw = base64.b64decode(payload["iv"]) + base64.b64decode(payload["ct"])
		plaintext = keys.open_site(
			"11408-resource", "notes/secret.md", raw, payload["iter"]
		)
		decrypted = json.loads(plaintext.decode("utf-8"))
		self.assertIn(CANARY, decrypted["content"])
		self.assertIn('href="#', decrypted["toc"])
		with self.assertRaises(keys.DecryptError):
			keys.open_site("wrong-password", "notes/secret.md", raw, payload["iter"])

		# The runtime assets are copied and injected only on the encrypted page.
		self.assertTrue((self.root / "site" / "js" / "encrypt.js").is_file())
		self.assertTrue((self.root / "site" / "css" / "encrypt.css").is_file())
		self.assertIn("encrypt.js", html)
		self.assertNotIn(
			"mkdocs_note_encrypt_options", self.page_html("notes/open/index.html")
		)
		self.assertNotIn("encrypt.js", self.page_html("index.html"))

		# Search, previews and the graph never see the plaintext.
		self.assert_no_canary()
		graph = json.loads(
			(self.root / "site" / "graph" / "graph.json").read_text(encoding="utf-8")
		)
		self.assertIn("notes/secret.md", {node["id"] for node in graph["nodes"]})

	def test_unencrypted_site_is_unchanged(self):
		"""Sites without encrypted notes get plain pages and no crypt assets."""
		self.write_config()
		self.write_docs("notes/open.md", OPEN_NOTE)

		with patch.dict(os.environ, {"CI": "1"}):
			self.build()

		html = self.page_html("notes/open/index.html")
		self.assertIn("这是一篇不需要加密的笔记", html)
		self.assertNotIn("mkdocs-note-encrypted", html)
		self.assertNotIn("mkdocs_note_encrypt_options", html)
		self.assertFalse((self.root / "site" / "js" / "encrypt.js").exists())
		self.assertFalse((self.root / "site" / "css" / "encrypt.css").exists())

	def test_undecryptable_envelope_gets_unavailable_stub_when_not_strict(self):
		"""Outside CI a corrupt envelope warns and shows the unavailable stub."""
		self.write_config()
		corrupt = envelope.build_envelope(NOTE, "permalink", "11408-resource")
		lines = corrupt.splitlines()
		for index, line in enumerate(lines):
			if len(line) > 40 and all(char.isalnum() or char in "+/=" for char in line):
				replacement = "A" if line[0] != "A" else "B"
				lines[index] = replacement + line[1:]
				break
		self.write_docs("notes/secret.md", "\n".join(lines) + "\n")

		with patch.dict(os.environ, {"CI": "0"}):
			self.build()

		html = self.page_html("notes/secret/index.html")
		self.assertIn("mkdocs-note-encrypted--unavailable", html)
		self.assertIn("could not be decrypted during the build", html)
		self.assertNotIn(CANARY, html)
		self.assert_no_canary()


class TestEncryptedBuildFailsClosed(CryptBuildTestCase):
	def assert_build_fails(self, expected: str) -> None:
		"""Build under CI and assert the error logged before the abort."""
		with self.assertLogs("mkdocs", level="ERROR") as captured:
			with self.assertRaises(Abort):
				self.build()
		self.assertIn(expected, "\n".join(captured.output))

	def test_plaintext_flagged_note_under_ci_aborts(self):
		"""A flagged note committed as plaintext must fail the CI build."""
		self.write_config()
		self.write_docs("notes/secret.md", NOTE)

		with patch.dict(os.environ, {"CI": "1"}):
			self.assert_build_fails("has encrypt: true but its source is plaintext")

	def test_flagged_note_without_password_or_permalink_aborts(self):
		"""Encryption without a password source is a configuration error."""
		self.write_config()
		unkeyed = NOTE.replace("permalink: 11408-resource\n", "")
		self.write_docs("notes/secret.md", unkeyed)

		with patch.dict(os.environ, {"CI": "1"}):
			self.assert_build_fails("requires a non-empty 'password' or 'permalink'")

	def test_blog_post_with_encrypt_aborts(self):
		"""Material blog posts refuse encryption because excerpts would leak."""
		self.write_config(BLOG_CONFIG)
		self.write_docs("notes/open.md", OPEN_NOTE)
		self.write_docs(
			"blog/posts/secret.md",
			"---\n"
			"title: Blog Secret\n"
			"date: 2026-11-06 09:02:00\n"
			"authors:\n"
			"  - tester\n"
			"permalink: blog-secret\n"
			"publish: true\n"
			"encrypt: true\n"
			"---\n"
			"\n"
			f"{CANARY_TEXT}\n",
		)

		with patch.dict(os.environ, {"CI": "1"}):
			self.assert_build_fails("not supported for Material blog posts")


class TestStubMarkup(unittest.TestCase):
	def test_prompt_line_breaks_become_br(self):
		"""Newlines in the prompt survive HTML minification as <br>."""
		stub = page.build_stub("Title", {"v": 1}, {"prompt": "Line one\n<b>two</b>"})
		self.assertIn("Line one<br>&lt;b&gt;two&lt;/b&gt;", stub)


if __name__ == "__main__":
	unittest.main()
