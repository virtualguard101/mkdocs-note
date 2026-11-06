"""Tests for the page-encryption key layer."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(
	0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from mkdocs_note.utils.crypt import keys


class TestPasswordResolution(unittest.TestCase):
	def test_password_takes_precedence(self):
		source = keys.resolve_password(
			{"encrypt": True, "password": "secret", "permalink": "slug"}
		)
		self.assertEqual(source.field, "password")
		self.assertEqual(source.password, "secret")

	def test_permalink_fallback(self):
		source = keys.resolve_password({"encrypt": True, "permalink": "slug"})
		self.assertEqual(source.field, "permalink")
		self.assertEqual(source.password, "slug")

	def test_empty_password_falls_back_to_permalink(self):
		source = keys.resolve_password(
			{"encrypt": True, "password": "  ", "permalink": "slug"}
		)
		self.assertEqual(source.field, "permalink")

	def test_missing_both_raises(self):
		with self.assertRaises(keys.PasswordError):
			keys.resolve_password({"encrypt": True})

	def test_empty_permalink_raises(self):
		with self.assertRaises(keys.PasswordError):
			keys.resolve_password({"encrypt": True, "permalink": ""})

	def test_normalizes_nfc_and_whitespace(self):
		# "é" as e + combining acute accent versus the precomposed character.
		source = keys.resolve_password({"encrypt": True, "password": "  café  "})
		self.assertEqual(source.password, "café")

	def test_password_for_explicit_field(self):
		self.assertEqual(
			keys.password_for_field(
				{"password": "secret", "permalink": "slug"}, "permalink"
			),
			"slug",
		)

	def test_password_for_unknown_field_raises(self):
		with self.assertRaises(keys.PasswordError):
			keys.password_for_field({"permalink": "slug"}, "title")

	def test_is_encrypted_truthiness(self):
		self.assertTrue(keys.is_encrypted({"encrypt": True}))
		self.assertFalse(keys.is_encrypted({"encrypt": False}))
		self.assertFalse(keys.is_encrypted({}))


class TestAtRestCrypto(unittest.TestCase):
	def test_round_trip(self):
		payload = keys.seal_at_rest("pw", "permalink", b"hello \xf0\x9f\x94\x92")
		self.assertEqual(
			keys.open_at_rest("pw", "permalink", payload), b"hello \xf0\x9f\x94\x92"
		)

	def test_deterministic(self):
		first = keys.seal_at_rest("pw", "permalink", b"same body")
		second = keys.seal_at_rest("pw", "permalink", b"same body")
		self.assertEqual(first, second)

	def test_wrong_password_rejected(self):
		payload = keys.seal_at_rest("pw", "permalink", b"body")
		with self.assertRaises(keys.DecryptError):
			keys.open_at_rest("other", "permalink", payload)

	def test_tampered_payload_rejected(self):
		payload = bytearray(keys.seal_at_rest("pw", "permalink", b"body"))
		payload[-1] ^= 0xFF
		with self.assertRaises(keys.DecryptError):
			keys.open_at_rest("pw", "permalink", bytes(payload))

	def test_key_field_is_authenticated(self):
		payload = keys.seal_at_rest("pw", "permalink", b"body")
		with self.assertRaises(keys.DecryptError):
			keys.open_at_rest("pw", "password", payload)

	def test_truncated_payload_rejected(self):
		with self.assertRaises(keys.DecryptError):
			keys.open_at_rest("pw", "permalink", b"short")


class TestSiteCrypto(unittest.TestCase):
	def test_round_trip(self):
		plaintext = '{"v":1,"content":"你好"}'.encode("utf-8")
		_salt, _aad, sealed = keys.seal_site("pw", "note/a.md", plaintext, 1000)
		self.assertEqual(keys.open_site("pw", "note/a.md", sealed, 1000), plaintext)

	def test_deterministic(self):
		args = ("pw", "note/a.md", b"page", 1000)
		self.assertEqual(keys.seal_site(*args), keys.seal_site(*args))

	def test_salt_is_stable_and_page_specific(self):
		self.assertEqual(keys.site_salt("a.md"), keys.site_salt("a.md"))
		self.assertNotEqual(keys.site_salt("a.md"), keys.site_salt("b.md"))
		self.assertEqual(len(keys.site_salt("a.md")), 16)

	def test_pbkdf2_known_answer(self):
		# RFC 7914 / widely published PBKDF2-HMAC-SHA256 vector.
		self.assertEqual(
			keys._pbkdf2("password", b"salt", 1).hex(),
			"120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b",
		)

	def test_hkdf_known_answer(self):
		# RFC 5869 test case 1.
		ikm = b"\x0b" * 22
		salt = bytes(range(13))
		info = bytes(range(0xF0, 0xFA))
		okm = keys._hkdf(ikm, salt=salt, info=info, length=42)
		self.assertEqual(
			okm.hex(),
			"3cb25f25faacd57a90434f64d0362f2a"
			"2d2d0a90cf1a5a4c5db02d56ecc4c5bf"
			"34007208d5b887185865",
		)

	def test_iterations_must_be_positive(self):
		with self.assertRaises(keys.CryptoError):
			keys.site_key("pw", b"salt", 0)


if __name__ == "__main__":
	unittest.main()
