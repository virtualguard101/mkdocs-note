"""Cryptographic primitives for mkdocs-note page encryption.

Two independent layers are used:

``at rest``
    Encrypts the body of a note before it enters git. The password is stored in
    the same file's clear frontmatter, so a fast HKDF is deliberate: a slow KDF
    would add build cost without protecting anything the reader cannot already
    see.

``site``
    Encrypts the rendered page for the browser. When a private repository
    publishes a public site the frontmatter is not public, so the slow
    PBKDF2-HMAC-SHA256 stretch is what protects the password.

Both layers use AES-256-GCM with a synthetic nonce derived through HMAC. A
synthetic nonce keeps encryption deterministic, which gives stable ``git
status`` output and reproducible builds; the AAD binds a payload to its page or
key field.
"""

from __future__ import annotations

import hashlib
import hmac
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from mkdocs.plugins import get_plugin_logger

logger = get_plugin_logger(__name__)

AT_REST_SALT = b"mkdocs-note/v1/at-rest"
AT_REST_INFO_ENC = b"mkdocs-note/v1/at-rest/enc"
AT_REST_INFO_NONCE = b"mkdocs-note/v1/at-rest/nonce"
SITE_INFO_NONCE = b"mkdocs-note/v1/site/nonce"
SITE_AAD_PREFIX = "mkdocs-note:v1:site:"
NONCE_SIZE = 12
TAG_SIZE = 16
KEY_SIZE = 32

DEFAULT_ITERATIONS = 600_000
PASSWORD_FIELDS = ("password", "permalink")


class CryptoError(Exception):
	"""Base class for encryption/decryption failures."""


class PasswordError(CryptoError):
	"""The frontmatter does not define a usable password."""


class DecryptError(CryptoError):
	"""The password is wrong or the ciphertext was tampered with."""


@dataclass(frozen=True)
class PasswordSource:
	"""The frontmatter field a password was taken from."""

	field: str
	password: str


def normalize_password(value: Any) -> str:
	"""Normalize a password the same way Python and JavaScript do.

	A Unicode NFC form plus surrounding-whitespace stripping keeps a password
	typed in a browser equal to the YAML value even when the source contains
	combining characters or accidental spacing.
	"""
	text = value if isinstance(value, str) else str(value)
	return unicodedata.normalize("NFC", text).strip()


def _warn_non_string(field: str, value: Any) -> None:
	if isinstance(value, str):
		return
	logger.warning(
		"Encryption field %r has a non-string YAML value (%r). Quote it in the "
		'frontmatter, e.g. %s: "%s".',
		field,
		value,
		field,
		value,
	)


def is_encrypted(meta: Mapping[str, Any]) -> bool:
	"""Return whether a page's frontmatter opts into encryption."""
	return bool(meta.get("encrypt", False))


def password_for_field(meta: Mapping[str, Any], field: str) -> str:
	"""Read the password stored in an explicit frontmatter *field*.

	Used for envelopes, whose header records which field was used when the
	ciphertext was created. Raises :class:`PasswordError` when the field is
	missing or empty.
	"""
	if field not in PASSWORD_FIELDS:
		raise PasswordError(
			f"Unsupported encryption key field {field!r}; expected one of "
			f"{', '.join(PASSWORD_FIELDS)}."
		)
	value = meta.get(field)
	if value is None:
		raise PasswordError(
			f"Frontmatter field {field!r} is missing; it is the password for "
			"this encrypted note."
		)
	password = normalize_password(value)
	if not password:
		raise PasswordError(
			f"Frontmatter field {field!r} is empty; it is the password for this "
			"encrypted note."
		)
	_warn_non_string(field, value)
	return password


def resolve_password(meta: Mapping[str, Any]) -> PasswordSource:
	"""Resolve a page's password: ``password`` first, then ``permalink``.

	Raises:
		PasswordError: when neither field is present and non-empty.
	"""
	for field in PASSWORD_FIELDS:
		value = meta.get(field)
		if value is None:
			continue
		password = normalize_password(value)
		if not password:
			continue
		_warn_non_string(field, value)
		return PasswordSource(field=field, password=password)
	raise PasswordError(
		"encrypt: true requires a non-empty 'password' or 'permalink' in the "
		"frontmatter."
	)


def _hkdf(ikm: bytes, *, salt: bytes, info: bytes, length: int = KEY_SIZE) -> bytes:
	return HKDF(
		algorithm=hashes.SHA256(),
		length=length,
		salt=salt,
		info=info,
	).derive(ikm)


def at_rest_aad(key_field: str) -> bytes:
	"""Additional authenticated data for an at-rest envelope."""
	return f"mkdocs-note:v1:{key_field}".encode("utf-8")


def _seal(
	enc_key: bytes,
	nonce_key: bytes,
	plaintext: bytes,
	aad: bytes,
) -> bytes:
	nonce = hmac.new(nonce_key, aad + b"\x00" + plaintext, hashlib.sha256).digest()[
		:NONCE_SIZE
	]
	ciphertext = AESGCM(enc_key).encrypt(nonce, plaintext, aad)
	return nonce + ciphertext


def _open(enc_key: bytes, payload: bytes, aad: bytes) -> bytes:
	if len(payload) < NONCE_SIZE + TAG_SIZE:
		raise DecryptError("Encrypted payload is truncated.")
	nonce = payload[:NONCE_SIZE]
	ciphertext = payload[NONCE_SIZE:]
	try:
		return AESGCM(enc_key).decrypt(nonce, ciphertext, aad)
	except InvalidTag as exc:
		raise DecryptError("Incorrect password or corrupted payload.") from exc


def seal_at_rest(password: str, key_field: str, plaintext: bytes) -> bytes:
	"""Encrypt a note body for storage in git.

	Returns ``nonce || ciphertext || tag``. The encryption is deterministic for
	the same ``(password, key_field, plaintext)`` triple.
	"""
	ikm = password.encode("utf-8")
	enc_key = _hkdf(ikm, salt=AT_REST_SALT, info=AT_REST_INFO_ENC)
	nonce_key = _hkdf(ikm, salt=AT_REST_SALT, info=AT_REST_INFO_NONCE)
	return _seal(enc_key, nonce_key, plaintext, at_rest_aad(key_field))


def open_at_rest(password: str, key_field: str, payload: bytes) -> bytes:
	"""Decrypt an at-rest payload produced by :func:`seal_at_rest`."""
	ikm = password.encode("utf-8")
	enc_key = _hkdf(ikm, salt=AT_REST_SALT, info=AT_REST_INFO_ENC)
	return _open(enc_key, payload, at_rest_aad(key_field))


def site_aad(src_uri: str) -> bytes:
	"""Additional authenticated data for a browser payload."""
	return (SITE_AAD_PREFIX + src_uri).encode("utf-8")


def site_salt(src_uri: str) -> bytes:
	"""Stable per-page PBKDF2 salt.

	The salt only has to separate pages, not to be secret; deriving it from the
	stable ``src_uri`` keeps a remembered browser key valid across deploys.
	"""
	return hashlib.sha256(site_aad(src_uri)).digest()[:16]


@lru_cache(maxsize=128)
def _pbkdf2(password: str, salt: bytes, iterations: int) -> bytes:
	return hashlib.pbkdf2_hmac(
		"sha256", password.encode("utf-8"), salt, iterations, dklen=KEY_SIZE
	)


def site_key(password: str, salt: bytes, iterations: int) -> bytes:
	"""Derive the browser AES key with PBKDF2-HMAC-SHA256.

	Results are cached per process so ``mkdocs serve`` rebuilds do not pay the
	600k-iteration cost again for an unchanged page.
	"""
	if iterations < 1:
		raise CryptoError("kdf_iterations must be a positive integer.")
	return _pbkdf2(password, salt, iterations)


def site_nonce_key(key: bytes) -> bytes:
	"""Derive the HMAC key used for deterministic site-payload nonces."""
	return _hkdf(key, salt=b"mkdocs-note/v1/site", info=SITE_INFO_NONCE)


def seal_site(
	password: str,
	src_uri: str,
	plaintext: bytes,
	iterations: int = DEFAULT_ITERATIONS,
) -> tuple[bytes, bytes, bytes]:
	"""Encrypt a rendered page for the browser.

	Returns ``(salt, aad, nonce || ciphertext || tag)``.
	"""
	salt = site_salt(src_uri)
	aad = site_aad(src_uri)
	key = site_key(password, salt, iterations)
	return salt, aad, _seal(key, site_nonce_key(key), plaintext, aad)


def open_site(
	password: str,
	src_uri: str,
	payload: bytes,
	iterations: int = DEFAULT_ITERATIONS,
) -> bytes:
	"""Decrypt a browser payload (used by tests and tooling)."""
	salt = site_salt(src_uri)
	key = site_key(password, salt, iterations)
	return _open(key, payload, site_aad(src_uri))
