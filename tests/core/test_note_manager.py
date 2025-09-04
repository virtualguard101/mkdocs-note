import unittest
import sys
import os
import datetime
import frontmatter
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call, mock_open

# Add src to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))

from mkdocs.structure.files import File
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig
from mkdocs_note.core.note_manager import (
    NoteLinkedMap,
    init_note_path,
    process_notes_path_node,
    set_note_permalink,
    set_note_uri,
    create_new_note,
    transform_notes_links,
    insert_recent_notes,
)
from mkdocs_note.core.file_manager import FileLinkedNode

class TestNoteManager(unittest.TestCase):

    def setUp(self):
        self.file = Mock(spec=File)
        self.file.src_uri = "test.md"

    def test_note_linked_map_initialization(self):
        note_map = NoteLinkedMap(self.file)
        self.assertIs(note_map.node, self.file)
        self.assertEqual(note_map.links, {})
        self.assertIsNone(note_map.inverse_links)

    def test_note_linked_map_clear_links(self):
        note_map = NoteLinkedMap(self.file)
        other_file = Mock(spec=File)
        other_node = FileLinkedNode(other_file)
        other_node.remove = MagicMock()
        note_map.links['some_uri'] = other_node
        note_map.inverse_links = "placeholder"

        note_map.clear_links()

        other_node.remove.assert_called_once()
        self.assertEqual(note_map.links, {})
        self.assertIsNone(note_map.inverse_links)

    @patch('pathlib.Path.mkdir')
    @patch('pathlib.Path.exists')
    def test_init_note_path(self, mock_exists, mock_mkdir):
        mock_exists.return_value = False
        path = Path("/fake/dir")
        
        result = init_note_path(path)
        
        self.assertEqual(result, 0)
        self.assertEqual(mock_exists.call_count, 2)
        mock_mkdir.assert_has_calls([
            call(parents=True, exist_ok=True),
            call(parents=True, exist_ok=True)
        ], any_order=True)

    def test_process_notes_path_node(self):
        self.file.src_uri = "notes/topic/note1.md"
        self.assertEqual(process_notes_path_node(self.file), ["notes", "topic", "note1"])

        self.file.src_uri = "/notes/topic/note2.md"
        self.assertEqual(process_notes_path_node(self.file), ["notes", "topic", "note2"])

        self.file.src_uri = "note3.md"
        self.assertEqual(process_notes_path_node(self.file), ["note3"])

    def test_set_note_permalink(self):
        self.file.src_uri = "notes/topic/note1.md"
        self.assertEqual(set_note_permalink(self.file), ["notes", "topic-note1"])

        self.file.src_uri = "root/single.md"
        self.assertEqual(set_note_permalink(self.file), ["root", "single"])

        self.file.src_uri = "justone.md"
        self.assertEqual(set_note_permalink(self.file), [])

    def test_set_note_uri(self):
        self.file.dest_uri = "old.html"
        self.file.url = "/old.html"
        self.file.abs_dest_path = "/path/to/old.html"
        
        set_note_uri(self.file, "new.html")
        self.assertEqual(self.file.dest_uri, "new.html")
        self.assertFalse(hasattr(self.file, 'url'))
        self.assertFalse(hasattr(self.file, 'abs_dest_path'))

        # Test with a callable
        set_note_uri(self.file, lambda uri: uri.replace('.html', '.php'))
        self.assertEqual(self.file.dest_uri, 'new.php')

    @patch('frontmatter.dump')
    @patch('builtins.open', new_callable=mock_open)
    @patch('frontmatter.load')
    @patch('pathlib.Path.exists')
    def test_create_new_note(self, mock_path_exists, mock_fm_load, mock_open_file, mock_fm_dump):
        mock_path_exists.return_value = True
        mock_post = frontmatter.Post(content="", metadata={'title': 'template_title'})
        mock_fm_load.return_value = mock_post

        note_path = Path("/notes/root/new_note.md")
        root_path = "/notes/root"
        template_path = "/templates/note.md"
        
        res = create_new_note(note_path, root_path, template_path)
        
        self.assertEqual(res, 0)
        mock_fm_load.assert_called_with(Path(template_path))
        mock_open_file.assert_called_with(note_path, 'w', encoding='utf-8')
        mock_fm_dump.assert_called()

        args, _ = mock_fm_dump.call_args
        dumped_post = args[0]
        self.assertIn('permalink', dumped_post)
        self.assertIn('date', dumped_post)
        self.assertEqual(dumped_post['title'], 'template_title')

'''
    def test_transform_notes_links(self):
        markdown = "This is a link to [[another_note]]. And here's one with a heading [[another_note#section]]."
        
        page_file = File('current.md', 'docs/', 'site/', False)
        page = Page('Current Page', page_file, {})
        
        another_note_file = File('another_note.md', 'docs/', 'site/', False)
        
        note_link_name_map = {'another_note.md': another_note_file}
        note_link_path_map = {
            'docs/current.md': NoteLinkedMap(page_file),
            'docs/another_note.md': NoteLinkedMap(another_note_file)
        }
        note_link_path_map['docs/another_note.md'].inverse_links = FileLinkedNode(page_file)

        mock_config = Mock(spec=MkDocsConfig)
        mock_config.mdx_configs = {
            'toc': {
                'slugify': lambda x, y: x.lower().replace(' ', '-'),
                'separator': '-'
            }
        }
        
        transformed_md = transform_notes_links(markdown, page, mock_config, note_link_name_map, note_link_path_map)
        
        self.assertIn('[another_note](../another_note.md)', transformed_md)
        self.assertIn('[another_note > section](../another_note.md#section)', transformed_md)

    def test_insert_recent_notes(self):
        markdown = "Some content
<!-- RECENT NOTES -->
Some other content"
        
        note1 = File('note1.md', 'docs/', 'site/', False)
        note1.url = '/note1/'
        note1.note_date = datetime.datetime(2023, 1, 1)

        note2 = File('note2.md', 'docs/', 'site/', False)
        note2.url = '/note2/'
        note2.note_date = datetime.datetime(2023, 1, 2)
        
        note_list = {'note1.md': note1, 'note2.md': note2}
        
        result_md = insert_recent_notes(markdown, note_list)

        self.assertIn('<a href="/note1/">note1</a><small>2023-01-01</small>', result_md)
        self.assertIn('<a href="/note2/">note2</a><small>2023-01-02</small>', result_md)
        self.assertNotIn('<!-- RECENT NOTES -->', result_md)

if __name__ == '__main__':
    unittest.main()
'''