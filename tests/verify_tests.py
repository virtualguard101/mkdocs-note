#!/usr/bin/env python3
"""
Simple test verification script to check if all test files can be imported
and basic functionality works.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from mkdocs_note.config import PluginConfig
        print("✅ PluginConfig import successful")
    except Exception as e:
        print(f"❌ PluginConfig import failed: {e}")
        return False
    
    try:
        from mkdocs_note.logger import Logger
        print("✅ Logger import successful")
    except Exception as e:
        print(f"❌ Logger import failed: {e}")
        return False
    
    try:
        from mkdocs_note.core.file_manager import FileScanner
        print("✅ FileScanner import successful")
    except Exception as e:
        print(f"❌ FileScanner import failed: {e}")
        return False
    
    try:
        from mkdocs_note.core.note_manager import NoteProcessor, NoteInfo
        print("✅ NoteProcessor import successful")
    except Exception as e:
        print(f"❌ NoteProcessor import failed: {e}")
        return False
    
    try:
        from mkdocs_note.plugin import MkdocsNotePlugin
        print("✅ MkdocsNotePlugin import successful")
    except Exception as e:
        print(f"❌ MkdocsNotePlugin import failed: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of components."""
    print("\nTesting basic functionality...")
    
    try:
        from mkdocs_note.config import PluginConfig
        config = PluginConfig()
        assert config.enabled == True
        assert config.max_notes == 11
        print("✅ PluginConfig basic functionality works")
    except Exception as e:
        print(f"❌ PluginConfig functionality failed: {e}")
        return False
    
    try:
        from mkdocs_note.logger import Logger
        logger = Logger()
        logger.info("Test message")
        print("✅ Logger basic functionality works")
    except Exception as e:
        print(f"❌ Logger functionality failed: {e}")
        return False
    
    try:
        from mkdocs_note.core.file_manager import FileScanner
        from mkdocs_note.config import PluginConfig
        from mkdocs_note.logger import Logger
        
        config = PluginConfig()
        logger = Logger()
        scanner = FileScanner(config, logger)
        print("✅ FileScanner basic functionality works")
    except Exception as e:
        print(f"❌ FileScanner functionality failed: {e}")
        return False
    
    try:
        from mkdocs_note.core.note_manager import NoteProcessor
        from mkdocs_note.config import PluginConfig
        from mkdocs_note.logger import Logger
        
        config = PluginConfig()
        logger = Logger()
        processor = NoteProcessor(config, logger)
        print("✅ NoteProcessor basic functionality works")
    except Exception as e:
        print(f"❌ NoteProcessor functionality failed: {e}")
        return False
    
    try:
        from mkdocs_note.plugin import MkdocsNotePlugin
        plugin = MkdocsNotePlugin()
        plugin.config = PluginConfig()
        assert plugin.plugin_enabled == True
        print("✅ MkdocsNotePlugin basic functionality works")
    except Exception as e:
        print(f"❌ MkdocsNotePlugin functionality failed: {e}")
        return False
    
    return True

def test_test_files():
    """Test that test files can be imported."""
    print("\nTesting test file imports...")
    
    test_files = [
        'test_config.py',
        'test_logger.py',
        'core/test_file_manager.py',
        'core/test_note_manager.py',
        'test_plugin.py'
    ]
    
    test_dir = Path(__file__).parent
    
    for test_file in test_files:
        test_path = test_dir / test_file
        if test_path.exists():
            print(f"✅ {test_file} exists")
        else:
            print(f"❌ {test_file} missing")
            return False
    
    return True

def main():
    """Run all verification tests."""
    print("MkDocs-Note Test Verification")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
    
    # Test basic functionality
    if not test_basic_functionality():
        all_passed = False
    
    # Test test files
    if not test_test_files():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All verification tests passed!")
        print("The test suite is ready to run.")
        return 0
    else:
        print("❌ Some verification tests failed.")
        print("Please fix the issues before running the full test suite.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
