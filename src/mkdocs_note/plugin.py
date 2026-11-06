from __future__ import annotations

import json
import os
import subprocess
from typing import ClassVar

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.exceptions import PluginError
from mkdocs.plugins import (
	BasePlugin,
	CombinedEvent,
	event_priority,
	get_plugin_logger,
)
from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Navigation
from mkdocs.structure.pages import Page
from mkdocs.structure.toc import TableOfContents

from mkdocs_note.config import MkdocsNoteConfig
from mkdocs_note.graph import (
	Graph,
	add_static_resouces,
	copy_static_assets,
	inject_graph_script,
)
from mkdocs_note.preview import (
	PreviewBuilder,
	add_preview_static_resources,
	copy_preview_static_assets,
	inject_preview_script,
	write_previews_file,
)
from mkdocs_note.utils import scanner
from mkdocs_note.utils.crypt import envelope, keys
from mkdocs_note.utils.crypt.page import (
	audit_plaintext_leaks,
	build_site_payload,
	build_stub,
	build_toc_html,
	build_unavailable_stub,
	collect_canaries,
	copy_encrypt_static_assets,
	ensure_heading,
	inject_encrypt_assets,
	labels_with_defaults,
)
from mkdocs_note.utils.meta import extract_date, extract_title


log = get_plugin_logger(__name__)


class MkdocsNotePlugin(BasePlugin[MkdocsNoteConfig]):
	"""Mkdocs Note Plugin entry point."""

	notes_list: ClassVar[list[File]] = []

	def load_config(self, options, config_file_path=None):
		"""Remember which plugin options the user explicitly configured."""
		self._user_config_keys = set(options or {})
		return super().load_config(options, config_file_path)

	@event_priority(100)
	def on_files(self, files: Files, config: MkDocsConfig) -> Files:
		"""Handle file processing."""
		self.notes_list.clear()
		invalid_files: list[File] = []

		self.notes_list, invalid_files = scanner.scan_notes(files, self.config)

		self.notes_list.sort(key=lambda f: f.note_date, reverse=True)

		for f in invalid_files:
			files.remove(f)

		return files

	def on_config(self, config: MkDocsConfig) -> MkDocsConfig:
		"""Handle plugin configuration."""
		self.static_dir = os.path.join(os.path.dirname(__file__), "static")

		# Per-build state (``mkdocs serve`` rebuilds reuse the plugin instance).
		self._encrypted_pages_seen = False
		self._leak_canaries: dict[str, tuple[str, list[str]]] = {}
		self._crypt_errors: dict[str, str] = {}
		self._warned_missing_filter = False

		add_static_resouces(config)

		if self.config.preview_config.get("enabled", False):
			add_preview_static_resources(config)

		if "notion_sync" in getattr(self, "_user_config_keys", set()):
			log.info(
				"Notion sync is deprecated since mkdocs-note 3.5.0 and will be "
				"removed in 4.0.0; encrypted notes are skipped by the command."
			)

		return config

	def on_pre_build(self, *, config: dict, **kwagrs) -> None:
		"""Handle pre-build."""
		if self.config.graph_config["enabled"]:
			self._graph = Graph(self.config.graph_config)
		if self.config.preview_config.get("enabled", False):
			from urllib.parse import urlparse

			site_url = config.get("site_url") if hasattr(config, "get") else None
			if site_url:
				base = urlparse(site_url).path
				if not base.endswith("/"):
					base += "/"
			else:
				base = "/"

			extra_src: set[str] = set()
			if self.config.recent_notes_config.get("enabled", False):
				n = int(self.config.recent_notes_config.get("insert_num", 10))
				extra_src = {f.src_path for f in self.notes_list[:n]}

			self._preview = PreviewBuilder(
				self.config.preview_config,
				site_base=base,
				markdown_extensions=config.get("markdown_extensions")
				if hasattr(config, "get")
				else None,
				mdx_configs=config.get("mdx_configs")
				if hasattr(config, "get")
				else None,
				extra_src_paths=extra_src,
			)

	def on_nav(
		self,
		nav: Navigation,
		*,
		config: MkDocsConfig,
		files: Files,
	) -> Navigation:
		"""Handle navigation.

		Args:
			nav (Navigation): The navigation object.
			config (MkDocsConfig): The MkDocs configuration.
			files (Files): The files object.

		Returns:
			Navigation: The navigation object.
		"""
		self._files = files
		return nav

	def _write_graph_file(self, config: MkDocsConfig) -> None:
		"""Write the graph data to a file."""
		log.info("Writing graph data to file...")
		output_dir = os.path.join(config["site_dir"], "graph")
		try:
			os.makedirs(output_dir, exist_ok=True)
			graph_file = os.path.join(output_dir, "graph.json")
			with open(graph_file, "w") as f:
				json.dump(self._graph.to_dict(), f)
		except OSError as e:
			log.error(f"Error writing graph file: {e}")

	def on_post_page(
		self,
		output: str,
		*,
		page: Page,
		config: MkDocsConfig,
	) -> str:
		"""Handle post page.

		Args:
			output (str): The output content.
			page (Page): The page object.
			config (MkDocsConfig): The MkDocs configuration.

		Returns:
			str: The output content.
		"""
		debug = self.config.graph_config.get("debug", False)
		output = inject_graph_script(output=output, config=config, debug=debug)

		if self.config.preview_config.get("enabled", False):
			output = inject_preview_script(
				output,
				config,
				self.config.preview_config,
				graph_enabled=bool(self.config.graph_config.get("enabled", False)),
			)

		page_meta = page.meta if isinstance(page.meta, dict) else {}
		if keys.is_encrypted(page_meta):
			encryption = self.config.encryption_config
			output = inject_encrypt_assets(
				output,
				page.url,
				{
					"remember": encryption.get("remember", "session"),
					"rerender": bool(encryption.get("rerender", True)),
					"labels": labels_with_defaults(encryption.get("labels")),
				},
			)
		return output

	def on_post_build(
		self,
		*,
		config: MkDocsConfig,
		**kwargs,
	) -> None:
		"""Handle post build.

		Args:
			config (MkDocsConfig): The MkDocs configuration.
		"""
		# Build graph if enabled
		if hasattr(self, "_graph") and hasattr(self, "_files"):
			self._graph(self._files)
			self._write_graph_file(config=config)

		if hasattr(self, "_preview") and hasattr(self, "_files"):
			try:
				# Refresh linked_only expansion sets at build time
				if self.config.recent_notes_config.get("enabled", False):
					n = int(self.config.recent_notes_config.get("insert_num", 10))
					self._preview.extra_src_paths = {
						f.src_path for f in self.notes_list[:n]
					}
				index_src: set[str] = set()
				for f in self._files.documentation_pages():
					if self.is_note_index_page(f):
						index_src.add(f.src_path)
				self._preview.index_src_paths = index_src
				if hasattr(self, "_graph") and getattr(self._graph, "nodes", None):
					self._preview.graph_src_paths = {
						n["id"] for n in self._graph.nodes if "id" in n
					}
				data = self._preview(self._files)
				write_previews_file(data, config)
			except OSError as e:
				log.error(f"Error writing previews file: {e}")

		log.info("Copying static assets...")
		try:
			copy_static_assets(static_dir=self.static_dir, config=config)
		except OSError as e:
			log.error(f"Error copying static assets: {e}")

		if self.config.preview_config.get("enabled", False):
			try:
				copy_preview_static_assets(static_dir=self.static_dir, config=config)
			except OSError as e:
				log.error(f"Error copying preview static assets: {e}")

		if self._encrypted_pages_seen:
			try:
				copy_encrypt_static_assets(static_dir=self.static_dir, config=config)
			except OSError as e:
				log.error(f"Error copying encryption static assets: {e}")

			if self.config.encryption_config.get("audit", True):
				self._run_leak_audit(config)

	def _run_leak_audit(self, config: MkDocsConfig) -> None:
		"""Warn when plaintext of an encrypted note leaked into the built site."""
		leaks = audit_plaintext_leaks(config["site_dir"], self._leak_canaries)
		for leak in leaks:
			log.warning(
				"Plaintext of encrypted note %s was found in %s (canary: %r).",
				leak.src_uri,
				", ".join(leak.files),
				leak.canary,
			)
		if not leaks:
			log.info(
				"Encryption leak audit: no plaintext found outside encrypted pages."
			)

	@event_priority(100)
	def _on_page_markdown_decrypt(
		self,
		markdown: str,
		page: Page,
		config: MkDocsConfig,
		files: Files,
	) -> str:
		"""Decrypt an at-rest envelope before other plugins see the page.

		The frontmatter stays clear, so MkDocs has already parsed ``page.meta``
		and the password is available even in a fresh CI checkout without the
		git filter.
		"""
		meta = page.meta if isinstance(page.meta, dict) else {}
		if not keys.is_encrypted(meta):
			return markdown

		self._encrypted_pages_seen = True
		self._warn_if_filter_missing(config)
		self._reject_blog_post(page, config)

		try:
			keys.resolve_password(meta)
		except keys.PasswordError as exc:
			raise PluginError(f"{page.file.src_uri}: {exc}") from exc

		if envelope.MARKER in markdown:
			try:
				body = envelope.decrypt_body(markdown, meta)
			except keys.CryptoError as exc:
				if self._strict_mode():
					raise PluginError(
						f"Cannot decrypt {page.file.src_uri}: {exc}"
					) from exc
				log.warning(f"Cannot decrypt {page.file.src_uri}: {exc}")
				self._crypt_errors[page.file.src_uri] = str(exc)
				return ""
		else:
			if self._strict_mode():
				raise PluginError(
					f"{page.file.src_uri} has encrypt: true but its source is "
					"plaintext. Run 'mkdocs-note crypt init' in this clone, then "
					"re-add the note with 'git add <file>'. Plaintext that was "
					"already committed remains in git history."
				)
			body = markdown

		self._leak_canaries[page.file.src_uri] = (
			page.file.dest_uri,
			collect_canaries(body),
		)
		return body

	def _on_page_markdown_recent(
		self,
		markdown: str,
		page: Page,
		config: MkDocsConfig,
		files: Files,
	) -> str:
		"""Handle recent-notes insertion on the note index page.

		Args:
			markdown (str): The markdown content.
			page (Page): The page object.
			config (MkDocsConfig): The MkDocs configuration.
			files (Files): The files object.

		Returns:
			str: The markdown content.
		"""
		# Only process recent notes on the note index page
		if self.config.recent_notes_config["enabled"] and self.is_note_index_page(
			page.file
		):
			markdown = insert_recent_note_links(
				markdown=markdown,
				notes_list=self.notes_list,
				insert_num=self.config.recent_notes_config["insert_num"],
				replace_marker=self.config.recent_notes_config["insert_marker"],
			)
			log.info(
				f"Inserted {self.config.recent_notes_config['insert_num']} recent notes into {page.file.src_uri}"
			)

		return markdown

	# Both handlers run through MkDocs' CombinedEvent; priority 100 on the
	# decrypt step puts it before every other plugin.
	on_page_markdown = CombinedEvent(
		_on_page_markdown_decrypt, _on_page_markdown_recent
	)

	@event_priority(-1000)
	def on_page_content(
		self,
		html: str,
		page: Page,
		config: MkDocsConfig,
		files: Files,
	) -> str:
		"""Replace a rendered encrypted page with its locked stub.

		Priority -1000 runs after every other plugin (including the site's own
		``hooks:``), so the payload contains the final HTML.
		"""
		meta = page.meta if isinstance(page.meta, dict) else {}
		if not keys.is_encrypted(meta):
			return html

		encryption = self.config.encryption_config
		labels = labels_with_defaults(encryption.get("labels"))
		title = str(meta.get("title") or page.title or page.file.name)

		if page.file.src_uri in self._crypt_errors:
			page.toc = TableOfContents([])
			return build_unavailable_stub(title, labels)

		try:
			source = keys.resolve_password(meta)
		except keys.PasswordError as exc:
			raise PluginError(f"{page.file.src_uri}: {exc}") from exc

		try:
			iterations = int(encryption.get("kdf_iterations", keys.DEFAULT_ITERATIONS))
		except (TypeError, ValueError) as exc:
			raise PluginError(
				"encryption_config.kdf_iterations must be an integer."
			) from exc

		toc_html = build_toc_html(page.toc, labels)
		content = ensure_heading(html, title)
		payload = build_site_payload(
			page.file.src_uri,
			content,
			toc_html,
			source.password,
			iterations,
		)
		# The search plugin reads page.toc after this event; the real headings
		# exist only inside the encrypted payload.
		page.toc = TableOfContents([])
		return build_stub(title, payload, labels)

	def _strict_mode(self) -> bool:
		"""Resolve ``encryption_config.strict`` (auto follows the CI variable)."""
		value = self.config.encryption_config.get("strict", "auto")
		if isinstance(value, str):
			normalized = value.strip().lower()
			if normalized in {"true", "yes", "on", "1"}:
				return True
			if normalized in {"false", "no", "off", "0"}:
				return False
			return _env_truthy("CI")
		return bool(value)

	def _warn_if_filter_missing(self, config: MkDocsConfig) -> None:
		"""Warn once when a local clone has encrypted notes but no git filter."""
		if self._warned_missing_filter:
			return
		self._warned_missing_filter = True
		if self._strict_mode():
			return
		docs_dir = str(config.get("docs_dir") or "docs")
		try:
			inside = subprocess.run(
				["git", "-C", docs_dir, "rev-parse", "--is-inside-work-tree"],
				capture_output=True,
				text=True,
				check=False,
			)
			if inside.returncode != 0 or inside.stdout.strip() != "true":
				return
			filter_config = subprocess.run(
				[
					"git",
					"-C",
					docs_dir,
					"config",
					"--get",
					"filter.mkdocs-note.process",
				],
				capture_output=True,
				text=True,
				check=False,
			)
		except OSError:
			return
		if filter_config.returncode != 0 or not filter_config.stdout.strip():
			log.warning(
				"Encrypted notes found but this git clone has no mkdocs-note "
				"filter configured; run 'mkdocs-note crypt init' so note bodies "
				"are stored encrypted."
			)

	def _reject_blog_post(self, page: Page, config: MkDocsConfig) -> None:
		"""Refuse encryption on Material blog posts (excerpts/RSS would leak)."""
		plugins = getattr(config, "plugins", None)
		if plugins is None:
			return
		# MkDocs stores Material plugins under their entry-point name
		# ("material/blog"); the short "blog" alias only works when a site
		# provides its own plugin of that name.
		blog_plugin = None
		for name in ("blog", "material/blog"):
			if name in plugins:
				blog_plugin = plugins[name]
				break
		if blog_plugin is None:
			return
		blog_dir = "blog"
		try:
			blog_dir = str(blog_plugin.config.get("blog_dir", "blog"))
		except (AttributeError, TypeError):
			pass
		prefix = blog_dir.strip("/") + "/"
		if page.file.src_uri.startswith(prefix):
			raise PluginError(
				f"Encrypted notes are not supported for Material blog posts: "
				f"{page.file.src_uri}. Blog excerpts and RSS entries would leak "
				"the content."
			)

	def is_note_index_page(self, f: File) -> bool:
		"""Check if the page is a note index page.

		Args:
			f (File): The file to check.

		Returns:
			bool: True if the page is a note index page, False otherwise.
		"""
		from pathlib import Path

		# Check if file ends with index.md
		if not f.src_uri.endswith("index.md"):
			return False

		# Check if file is the index.md directly under notes_root
		try:
			notes_dir = (
				Path(self.config.notes_root)
				if isinstance(self.config.notes_root, str)
				else self.config.notes_root
			)
			file_path = Path(f.abs_src_path)
			# Get the relative path from notes_root to the file
			rel_path = file_path.relative_to(notes_dir)
			# If the relative path is exactly "index.md", it's the index page
			return str(rel_path) == "index.md"
		except (ValueError, AttributeError):
			# File is not within notes_root
			return False


def _env_truthy(name: str) -> bool:
	"""Return whether an environment variable is set to a truthy value."""
	value = os.environ.get(name, "").strip().lower()
	return value not in {"", "0", "false", "no", "off"}


def insert_recent_note_links(
	markdown: str,
	notes_list: list[File],
	insert_num: int,
	replace_marker: str,
) -> str:
	"""Insert recent note links into the markdown.

	Args:
	    markdown (str): The markdown content.
	    notes_list (list[File]): The list of valid notes.
	    insert_num (int): The number of recent notes to insert.
	    replace_marker (str): The marker to replace.

	Returns:
	    str: The markdown content with recent note links inserted.
	"""

	content = "<ul>\n"
	for f in notes_list[:insert_num]:
		title = extract_title(f)
		date = extract_date(f).strftime("%Y-%m-%d %H:%M:%S")
		content += f'<li><div style="display:flex; justify-content:space-between; align-items:center;"><a href="{f.page.abs_url}">{title}</a><span style="font-size:0.8em; color:#888;">{date}</span></div></li>\n'
	content += "</ul>\n"
	return markdown.replace(replace_marker, content)
