import unittest
import sys
import os
from unittest.mock import Mock, patch

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs.structure.files import File
from mkdocs_note.core.file_manager import FileLinkedNode, process_attachment

class TestFileLinkedNode(unittest.TestCase):

    def setUp(self):
        # Create mock files for use in tests
        self.file1 = File('page1.md', 'docs', 'site', False)
        self.file2 = File('page2.md', 'docs', 'site', False)
        self.file3 = File('page3.md', 'docs', 'site', False)
        
        # Create nodes
        self.node1 = FileLinkedNode(self.file1)
        self.node2 = FileLinkedNode(self.file2)
        self.node3 = FileLinkedNode(self.file3)

    def test_initialization(self):
        self.assertIs(self.node1.file, self.file1)
        self.assertIsNone(self.node1.prev)
        self.assertIsNone(self.node1.next)

    def test_insert_single_node(self):
        # Insert node2 after node1
        self.node2.insert(self.node1)
        
        self.assertIs(self.node1.next, self.node2)
        self.assertIs(self.node2.prev, self.node1)
        self.assertIsNone(self.node1.prev)
        self.assertIsNone(self.node2.next)

    def test_insert_middle_node(self):
        # Initial list: node1 <-> node2
        self.node2.insert(self.node1)
        
        # Insert node3 between node1 and node2
        self.node3.insert(self.node1)
        
        self.assertIs(self.node1.next, self.node3)
        self.assertIs(self.node3.prev, self.node1)
        self.assertIs(self.node3.next, self.node2)
        self.assertIs(self.node2.prev, self.node3)

    def test_remove_middle_node(self):
        # Initial list: node1 <-> node3 <-> node2
        self.node2.insert(self.node1)
        self.node3.insert(self.node1)
        
        # Remove node3
        self.node3.remove()
        
        self.assertIs(self.node1.next, self.node2)
        self.assertIs(self.node2.prev, self.node1)
        self.assertIsNone(self.node3.prev)
        self.assertIsNone(self.node3.next)

    def test_remove_first_node(self):
        # Initial list: node1 <-> node2 -> node3
        self.node2.insert(self.node1)
        self.node3.insert(self.node2)

        # Remove node1
        self.node1.remove()

        self.assertIs(self.node2.prev, None)
        self.assertIs(self.node3.prev, self.node2)
        self.assertIs(self.node2.next, self.node3)

    def test_remove_last_node(self):
        # Initial list: node1 <-> node2 -> node3
        self.node2.insert(self.node1)
        self.node3.insert(self.node2)

        # Remove node3
        self.node3.remove()
        
        self.assertIs(self.node2.next, None)
        self.assertIs(self.node1.next, self.node2)
        self.assertIs(self.node2.prev, self.node1)

class TestProcessAttachment(unittest.TestCase):

    @patch('mkdocs_note.core.note_manager.set_note_uri')
    def test_process_attachment(self, mock_set_note_uri):
        # Create a mock file. It doesn't need many attributes because we are mocking set_note_uri
        mock_file = File('image.png', 'docs', 'site', use_directory_urls=False)
        
        # Create a mock config object for PluginConfig
        mock_config = Mock()
        mock_config.attachment_path = 'assets/attachments'
        
        # Call the function to be tested
        process_attachment(mock_file, mock_config)

        # Assert that set_note_uri was called correctly
        self.assertTrue(mock_set_note_uri.called)
        
        # Get the arguments passed to the mock
        args, kwargs = mock_set_note_uri.call_args
        
        # Check the file argument
        self.assertIs(args[0], mock_file)
        self.assertEqual(len(args), 2)
        
        # Get the transform function
        transform_func = args[1]
        self.assertTrue(callable(transform_func))
        
        # Test the transform function's behavior
        uri_with_path = 'some/prefix/assets/attachments/image.png'
        expected_transformed_uri = 'assets/attachments/image.png'
        self.assertEqual(transform_func(uri_with_path), expected_transformed_uri)
        
        uri_without_path = 'another/path/image.png'
        self.assertEqual(transform_func(uri_without_path), uri_without_path)
        
        uri_with_value_error = 'no_path_here.png'
        self.assertEqual(transform_func(uri_with_value_error), uri_with_value_error)

if __name__ == '__main__':
    unittest.main()