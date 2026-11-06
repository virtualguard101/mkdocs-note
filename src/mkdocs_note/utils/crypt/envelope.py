"""At-rest envelope format: clear frontmatter plus an encrypted body.

An envelope keeps the note's YAML frontmatter readable so MkDocs, the plugin
scanner, GitHub and ``git diff`` can work without a key, and encrypts only the
body::

	---
	title: Example
	permalink: example
	encrypt: true
	---

	> 🔒 This note is encrypted by mkdocs-note. Read it on the published site.

	<!-- mkdocs-note:encrypted v1 key=permalink
	<base64 of nonce | ciphertext | tag, wrapped at 76 columns>
	-->

The format is deterministic and fixed per version, which keeps ``git status``
stable and makes a byte-exact smudge possible.
"""

from __future__ import annotations

import base64
import binascii
import re
import sys
import textwrap
from dataclasses import dataclass
from typing import Any

import yaml
from mkdocs.utils import meta as mkdocs_meta

from mkdocs_note.utils.crypt import keys

NOTICE = "> 🔒 This note is encrypted by mkdocs-note. Read it on the published site."
MARKER = "mkdocs-note:encrypted"
FORMAT_VERSION = 1
WRAP_COLUMNS = 76

_MARKER_RE = re.compile(
	r"<!--\s*mkdocs-note:encrypted\s+v(?P<version>\d+)\s+"
	r"key=(?P<field>[A-Za-z_][A-Za-z0-9_-]*)\s*\n"
	r"(?P<b64>[A-Za-z0-9+/=\s]*?)\s*-->"
)


class EnvelopeError(keys.CryptoError):
	"""The note looks like an envelope but cannot be parsed."""


@dataclass(frozen=True)
class Envelope:
	"""A parsed at-rest envelope."""

	frontmatter: str
	"""The original frontmatter block, including the ``---`` delimiters."""

	meta: dict[str, Any]
	"""Frontmatter parsed from :attr:`frontmatter`."""

	key_field: str
	"""Frontmatter field that holds the password (``password``/``permalink``)."""

	payload: bytes
	"""``nonce || ciphertext || tag``."""

	body: str
	"""Everything after the frontmatter, including the notice and comment."""


def normalize_text(text: str) -> str:
	"""Drop a UTF-8 BOM and convert CRLF/CR line endings to LF."""
	if text.startswith("﻿"):
		text = text[1:]
	return text.replace("\r\n", "\n").replace("\r", "\n")


def split_frontmatter(text: str) -> tuple[str, str, dict[str, Any]] | None:
	"""Split YAML frontmatter from a note with MkDocs' own boundary rules.

	Returns:
		``(frontmatter, body, meta)`` with the frontmatter text kept verbatim,
		or ``None`` when the file has no YAML frontmatter.
	"""
	match = mkdocs_meta.YAML_RE.match(text)
	if match is None:
		return None
	try:
		loaded = yaml.safe_load(match.group(1))
	except yaml.YAMLError:
		loaded = None
	meta = loaded if isinstance(loaded, dict) else {}
	return match.group(0), text[match.end() :], meta


def _marker_in_body(body: str) -> re.Match[str] | None:
	"""Return the envelope marker only when it opens the note body.

	A real envelope starts with the public notice followed by the marker
	comment. Matching the marker anywhere would misclassify documentation that
	mentions the format (``crypt check`` would reject it) and, worse, make
	``clean`` pass a flagged plaintext note through unchanged.
	"""
	pos = 1 if body.startswith("﻿") else 0
	while pos < len(body) and body[pos].isspace():
		pos += 1
	if not body.startswith(NOTICE, pos):
		return None
	pos += len(NOTICE)
	while pos < len(body) and body[pos].isspace():
		pos += 1
	return _MARKER_RE.match(body, pos)


def looks_encrypted(text: str) -> bool:
	"""Return whether *text* is an at-rest envelope (notice + marker header)."""
	split = split_frontmatter(text)
	body = split[1] if split is not None else text
	return _marker_in_body(body) is not None


def _decode_payload(match: re.Match[str]) -> bytes:
	b64 = re.sub(r"\s+", "", match.group("b64"))
	try:
		payload = base64.b64decode(b64, validate=True)
	except (binascii.Error, ValueError) as exc:
		raise EnvelopeError("Encrypted payload is not valid base64.") from exc
	if len(payload) < keys.NONCE_SIZE + keys.TAG_SIZE:
		raise EnvelopeError("Encrypted payload is truncated.")
	return payload


def parse_envelope(text: str) -> Envelope | None:
	"""Parse an envelope, or return ``None`` when *text* is not one.

	Raises:
		EnvelopeError: when the marker exists but the payload or version is
			invalid.
	"""
	split = split_frontmatter(text)
	if split is None:
		return None
	frontmatter, body, meta = split
	match = _marker_in_body(body)
	if match is None:
		return None
	version = int(match.group("version"))
	if version != FORMAT_VERSION:
		raise EnvelopeError(
			f"Unsupported encrypted envelope version {version}; "
			f"this mkdocs-note understands v{FORMAT_VERSION}."
		)
	return Envelope(
		frontmatter=frontmatter,
		meta=meta,
		key_field=match.group("field"),
		payload=_decode_payload(match),
		body=body,
	)


def build_envelope(text: str, key_field: str, password: str) -> str:
	"""Encrypt the body of *text* and return the envelope representation."""
	split = split_frontmatter(text)
	if split is None:
		raise EnvelopeError(
			"Cannot encrypt a note without YAML frontmatter delimited by '---'."
		)
	frontmatter, body, _meta = split
	payload = keys.seal_at_rest(password, key_field, body.encode("utf-8"))
	encoded = base64.b64encode(payload).decode("ascii")
	wrapped = "\n".join(textwrap.wrap(encoded, WRAP_COLUMNS))
	return (
		f"{frontmatter}\n{NOTICE}\n\n"
		f"<!-- {MARKER} v{FORMAT_VERSION} key={key_field}\n{wrapped}\n-->\n"
	)


def decrypt_envelope(text: str, password: str | None = None) -> str:
	"""Decrypt a whole-file envelope.

	When *password* is omitted it is read from the frontmatter field recorded in
	the envelope header.
	"""
	envelope = parse_envelope(text)
	if envelope is None:
		return text
	if password is None:
		password = keys.password_for_field(envelope.meta, envelope.key_field)
	plaintext = keys.open_at_rest(password, envelope.key_field, envelope.payload)
	try:
		body = plaintext.decode("utf-8")
	except UnicodeDecodeError as exc:
		raise EnvelopeError("Decrypted body is not valid UTF-8.") from exc
	return envelope.frontmatter + body


def decrypt_body(
	body: str,
	meta: dict[str, Any],
	password: str | None = None,
) -> str:
	"""Decrypt the body of a page when MkDocs already removed its frontmatter.

	The password is taken from *meta* using the key field recorded in the
	envelope header. A body without a marker is returned unchanged.
	"""
	match = _marker_in_body(body)
	if match is None:
		return body
	key_field = match.group("field")
	if password is None:
		password = keys.password_for_field(meta, key_field)
	payload = _decode_payload(match)
	plaintext = keys.open_at_rest(password, key_field, payload)
	try:
		return plaintext.decode("utf-8")
	except UnicodeDecodeError as exc:
		raise EnvelopeError("Decrypted body is not valid UTF-8.") from exc


def clean_bytes(data: bytes) -> bytes:
	"""Git clean filter: plaintext note bytes -> envelope bytes.

	Files that are not flagged (or are not valid UTF-8) pass through
	byte-for-byte. Flagged files are normalized to UTF-8 without BOM and with LF
	line endings so the envelope is stable across platforms.
	"""
	try:
		text = data.decode("utf-8")
	except UnicodeDecodeError:
		return data
	normalized = normalize_text(text)
	split = split_frontmatter(normalized)
	if split is None:
		return data
	_frontmatter, body, meta = split
	if not keys.is_encrypted(meta):
		return data
	if _marker_in_body(body) is not None:
		# Already an envelope; clean is idempotent.
		return normalized.encode("utf-8")
	source = keys.resolve_password(meta)
	envelope = build_envelope(normalized, source.field, source.password)
	return envelope.encode("utf-8")


def smudge_bytes(data: bytes) -> bytes:
	"""Git smudge filter: envelope bytes -> plaintext note bytes.

	A checkout must never fail because of a password problem, so an
	undecryptable envelope is emitted unchanged with a single stderr warning.
	"""
	try:
		text = data.decode("utf-8")
	except UnicodeDecodeError:
		return data
	normalized = normalize_text(text)
	try:
		envelope = parse_envelope(normalized)
	except EnvelopeError as exc:
		_warn_smudge(exc)
		return data
	if envelope is None:
		return data
	try:
		password = keys.password_for_field(envelope.meta, envelope.key_field)
		plaintext = keys.open_at_rest(password, envelope.key_field, envelope.payload)
		body = plaintext.decode("utf-8")
	except (keys.CryptoError, UnicodeDecodeError) as exc:
		_warn_smudge(exc)
		return data
	return (envelope.frontmatter + body).encode("utf-8")


def _warn_smudge(error: Exception) -> None:
	print(
		f"mkdocs-note: warning: cannot decrypt an encrypted note during "
		f"checkout ({error}); leaving the envelope unchanged.",
		file=sys.stderr,
	)
