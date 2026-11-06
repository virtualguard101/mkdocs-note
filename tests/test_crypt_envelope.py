"""Tests for the at-rest note envelope format."""

from __future__ import annotations

import os
import re
import sys
import unittest

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.crypt import envelope, keys

PLAIN = (
	"---\n"
	"title: 测试笔记\n"
	"date: 2026-11-06 09:02:00\n"
	"permalink: 11408-resource\n"
	"publish: true\n"
	"encrypt: true\n"
	"---\n"
	"\n"
	"## 第一节\n"
	"\n"
	"这是一段需要加密的正文。\n"
)


class TestEnvelopeRoundTrip(unittest.TestCase):
	def test_build_parse_round_trip(self):
		built = envelope.build_envelope(PLAIN, "permalink", "11408-resource")
		parsed = envelope.parse_envelope(built)
		self.assertIsNotNone(parsed)
		assert parsed is not None
		self.assertEqual(parsed.key_field, "permalink")
		self.assertEqual(parsed.meta["permalink"], "11408-resource")
		self.assertIn(envelope.NOTICE, built)
		self.assertNotIn("这是一段需要加密的正文", built)
		self.assertEqual(envelope.decrypt_envelope(built), PLAIN)

	def test_smudge_after_clean_is_byte_exact(self):
		cleaned = envelope.clean_bytes(PLAIN.encode("utf-8"))
		self.assertNotEqual(cleaned, PLAIN.encode("utf-8"))
		self.assertEqual(envelope.smudge_bytes(cleaned), PLAIN.encode("utf-8"))

	def test_leading_blank_lines_preserved(self):
		text = PLAIN.replace("---\n\n##", "---\n\n\n##")
		cleaned = envelope.clean_bytes(text.encode("utf-8"))
		self.assertEqual(envelope.smudge_bytes(cleaned), text.encode("utf-8"))

	def test_deterministic_envelope(self):
		first = envelope.clean_bytes(PLAIN.encode("utf-8"))
		second = envelope.clean_bytes(PLAIN.encode("utf-8"))
		self.assertEqual(first, second)

	def test_clean_is_idempotent(self):
		cleaned = envelope.clean_bytes(PLAIN.encode("utf-8"))
		self.assertEqual(envelope.clean_bytes(cleaned), cleaned)

	def test_key_field_in_header_is_honored(self):
		built = envelope.build_envelope(PLAIN, "permalink", "11408-resource")
		# Adding an unrelated password field must not change how smudge reads
		# the existing envelope.
		with_password = built.replace(
			"encrypt: true\n", "encrypt: true\npassword: other\n"
		)
		expected = PLAIN.replace("encrypt: true\n", "encrypt: true\npassword: other\n")
		self.assertEqual(envelope.decrypt_envelope(with_password), expected)

	def test_wrong_password_raises(self):
		built = envelope.build_envelope(PLAIN, "permalink", "right")
		with self.assertRaises(keys.DecryptError):
			envelope.decrypt_envelope(built, password="wrong")

	def test_corrupt_base64_raises(self):
		built = envelope.build_envelope(PLAIN, "permalink", "pw")
		# Marker intact, payload replaced with invalid base64 padding.
		corrupt = re.sub(
			r"(v1 key=permalink\n)[A-Za-z0-9+/=\n]+(-->)",
			r"\1abc\2",
			built,
		)
		with self.assertRaises(envelope.EnvelopeError):
			envelope.parse_envelope(corrupt)

	def test_unsupported_version_raises(self):
		built = envelope.build_envelope(PLAIN, "permalink", "pw")
		with self.assertRaises(envelope.EnvelopeError):
			envelope.parse_envelope(built.replace("encrypted v1 ", "encrypted v9 "))

	def test_body_without_marker_returns_unchanged(self):
		body = "just a plain body\n"
		self.assertEqual(envelope.decrypt_body(body, {}), body)

	def test_marker_mention_in_prose_is_not_an_envelope(self):
		"""Only a notice + marker header at the start marks an envelope."""
		mentioned = PLAIN + "\n<!-- mkdocs-note:encrypted v1 key=permalink\nAAAA\n-->\n"
		self.assertFalse(envelope.looks_encrypted(mentioned))
		self.assertIsNone(envelope.parse_envelope(mentioned))
		_frontmatter, body, meta = envelope.split_frontmatter(mentioned)
		self.assertEqual(envelope.decrypt_body(body, meta), body)

	def test_flagged_note_mentioning_marker_is_still_encrypted(self):
		"""An inline marker mention must not make clean skip encryption."""
		mentioned = PLAIN + "\n<!-- mkdocs-note:encrypted v1 key=permalink\nAAAA\n-->\n"
		cleaned = envelope.clean_bytes(mentioned.encode("utf-8"))
		self.assertNotEqual(cleaned, mentioned.encode("utf-8"))
		self.assertNotIn("这是一段需要加密的正文", cleaned.decode("utf-8"))
		self.assertEqual(envelope.decrypt_envelope(cleaned.decode("utf-8")), mentioned)


class TestCleanPassthrough(unittest.TestCase):
	def test_non_flagged_file_is_byte_identical(self):
		data = b"---\r\ntitle: x\r\n---\r\n\r\nbody\r\n"
		self.assertEqual(envelope.clean_bytes(data), data)

	def test_non_flagged_bom_preserved(self):
		data = b"\xef\xbb\xbf---\ntitle: x\n---\nbody\n"
		self.assertEqual(envelope.clean_bytes(data), data)

	def test_invalid_utf8_passthrough(self):
		data = b"---\ntitle: \xff\xfe\n---\nbody\n"
		self.assertEqual(envelope.clean_bytes(data), data)
		self.assertEqual(envelope.smudge_bytes(data), data)

	def test_no_frontmatter_passthrough(self):
		data = b"plain text, no frontmatter\n"
		self.assertEqual(envelope.clean_bytes(data), data)

	def test_unflagged_body_containing_marker_passthrough(self):
		data = b"---\ntitle: x\n---\n<!-- mkdocs-note:encrypted v1 key=permalink\nAAAA\n-->\n"
		self.assertEqual(envelope.clean_bytes(data), data)

	def test_missing_password_raises_for_flagged_file(self):
		data = (
			b"---\ntitle: x\ndate: 2026-11-06\nencrypt: true\npublish: true\n---\n"
			b"body\n"
		)
		with self.assertRaises(keys.PasswordError):
			envelope.clean_bytes(data)


class TestLineEndings(unittest.TestCase):
	def test_crlf_flagged_plaintext_normalizes(self):
		crlf = PLAIN.replace("\n", "\r\n")
		cleaned = envelope.clean_bytes(crlf.encode("utf-8"))
		lf = PLAIN.encode("utf-8")
		self.assertEqual(cleaned, envelope.clean_bytes(lf))
		self.assertEqual(envelope.smudge_bytes(cleaned), lf)

	def test_bom_flagged_plaintext_drops_bom(self):
		data = ("﻿" + PLAIN).encode("utf-8")
		cleaned = envelope.clean_bytes(data)
		self.assertEqual(cleaned, envelope.clean_bytes(PLAIN.encode("utf-8")))

	def test_crlf_converted_envelope_smudges(self):
		cleaned = envelope.clean_bytes(PLAIN.encode("utf-8"))
		crlf_envelope = cleaned.replace(b"\n", b"\r\n")
		self.assertEqual(envelope.smudge_bytes(crlf_envelope), PLAIN.encode("utf-8"))

	def test_undecryptable_envelope_is_left_alone_on_smudge(self):
		cleaned = envelope.clean_bytes(PLAIN.encode("utf-8"))
		changed = cleaned.replace(b"permalink: 11408-resource", b"permalink: changed")
		# The envelope header still points at permalink; the password no longer
		# matches, so smudge keeps the envelope bytes rather than failing.
		self.assertEqual(envelope.smudge_bytes(changed), changed)


class TestDecryptBody(unittest.TestCase):
	def test_decrypt_body_with_meta(self):
		built = envelope.build_envelope(PLAIN, "permalink", "11408-resource")
		frontmatter, body, meta = envelope.split_frontmatter(built)
		self.assertTrue(envelope.looks_encrypted(built))
		self.assertEqual(envelope.decrypt_body(body, meta), PLAIN[len(frontmatter) :])

	def test_decrypt_body_plaintext_is_noop(self):
		frontmatter, body, meta = envelope.split_frontmatter(PLAIN)
		self.assertEqual(envelope.decrypt_body(body, meta), body)


if __name__ == "__main__":
	unittest.main()
