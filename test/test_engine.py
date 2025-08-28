import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from mkdocs_note.core.engine import NoteNode, NoteGraph, build_tree, parse_note_links, build_note_graph

class TestNoteNode(unittest.TestCase):
    """测试NoteNode类的属性和行为"""
    
    def test_note_node_creation(self):
        """验证笔记节点创建时的属性初始化"""
        node = NoteNode(Path('/path/to/note.md'))
        self.assertTrue(node.is_note)
        self.assertEqual(node.metadata, {})
        self.assertEqual(node.out_links, [])
        self.assertEqual(node.backlinks, [])

    def test_non_note_node(self):
        """验证非Markdown文件节点的识别"""
        node = NoteNode(Path('/path/to/file.txt'))
        self.assertFalse(node.is_note)

class TestNoteGraph(unittest.TestCase):
    """测试NoteGraph类的图操作功能"""
    
    def test_graph_operations(self):
        """
        验证图结构的基本操作：
        - 添加节点
        - 添加边
        - 获取反链
        """
        graph = NoteGraph()
        node = NoteNode(Path('/note1.md'))
        
        graph.add_node(node)
        self.assertIn(str(node.path.absolute()), graph.nodes)
        
        graph.add_edge(str(node.path.absolute()), '/note2.md')
        self.assertEqual(graph.adjacency_list[str(node.path.absolute())], ['/note2.md'])
        
        backlinks = graph.get_backlinks('/note2.md')
        self.assertEqual(backlinks, [str(node.path.absolute())])

class TestEngineFunctions(unittest.TestCase):
    """测试引擎核心功能函数"""
    
    @patch('mkdocs_note.core.engine.Path')
    def test_build_tree(self, mock_path):
        """验证目录树构建功能，包括隐藏文件过滤"""
        mock_path.is_dir.return_value = True
        mock_path.iterdir.return_value = [
            MagicMock(name='file1.md', is_dir=False, suffix='.md'),
            MagicMock(name='file2.md', is_dir=False, suffix='.md'),  # 添加第二个文件
            MagicMock(name='.hidden', is_dir=False),
            MagicMock(name='subdir', is_dir=True)
        ]
        
        root = build_tree(mock_path)
        # 预期3个子节点：2个文件 + 1个子目录
        self.assertEqual(len(root.children), 3, "应包含2个文件和1个子目录")
        
    @patch('mkdocs_note.core.engine.Path')
    def test_parse_note_links(self, mock_path):
        """验证从Markdown内容解析[[维基链接]]的功能"""
        mock_path.is_file.return_value = True
        mock_path.suffix = '.md'
        mock_path.read_text.return_value = 'Content with [[link1]] and [[link2]]'
        mock_path.parent = Path('/parent')
        
        links = parse_note_links(mock_path)
        self.assertEqual(links, ['/parent/link1', '/parent/link2'])
        
    def test_parse_note_links_permission_error(self):
        """验证处理文件读取权限错误"""
        with patch('mkdocs_note.core.engine.Path') as mock_path:
            mock_path.is_file.return_value = True
            mock_path.suffix = '.md'
            mock_path.read_text.side_effect = PermissionError("Permission denied")
            
            links = parse_note_links(mock_path)
            self.assertEqual(links, [], "权限错误时应返回空链接列表")
    
    def test_build_note_graph(self):
        """验证从笔记树构建图结构的完整流程"""
        # 使用临时目录避免权限问题
        with tempfile.TemporaryDirectory() as tmpdir:
            root_path = Path(tmpdir)
            note1_path = root_path / "note1.md"
            note2_path = root_path / "note2.md"
            
            # 创建测试文件
            note1_path.write_text("[[note2]]")
            note2_path.write_text("Content")
            
            root = NoteNode(root_path)
            child1 = NoteNode(note1_path)
            child2 = NoteNode(note2_path)
            root.add_child(child1)
            root.add_child(child2)
            
            graph = build_note_graph(root)
            self.assertEqual(len(graph.nodes), 3)
            self.assertEqual(
                graph.adjacency_list[str(child1.path.absolute())],
                [str(child2.path.absolute())]
            )
            self.assertEqual(
                child2.backlinks,
                [str(child1.path.absolute())]
            )

if __name__ == '__main__':
    unittest.main()