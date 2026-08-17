import re
import unittest

from click.testing import CliRunner

from mkdocs_note.cli import cli


class TestHelpOptions(unittest.TestCase):
	"""Test that --help and -h options work correctly and produce the same output."""

	def __init__(self, methodName: str = "runTest") -> None:
		super().__init__(methodName)
		self.runner: CliRunner = CliRunner()

	def setUp(self):
		"""Set up the test environment."""
		self.runner = CliRunner()

	def run_cli_command(self, args):
		"""Run a CLI command and return the output.

		Returns tuple of (stdout, stderr, returncode) for compatibility.
		"""
		result = self.runner.invoke(cli, args)
		# Click's CliRunner puts all output in stdout, stderr is usually empty
		return result.output, "", result.exit_code

	def test_help_long_option(self):
		"""Test that --help option works without errors."""
		stdout, _stderr, returncode = self.run_cli_command(["--help"])

		# Should not throw error
		self.assertEqual(
			returncode,
			0,
			f"--help failed with return code {returncode}. stderr: {_stderr}",
		)

		# Should contain help text
		self.assertIn("MkDocs Note CLI", stdout)
		self.assertIn("Commands:", stdout)

	def test_help_short_option(self):
		"""Test that -h option works without errors."""
		stdout, _stderr, returncode = self.run_cli_command(["-h"])

		# Should not throw error
		self.assertEqual(
			returncode,
			0,
			f"-h failed with return code {returncode}. stderr: {_stderr}",
		)

		# Should contain help text
		self.assertIn("MkDocs Note CLI", stdout)
		self.assertIn("Commands:", stdout)

	def test_help_options_equal(self):
		"""Test that --help and -h produce the same output."""
		stdout_long, _stderr_long, _ = self.run_cli_command(["--help"])
		stdout_short, _stderr_short, _ = self.run_cli_command(["-h"])

		# Both should produce the same output
		self.assertEqual(
			stdout_long, stdout_short, "--help and -h should produce identical output"
		)

	def test_version_option(self):
		"""Test that --version option works."""
		stdout, _stderr, returncode = self.run_cli_command(["--version"])

		# Should not throw error
		self.assertEqual(
			returncode,
			0,
			f"--version failed with return code {returncode}. stderr: {_stderr}",
		)

		# Should contain version information
		# Version output format is "cli, version X.Y.Z"
		self.assertIn("version", stdout.lower())
		# Should contain version number pattern
		self.assertTrue(
			re.search(r"\d+\.\d+\.\d+", stdout),
			f"No version number found in: {stdout}",
		)

	def test_help_with_subcommand(self):
		"""Test that help works with subcommands."""
		# Test with 'new' command
		stdout, _stderr, returncode = self.run_cli_command(["new", "--help"])
		self.assertEqual(
			returncode,
			0,
			f"new --help failed with return code {returncode}. stderr: {_stderr}",
		)
		self.assertIn("Create a new note", stdout)

		# Test with 'new' command using -h
		stdout_h, stderr_h, returncode_h = self.run_cli_command(["new", "-h"])
		self.assertEqual(
			returncode_h,
			0,
			f"new -h failed with return code {returncode_h}. stderr: {stderr_h}",
		)
		self.assertIn("Create a new note", stdout_h)

		# Both should produce the same output
		self.assertEqual(
			stdout, stdout_h, "new --help and new -h should produce identical output"
		)

	def test_notion_sync_help_images_and_resume(self):
		"""3.3.0: --images / --no-resume; --no-images removed."""
		stdout, _stderr, returncode = self.run_cli_command(["notion-sync", "--help"])
		self.assertEqual(returncode, 0)
		self.assertIn("--images", stdout)
		self.assertIn("--no-resume", stdout)
		self.assertNotIn("--no-images", stdout)

		stdout_ns, _stderr_ns, code_ns = self.run_cli_command(["ns", "--help"])
		self.assertEqual(code_ns, 0)
		self.assertIn("--images", stdout_ns)
		self.assertNotIn("--no-images", stdout_ns)

	def test_ns_help_matches_notion_sync_options(self):
		"""Alias ``ns --help`` must include the same option help as notion-sync."""
		stdout_ns, _stderr_ns, code_ns = self.run_cli_command(["ns", "--help"])
		stdout_full, _stderr_full, code_full = self.run_cli_command(
			["notion-sync", "--help"]
		)
		self.assertEqual(code_ns, 0)
		self.assertEqual(code_full, 0)
		self.assertIn("Process all nav pages", stdout_ns)
		self.assertIn("[upload|site]", stdout_ns)
		self.assertIn("resume checkpoint", stdout_ns)

		def options_block(text: str) -> str:
			idx = text.find("Options:")
			self.assertGreaterEqual(idx, 0, f"no Options section in:\n{text}")
			return text[idx:]

		self.assertEqual(options_block(stdout_ns), options_block(stdout_full))

	def test_help_with_all_commands(self):
		"""Test that help works for all commands."""
		commands = ["new", "remove", "rm", "move", "mv", "clean"]

		for cmd in commands:
			with self.subTest(command=cmd):
				stdout, _stderr, returncode = self.run_cli_command([cmd, "--help"])
				self.assertEqual(
					returncode,
					0,
					f"{cmd} --help failed with return code {returncode}",
				)
				# Should contain help text (not empty)
				self.assertTrue(len(stdout) > 50, f"{cmd} help text too short")


if __name__ == "__main__":
	unittest.main()
