from pathlib import Path
from typing import Dict, Any, Optional
from mkdocs.config import Config
from mkdocs.config import config_options as config_opt
import yaml


class UpperCaseChoice(config_opt.Choice):
	"""A Choice option that automatically converts input to uppercase."""

	def run_validation(self, value):
		"""Convert value to uppercase before validation."""
		if isinstance(value, str):
			value = value.upper()
		return super().run_validation(value)


class PluginConfig(Config):
	"""Configuration class, managing all configuration parameters."""

	enabled = config_opt.Type(bool, default=True)
	"""Whether the plugin is enabled.
    """

	project_root = config_opt.Type(Path, default=Path(__file__).parent.parent)
	"""The root path of the project, which is the absolute benchmark for the path system of the plugin.
    Used for git operations (timestamp calculation) and relative path generation.
    """

	notes_dir = config_opt.Dir(exists=False, default="docs")
	"""The directory of the notes, which defines the plugin's working scope.
    All note scanning, file operations, and asset management are limited to this directory.
    """

	index_file = config_opt.File(exists=False, default="docs/index.md")
	"""The index file of the notes, where recent notes will be inserted.
    Also serves as the relative benchmark for MkDocs URL generation.
    """

	start_marker = config_opt.Type(str, default="<!-- recent_notes_start -->")
	"""The start marker of the recent notes.
    """

	end_marker = config_opt.Type(str, default="<!-- recent_notes_end -->")
	"""The end marker of the recent notes.
    """

	max_notes = config_opt.Type(int, default=10)
	"""The maximum number of recent notes, excluding the index page.
    """

	git_date_format = config_opt.Type(str, default="%a %b %d %H:%M:%S %Y %z")
	"""The date format of the git.
    """

	output_date_format = config_opt.Type(str, default="%Y-%m-%d %H:%M:%S")
	"""The date format of the output.
    """

	supported_extensions = config_opt.Type(set, default={".md", ".ipynb"})
	"""The supported extensions of the notes.
    """

	exclude_patterns = config_opt.Type(set, default={"index.md", "README.md"})
	"""File name patterns to exclude from plugin management.
    Files matching these patterns will not be:
    - Scanned as notes
    - Listed in recent notes
    - Created via 'mkdocs-note new'
    - Moved via 'mkdocs-note move'
    - Managed by asset system
    These patterns only apply within the notes_dir scope.
    """

	exclude_dirs = config_opt.Type(set, default={"__pycache__", ".git", "node_modules"})
	"""Directory names to exclude from note scanning.
    Any note files within these directories will be ignored.
    """

	cache_size = config_opt.Type(int, default=256)
	"""The size of the cache.
    """

	use_git_timestamps = config_opt.Type(bool, default=True)
	"""Whether to use Git commit timestamps for sorting instead of file system timestamps.
    This is recommended for consistent sorting across different deployment environments.
    """

	log_level = UpperCaseChoice(
		choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO"
	)
	"""The logging level for the plugin.
    Controls the verbosity of log messages: DEBUG (most verbose) to CRITICAL (least verbose).
    """

	assets_dir = config_opt.Dir(exists=False, default="docs/notes/assets")
	"""The directory of the assets. [Deprecated after v2.0.0]
    """

	notes_template = config_opt.Type(str, default="overrides/templates/default.md")
	"""The template of the notes.
    """

	timestamp_zone = config_opt.Type(str, default="UTC+0")
	"""The timezone for timestamp display (e.g., 'UTC+0', 'UTC+8', 'UTC-5').
    This ensures consistent timestamp display across different deployment environments.
    """

	# Network Graph Configuration
	enable_network_graph = config_opt.Type(bool, default=False)
	"""Whether to enable the interactive network graph visualization.
    When enabled, an interactive graph showing relationships between notes will be displayed.
    """

	graph_config = config_opt.Type(
		dict,
		default={
			"name": "title",  # Node naming strategy: "title" or "file_name"
			"debug": False,  # Enable debug logging for graph generation
		},
	)
	"""Configuration for the network graph visualization.
    
    Available options:
    - name: Node naming strategy ("title" or "file_name")
    - debug: Enable debug logging for graph generation
    """


def load_config_from_mkdocs_yml(config_path: Optional[Path] = None) -> PluginConfig:
	"""Load plugin configuration from mkdocs.yml file.

	This function parses the mkdocs.yml file and extracts the mkdocs-note plugin
	configuration. If no config file is provided or the plugin is not configured,
	it returns a default PluginConfig instance.

	Args:
	    config_path: Path to the mkdocs.yml file. If None, tries to find it in:
	                1. Current working directory
	                2. Parent directories (up to 3 levels)

	Returns:
	    PluginConfig: A configured PluginConfig instance

	Raises:
	    FileNotFoundError: If the config file is specified but doesn't exist
	    ValueError: If the config file is invalid or cannot be parsed
	"""
	# Try to find mkdocs.yml if not specified
	if config_path is None:
		config_path = _find_mkdocs_yml()

	if config_path is None:
		# No config file found, return default config
		return PluginConfig()

	config_path = Path(config_path)

	if not config_path.exists():
		raise FileNotFoundError(f"Config file not found: {config_path}")

	try:
		with open(config_path, "r", encoding="utf-8") as f:
			# Use UnsafeLoader to handle Python object references in mkdocs.yml
			# This is safe in our context because:
			# 1. We're only reading the project's own configuration file
			# 2. We only extract the plugin configuration, not execute any code
			# 3. MkDocs itself also loads and trusts this file
			mkdocs_config = yaml.load(f, Loader=yaml.UnsafeLoader)
	except yaml.YAMLError as e:
		raise ValueError(f"Failed to parse YAML config file: {e}")
	except Exception as e:
		raise ValueError(f"Failed to read config file: {e}")

	# Extract plugin configuration
	plugin_config_dict = _extract_plugin_config(mkdocs_config)

	# Create PluginConfig instance with extracted config
	config = PluginConfig()

	# Apply user configuration to the config instance
	if plugin_config_dict:
		for key, value in plugin_config_dict.items():
			if hasattr(config, key):
				setattr(config, key, value)

	return config


def _find_mkdocs_yml() -> Optional[Path]:
	"""Find mkdocs.yml file in current or parent directories.

	Searches for mkdocs.yml in:
	1. Current working directory
	2. Up to 3 parent directories

	Returns:
	    Optional[Path]: Path to mkdocs.yml if found, None otherwise
	"""
	current_dir = Path.cwd()

	# Check current directory
	for filename in ["mkdocs.yml", "mkdocs.yaml"]:
		config_path = current_dir / filename
		if config_path.exists():
			return config_path

	# Check parent directories (up to 3 levels)
	for _ in range(3):
		current_dir = current_dir.parent
		for filename in ["mkdocs.yml", "mkdocs.yaml"]:
			config_path = current_dir / filename
			if config_path.exists():
				return config_path

	return None


def _extract_plugin_config(mkdocs_config: Dict[str, Any]) -> Dict[str, Any]:
	"""Extract mkdocs-note plugin configuration from MkDocs config.

	Args:
	    mkdocs_config: The parsed MkDocs configuration dictionary

	Returns:
	    Dict[str, Any]: The plugin configuration dictionary
	"""
	if not mkdocs_config or "plugins" not in mkdocs_config:
		return {}

	plugins = mkdocs_config["plugins"]

	# Handle both list and dict plugin configurations
	if isinstance(plugins, list):
		for plugin in plugins:
			if isinstance(plugin, dict) and "mkdocs-note" in plugin:
				return plugin["mkdocs-note"]
			elif isinstance(plugin, str) and plugin == "mkdocs-note":
				return {}  # Plugin enabled with default config
	elif isinstance(plugins, dict):
		if "mkdocs-note" in plugins:
			return plugins["mkdocs-note"]

	return {}
