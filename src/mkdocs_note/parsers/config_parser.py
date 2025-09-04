from typing import List
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

    path_blacklist = config_opt.Type(List[str], default=[])
    """A list of directories to exclude from note processing.

    Example:

        ```yml
        plugins:
        - mkdocs-note:
            path_blacklist:
            - 'notes/private'
            - 'notes/archived'
        ```
    """

    attachment_path = config_opt.Type(str, default='notes/attachments')
    """The path to the directory for storing attachments, with 'notes/attachments' as the default.

    Example:

        ```yml
        plugins:
        - mkdocs-note:
            attachment_path: 'notes/attachments'
        ```
    """
