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

	# Network Graph Configuration
	graph_config = config_opt.Type(
		dict,
		default={
			"enabled": False,
			"name": "title",  # Node naming strategy: "title" or "file_name"
			"debug": False,  # Enable debug logging for graph generation
			"max_full_nodes": 220,  # Max nodes allowed in full graph view before fallback
			"max_full_edges": 400,  # Max edges allowed in full graph view before fallback
			"fallback_hops": 2,  # Hop depth to use when graph is too large
			"label_threshold": 120,  # Hide labels when node count exceeds this value
			"arrow_threshold": 160,  # Hide arrowheads when node count exceeds this value
			"alpha_decay": 0.08,  # Force simulation alphaDecay for faster settling
			"velocity_decay": 0.45,  # Force simulation velocityDecay to damp movement
			"max_ticks": 180,  # Maximum ticks before simulation stops to prevent lockups
		},
	)
	"""Configuration for the network graph visualization.
    
    Available options:
    - name: Node naming strategy ("title" or "file_name")
    - debug: Enable debug logging for graph generation
    """
