#!/usr/bin/env python3
"""
Smoke test for mkdocs-note package.
This script performs basic validation to ensure the package was built correctly
and can be imported and used without critical errors.

This test is designed to run in CI/CD environments after package building
and before publishing to PyPI.
"""

import sys
import os
from pathlib import Path


def test_package_import():
    """Test that the main package can be imported."""
    print("Testing package import...")
    
    try:
        import mkdocs_note
        print("✅ mkdocs_note package imported successfully")
        assert True
    except ImportError as e:
        print(f"❌ Failed to import mkdocs_note: {e}")
        assert False, f"Failed to import mkdocs_note: {e}"


def test_core_modules():
    """Test that core modules can be imported."""
    print("Testing core modules...")
    
    modules_to_test = [
        ('mkdocs_note.config', 'PluginConfig'),
        ('mkdocs_note.logger', 'Logger'),
        ('mkdocs_note.utils.file_manager', 'NoteScanner'),
        ('mkdocs_note.utils.file_manager', 'AssetScanner'),
        ('mkdocs_note.utils.data_models', 'NoteInfo'),
        ('mkdocs_note.utils.notes.note_manager', 'NoteProcessor'),
        ('mkdocs_note.utils.notes.note_creator', 'NoteCreator'),
        ('mkdocs_note.utils.notes.note_initializer', 'NoteInitializer'),
        ('mkdocs_note.utils.assets.assets_manager', 'AssetsProcessor'),
        ('mkdocs_note.plugin', 'MkdocsNotePlugin'),
    ]
    
    all_passed = True
    
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✅ {module_name}.{class_name} imported successfully")
        except (ImportError, AttributeError) as e:
            print(f"❌ Failed to import {module_name}.{class_name}: {e}")
            all_passed = False
    
    assert all_passed, "Some core modules failed to import"


def test_basic_functionality():
    """Test basic functionality of key components."""
    print("Testing basic functionality...")
    
    all_passed = True
    
    # Test PluginConfig
    try:
        from mkdocs_note.config import PluginConfig
        config = PluginConfig()
        assert hasattr(config, 'enabled')
        assert hasattr(config, 'max_notes')
        print("✅ PluginConfig basic functionality works")
    except Exception as e:
        print(f"❌ PluginConfig functionality failed: {e}")
        all_passed = False
    
    # Test Logger
    try:
        from mkdocs_note.logger import Logger
        logger = Logger()
        logger.info("Smoke test message")
        print("✅ Logger basic functionality works")
    except Exception as e:
        print(f"❌ Logger functionality failed: {e}")
        all_passed = False
    
    # Test NoteScanner
    try:
        from mkdocs_note.utils.file_manager import NoteScanner
        from mkdocs_note.config import PluginConfig
        from mkdocs_note.logger import Logger
        
        config = PluginConfig()
        logger = Logger()
        scanner = NoteScanner(config, logger)
        print("✅ NoteScanner basic functionality works")
    except Exception as e:
        print(f"❌ NoteScanner functionality failed: {e}")
        all_passed = False
    
    # Test data models
    try:
        from mkdocs_note.utils.data_models import NoteInfo, AssetsInfo
        print("✅ Data models basic functionality works")
    except Exception as e:
        print(f"❌ Data models functionality failed: {e}")
        all_passed = False
    
    # Test NoteProcessor
    try:
        from mkdocs_note.utils.notes.note_manager import NoteProcessor
        from mkdocs_note.config import PluginConfig
        from mkdocs_note.logger import Logger
        
        config = PluginConfig()
        logger = Logger()
        processor = NoteProcessor(config, logger)
        print("✅ NoteProcessor basic functionality works")
    except Exception as e:
        print(f"❌ NoteProcessor functionality failed: {e}")
        all_passed = False
    
    # Test MkdocsNotePlugin
    try:
        from mkdocs_note.plugin import MkdocsNotePlugin
        from mkdocs_note.config import PluginConfig
        
        plugin = MkdocsNotePlugin()
        plugin.config = PluginConfig()
        assert hasattr(plugin, 'plugin_enabled')
        print("✅ MkdocsNotePlugin basic functionality works")
    except Exception as e:
        print(f"❌ MkdocsNotePlugin functionality failed: {e}")
        all_passed = False
    
    # Test NoteCreator
    try:
        from mkdocs_note.utils.notes.note_creator import NoteCreator
        from mkdocs_note.config import PluginConfig
        from mkdocs_note.logger import Logger
        
        config = PluginConfig()
        logger = Logger()
        creator = NoteCreator(config, logger)
        print("✅ NoteCreator basic functionality works")
    except Exception as e:
        print(f"❌ NoteCreator functionality failed: {e}")
        all_passed = False
    
    # Test NoteInitializer
    try:
        from mkdocs_note.utils.notes.note_initializer import NoteInitializer
        from mkdocs_note.config import PluginConfig
        from mkdocs_note.logger import Logger
        
        config = PluginConfig()
        logger = Logger()
        initializer = NoteInitializer(config, logger)
        print("✅ NoteInitializer basic functionality works")
    except Exception as e:
        print(f"❌ NoteInitializer functionality failed: {e}")
        all_passed = False
    
    # Test AssetsProcessor
    try:
        from mkdocs_note.utils.assets.assets_manager import AssetsProcessor
        from mkdocs_note.config import PluginConfig
        from mkdocs_note.logger import Logger
        
        config = PluginConfig()
        logger = Logger()
        processor = AssetsProcessor(config, logger)
        print("✅ AssetsProcessor basic functionality works")
    except Exception as e:
        print(f"❌ AssetsProcessor functionality failed: {e}")
        all_passed = False
    
    assert all_passed, "Basic functionality tests failed"


def test_package_metadata():
    """Test that package metadata is accessible."""
    print("Testing package metadata...")
    
    try:
        import mkdocs_note
        # Check if __version__ exists
        if hasattr(mkdocs_note, '__version__'):
            version = mkdocs_note.__version__
            print(f"✅ Package version: {version}")
        else:
            print("⚠️  Package version not found")
        
        # Check if __author__ exists
        if hasattr(mkdocs_note, '__author__'):
            author = mkdocs_note.__author__
            print(f"✅ Package author: {author}")
        else:
            print("⚠️  Package author not found")
        
        assert True
    except Exception as e:
        print(f"❌ Package metadata test failed: {e}")
        assert False, f"Package metadata test failed: {e}"


def main():
    """Run all smoke tests."""
    print("MkDocs-Note Package Smoke Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Python path: {sys.executable}")
    print("=" * 50)
    
    all_passed = True
    
    # Run all tests
    tests = [
        ("Package Import", test_package_import),
        ("Core Modules", test_core_modules),
        ("Basic Functionality", test_basic_functionality),
        ("Package Metadata", test_package_metadata),
    ]
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if not test_func():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All smoke tests passed!")
        print("Package is ready for publishing.")
        return 0
    else:
        print("❌ Some smoke tests failed.")
        print("Package should NOT be published.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
