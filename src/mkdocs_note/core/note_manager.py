import os
import datetime
import posixpath
import frontmatter
import re

from pathlib import Path
from typing import Dict, Union, Callable, List, Optional
from mkdocs.structure.files import File, Files
from mkdocs.utils import meta, get_relative_url
from mkdocs.structure.pages import Page
from mkdocs.config.defaults import MkDocsConfig

from mkdocs_note.core.file_manager import FileLinkedNode
from mkdocs_note.parsers.config_parser import PluginConfig
from mkdocs_note.logger import logger

class NoteLinkedMap(object):
    """Note linked map class, which use for recording the links of 
       an instance itself refer to other instances and the links of
       other instances refer to itself.

    Attributes:
        node (File): The file associated with this note.
        links (Dict[str, FileLinkedNode]): The links from this note to other notes, which is a dictionary mapping note IDs to their linked nodes.
        inverse_links (Optional[FileLinkedNode]): The links from other notes to this note, which is a linked list with head node.
    """
    def __init__(self, node: File):
        self.node = node
        self.links: Dict[str, FileLinkedNode] = {}
        self.inverse_links: Optional[FileLinkedNode] = None

    def clear_links(self):
        """Clear all active links (i.e., links pointing to other
           articles from oneself) and remove the relevant nodes from
           the corresponding reverse linked list.
        """
        for link in list(self.links.values()):
            link.remove()
        self.links.clear()
        self.inverse_links = None


def init_note_path(path: Path) -> int:
    """Initialize the note path.

    Args:
        path (Path): The path to initialize.
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)

    attachment_path = path / "attachments"
    if not attachment_path.exists():
        attachment_path.mkdir(parents=True, exist_ok=True)

    return 0

def process_notes_path_node(file: File) -> List[str]:
    """Extract the notes path node, and remove its extension.

    Args:
        file (File): The file to process.

    Returns:
        List[str]: The processed nodes list.
    """
    original_uri = file.src_uri

    normalized = posixpath.normpath(original_uri).lstrip('/')

    # Split path nodes
    parts = normalized.split('/')

    # Remove the extension of the last node (filename)
    if parts and '.' in parts[-1]:
        filename = parts[-1]
        parts[-1] = posixpath.splitext(filename)[0]
    
    return [part for part in parts if part]

def set_note_permalink(file: File) -> List[str]:
    """Set the permalink for a note file.

    Args:
        file (File): The note file to set the permalink for.

    Returns:
        List[str]: The list with 2 elements: the first is first node of the processed path, and the second is the permalink formed by connecting various nodes through '-'.
    """
    nodes_list = process_notes_path_node(file)

    if not nodes_list:
        return []

    head = nodes_list[1]
    permalink = head
    for node in nodes_list[2:]:
        permalink += ('-' + node)

    return [nodes_list[0], permalink]

def create_new_note(path: Path, notes_root_path: str, notes_template: str) -> int:
    """Create a new note at the specified path using the defined template.

    Args:
        path (Path): The path where the new note will be created.
        notes_root_path (str): The root path of the notes.
        notes_template (str): The template used for new notes.
    """
    template_path = Path(notes_template)

    if not template_path.exists():
        return 1

    post = frontmatter.load(template_path)

    # Create a mock File object for permalink generation
    try:
        relative_path = path.relative_to(Path(notes_root_path))
    except ValueError:
        logger.error(f"Cannot create new note: the path '{path}' is not inside the notes root directory '{notes_root_path}'.")
        return 1
    
    mock_file = type('MockFile', (), {'src_uri': str(relative_path)})()
    
    permalink_result = set_note_permalink(mock_file)
    if not permalink_result:
        logger.error(f"Failed to generate permalink for new note at '{path}'.")
        return 1
        
    frontmatter_args = {
        "date": datetime.datetime.now().isoformat(timespec='seconds'),
        "permalink": permalink_result[1],
        "publish": False
    }

    for key, value in post.metadata.items():
        if key not in frontmatter_args:
            frontmatter_args[key] = value

    # Update post metadata with new frontmatter
    for key, value in frontmatter_args.items():
        post[key] = value

    with open(path, 'w', encoding='utf-8') as f:
        f.write(frontmatter.dump(post))

    return 0

def set_note_uri(file: File, dest_uri: Union[str, Callable[[str], str]]) -> None:
    """Set the URI for a note file.

    Args:
        file (File): The note file to set the URI for.
        dest_uri (Union[str, Callable[[str], str]]): The destination URI or a function to generate it.
    """
    file.dest_uri = dest_uri if isinstance(dest_uri, str) else dest_uri(file.dest_uri)

    # Helper function to delete an attribute if it exists
    def delattr_if_exists(obj, attr: str) -> None:
        if hasattr(obj, attr):
            delattr(obj, attr)

    # Delete the 'url' and 'abs_dest_path' attribute if it exists
    delattr_if_exists(file, 'url')
    delattr_if_exists(file, 'abs_dest_path')

def transform_notes_links(markdown: str, page: Page, config: MkDocsConfig, note_link_name_map: dict, note_link_path_map: dict) -> str:
    """Transform note links in the markdown content.

    Args:
        markdown (str): The markdown content to transform
        page (Page): The page being processed
        config (MkDocsConfig): The MkDocs configuration
        note_link_name_map (dict): Dictionary mapping note names to File objects
        note_link_path_map (dict): Dictionary mapping note paths to NoteLinkedMap objects

    Returns:
        str: The transformed markdown content with wiki links converted to markdown links
    """
    link_list = note_link_path_map.get(page.file.src_uri)

    if link_list is not None:
        assert link_list.node == page.file
        link_list.clear_links()

    def record_link(target_file: File):
        if link_list is None or target_file.src_uri in link_list.links:
            return

        from mkdocs_note.core.file_manager import FileLinkedNode
        node = FileLinkedNode(page.file)
        link_list.links[target_file.src_uri] = node
        node.insert(note_link_path_map[target_file.src_uri].inverse_links)

    def repl(m: re.Match[str]):
        is_media = m.group(1) is not None

        # [[name#heading|alias]]
        # In tables, use '\\|' instead of '|', so remove '\\'
        m2 = re.match(r'^(.+?)(#(.*?))?(\|(.*))?$', m.group(2).replace('\\', ''), flags=re.U)
        name = m2.group(1).strip()
        heading = m2.group(3)
        alias = m2.group(5)

        # Automatically add .md extension to documents
        if not is_media and (name + '.md') in note_link_name_map:
            name += '.md'

        if heading:
            heading = heading.strip()
        if alias:
            alias = alias.strip()

        if name.count('/') == 0 and name in note_link_name_map:
            # name is a filename
            md_link = note_link_name_map[name].src_uri
        else:
            # name is a file path, expand to absolute path
            abs_path = posixpath.normpath(posixpath.join(posixpath.dirname(page.file.src_uri), name))

            if abs_path in note_link_path_map:
                md_link = note_link_path_map[abs_path].node.src_uri
            else:
                md_link = abs_path

        # Record reverse links
        if not is_media:
            if md_link in note_link_path_map:
                record_link(note_link_path_map[md_link].node)
            else:
                logger.warning('Failed to resolve link \'%s\' in \'%s\'', md_link, page.file.src_uri)

        # Convert to relative path so MkDocs will warn if link is not found
        md_link = get_relative_url(md_link, page.file.src_uri)
        title = posixpath.splitext(posixpath.basename(name))[0]  # Title without extension

        if heading:
            # Generate heading ID based on toc configuration
            # https://python-markdown.github.io/extensions/toc/
            toc_config = config.mdx_configs['toc']
            heading_id = toc_config['slugify'](heading, toc_config.get('separator', '-'))
            md_link += f'#{heading_id}'

        if alias:
            display_name = alias
        elif heading:
            display_name = f'{title} > {heading}'
        else:
            display_name = title

        return ('!' if is_media else '') + f'[{display_name}]({md_link})'

    # Use lazy matching to avoid merging multiple link contents
    return re.sub(r'(!)?\[\[(.*?)\]\]', repl, markdown, flags=re.M|re.U)

def insert_recent_notes(markdown: str, note_list: Dict[str, File]) -> str:
    """Insert recent notes into the notes root index.

    Args:
        markdown (str): The markdown content to insert recent notes into.
        note_list (Dict[str, File]): Dictionary of note files.

    Returns:
        str: The markdown content with recent notes inserted.
    """
    content = ''
    for f in list(note_list.values())[:10]:
        title = posixpath.splitext(posixpath.basename(f.src_uri))[0]
        date = f.note_date.strftime('%Y-%m-%d')
        content += f'- <div class="recent-notes"><a href="{f.url}">{title}</a><small>{date}</small></div>\n'
    return markdown.replace('<!-- RECENT NOTES -->', content)
