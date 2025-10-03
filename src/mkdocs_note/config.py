from pathlib import Path
from typing import Set
from mkdocs.config import Config
from mkdocs.config import base, config_options as config_opt

class PluginConfig(Config):
    """Configuration class, managing all configuration parameters.
    """
    enabled = config_opt.Type(bool, default=True)
    """Whether the plugin is enabled.
    """

    project_root = config_opt.Type(Path, default=Path(__file__).parent.parent)
    """The root path of the project.
    """

    notes_dir = config_opt.Dir(exists=False, default='docs/notes')
    """The directory of the notes.
    """

    index_file = config_opt.File(exists=False, default='docs/notes/index.md')
    """The index file of the notes.
    """
    
    start_marker = config_opt.Type(str, default='<!-- recent_notes_start -->')
    """The start marker of the recent notes.
    """
    
    end_marker = config_opt.Type(str, default='<!-- recent_notes_end -->')
    """The end marker of the recent notes.
    """
    
    max_notes = config_opt.Type(int, default=11)
    """The maximum number of recent notes.
    """
    
    git_date_format = config_opt.Type(str, default='%a %b %d %H:%M:%S %Y %z')
    """The date format of the git.
    """
    
    output_date_format = config_opt.Type(str, default='%Y-%m-%d %H:%M:%S')
    """The date format of the output.
    """
    
    supported_extensions = config_opt.Type(set, default={'.md', '.ipynb'})
    """The supported extensions of the notes.
    """
    
    exclude_patterns = config_opt.Type(set, default={'index.md', 'README.md'})
    """The patterns to exclude from the notes.
    """
    
    exclude_dirs = config_opt.Type(set, default={'__pycache__', '.git', 'node_modules'})
    """The directories to exclude from the notes.
    """

    cache_size = config_opt.Type(int, default=256)
    """The size of the cache.
    """
    
    use_git_timestamps = config_opt.Type(bool, default=True)
    """Whether to use Git commit timestamps for sorting instead of file system timestamps.
    This is recommended for consistent sorting across different deployment environments.
    """