from mkdocs.config.defaults import MkDocsConfig
from mkdocs.config import base, config_options as config_opt
from mkdocs.config import Config


class PluginConfig(Config):
    """The configuration options for the plugin, written in `mkdocs.yml`.
    """
    enabled = config_opt.Type(bool, default=True)
    """Whether to enable the plugin."""

    notes_root_path = config_opt.Type(str, default='notes')
    """The root path of the notes, relative to the documentation root.

    Example:

        ```yml
        plugins:
        - mkdocs-note:
            notes_root_path: 'notes'
        ```
    """

    notes_template = config_opt.Type(str, default='notes/templates/default.md')
    """The template file to use for new notes.

    Example:

        ```yml
        plugins:
        - mkdocs-note:
            notes_template: 'notes/templates/custom.md'
        ```
    """
