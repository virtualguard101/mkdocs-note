#!/usr/bin/env python3
"""
Smoke test for mkdocs-note package.
This script performs basic validation to ensure the package was built correctly
and can be imported and used without critical errors.

This test is designed to run in CI/CD environments after package building
and before publishing to PyPI.
"""

import sys


def test_package_import():
	"""Test that the main package can be imported."""
	print("Testing package import...")

	try:
		# Test that the package can be imported
		import mkdocs_note  # noqa: F401

		print("✅ mkdocs_note package imported successfully")
		assert True
	except ImportError as e:
		print(f"❌ Failed to import mkdocs_note: {e}")
		assert False, f"Failed to import mkdocs_note: {e}"


def test_core_modules():
	"""Test that core modules can be imported."""
	print("Testing core modules...")

	# Test config module
	try:
		from mkdocs_note.config import MkdocsNoteConfig

		config = MkdocsNoteConfig()
		assert config is not None
		print("✅ MkdocsNoteConfig works")
	except Exception as e:
		print(f"❌ MkdocsNoteConfig failed: {e}")
		assert False, f"MkdocsNoteConfig failed: {e}"

	# Test plugin module
	try:
		from mkdocs_note.plugin import MkdocsNotePlugin

		plugin = MkdocsNotePlugin()
		assert plugin is not None
		print("✅ MkdocsNotePlugin works")
	except Exception as e:
		print(f"❌ MkdocsNotePlugin failed: {e}")
		assert False, f"MkdocsNotePlugin failed: {e}"

	# Test utils.meta module
	try:
		from mkdocs_note.utils.meta import (
			validate_frontmatter,
			extract_date,
			extract_title,
		)

		assert validate_frontmatter is not None
		assert extract_date is not None
		assert extract_title is not None
		print("✅ utils.meta works")
	except Exception as e:
		print(f"❌ utils.meta failed: {e}")
		assert False, f"utils.meta failed: {e}"

	# Test utils.scanner module
	try:
		from mkdocs_note.utils.scanner import scan_notes

		assert scan_notes is not None
		print("✅ utils.scanner works")
	except Exception as e:
		print(f"❌ utils.scanner failed: {e}")
		assert False, f"utils.scanner failed: {e}"

	# Test graph module
	try:
		from mkdocs_note.graph import Graph

		assert Graph is not None
		print("✅ Graph works")
	except Exception as e:
		print(f"❌ Graph failed: {e}")
		assert False, f"Graph failed: {e}"


def test_plugin_entry_point():
	"""Test that plugin entry point is properly configured."""
	print("Testing plugin entry point...")

	try:
		from importlib import metadata

		entry_points = metadata.entry_points()

		# Try to find mkdocs.plugins entry points
		mkdocs_plugins = None
		if hasattr(entry_points, "select"):
			# Python 3.10+
			mkdocs_plugins = entry_points.select(group="mkdocs.plugins")
		else:
			# Python 3.9
			mkdocs_plugins = entry_points.get("mkdocs.plugins", [])

		# Check if mkdocs-note plugin is registered
		plugin_found = False
		for ep in mkdocs_plugins:
			if ep.name == "mkdocs-note":
				plugin_found = True
				break

		assert plugin_found, "mkdocs-note plugin not found in entry points"
		print("✅ Plugin entry point is properly configured")

	except Exception as e:
		print(f"❌ Plugin entry point test failed: {e}")
		assert False, f"Plugin entry point test failed: {e}"


def test_cli_entry_point():
	"""Test that CLI entry point is properly configured."""
	print("Testing CLI entry point...")

	try:
		from importlib import metadata

		entry_points = metadata.entry_points()

		# Try to find console_scripts entry points
		console_scripts = None
		if hasattr(entry_points, "select"):
			# Python 3.10+
			console_scripts = entry_points.select(group="console_scripts")
		else:
			# Python 3.9
			console_scripts = entry_points.get("console_scripts", [])

		# Check if mkdocs-note CLI is registered
		cli_found = False
		for ep in console_scripts:
			if ep.name == "mkdocs-note":
				cli_found = True
				break

		assert cli_found, "mkdocs-note CLI not found in entry points"
		print("✅ CLI entry point is properly configured")

	except Exception as e:
		print(f"❌ CLI entry point test failed: {e}")
		assert False, f"CLI entry point test failed: {e}"


def test_version():
	"""Test that package version can be retrieved."""
	print("Testing package version...")

	try:
		from importlib import metadata

		version = metadata.version("mkdocs-note")
		assert version is not None
		assert len(version) > 0
		print(f"✅ Package version: {version}")

	except Exception as e:
		print(f"❌ Version retrieval failed: {e}")
		assert False, f"Version retrieval failed: {e}"


def run_all_tests():
	"""Run all smoke tests."""
	print("\n" + "=" * 60)
	print("Running MkDocs-Note Smoke Tests")
	print("=" * 60 + "\n")

	tests = [
		test_package_import,
		test_core_modules,
		test_plugin_entry_point,
		test_cli_entry_point,
		test_version,
	]

	failed_tests = []

	for test in tests:
		try:
			test()
		except AssertionError as e:
			failed_tests.append((test.__name__, str(e)))
			print(f"\n❌ Test '{test.__name__}' failed: {e}\n")
		except Exception as e:
			failed_tests.append((test.__name__, str(e)))
			print(f"\n❌ Test '{test.__name__}' raised exception: {e}\n")

	print("\n" + "=" * 60)
	if failed_tests:
		print(f"❌ {len(failed_tests)} test(s) failed:")
		for test_name, error in failed_tests:
			print(f"  - {test_name}: {error}")
		print("=" * 60)
		sys.exit(1)
	else:
		print("✅ All smoke tests passed!")
		print("=" * 60)
		sys.exit(0)


if __name__ == "__main__":
	run_all_tests()
