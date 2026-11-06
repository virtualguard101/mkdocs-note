"""Build-time helpers for encrypted pages.

The browser payload is a UTF-8 JSON document encrypted with AES-256-GCM; the
page HTML only ever contains the locked stub and that ciphertext. The helpers
here also render the Material-compatible table of contents that travels inside
the payload and collect plaintext canaries for the post-build leak audit.
"""

from __future__ import annotations

import base64
import html
import json
import os
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from mkdocs.structure.toc import TableOfContents
from mkdocs.plugins import get_plugin_logger
from mkdocs.utils import get_relative_url

from mkdocs_note.utils.crypt import keys

logger = get_plugin_logger(__name__)

STUB_CLASS = "mkdocs-note-encrypted"
PAYLOAD_CLASS = "mkdocs-note-encrypted__payload"
PASSWORD_INPUT_ID = "mkdocs-note-encrypted-password"
MAX_CANARIES_PER_PAGE = 8
MAX_CANARY_LENGTH = 120
MAX_AUDIT_FILE_BYTES = 32 * 1024 * 1024

DEFAULT_LABELS: dict[str, str] = {
	"title": "Encrypted note",
	"prompt": "This note is encrypted. Enter the password to read it.",
	"placeholder": "Password",
	"submit": "Unlock",
	"error": "Incorrect password.",
	"unsupported": "Decryption needs a modern browser over HTTPS.",
	"noscript": "JavaScript is required to read this note.",
	"toc": "Table of contents",
	"unavailable": "This encrypted note could not be decrypted during the build.",
}


def labels_with_defaults(labels: Mapping[str, Any] | None) -> dict[str, str]:
	"""Merge user labels over the built-in English strings."""
	merged = dict(DEFAULT_LABELS)
	for key, value in (labels or {}).items():
		if isinstance(value, str) and value:
			merged[str(key)] = value
	return merged


def label(labels: Mapping[str, str], key: str) -> str:
	"""Return an escaped UI label."""
	return html.escape(labels.get(key, DEFAULT_LABELS.get(key, "")))


def ensure_heading(content: str, title: str) -> str:
	"""Prepend the page title when Material would have added it itself.

	Material's ``content.html`` adds ``<h1>{{ page.title }}</h1>`` only when the
	rendered content has no literal ``<h1``. Since the real content is encrypted
	and replaced by a stub, that heading has to travel inside the payload.
	"""
	if "<h1" in content:
		return content
	return f"<h1>{html.escape(title)}</h1>\n{content}"


def _strip_inline_markdown(text: str) -> str:
	try:
		from mkdocs_note.preview import strip_markdown_inline

		return strip_markdown_inline(text)
	except Exception:  # pragma: no cover - defensive: preview is always importable
		return text


def collect_canaries(body: str, limit: int = MAX_CANARIES_PER_PAGE) -> list[str]:
	"""Pick distinctive plaintext snippets for the post-build leak audit.

	Heading lines are skipped because the page title is intentionally public.
	Markdown inline formatting is removed so a canary also matches the rendered
	HTML form.
	"""
	canaries: list[str] = []
	seen: set[str] = set()
	for raw_line in body.splitlines():
		line = raw_line.strip()
		if len(line) < 20 or line.startswith("#"):
			continue
		candidate = _strip_inline_markdown(line).strip()
		if len(candidate) < 20:
			continue
		candidate = candidate[:MAX_CANARY_LENGTH]
		if candidate in seen:
			continue
		seen.add(candidate)
		canaries.append(candidate)
		if len(canaries) >= limit:
			break
	return canaries


def build_site_payload(
	src_uri: str,
	content: str,
	toc_html: str,
	password: str,
	iterations: int = keys.DEFAULT_ITERATIONS,
) -> dict[str, Any]:
	"""Encrypt the rendered page and return the JSON-safe browser payload."""
	plaintext = json.dumps(
		{"v": 1, "content": content, "toc": toc_html},
		ensure_ascii=False,
		separators=(",", ":"),
	).encode("utf-8")
	salt, aad, sealed = keys.seal_site(password, src_uri, plaintext, iterations)
	return {
		"v": 1,
		"iter": int(iterations),
		"salt": _b64(salt),
		"iv": _b64(sealed[: keys.NONCE_SIZE]),
		"aad": _b64(aad),
		"ct": _b64(sealed[keys.NONCE_SIZE :]),
	}


def _b64(data: bytes) -> str:
	return base64.b64encode(data).decode("ascii")


def _toc_items(items: Iterable[Any]) -> str:
	chunks: list[str] = []
	for item in items:
		children = list(getattr(item, "children", ()) or ())
		title = _strip_tags(str(getattr(item, "title", "")))
		url = html.escape(str(getattr(item, "url", "")))
		parts = [
			'<li class="md-nav__item">',
			f'<a href="{url}" class="md-nav__link">',
			f'<span class="md-ellipsis">{html.escape(title)}</span>',
			"</a>",
		]
		if children:
			parts.append(
				f'<nav class="md-nav" aria-label="{html.escape(title)}">'
				'<ul class="md-nav__list">'
			)
			parts.append(_toc_items(children))
			parts.append("</ul></nav>")
		parts.append("</li>")
		chunks.append("".join(parts))
	return "".join(chunks)


def _strip_tags(text: str) -> str:
	return re.sub(r"<[^>]+>", "", text)


def build_toc_html(
	toc: TableOfContents | Iterable[Any],
	labels: Mapping[str, str],
) -> str:
	"""Render ``page.toc`` with Material's markup, ready for the sidebar."""
	items = list(toc)
	if not items:
		return ""
	first = items[0]
	# Material skips a leading level-1 entry (the page title) and lists its
	# children instead, see partials/toc.html.
	if getattr(first, "level", 0) == 1:
		items = list(getattr(first, "children", ()) or ())
		if not items:
			return ""
	toc_label = html.escape(labels.get("toc", DEFAULT_LABELS["toc"]))
	return (
		'<label class="md-nav__title" for="__toc">'
		'<span class="md-nav__icon md-icon"></span>'
		f"{toc_label}</label>"
		'<ul class="md-nav__list" data-md-component="toc" data-md-scrollfix>'
		f"{_toc_items(items)}"
		"</ul>"
	)


def build_stub(
	title: str,
	payload: Mapping[str, Any],
	labels: Mapping[str, str],
) -> str:
	"""Return the locked page HTML with the encrypted payload attached."""
	escaped_title = html.escape(title)
	payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
	return (
		f'<div class="{STUB_CLASS}" data-mkdocs-note-encrypted>'
		f"<h1>{escaped_title}</h1>"
		f'<p class="{STUB_CLASS}__title">{label(labels, "title")}</p>'
		f'<form class="{STUB_CLASS}__form" autocomplete="off">'
		f'<p class="{STUB_CLASS}__prompt">{label(labels, "prompt")}</p>'
		f'<label class="{STUB_CLASS}__label" for="{PASSWORD_INPUT_ID}">'
		f"{label(labels, 'placeholder')}</label>"
		f'<div class="{STUB_CLASS}__row">'
		f'<input id="{PASSWORD_INPUT_ID}" class="{STUB_CLASS}__input" '
		f'type="password" name="password" '
		f'placeholder="{label(labels, "placeholder")}" '
		'autocomplete="current-password" required>'
		f'<button class="md-button md-button--primary {STUB_CLASS}__submit" '
		f'type="submit">{label(labels, "submit")}</button>'
		"</div>"
		f'<p class="{STUB_CLASS}__error" role="alert" aria-live="polite"></p>'
		"</form>"
		f'<noscript><p class="{STUB_CLASS}__noscript">'
		f"{label(labels, 'noscript')}</p></noscript>"
		f'<script type="application/json" class="{PAYLOAD_CLASS}">'
		f"{payload_json}</script>"
		"</div>"
	)


def build_unavailable_stub(title: str, labels: Mapping[str, str]) -> str:
	"""Return a stub for a page that could not be decrypted during the build."""
	return (
		f'<div class="{STUB_CLASS} {STUB_CLASS}--unavailable" '
		"data-mkdocs-note-encrypted>"
		f"<h1>{html.escape(title)}</h1>"
		f'<p class="{STUB_CLASS}__error">{label(labels, "unavailable")}</p>'
		"</div>"
	)


def inject_encrypt_assets(
	output: str,
	page_url: str,
	options: Mapping[str, Any],
) -> str:
	"""Inject the encryption stylesheet, script and runtime options."""
	css_url = html.escape(get_relative_url("css/encrypt.css", page_url))
	js_url = html.escape(get_relative_url("js/encrypt.js", page_url))
	payload = json.dumps(options, ensure_ascii=False).replace("</", "<\\/")
	scripts = (
		f"<script>window.mkdocs_note_encrypt_options = {payload};</script>"
		f'<script src="{js_url}" defer></script>'
	)
	if "</head>" in output:
		output = output.replace(
			"</head>", f'<link rel="stylesheet" href="{css_url}"></head>', 1
		)
	if "</body>" in output:
		output = output.replace("</body>", f"{scripts}</body>", 1)
	return output


def copy_encrypt_static_assets(static_dir: str, config: Any) -> None:
	"""Copy ``encrypt.js`` / ``encrypt.css`` into the site directory."""
	js_output_dir = os.path.join(config["site_dir"], "js")
	os.makedirs(js_output_dir, exist_ok=True)
	shutil.copy(os.path.join(static_dir, "encrypt.js"), js_output_dir)

	css_output_dir = os.path.join(config["site_dir"], "css")
	os.makedirs(css_output_dir, exist_ok=True)
	shutil.copy(os.path.join(static_dir, "encrypt.css"), css_output_dir)


@dataclass(frozen=True)
class Leak:
	"""A plaintext canary found outside its own page in the built site."""

	src_uri: str
	canary: str
	files: tuple[str, ...]


def _variants(canary: str) -> tuple[str, ...]:
	escaped = html.escape(canary)
	json_escaped = json.dumps(canary)[1:-1]
	return tuple(dict.fromkeys((canary, escaped, json_escaped)))


def audit_plaintext_leaks(
	site_dir: str | os.PathLike[str],
	pages: Mapping[str, Sequence[Any]],
) -> list[Leak]:
	"""Search the built site for plaintext of encrypted pages.

	Args:
		site_dir: Built site directory.
		pages: Mapping of ``src_uri`` to ``(dest_uri, canaries)``.

	Returns:
		Leaks found outside each page's own output file.
	"""
	root = Path(site_dir)
	targets = [
		path
		for path in root.rglob("*")
		if path.is_file() and path.suffix.lower() in {".html", ".json", ".xml"}
	]
	leaks: list[Leak] = []
	for src_uri, entry in pages.items():
		dest_uri, canaries = entry[0], list(entry[1])
		if not canaries:
			continue
		own_output = (root / str(dest_uri)).resolve()
		canary_variants = [(canary, _variants(canary)) for canary in canaries]
		hits: dict[str, list[str]] = {canary: [] for canary in canaries}
		for path in targets:
			try:
				if path.resolve() == own_output:
					continue
				if path.stat().st_size > MAX_AUDIT_FILE_BYTES:
					continue
				text = path.read_text(encoding="utf-8", errors="ignore")
			except OSError:
				continue
			for canary, variants in canary_variants:
				if any(variant in text for variant in variants):
					hits[canary].append(str(path.relative_to(root)))
		for canary, files in hits.items():
			if files:
				leaks.append(Leak(src_uri, canary, tuple(files)))
	return leaks
