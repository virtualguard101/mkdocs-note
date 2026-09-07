"""Regression tests for Notion section parent resolution (issue #74)."""

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
	MigrationState,
	ensure_section,
	resolve_parent_id,
)
from mkdocs_note.utils.tree import TreeNode


def _nav(*nodes: TreeNode) -> dict[str, TreeNode]:
	return {node.key: node for node in nodes}


def _state(**kwargs) -> MigrationState:
	defaults = {
		"root_page_id": "db-id",
		"data_source_id": "ds-id",
		"title_property": "页面",
	}
	defaults.update(kwargs)
	return MigrationState(**defaults)


class TestEnsureSectionParent(unittest.TestCase):
	def test_new_section_under_notebook_uses_data_source(self):
		notebook = TreeNode(
			key="Notebook", title="Notebook", file_rel=None, parent_key=""
		)
		section = TreeNode(
			key="Notebook/音视频",
			title="音视频",
			file_rel=None,
			parent_key="Notebook",
		)
		nav_index = _nav(notebook, section)
		state = _state()

		with tempfile.TemporaryDirectory() as tmp:
			state_path = Path(tmp) / "state.json"
			with patch(
				"mkdocs_note.utils.notion.sync.create_page",
				return_value={
					"id": "section-page",
					"url": "https://www.notion.so/section-page",
				},
			) as create:
				page_id = ensure_section(
					"token",
					state,
					state_path,
					nav_index,
					"Notebook/音视频",
					delay=0.0,
					dry_run=False,
				)

		self.assertEqual(page_id, "section-page")
		create.assert_called_once()
		kwargs = create.call_args.kwargs
		self.assertEqual(create.call_args.args[1], "ds-id")
		self.assertEqual(kwargs["parent_kind"], "data_source")
		self.assertNotEqual(create.call_args.args[1], "db-id")

	def test_nested_section_under_notebook_child_uses_page(self):
		notebook = TreeNode(
			key="Notebook", title="Notebook", file_rel=None, parent_key=""
		)
		parent_section = TreeNode(
			key="Notebook/音视频",
			title="音视频",
			file_rel=None,
			parent_key="Notebook",
		)
		child_section = TreeNode(
			key="Notebook/音视频/进阶",
			title="进阶",
			file_rel=None,
			parent_key="Notebook/音视频",
		)
		nav_index = _nav(notebook, parent_section, child_section)
		state = _state()
		created: list[tuple[str, str]] = []

		def _create(_token, parent_id, title, **kwargs):
			page_id = f"page-{title}"
			created.append((parent_id, kwargs["parent_kind"]))
			return {
				"id": page_id,
				"url": f"https://www.notion.so/{page_id}",
			}

		with tempfile.TemporaryDirectory() as tmp:
			state_path = Path(tmp) / "state.json"
			with patch(
				"mkdocs_note.utils.notion.sync.create_page",
				side_effect=_create,
			):
				page_id = ensure_section(
					"token",
					state,
					state_path,
					nav_index,
					"Notebook/音视频/进阶",
					delay=0.0,
					dry_run=False,
				)

		self.assertEqual(page_id, "page-进阶")
		self.assertEqual(created, [("ds-id", "data_source"), ("page-音视频", "page")])

	def test_top_level_section_uses_wiki_root(self):
		projects = TreeNode(
			key="Projects", title="Projects", file_rel=None, parent_key=""
		)
		nav_index = _nav(projects)
		state = _state()

		with tempfile.TemporaryDirectory() as tmp:
			state_path = Path(tmp) / "state.json"
			with patch(
				"mkdocs_note.utils.notion.sync.create_page",
				return_value={
					"id": "projects-page",
					"url": "https://www.notion.so/projects-page",
				},
			) as create:
				page_id = ensure_section(
					"token",
					state,
					state_path,
					nav_index,
					"Projects",
					delay=0.0,
					dry_run=False,
				)

		self.assertEqual(page_id, "projects-page")
		self.assertEqual(create.call_args.args[1], "ds-id")
		self.assertEqual(create.call_args.kwargs["parent_kind"], "data_source")


class TestResolveParentId(unittest.TestCase):
	def test_notebook_child_content_uses_data_source(self):
		notebook = TreeNode(
			key="Notebook", title="Notebook", file_rel=None, parent_key=""
		)
		nav_index = _nav(notebook)
		state = _state()

		with tempfile.TemporaryDirectory() as tmp:
			state_path = Path(tmp) / "state.json"
			parent_id, kind = resolve_parent_id(
				"token",
				state,
				state_path,
				nav_index,
				"Notebook",
				delay=0.0,
				dry_run=False,
			)

		self.assertEqual(parent_id, "ds-id")
		self.assertEqual(kind, "data_source")
		self.assertEqual(state.pages["Notebook"]["id"], "db-id")

	def test_content_under_new_section_uses_page(self):
		notebook = TreeNode(
			key="Notebook", title="Notebook", file_rel=None, parent_key=""
		)
		section = TreeNode(
			key="Notebook/音视频",
			title="音视频",
			file_rel=None,
			parent_key="Notebook",
		)
		nav_index = _nav(notebook, section)
		state = _state()

		with tempfile.TemporaryDirectory() as tmp:
			state_path = Path(tmp) / "state.json"
			with patch(
				"mkdocs_note.utils.notion.sync.create_page",
				return_value={
					"id": "section-page",
					"url": "https://www.notion.so/section-page",
				},
			):
				parent_id, kind = resolve_parent_id(
					"token",
					state,
					state_path,
					nav_index,
					"Notebook/音视频",
					delay=0.0,
					dry_run=False,
				)

		self.assertEqual(parent_id, "section-page")
		self.assertEqual(kind, "page")


if __name__ == "__main__":
	unittest.main()
