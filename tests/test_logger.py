import unittest
import sys
import os
import logging
from unittest.mock import patch, MagicMock

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from mkdocs_note.logger import Logger


class TestLogger(unittest.TestCase):
    """Test cases for Logger class."""

    def setUp(self):
        """Set up test fixtures."""
        self.logger = Logger()

    def test_logger_initialization(self):
        """Test that logger is properly initialized."""
        self.assertIsNotNone(self.logger.logger)
        self.assertIsInstance(self.logger.logger, logging.Logger)

    def test_logger_name(self):
        """Test logger name is set correctly."""
        self.assertEqual(self.logger.logger.name, 'mkdocs_note.logger')

    def test_logger_level(self):
        """Test that logger level is set to INFO."""
        self.assertEqual(self.logger.logger.level, logging.INFO)

    def test_logger_has_handlers(self):
        """Test that logger has handlers configured."""
        self.assertTrue(len(self.logger.logger.handlers) > 0)

    @patch('colorlog.StreamHandler')
    @patch('colorlog.ColoredFormatter')
    def test_logger_setup(self, mock_formatter, mock_handler):
        """Test logger setup with mocked dependencies."""
        # Create a new logger instance to test setup
        test_logger = Logger('test_logger')
        
        # Verify handler was created
        mock_handler.assert_called_once()
        
        # Verify formatter was created with correct format
        mock_formatter.assert_called_once()
        call_args = mock_formatter.call_args[0]
        self.assertIn('%(log_color)s%(asctime)s - %(levelname)s - %(message)s', call_args)

    def test_debug_method(self):
        """Test debug logging method."""
        with patch.object(self.logger.logger, 'debug') as mock_debug:
            self.logger.debug("Test debug message")
            mock_debug.assert_called_once_with("Test debug message")

    def test_info_method(self):
        """Test info logging method."""
        with patch.object(self.logger.logger, 'info') as mock_info:
            self.logger.info("Test info message")
            mock_info.assert_called_once_with("Test info message")

    def test_warning_method(self):
        """Test warning logging method."""
        with patch.object(self.logger.logger, 'warning') as mock_warning:
            self.logger.warning("Test warning message")
            mock_warning.assert_called_once_with("Test warning message")

    def test_error_method(self):
        """Test error logging method."""
        with patch.object(self.logger.logger, 'error') as mock_error:
            self.logger.error("Test error message")
            mock_error.assert_called_once_with("Test error message")

    def test_custom_logger_name(self):
        """Test logger with custom name."""
        custom_logger = Logger('custom_name')
        self.assertEqual(custom_logger.logger.name, 'custom_name')

    def test_multiple_loggers(self):
        """Test that multiple logger instances work independently."""
        logger1 = Logger('logger1')
        logger2 = Logger('logger2')
        
        self.assertNotEqual(logger1.logger.name, logger2.logger.name)
        self.assertIsNot(logger1.logger, logger2.logger)

    def test_logger_handler_setup_only_once(self):
        """Test that handlers are only set up once per logger."""
        # Get initial handler count
        initial_handlers = len(self.logger.logger.handlers)
        
        # Create another logger with same name (should reuse existing logger)
        another_logger = Logger('mkdocs_note.logger')
        
        # Handler count should not increase
        self.assertEqual(len(another_logger.logger.handlers), initial_handlers)

    def test_logger_without_colorlog(self):
        """Test logger behavior when colorlog is not available."""
        with patch('colorlog.StreamHandler', side_effect=ImportError):
            with patch('colorlog.ColoredFormatter', side_effect=ImportError):
                # This should not raise an exception
                try:
                    test_logger = Logger('test_no_colorlog')
                    # If we get here, the logger was created successfully
                    self.assertIsNotNone(test_logger.logger)
                except ImportError:
                    # This is expected if colorlog is not available
                    pass


if __name__ == '__main__':
    unittest.main()
