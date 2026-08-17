"""Tests for Notion full-sync resume checkpoints."""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.notion.sync import (
	CACHE_GITIGNORE,
	MigrationState,
	SyncOptions,
	checkpoint_path,
	clear_checkpoint,
	ensure_cache_gitignore,
	full_sync_fingerprint,
	load_checkpoint,
	normalize_local_images,
	run_sync,
	save_checkpoint,
	save_state,
)


def _options(root: Path, **kwargs) -> SyncOptions:
	defaults = {
		"project_root": root,
		"docs_dir": root / "docs",
		"notes_root": root / "docs",
		"nav_file": root / "docs" / ".nav.yml",
		"database_id": "db",
		"data_source_id": "ds",
		"site_url": "https://example.com",
		"state_path": root / ".notion_sync_state.json",
		"delay": 0.0,
		"local_images": "upload",
		"cache_dir": root / ".cache" / "mkdocs-note",
		"full": True,
	}
	defaults.update(kwargs)
	return SyncOptions(**defaults)


class TestLocalImagesMode(unittest.TestCase):
	def test_normalize(self):
		self.assertEqual(normalize_local_images("upload"), "upload")
		self.assertEqual(normalize_local_images("SITE"), "site")
		self.assertEqual(normalize_local_images("nope"), "upload")

	def test_site_mode_requires_site_url(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			code = run_sync(
				_options(
					root,
					site_url="",
					local_images="site",
					dry_run=True,
					full=True,
				)
			)
			self.assertEqual(code, 1)


class TestCheckpoint(unittest.TestCase):
	def test_gitignore_created_on_save(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			cache = root / ".cache" / "mkdocs-note"
			path = checkpoint_path(cache)
			fp = {"full": True, "sections": []}
			save_checkpoint(path, fp, ["a.md"])
			gitignore = cache / ".gitignore"
			self.assertTrue(gitignore.is_file())
			self.assertEqual(gitignore.read_text(encoding="utf-8"), CACHE_GITIGNORE)
			self.assertIn("*", gitignore.read_text(encoding="utf-8"))

	def test_gitignore_not_overwritten(self):
		with tempfile.TemporaryDirectory() as tmp:
			cache = Path(tmp) / "cache"
			ensure_cache_gitignore(cache)
			custom = cache / ".gitignore"
			custom.write_text("keep\n", encoding="utf-8")
			ensure_cache_gitignore(cache)
			self.assertEqual(custom.read_text(encoding="utf-8"), "keep\n")

	def test_fingerprint_mismatch_is_detectable(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			opts = _options(root)
			fp = full_sync_fingerprint(opts, full=True)
			other = full_sync_fingerprint(
				_options(root, local_images="site"), full=True
			)
			self.assertNotEqual(fp, other)

	def test_resume_skips_done_via_loaded_list(self):
		with tempfile.TemporaryDirectory() as tmp:
			root = Path(tmp)
			cache = root / ".cache" / "mkdocs-note"
			path = checkpoint_path(cache)
			opts = _options(root)
			fp = full_sync_fingerprint(opts, full=True)
			save_checkpoint(path, fp, ["notes/a.md", "notes/b.md"])
			loaded = load_checkpoint(path)
			self.assertIsNotNone(loaded)
			self.assertEqual(loaded["fingerprint"], fp)
			self.assertEqual(loaded["done"], ["notes/a.md", "notes/b.md"])

	def test_clear_keeps_gitignore(self):
		with tempfile.TemporaryDirectory() as tmp:
			cache = Path(tmp) / ".cache" / "mkdocs-note"
			path = checkpoint_path(cache)
			save_checkpoint(path, {"full": True}, ["x.md"])
			clear_checkpoint(path)
			self.assertFalse(path.exists())
			self.assertTrue((cache / ".gitignore").is_file())


class TestResumeRunSync(unittest.TestCase):
	def _project(self) -> Path:
		tmp = tempfile.TemporaryDirectory()
		self.addCleanup(tmp.cleanup)
		root = Path(tmp.name)
		docs = root / "docs"
		docs.mkdir()
		(docs / "a.md").write_text("# A\n", encoding="utf-8")
		(docs / "b.md").write_text("# B\n", encoding="utf-8")
		(docs / ".nav.yml").write_text("- a.md\n- b.md\n", encoding="utf-8")
		save_state(
			root / ".notion_sync_state.json",
			MigrationState(
				root_page_id="db",
				data_source_id="ds",
				pages={"a.md": {"id": "pa"}, "b.md": {"id": "pb"}},
			),
		)
		return root

	@staticmethod
	def _synced(fake):
		return [call.args[4].file_rel for call in fake.call_args_list]

	def test_success_clears_checkpoint(self):
		root = self._project()
		cache = root / ".cache" / "mkdocs-note"
		ck = checkpoint_path(cache)
		with patch(
			"mkdocs_note.utils.notion.sync.sync_one_page",
			return_value="updated",
		) as fake:
			code = run_sync(_options(root, token="t", full=True))
		self.assertEqual(code, 0)
		self.assertEqual(self._synced(fake), ["a.md", "b.md"])
		self.assertFalse(ck.exists())
		self.assertTrue((cache / ".gitignore").is_file())
		self.assertIn("*", (cache / ".gitignore").read_text(encoding="utf-8"))

	def test_resume_skips_done_pages(self):
		root = self._project()
		opts = _options(root, token="t", full=True)
		ck = checkpoint_path(opts.cache_dir)
		save_checkpoint(ck, full_sync_fingerprint(opts, full=True), ["a.md"])
		with patch(
			"mkdocs_note.utils.notion.sync.sync_one_page",
			return_value="updated",
		) as fake:
			code = run_sync(opts)
		self.assertEqual(code, 0)
		self.assertEqual(self._synced(fake), ["b.md"])
		self.assertFalse(ck.exists())

	def test_fingerprint_mismatch_does_not_skip(self):
		root = self._project()
		opts = _options(root, token="t", full=True)
		ck = checkpoint_path(opts.cache_dir)
		save_checkpoint(
			ck,
			full_sync_fingerprint(_options(root, local_images="site"), full=True),
			["a.md"],
		)
		with patch(
			"mkdocs_note.utils.notion.sync.sync_one_page",
			return_value="updated",
		) as fake:
			code = run_sync(opts)
		self.assertEqual(code, 0)
		self.assertEqual(self._synced(fake), ["a.md", "b.md"])
		self.assertFalse(ck.exists())

	def test_interrupt_keeps_checkpoint_then_resume_skips_done(self):
		root = self._project()
		opts = _options(root, token="t", full=True)
		ck = checkpoint_path(opts.cache_dir)

		def fail_on_second(*args, **_kwargs):
			item = args[4]
			if item.file_rel == "b.md":
				raise KeyboardInterrupt
			return "updated"

		with (
			patch(
				"mkdocs_note.utils.notion.sync.sync_one_page",
				side_effect=fail_on_second,
			),
			self.assertRaises(KeyboardInterrupt),
		):
			run_sync(opts)

		loaded = load_checkpoint(ck)
		self.assertIsNotNone(loaded)
		self.assertEqual(loaded["done"], ["a.md"])
		self.assertEqual(loaded["fingerprint"], full_sync_fingerprint(opts, full=True))

		with patch(
			"mkdocs_note.utils.notion.sync.sync_one_page",
			return_value="updated",
		) as fake:
			code = run_sync(_options(root, token="t", full=True))
		self.assertEqual(code, 0)
		self.assertEqual(self._synced(fake), ["b.md"])
		self.assertFalse(ck.exists())

	def test_no_resume_discards_checkpoint(self):
		root = self._project()
		opts = _options(root, token="t", full=True, no_resume=True)
		ck = checkpoint_path(opts.cache_dir)
		save_checkpoint(ck, full_sync_fingerprint(opts, full=True), ["a.md"])
		with patch(
			"mkdocs_note.utils.notion.sync.sync_one_page",
			return_value="updated",
		) as fake:
			code = run_sync(opts)
		self.assertEqual(code, 0)
		self.assertEqual(self._synced(fake), ["a.md", "b.md"])
		self.assertFalse(ck.exists())


if __name__ == "__main__":
	unittest.main()
