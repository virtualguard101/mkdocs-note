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

	enable_asset_fallback = config_opt.Type(bool, default=True)
	"""Whether to fallback to original asset paths when assets with processed uri are not found.
    
    When enabled (default: True), if a processed asset file doesn't exist, 
    the original asset path will be preserved instead of being replaced.
    This prevents broken image links when assets haven't been moved to the 
    co-located asset directory structure yet.
    """
