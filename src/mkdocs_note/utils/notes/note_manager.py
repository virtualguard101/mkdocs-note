import json
import hashlib
import subprocess
import re
from typing import List, Optional

from datetime import datetime, timezone, timedelta
from pathlib import Path

from mkdocs_note.config import PluginConfig
from mkdocs_note.logger import Logger
from mkdocs_note.utils.file_manager import NoteScanner
from mkdocs_note.utils.data_models import NoteInfo, AssetsInfo, NoteFrontmatter
from mkdocs_note.utils.assets.assets_manager import AssetsProcessor
from mkdocs_note.utils.frontmatter.frontmatter_manager import FrontmatterManager

class NoteProcessor:
    """Note processor, which serve as the center process unit
    and act as a bridge between the file manager and the assets manager.
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
        # Use recent_notes_index_file for backward compatibility, fallback to default
        index_file_path = getattr(self.config, 'recent_notes_index_file', 'docs/notes/index.md')
        index_file = Path(index_file_path)
        
        try:
            relpath = file_path.relative_to(index_file.parent)
            relurl = relpath.with_suffix('').as_posix() + '/'
            
            # Process index file
            if 'index' in relurl:
                relurl = relurl.replace('index/', '')
            
            return relurl
        except ValueError:
            # If file is not under index file parent, generate relative to docs
            docs_dir = Path('docs')
            try:
                relpath = file_path.relative_to(docs_dir)
                return relpath.with_suffix('').as_posix() + '/'
            except ValueError:
                # Fallback to filename
                return file_path.stem + '/'
    
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


