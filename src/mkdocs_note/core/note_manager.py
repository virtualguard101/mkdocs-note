import json
import hashlib
import subprocess
import re
from typing import List, Optional

from datetime import datetime, timezone, timedelta
from pathlib import Path

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.core.file_manager import NoteScanner
from mkdocs_note.core.data_models import NoteInfo, AssetsInfo, NoteFrontmatter
from mkdocs_note.core.assets_manager import AssetsProcessor
from mkdocs_note.core.frontmatter_manager import FrontmatterManager

class NoteProcessor:
    """Note processor
    """
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
        self.assets_processor = AssetsProcessor(config, logger)
        self.frontmatter_manager = FrontmatterManager()
        self._timezone = self._parse_timezone(config.timestamp_zone)
    
    def _parse_timezone(self, timezone_str: str) -> timezone:
        """Parse timezone string to timezone object.
        
        Args:
            timezone_str (str): Timezone string in format 'UTC+X' or 'UTC-X'
            
        Returns:
            timezone: The timezone object
        """
        try:
            # Match pattern like 'UTC+8', 'UTC-5', 'UTC+0'
            match = re.match(r'UTC([+-])(\d+(?:\.\d+)?)', timezone_str)
            if match:
                sign = match.group(1)
                hours = float(match.group(2))
                offset_hours = hours if sign == '+' else -hours
                return timezone(timedelta(hours=offset_hours))
            else:
                self.logger.warning(f"Invalid timezone format: {timezone_str}, using UTC+0")
                return timezone.utc
        except Exception as e:
            self.logger.warning(f"Error parsing timezone {timezone_str}: {e}, using UTC+0")
            return timezone.utc
    
    def _format_timestamp(self, timestamp: float) -> str:
        """Format timestamp with configured timezone.
        
        Args:
            timestamp (float): Unix timestamp
            
        Returns:
            str: Formatted datetime string
        """
        dt = datetime.fromtimestamp(timestamp, tz=self._timezone)
        return dt.strftime(self.config.output_date_format)
    
    def process_note(self, file_path: Path) -> Optional[NoteInfo]:
        """Process a single note file, extract information

        Args:
            file_path (Path): The path of the file to process

        Returns:
            Optional[NoteInfo]: The note information if successful, None otherwise
        """
        try:
            # Get basic information
            stat = file_path.stat()
            
            # Extract frontmatter (if present)
            frontmatter = self._extract_frontmatter(file_path)
            
            # Extract title
            title = self._extract_title(file_path)
            if not title or title == "Notebook":
                return None
            
            # Generate relative URL
            relative_url = self._generate_relative_url(file_path)
            
            # Get modification time - prefer Git commit time for consistent sorting
            if self.config.use_git_timestamps:
                git_time = self._get_git_commit_time(file_path)
                if git_time:
                    modified_time = git_time
                    modified_date = self._format_timestamp(git_time)
                    self.logger.debug(f"Using Git commit time for {file_path.name}: {modified_date}")
                else:
                    # Fallback to file system time
                    modified_time = stat.st_mtime
                    modified_date = self._format_timestamp(stat.st_mtime)
                    self.logger.debug(f"Git time unavailable, using file system time for {file_path.name}: {modified_date}")
            else:
                # Use file system time
                modified_time = stat.st_mtime
                modified_date = self._format_timestamp(stat.st_mtime)
                self.logger.debug(f"Using file system time for {file_path.name}: {modified_date}")
            
            return NoteInfo(
                file_path=file_path,
                title=title,
                relative_url=relative_url,
                modified_date=modified_date,
                file_size=stat.st_size,
                modified_time=modified_time,
                assets_list=self._extract_assets(file_path),
                frontmatter=frontmatter
            )
            
        except Exception as e:
            self.logger.error(f"Failed to process note {file_path}: {e}")
            return None

    def _extract_frontmatter(self, file_path: Path) -> Optional[NoteFrontmatter]:
        """Extract frontmatter from file.
        
        Args:
            file_path (Path): The path of the file to extract frontmatter from
            
        Returns:
            Optional[NoteFrontmatter]: The frontmatter if successful, None otherwise
        """
        # Only process markdown files for frontmatter
        if file_path.suffix.lower() != '.md':
            return None
        
        try:
            frontmatter_dict, _ = self.frontmatter_manager.parse_file(file_path)
            
            if frontmatter_dict:
                return NoteFrontmatter.from_dict(frontmatter_dict)
            else:
                return None
                
        except Exception as e:
            self.logger.debug(f"No frontmatter found in {file_path.name}: {e}")
            return None
   
    def _extract_title(self, file_path: Path) -> Optional[str]:
        """Extract title from file

        Args:
            file_path (Path): The path of the file to extract title from

        Returns:
            Optional[str]: The title if successful, None otherwise
        """
        if file_path.suffix == '.ipynb':
            return self._extract_title_from_notebook(file_path)
        else:
            return self._extract_title_from_markdown(file_path)
    
    def _extract_title_from_notebook(self, file_path: Path) -> Optional[str]:
        """Extract title from Jupyter Notebook

        Args:
            file_path (Path): The path of the file to extract title from

        Returns:
            Optional[str]: The title if successful, None otherwise
        """
        try:
            with file_path.open('r', encoding='utf-8') as f:
                notebook = json.load(f)
            
            for cell in notebook.get('cells', []):
                if cell.get('cell_type') == 'markdown':
                    source = cell.get('source', [])
                    if isinstance(source, list):
                        content = ''.join(source)
                    else:
                        content = source
                    
                    # Find the first level-1 title
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.startswith('# '):
                            return line[2:].strip()
                            
        except Exception as e:
            self.logger.warning(f"Failed to extract title from notebook {file_path}: {e}")
        
        return file_path.stem
    
    def _extract_title_from_markdown(self, file_path: Path) -> Optional[str]:
        """Extract title from Markdown file

        Args:
            file_path (Path): The path of the file to extract title from

        Returns:
            Optional[str]: The title if successful, None otherwise
        """
        try:
            with file_path.open('r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('# '):
                        return line[2:].strip()
        except Exception as e:
            self.logger.warning(f"Failed to extract title from markdown {file_path}: {e}")
        
        return file_path.stem

    def _extract_assets(self, file_path: Path) -> List[AssetsInfo]:
        """Extract assets from each note file

        Args:
            file_path (Path): The path of the file to extract assets from

        Returns:
            List[AssetsInfo]: The list of assets information
        """
        # Create a temporary NoteInfo object for assets processing
        temp_note_info = NoteInfo(
            file_path=file_path,
            title="",  # Will be filled later
            relative_url="",
            modified_date="",
            file_size=0,
            modified_time=0.0,
            assets_list=[]
        )
        
        return self.assets_processor.process_assets(temp_note_info)
    
    def _generate_relative_url(self, file_path: Path) -> str:
        """Generate MkDocs format relative URL

        Args:
            file_path (Path): The path of the file to generate relative URL from

        Returns:
            str: The relative URL
        """
        index_file = Path(self.config.index_file)
        relpath = file_path.relative_to(index_file.parent)
        relurl = relpath.with_suffix('').as_posix() + '/'
        
        # Process index file
        if 'index' in relurl:
            relurl = relurl.replace('index/', '')
        
        return relurl
    
    def _get_git_commit_time(self, file_path: Path) -> Optional[float]:
        """Get the last commit time for a file from Git
        
        Args:
            file_path (Path): The path of the file to get commit time for
            
        Returns:
            Optional[float]: The Unix timestamp of the last commit, None if not available
        """
        try:
            # Get the relative path from the project root
            project_root = Path(self.config.project_root)
            try:
                relative_path = file_path.relative_to(project_root)
            except ValueError:
                # File is not under project root, try to get relative path from current working directory
                relative_path = file_path
            
            # Run git log command to get the last commit time
            cmd = [
                'git', 'log', '-1', '--format=%ct', '--', str(relative_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=5  # 5 second timeout
            )
            
            if result.returncode == 0 and result.stdout.strip():
                timestamp = float(result.stdout.strip())
                return timestamp
            else:
                self.logger.debug(f"Git log failed for {relative_path}: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            self.logger.debug(f"Git log timeout for {file_path}")
            return None
        except Exception as e:
            self.logger.debug(f"Error getting Git commit time for {file_path}: {e}")
            return None


class CacheManager:
    """Cache manager
    """
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self._last_notes_hash: Optional[str] = None
        self._last_content_hash: Optional[str] = None
    
    def should_update_notes(self, notes: List[NoteInfo]) -> bool:
        """Check if notes list needs to be updated

        Args:
            notes (List[NoteInfo]): The list of notes to check

        Returns:
            bool: True if the notes list needs to be updated, False otherwise
        """
        current_hash = self._calculate_notes_hash(notes)
        if self._last_notes_hash != current_hash:
            self._last_notes_hash = current_hash
            return True
        return False
    
    def should_update_content(self, content: str) -> bool:
        """Check if file content needs to be updated

        Args:
            content (str): The content to check

        Returns:
            bool: True if the file content needs to be updated, False otherwise
        """
        content_hash = hashlib.md5(content.encode()).hexdigest()
        if self._last_content_hash != content_hash:
            self._last_content_hash = content_hash
            return True
        return False
    
    def _calculate_notes_hash(self, notes: List[NoteInfo]) -> str:
        """Calculate notes list hash

        Args:
            notes (List[NoteInfo]): The list of notes to calculate hash from

        Returns:
            str: The hash of the notes list
        """
        notes_info = []
        for note in notes:
            notes_info.append(f"{note.file_path.name}:{note.modified_time}:{note.file_size}")
        return hashlib.md5('|'.join(notes_info).encode()).hexdigest()


class IndexUpdater:
    """Index file updater
    """
    
    def __init__(self, config: PluginConfig, logger: Logger):
        self.config = config
        self.logger = logger
    
    def update_index(self, notes: List[NoteInfo]) -> bool:
        """Update index file

        Args:
            notes (List[NoteInfo]): The list of notes to update index file

        Returns:
            bool: True if the index file is updated successfully, False otherwise
        """
        index_file = Path(self.config.index_file)
        if not index_file.exists():
            self.logger.error(f"Index file does not exist: {index_file}")
            return False
        
        try:
            # Read existing content
            content = index_file.read_text(encoding='utf-8')
            
            # Generate new notes list HTML
            new_section = self._generate_html_list(notes)
            
            # Replace content
            updated_content = self._replace_section(content, new_section)
            if updated_content is None:
                return False
            
            # Write to file
            index_file.write_text(updated_content, encoding='utf-8')
            self.logger.debug(f"Updated index file with {len(notes) - 1} notes")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update index file: {e}")
            return False
    
    def _generate_html_list(self, notes: List[NoteInfo]) -> str:
        """Generate HTML list

        Args:
            notes (List[NoteInfo]): The list of notes to generate HTML list from

        Returns:
            str: The HTML list
        """
        items = []
        for note in notes:
            items.append(
                f'<li><div style="display:flex; justify-content:space-between; align-items:center;">'
                f'<a href="{note.relative_url}">{note.title}</a>'
                f'<span style="font-size:0.8em;">{note.modified_date}</span>'
                '</div></li>'
            )
        
        return '<ul>\n' + '\n'.join(items) + '\n</ul>'
    
    def _replace_section(self, content: str, new_section: str) -> Optional[str]:
        """Replace content between specified markers

        Args:
            content (str): The content to replace
            new_section (str): The new section to replace

        Returns:
            Optional[str]: The replaced content if successful, None otherwise
        """
        start_idx = content.find(self.config.start_marker)
        end_idx = content.find(self.config.end_marker)
        
        if start_idx == -1 or end_idx == -1:
            self.logger.error(
                f"Markers not found. Please add {self.config.start_marker} "
                f"and {self.config.end_marker} to the index file."
            )
            return None
        
        # Ensure end marker is after start marker
        if end_idx <= start_idx:
            self.logger.error("End marker found before start marker")
            return None
        
        start_pos = start_idx + len(self.config.start_marker)
        end_pos = end_idx
        
        return (
            content[:start_pos] + 
            '\n' + new_section + '\n' + 
            content[end_pos:]
        )


class RecentNotesUpdater:
    """Recent notes updater main class
    """
    
    def __init__(self, config: Optional[PluginConfig] = None):
        self.config = config or PluginConfig()
        self.logger = Logger()
        
        # Initialize components
        self.file_scanner = NoteScanner(self.config, self.logger)
        self.note_processor = NoteProcessor(self.config, self.logger)
        self.cache_manager = CacheManager(self.logger)
        self.index_updater = IndexUpdater(self.config, self.logger)
    
    def update(self) -> bool:
        """Execute update operation

        Returns:
            bool: True if the recent notes update is successful, False otherwise
        """
        self.logger.debug("Starting recent notes update...")
        
        try:
            # Scan note files
            note_files = self.file_scanner.scan_notes()
            if not note_files:
                self.logger.warning("No note files found")
                return False
            
            # Process note files
            notes = []
            for file_path in note_files:
                note_info = self.note_processor.process_note(file_path)
                if note_info:
                    notes.append(note_info)
            
            if not notes:
                self.logger.warning("No valid notes found")
                return False
            
            # Check cache
            if not self.cache_manager.should_update_notes(notes):
                self.logger.debug("Notes unchanged, skipping update")
                return True
            
            # Sort by modified time
            notes.sort(key=lambda n: n.modified_time, reverse=True)
            recent_notes = notes[:self.config.max_notes]
            
            # Update index file
            success = self.index_updater.update_index(recent_notes)
            if success:
                self.logger.debug(f"Successfully updated recent notes ({len(recent_notes) - 1} notes)")
            else:
                self.logger.error("Failed to update index file")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Unexpected error during update: {e}")
            return False
