"""Python → JavaScript interoperability for encrypted page payloads.

The build seals page payloads in Python; the browser opens them with WebCrypto
in ``static/encrypt.js``. This test runs the exact JavaScript routines under
Node so a drift between the two implementations (normalization, PBKDF2, AAD,
nonce layout) fails the suite instead of only showing up in a browser.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import unittest
from pathlib import Path

from mkdocs_note.utils.crypt import page

ENCRYPT_JS = (
	Path(__file__).resolve().parents[1]
	/ "src"
	/ "mkdocs_note"
	/ "static"
	/ "encrypt.js"
)

NODE_SCRIPT = """
global.window = globalThis;
globalThis.isSecureContext = true;
if (!globalThis.crypto) {
  globalThis.crypto = require("node:crypto").webcrypto;
}
const fs = require("fs");
const mod = require(process.argv[1]);
const input = JSON.parse(fs.readFileSync(0, "utf8"));
(async () => {
  const key = await mod.deriveKey(input.password, input.payload);
  const data = await mod.decryptPayload(input.payload, key);
  process.stdout.write(JSON.stringify(data));
})().catch((error) => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exit(1);
});
"""


class JavaScriptInteropTestCase(unittest.TestCase):
	"""Verify that encrypt.js decrypts Python-sealed payloads."""

	def setUp(self):
		self.node = shutil.which("node")
		if self.node is None:
			self.skipTest("node is not installed")
		if not ENCRYPT_JS.is_file():
			self.skipTest(f"{ENCRYPT_JS} is missing")

	def _run_node(self, payload: dict, password: str) -> dict:
		process = subprocess.run(
			[self.node, "-e", NODE_SCRIPT, str(ENCRYPT_JS)],
			input=json.dumps({"password": password, "payload": payload}),
			capture_output=True,
			text=True,
			timeout=60,
			check=False,
		)
		self.assertEqual(
			process.returncode,
			0,
			f"node failed:\nstdout: {process.stdout}\nstderr: {process.stderr}",
		)
		return json.loads(process.stdout)

	def test_browser_runtime_decrypts_python_payload(self):
		content = "<h1>Demo</h1><p>CANARY-INTEROP-2026 — 中文内容</p>"
		toc_html = '<ul class="md-nav__list"><li>Demo</li></ul>'
		payload = page.build_site_payload(
			"notes/interop.md",
			content,
			toc_html,
			"mkdocs-note-demo",
			iterations=1000,
		)

		data = self._run_node(payload, "mkdocs-note-demo")

		self.assertEqual(data["v"], 1)
		self.assertEqual(data["content"], content)
		self.assertEqual(data["toc"], toc_html)

	def test_browser_runtime_normalizes_password_like_python(self):
		payload = page.build_site_payload(
			"notes/interop.md",
			"<p>normalized</p>",
			"",
			"mkdocs-note-demo",
			iterations=1000,
		)

		# The browser trims and NFC-normalizes whatever the reader types.
		data = self._run_node(payload, "  mkdocs-note-demo\t")

		self.assertEqual(data["content"], "<p>normalized</p>")

	def test_browser_runtime_rejects_wrong_password(self):
		payload = page.build_site_payload(
			"notes/interop.md",
			"<p>secret</p>",
			"",
			"mkdocs-note-demo",
			iterations=1000,
		)

		with self.assertRaises(AssertionError):
			self._run_node(payload, "wrong-password")


if __name__ == "__main__":
	unittest.main()
