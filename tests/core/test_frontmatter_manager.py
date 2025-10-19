"""
Tests for frontmatter management system.
"""

import pytest
from mkdocs_note.utils.dataps.frontmatter.handlers import (
	MetadataField,
	MetadataRegistry,
	FrontmatterParser,
	FrontmatterManager,
	get_registry,
	register_field,
)
from mkdocs_note.utils.dataps.meta import NoteFrontmatter


class TestMetadataField:
	"""Tests for MetadataField"""

	def test_field_creation(self):
		"""Test creating a metadata field"""
		field = MetadataField(
			name="test_field",
			field_type=str,
			default="default_value",
			required=True,
			description="Test field",
		)

		assert field.name == "test_field"
		assert field.field_type is str
		assert field.default == "default_value"
		assert field.required is True
		assert field.description == "Test field"

	def test_field_validation_success(self):
		"""Test field validation with valid value"""
		field = MetadataField(name="test", field_type=str, required=False)
		assert field.validate("test_value") is True
		assert field.validate(None) is True

	def test_field_validation_type_error(self):
		"""Test field validation with wrong type"""
		field = MetadataField(name="test", field_type=str, required=False)
		assert field.validate(123) is False

	def test_field_validation_required_error(self):
		"""Test field validation with required field missing"""
		field = MetadataField(name="test", field_type=str, required=True)
		assert field.validate(None) is False

	def test_field_validation_custom_validator(self):
		"""Test field validation with custom validator"""

		def is_positive(value):
			return value > 0

		field = MetadataField(
			name="test", field_type=int, required=False, validator=is_positive
		)

		assert field.validate(10) is True
		assert field.validate(-5) is False


class TestMetadataRegistry:
	"""Tests for MetadataRegistry"""

	def test_default_fields_registered(self):
		"""Test that default fields are registered"""
		registry = MetadataRegistry()

		assert registry.get_field("date") is not None
		assert registry.get_field("permalink") is not None
		assert registry.get_field("publish") is not None

	def test_register_new_field(self):
		"""Test registering a new field"""
		registry = MetadataRegistry()

		field = MetadataField(name="custom_field", field_type=str)
		registry.register(field)

		assert registry.get_field("custom_field") is not None

	def test_register_duplicate_field_error(self):
		"""Test that registering duplicate field raises error"""
		registry = MetadataRegistry()

		field1 = MetadataField(name="test", field_type=str)
		field2 = MetadataField(name="test", field_type=int)

		registry.register(field1)

		with pytest.raises(ValueError):
			registry.register(field2)

	def test_unregister_field(self):
		"""Test unregistering a field"""
		registry = MetadataRegistry()

		field = MetadataField(name="temp_field", field_type=str)
		registry.register(field)

		assert registry.get_field("temp_field") is not None

		registry.unregister("temp_field")

		assert registry.get_field("temp_field") is None

	def test_get_all_fields(self):
		"""Test getting all registered fields"""
		registry = MetadataRegistry()

		all_fields = registry.get_all_fields()

		assert "date" in all_fields
		assert "permalink" in all_fields
		assert "publish" in all_fields

	def test_get_default_values(self):
		"""Test getting default values"""
		registry = MetadataRegistry()

		defaults = registry.get_default_values()

		assert defaults["date"] is None
		assert defaults["permalink"] is None
		assert defaults["publish"] is True

	def test_validate_data_success(self):
		"""Test validating data successfully"""
		registry = MetadataRegistry()

		data = {"date": "2024-01-01", "permalink": "/test", "publish": True}

		is_valid, errors = registry.validate_data(data)

		assert is_valid is True
		assert len(errors) == 0

	def test_validate_data_type_error(self):
		"""Test validating data with type error"""
		registry = MetadataRegistry()

		data = {
			"date": "2024-01-01",
			"publish": "not_a_boolean",  # Should be bool
		}

		is_valid, errors = registry.validate_data(data)

		assert is_valid is False
		assert len(errors) > 0


class TestFrontmatterParser:
	"""Tests for FrontmatterParser"""

	def test_parse_with_frontmatter(self):
		"""Test parsing content with frontmatter"""
		parser = FrontmatterParser()

		content = """---
date: '2024-01-01'
title: Test
publish: true
---

# Test Content

This is a test."""

		frontmatter, body = parser.parse(content)

		assert frontmatter["date"] == "2024-01-01"
		assert frontmatter["title"] == "Test"
		assert frontmatter["publish"] is True
		assert "# Test Content" in body

	def test_parse_without_frontmatter(self):
		"""Test parsing content without frontmatter"""
		parser = FrontmatterParser()

		content = """# Test Content

This is a test."""

		frontmatter, body = parser.parse(content)

		assert frontmatter == {}
		assert body == content

	def test_parse_invalid_yaml(self):
		"""Test parsing content with invalid YAML"""
		parser = FrontmatterParser()

		content = """---
invalid: yaml: structure:
---

# Test Content"""

		frontmatter, body = parser.parse(content)

		# Should return empty frontmatter and original content
		assert frontmatter == {}
		assert body == content

	def test_generate_frontmatter(self):
		"""Test generating content with frontmatter"""
		parser = FrontmatterParser()

		frontmatter = {"date": "2024-01-01", "title": "Test", "publish": True}

		body = "# Test Content\n\nThis is a test."

		content = parser.generate(frontmatter, body)

		assert "---" in content
		assert "date: 2024-01-01" in content or "date: '2024-01-01'" in content
		assert "title: Test" in content
		assert "publish: true" in content
		assert "# Test Content" in content

	def test_update_frontmatter_merge(self):
		"""Test updating frontmatter with merge"""
		parser = FrontmatterParser()

		original_content = """---
date: '2024-01-01'
title: Original
---

# Content"""

		updates = {"title": "Updated", "new_field": "new_value"}

		updated_content = parser.update_frontmatter(
			original_content, updates, merge=True
		)

		updated_fm, _ = parser.parse(updated_content)

		assert updated_fm["date"] == "2024-01-01"  # Original preserved
		assert updated_fm["title"] == "Updated"  # Updated
		assert updated_fm["new_field"] == "new_value"  # Added

	def test_update_frontmatter_replace(self):
		"""Test updating frontmatter with replace"""
		parser = FrontmatterParser()

		original_content = """---
date: 2024-01-01
title: Original
---

# Content"""

		updates = {"title": "Updated"}

		updated_content = parser.update_frontmatter(
			original_content, updates, merge=False
		)

		updated_fm, _ = parser.parse(updated_content)

		assert "date" not in updated_fm  # Original removed
		assert updated_fm["title"] == "Updated"  # Only new data

	def test_remove_frontmatter(self):
		"""Test removing frontmatter"""
		parser = FrontmatterParser()

		content = """---
date: 2024-01-01
---

# Content"""

		body_only = parser.remove_frontmatter(content)

		assert "---" not in body_only
		assert "date" not in body_only
		assert "# Content" in body_only


class TestFrontmatterManager:
	"""Tests for FrontmatterManager"""

	def test_create_default_frontmatter(self):
		"""Test creating default frontmatter"""
		manager = FrontmatterManager()

		frontmatter = manager.create_default_frontmatter()

		assert frontmatter["date"] is None
		assert frontmatter["permalink"] is None
		assert frontmatter["publish"] is True

	def test_create_default_frontmatter_with_custom_values(self):
		"""Test creating default frontmatter with custom values"""
		manager = FrontmatterManager()

		custom_values = {"date": "2024-01-01", "custom_field": "custom_value"}

		frontmatter = manager.create_default_frontmatter(custom_values)

		assert frontmatter["date"] == "2024-01-01"
		assert frontmatter["custom_field"] == "custom_value"
		assert frontmatter["publish"] is True  # Default value

	def test_create_note_content_valid(self):
		"""Test creating note content with valid frontmatter"""
		manager = FrontmatterManager()

		frontmatter = {"date": "2024-01-01", "publish": True}

		body = "# Test Note"

		content, errors = manager.create_note_content(frontmatter, body, validate=True)

		assert len(errors) == 0
		assert "---" in content
		assert "# Test Note" in content

	def test_register_custom_field(self):
		"""Test registering a custom field"""
		manager = FrontmatterManager()

		custom_field = MetadataField(name="author", field_type=str, default="Anonymous")

		manager.register_field(custom_field)

		field_info = manager.get_field_info("author")

		assert field_info is not None
		assert field_info.name == "author"
		assert field_info.default == "Anonymous"

	def test_list_all_fields(self):
		"""Test listing all registered fields"""
		manager = FrontmatterManager()

		all_fields = manager.list_all_fields()

		assert "date" in all_fields
		assert "permalink" in all_fields
		assert "publish" in all_fields


class TestNoteFrontmatter:
	"""Tests for NoteFrontmatter data class"""

	def test_create_frontmatter(self):
		"""Test creating NoteFrontmatter"""
		fm = NoteFrontmatter(
			date="2024-01-01",
			permalink="/test",
			publish=True,
			custom={"author": "Test Author"},
		)

		assert fm.date == "2024-01-01"
		assert fm.permalink == "/test"
		assert fm.publish is True
		assert fm.custom["author"] == "Test Author"

	def test_to_dict(self):
		"""Test converting frontmatter to dictionary"""
		fm = NoteFrontmatter(
			date="2024-01-01",
			permalink="/test",
			publish=False,
			custom={"author": "Test"},
		)

		data = fm.to_dict()

		assert data["date"] == "2024-01-01"
		assert data["permalink"] == "/test"
		assert data["publish"] is False
		assert data["author"] == "Test"

	def test_from_dict(self):
		"""Test creating frontmatter from dictionary"""
		data = {
			"date": "2024-01-01",
			"permalink": "/test",
			"publish": True,
			"author": "Test Author",
			"tags": ["tag1", "tag2"],
		}

		fm = NoteFrontmatter.from_dict(data)

		assert fm.date == "2024-01-01"
		assert fm.permalink == "/test"
		assert fm.publish is True
		assert fm.custom["author"] == "Test Author"
		assert fm.custom["tags"] == ["tag1", "tag2"]

	def test_to_dict_none_values(self):
		"""Test to_dict with None values"""
		fm = NoteFrontmatter(date=None, permalink=None, publish=True)

		data = fm.to_dict()

		# None values should not be included
		assert "date" not in data
		assert "permalink" not in data
		assert data["publish"] is True


class TestGlobalRegistry:
	"""Tests for global registry functions"""

	def test_get_global_registry(self):
		"""Test getting global registry"""
		registry = get_registry()

		assert registry is not None
		assert isinstance(registry, MetadataRegistry)

	def test_register_field_global(self):
		"""Test registering field to global registry"""
		# Register a new field
		field = MetadataField(name="global_test_field", field_type=str)
		register_field(field)

		# Check field was registered
		assert get_registry().get_field("global_test_field") is not None

		# Cleanup
		get_registry().unregister("global_test_field")
