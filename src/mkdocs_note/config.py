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
		},
	)
	"""Configuration for the network graph visualization.
    
    Available options:
    - name: Node naming strategy ("title" or "file_name")
    - debug: Enable debug logging for graph generation
    """

	notion_sync = config_opt.Type(
		dict,
		default={
			"docs_dir": "docs",
			"nav_file": "docs/.nav.yml",
			"database_id": "",
			"data_source_id": "",
			"title_property": "页面",
			"tags_property": "标签",
			"site_url": "",
			"state_path": ".notion_sync_state.json",
			"delay": 0.35,
			"local_images": "upload",
			"cache_dir": ".cache/mkdocs-note",
			"allow_cursor_mcp_token": False,
			"silence_mcp_token_warning": False,
		},
	)
	"""Configuration for Notion wiki sync (CLI: ``mkdocs-note notion-sync``).

    Available options:
    - docs_dir: Documentation root (git diff / relative path base)
    - nav_file: Path to awesome-nav ``.nav.yml`` (relative to project root)
    - database_id: Notion wiki database / page ID (or env NOTION_WIKI_DATABASE)
    - data_source_id: Notion data source ID (or env NOTION_WIKI_DATA_SOURCE)
    - title_property: Title property name (default: 页面)
    - tags_property: Multi-select tags property name (default: 标签)
    - site_url: Public site URL for remote image fallbacks
    - state_path: Local page-map JSON path
    - delay: Seconds between Notion API calls
    - local_images: ``upload`` local files, or ``site`` to use MkDocs site URLs
    - cache_dir: Directory for ``--full`` resume checkpoints
    - allow_cursor_mcp_token: Developer-only; allow reading token from Cursor mcp.json
    - silence_mcp_token_warning: Suppress the MCP-token usage warning
    """
