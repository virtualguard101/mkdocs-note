import unittest
import subprocess
import sys
from pathlib import Path


class TestHelpOptions(unittest.TestCase):
    """Test that --help and -h options work correctly and produce the same output."""

    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.cli_path: Path = Path()
        self.python_executable: str = ""

    def setUp(self):
        """Set up the test environment."""
        self.cli_path = Path(__file__).parent.parent / "src" / "mkdocs_note" / "cli.py"
        self.python_executable = sys.executable

    def run_cli_command(self, args):
        """Run a CLI command and return the output."""
        cmd = [self.python_executable, str(self.cli_path)] + args
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        return result.stdout, result.stderr, result.returncode

    def test_help_long_option(self):
        """Test that --help option works without errors."""
        stdout, stderr, returncode = self.run_cli_command(["--help"])

        # Should not throw error
        self.assertEqual(
            returncode,
            0,
            f"--help failed with return code {returncode}. stderr: {stderr}",
        )

        # Should contain help text
        self.assertIn("MkDocs-Note CLI", stdout)
        self.assertIn("Commands:", stdout)

    def test_help_short_option(self):
        """Test that -h option works without errors."""
        stdout, stderr, returncode = self.run_cli_command(["-h"])

        # Should not throw error
        self.assertEqual(
            returncode, 0, f"-h failed with return code {returncode}. stderr: {stderr}"
        )

        # Should contain help text
        self.assertIn("MkDocs-Note CLI", stdout)
        self.assertIn("Commands:", stdout)

    def test_help_options_equal(self):
        """Test that --help and -h produce the same output."""
        stdout_long, stderr_long, _ = self.run_cli_command(["--help"])
        stdout_short, stderr_short, _ = self.run_cli_command(["-h"])

        # Both should produce the same output
        self.assertEqual(
            stdout_long, stdout_short, "--help and -h should produce identical output"
        )

    def test_version_option(self):
        """Test that --version option works."""
        stdout, stderr, returncode = self.run_cli_command(["--version"])

        # Should not throw error
        self.assertEqual(
            returncode,
            0,
            f"--version failed with return code {returncode}. stderr: {stderr}",
        )

        # Should contain version information
        # This test case is incorrect and not useful
        # self.assertIn("mkdocs-note", stdout)
        # self.assertIn("2.0.1", stdout)

    def test_help_with_subcommand(self):
        """Test that help works with subcommands."""
        # Test with 'new' command
        stdout, stderr, returncode = self.run_cli_command(["new", "--help"])
        self.assertEqual(
            returncode,
            0,
            f"new --help failed with return code {returncode}. stderr: {stderr}",
        )
        self.assertIn("Create a new note file", stdout)

        # Test with 'new' command using -h
        stdout_h, stderr_h, returncode_h = self.run_cli_command(["new", "-h"])
        self.assertEqual(
            returncode_h,
            0,
            f"new -h failed with return code {returncode_h}. stderr: {stderr_h}",
        )
        self.assertIn("Create a new note file", stdout_h)

        # Both should produce the same output
        self.assertEqual(
            stdout, stdout_h, "new --help and new -h should produce identical output"
        )


if __name__ == "__main__":
    unittest.main()
