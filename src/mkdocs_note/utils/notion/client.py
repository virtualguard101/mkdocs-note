"""Notion HTTP API helpers for page sync.

Handles page create/update, tags schema, file uploads, and block operations.
Wiki IDs are always passed by the caller — never hardcoded here.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import re
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mkdocs_note.utils.notion.convert import CONTENT_TYPES

log = logging.getLogger("mkdocs_note.notion")

NOTION_VERSION_PAGES = "2025-09-03"
NOTION_VERSION_MARKDOWN = "2026-03-11"


def notion_request(
	token: str,
	method: str,
	path: str,
	payload: dict | None = None,
	notion_version: str = NOTION_VERSION_PAGES,
	retries: int = 6,
) -> dict:
	"""Perform a Notion REST request with retries on transient failures.

	Args:
	    token: Notion integration bearer token.
	    method: HTTP method (GET, POST, PATCH, DELETE, …).
	    path: API path under ``https://api.notion.com/v1/``.
	    payload: Optional JSON body.
	    notion_version: Notion-Version header value.
	    retries: Max attempts for rate-limit / network errors.

	Returns:
	    Parsed JSON response dict (empty if body is empty).
	"""
	import http.client
	import ssl

	url = f"https://api.notion.com/v1/{path}"
	data = json.dumps(payload).encode("utf-8") if payload is not None else None
	last_error: Exception | None = None
	for attempt in range(retries):
		try:
			req = urllib.request.Request(
				url,
				data=data,
				method=method,
				headers={
					"Authorization": f"Bearer {token}",
					"Notion-Version": notion_version,
					"Content-Type": "application/json",
				},
			)
			with urllib.request.urlopen(req, timeout=180) as resp:
				body = resp.read().decode("utf-8")
				return json.loads(body) if body else {}
		except urllib.error.HTTPError as exc:
			last_error = exc
			err_body = exc.read().decode("utf-8", errors="replace")
			if exc.code in (429, 502, 503, 504):
				wait = 2.0 * (attempt + 1)
				log.warning("HTTP %s; retry in %.1fs", exc.code, wait)
				time.sleep(wait)
				continue
			raise urllib.error.HTTPError(
				url, exc.code, err_body, exc.headers, None
			) from exc
		except (
			urllib.error.URLError,
			TimeoutError,
			http.client.IncompleteRead,
			http.client.RemoteDisconnected,
			ssl.SSLError,
			ConnectionResetError,
			BrokenPipeError,
		) as exc:
			last_error = exc
			wait = 1.5 * (attempt + 1)
			log.warning(
				"transient network error (%s); retry in %.1fs",
				type(exc).__name__,
				wait,
			)
			time.sleep(wait)
	assert last_error is not None
	raise last_error


def create_page(
	token: str,
	parent_id: str,
	title: str,
	*,
	title_property: str,
	parent_kind: str,
) -> dict[str, str]:
	"""Create a Notion page under a wiki data source or parent page.

	Args:
	    token: Notion bearer token.
	    parent_id: Parent data-source, database, or page id.
	    title: Page title (truncated to 2000 chars).
	    title_property: Title property name on the parent schema.
	    parent_kind: One of ``data_source``, ``database``, or ``page``.

	Returns:
	    Dict with ``id`` and ``url`` keys.
	"""
	if parent_kind == "data_source":
		parent: dict = {"type": "data_source_id", "data_source_id": parent_id}
	elif parent_kind == "database":
		parent = {"type": "database_id", "database_id": parent_id}
	else:
		parent = {"page_id": parent_id}

	# Wiki pages (including nested children) use the data-source title property.
	prop_name = title_property or "title"
	props = {
		prop_name: {
			"title": [{"type": "text", "text": {"content": title[:2000]}}],
		}
	}
	try:
		page = notion_request(
			token, "POST", "pages", {"parent": parent, "properties": props}
		)
	except urllib.error.HTTPError as exc:
		# Some parent page_id contexts only accept the generic "title" property.
		if prop_name != "title" and "title" in str(exc):
			props = {
				"title": {
					"title": [{"type": "text", "text": {"content": title[:2000]}}],
				}
			}
			page = notion_request(
				token, "POST", "pages", {"parent": parent, "properties": props}
			)
		else:
			raise
	return {"id": page["id"], "url": page.get("url", "")}


def update_page_markdown(token: str, page_id: str, markdown: str) -> None:
	"""Replace page content via the Notion markdown PATCH endpoint."""
	notion_request(
		token,
		"PATCH",
		f"pages/{page_id}/markdown",
		{
			"type": "replace_content",
			"replace_content": {"new_str": markdown},
		},
		notion_version=NOTION_VERSION_MARKDOWN,
	)


@dataclass
class TagsSchemaCache:
	"""Cached multi_select options for a wiki tags property.

	Args:
	    data_source_id: Notion data source id (caller-supplied).
	    property_name: Multi-select property name (default ``标签``).
	"""

	data_source_id: str
	property_name: str = "标签"
	option_names: set[str] = field(default_factory=set)
	loaded: bool = False

	def refresh(self, token: str) -> None:
		"""Load current multi_select option names from the data source schema."""
		ds = notion_request(token, "GET", f"data_sources/{self.data_source_id}")
		prop = (ds.get("properties") or {}).get(self.property_name) or {}
		if prop.get("type") != "multi_select":
			raise RuntimeError(
				f"Notion property {self.property_name!r} is not multi_select "
				f"(got {prop.get('type')!r})"
			)
		options = (prop.get("multi_select") or {}).get("options") or []
		self.option_names = {
			str(o.get("name", "")).strip() for o in options if o.get("name")
		}
		self.loaded = True

	def ensure_options(self, token: str, tags: list[str]) -> None:
		"""Merge missing tag names into the data source schema (preserving existing)."""
		if not tags:
			return
		if not self.loaded:
			self.refresh(token)
		missing = [t for t in tags if t not in self.option_names]
		if not missing:
			return

		ds = notion_request(token, "GET", f"data_sources/{self.data_source_id}")
		prop = (ds.get("properties") or {}).get(self.property_name) or {}
		existing = (prop.get("multi_select") or {}).get("options") or []
		# Keep id/name/color so Notion does not wipe prior options.
		merged: list[dict] = []
		seen: set[str] = set()
		for opt in existing:
			name = str(opt.get("name", "")).strip()
			if not name or name in seen:
				continue
			entry: dict = {"id": opt["id"], "name": name}
			if opt.get("color"):
				entry["color"] = opt["color"]
			merged.append(entry)
			seen.add(name)
		for name in tags:
			if name not in seen:
				merged.append({"name": name})
				seen.add(name)

		log.info(
			"adding %d tag option(s) to schema: %s",
			len(missing),
			", ".join(missing),
		)
		notion_request(
			token,
			"PATCH",
			f"data_sources/{self.data_source_id}",
			{
				"properties": {
					self.property_name: {
						"multi_select": {"options": merged},
					}
				}
			},
		)
		self.option_names = seen
		self.loaded = True


def update_page_tags(
	token: str,
	page_id: str,
	tags: list[str],
	*,
	property_name: str = "标签",
	tags_cache: TagsSchemaCache | None = None,
) -> list[str]:
	"""Write frontmatter tags into a Notion multi_select property; return applied names.

	Wiki quirk: assigning a multi_select name that is not yet in the data-source
	schema returns HTTP 200 but leaves the property empty. Ensure options first.
	"""
	if tags_cache is not None:
		tags_cache.ensure_options(token, tags)

	page = notion_request(
		token,
		"PATCH",
		f"pages/{page_id}",
		{
			"properties": {
				property_name: {
					"multi_select": [{"name": t} for t in tags],
				}
			}
		},
	)
	prop = (page.get("properties") or {}).get(property_name) or {}
	applied = [
		str(o.get("name", "")).strip()
		for o in (prop.get("multi_select") or [])
		if o.get("name")
	]
	if set(applied) != set(tags):
		raise RuntimeError(
			f"tags write mismatch on {page_id}: wanted {tags}, got {applied}"
		)
	return applied


def upload_local_file(token: str, path: Path, cache: dict[str, str]) -> str:
	"""Upload a local file to Notion and return a ``file-upload://`` source URI."""
	key = str(path.resolve())
	if key in cache:
		return cache[key]

	suffix = path.suffix.lower()
	filename = path.name
	if suffix == ".awebp":
		filename = path.stem + ".webp"
		suffix = ".webp"

	content_type = (
		CONTENT_TYPES.get(suffix)
		or mimetypes.guess_type(filename)[0]
		or "application/octet-stream"
	)
	created = notion_request(
		token,
		"POST",
		"file_uploads",
		{"filename": filename, "content_type": content_type},
	)
	upload_id = created["id"]

	boundary = f"----NotionBoundary{int(time.time() * 1000)}"
	file_bytes = path.read_bytes()
	body = (
		(
			f"--{boundary}\r\n"
			f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
			f"Content-Type: {content_type}\r\n\r\n"
		).encode()
		+ file_bytes
		+ f"\r\n--{boundary}--\r\n".encode()
	)

	url = f"https://api.notion.com/v1/file_uploads/{upload_id}/send"
	req = urllib.request.Request(
		url,
		data=body,
		method="POST",
		headers={
			"Authorization": f"Bearer {token}",
			"Notion-Version": NOTION_VERSION_PAGES,
			"Content-Type": f"multipart/form-data; boundary={boundary}",
		},
	)
	with urllib.request.urlopen(req, timeout=180) as resp:
		json.loads(resp.read().decode("utf-8"))

	source = f"file-upload://{upload_id}"
	cache[key] = source
	return source


def iter_blocks(token: str, block_id: str) -> Iterator[dict[str, Any]]:
	"""Recursively yield child blocks under ``block_id`` (depth-first)."""
	cursor: str | None = None
	while True:
		path = f"blocks/{block_id}/children?page_size=100"
		if cursor:
			path += f"&start_cursor={cursor}"
		data = notion_request(token, "GET", path)
		for block in data.get("results", []):
			yield block
			btype = block.get("type")
			if block.get("has_children") and btype not in (
				"child_page",
				"child_database",
			):
				yield from iter_blocks(token, block["id"])
		if not data.get("has_more"):
			break
		cursor = data.get("next_cursor")


def rich_text_plain(block: dict) -> str:
	"""Concatenate plain_text from a block's rich_text array."""
	btype = block.get("type")
	payload = block.get(btype) or {}
	parts = payload.get("rich_text") or []
	return "".join(p.get("plain_text", "") for p in parts)


def delete_block(token: str, block_id: str) -> None:
	"""Delete (archive) a Notion block."""
	notion_request(token, "DELETE", f"blocks/{block_id}")


def insert_image_after(
	token: str,
	parent_id: str,
	after_block_id: str,
	upload_id: str,
	caption: str = "",
) -> None:
	"""Insert an uploaded image block after ``after_block_id``."""
	image: dict = {
		"type": "file_upload",
		"file_upload": {"id": upload_id},
	}
	if caption:
		image["caption"] = [{"type": "text", "text": {"content": caption[:2000]}}]
	notion_request(
		token,
		"PATCH",
		f"blocks/{parent_id}/children",
		{
			"after": after_block_id,
			"children": [
				{
					"object": "block",
					"type": "image",
					"image": image,
				}
			],
		},
	)


def attach_placeholder_images(
	token: str,
	page_id: str,
	image_paths: list[Path],
) -> int:
	"""Replace ``⟦LOCALIMG:N⟧`` placeholders with uploaded image blocks.

	Returns:
	    Number of images successfully attached.
	"""
	upload_cache: dict[str, str] = {}
	attached = 0
	placeholder_re = re.compile(r"^⟦LOCALIMG:(\d+)⟧$")

	matches: list[tuple[dict, int]] = []
	for block in iter_blocks(token, page_id):
		if block.get("type") != "paragraph":
			continue
		text = rich_text_plain(block).strip()
		m = placeholder_re.match(text)
		if not m:
			continue
		matches.append((block, int(m.group(1))))

	for block, idx in matches:
		if idx < 0 or idx >= len(image_paths):
			log.warning("placeholder index out of range: %s", idx)
			continue
		path = image_paths[idx]
		source = upload_local_file(token, path, upload_cache)
		upload_id = source.split("://", 1)[1]
		parent = block.get("parent", {})
		parent_id = parent.get("page_id") or parent.get("block_id") or page_id
		insert_image_after(token, parent_id, block["id"], upload_id, caption=path.name)
		delete_block(token, block["id"])
		attached += 1
		time.sleep(0.15)
	return attached


def page_title(page: dict, title_property: str = "页面") -> str:
	"""Extract the title plain text from a Notion page object.

	Args:
	    page: Notion page JSON.
	    title_property: Preferred title property name to try first.
	"""
	props = page.get("properties", {})
	for key in (title_property, "页面", "title", "Title", "Name", "名称"):
		prop = props.get(key)
		if not prop or prop.get("type") != "title":
			continue
		parts = prop.get("title") or []
		return "".join(t.get("plain_text", "") for t in parts)
	for prop in props.values():
		if prop.get("type") == "title":
			parts = prop.get("title") or []
			return "".join(t.get("plain_text", "") for t in parts)
	return ""


def list_wiki_pages(token: str, data_source_id: str) -> list[dict]:
	"""Query all pages in a wiki data source (paginated)."""
	pages: list[dict] = []
	cursor: str | None = None
	while True:
		payload: dict = {"page_size": 100}
		if cursor:
			payload["start_cursor"] = cursor
		data = notion_request(
			token, "POST", f"data_sources/{data_source_id}/query", payload
		)
		pages.extend(data.get("results", []))
		if not data.get("has_more"):
			break
		cursor = data.get("next_cursor")
	return pages
