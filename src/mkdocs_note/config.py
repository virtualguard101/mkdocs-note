from mkdocs.config import Config
from mkdocs.config import config_options as config_opt


class MkdocsNoteConfig(Config):
	"""Configuration class, managing all configuration parameters."""

	enabled = config_opt.Type(bool, default=True)
	"""Whether the plugin is enabled.
    """

	notes_root = config_opt.Dir(exists=False, default="docs")
	"""The directory of the notes, which defines the plugin's working scope.
    All note scanning, file operations, and asset management are limited to this directory.
    """

	recent_notes_config = config_opt.Type(
		dict,
		default={
			"enabled": False,
			"insert_marker": "<!-- recent_notes -->",
			"insert_num": 10,
		},
	)
	"""Configuration for the recent notes.
    Available options:
    - enabled: Whether to enable the recent notes
    - insert_marker: The marker to insert the recent notes
    - insert_num: The number of recent notes to insert
    """

	notes_template = config_opt.Type(str, default="overrides/templates/default.md")
	"""The template of the notes.
    """

	# Network Graph Configuration
	graph_config = config_opt.Type(
		dict,
		default={
			"enabled": False,
			"name": "title",  # Node naming strategy: "title" or "file_name"
			"debug": False,  # Enable debug logging for graph generation
		},
	)
	"""Configuration for the network graph visualization.
    
    Available options:
    - name: Node naming strategy ("title" or "file_name")
    - debug: Enable debug logging for graph generation
    """

	# CLI-specific configuration
	supported_extensions = config_opt.Type(list, default=[".md"])
	"""List of supported note file extensions.
    Used by CLI commands to validate note file types.
    """

	exclude_patterns = config_opt.Type(list, default=["index.md", "README.md"])
	"""List of filename patterns to exclude from note management.
    Files matching these patterns will not be created, moved, or managed by CLI commands.
    """

	timestamp_format = config_opt.Type(str, default="%Y-%m-%d %H:%M:%S")
	"""Date format string for timestamp output.
    Uses Python strftime format codes.
    """
