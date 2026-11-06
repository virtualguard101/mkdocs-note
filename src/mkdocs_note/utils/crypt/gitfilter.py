"""Git clean/smudge filter for encrypted note bodies.

Implements the long-running filter process protocol, version 2, documented in
``gitattributes(5)`` under "Long Running Filter Process", plus the single-shot
``clean`` and ``smudge`` helpers used as fallbacks. Protocol data is the only
thing written to stdout; every diagnostic goes to stderr.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from typing import BinaryIO

from mkdocs_note.utils.crypt import envelope

FLUSH_PACKET = b"0000"
DELIM_PACKET = b"0001"
RESPONSE_END_PACKET = b"0002"
CLIENT_GREETING = b"git-filter-client"
SERVER_GREETING = b"git-filter-server"
PROTOCOL_VERSION = "2"
MAX_PACKET_DATA = 65500


class FilterProtocolError(RuntimeError):
	"""The peer sent data that is not valid pkt-line filter protocol."""


class PacketReader:
	"""Read pkt-line packets from a binary stream."""

	def __init__(self, stream: BinaryIO) -> None:
		self._stream = stream

	def read_packet(self) -> bytes | None:
		"""Read one packet; ``None`` means a flush/delimiter packet.

		Raises:
			EOFError: at end of stream.
			FilterProtocolError: on a malformed length header.
		"""
		header = self._stream.read(4)
		if not header:
			raise EOFError
		if len(header) != 4:
			raise FilterProtocolError("truncated pkt-line header")
		if header in (FLUSH_PACKET, DELIM_PACKET, RESPONSE_END_PACKET):
			return None
		try:
			size = int(header, 16)
		except ValueError as exc:
			raise FilterProtocolError(f"invalid pkt-line length {header!r}") from exc
		if size < 4:
			raise FilterProtocolError(f"invalid pkt-line length {size}")
		data = self._stream.read(size - 4)
		if len(data) != size - 4:
			raise FilterProtocolError("truncated pkt-line payload")
		return data


class PacketWriter:
	"""Write pkt-line packets to a binary stream."""

	def __init__(self, stream: BinaryIO) -> None:
		self._stream = stream

	def write_packet(self, data: bytes) -> None:
		"""Write one packet, splitting payloads larger than the pkt-line limit."""
		for start in range(0, len(data), MAX_PACKET_DATA):
			chunk = data[start : start + MAX_PACKET_DATA]
			self._stream.write(f"{len(chunk) + 4:04x}".encode("ascii"))
			self._stream.write(chunk)

	def write_content(self, data: bytes) -> None:
		"""Write file content; empty content is represented by the flush alone."""
		if data:
			self.write_packet(data)

	def write_flush(self) -> None:
		"""Write a flush packet."""
		self._stream.write(FLUSH_PACKET)

	def flush(self) -> None:
		"""Flush the underlying stream."""
		self._stream.flush()


@dataclass(frozen=True)
class FilterRequest:
	"""One ``clean`` or ``smudge`` request from git."""

	command: str
	pathname: str
	data: bytes


def _packet_text(packet: bytes) -> str:
	"""Decode a protocol key/value packet and drop git's trailing newline."""
	return packet.decode("utf-8", "replace").rstrip("\n")


def _handshake(
	reader: PacketReader,
	writer: PacketWriter,
	capabilities: frozenset[str],
) -> None:
	"""Negotiate protocol version 2 and the filter commands.

	The handshake has two phases:

	1. git sends ``git-filter-client``, the filter answers
	   ``git-filter-server``; git sends ``version=2``, the filter echoes it;
	   both finish with a flush packet.
	2. git lists the capabilities it supports (``clean``, ``smudge``,
	   ``delay``); the filter answers with the subset it implements.
	"""
	greeting = reader.read_packet()
	if greeting is None or _packet_text(greeting) != CLIENT_GREETING.decode():
		raise FilterProtocolError("expected a 'git-filter-client' greeting")

	version: str | None = None
	while True:
		packet = reader.read_packet()
		if packet is None:
			break
		text = _packet_text(packet)
		if text.startswith("version="):
			version = text.split("=", 1)[1]
	if version != PROTOCOL_VERSION:
		raise FilterProtocolError(
			f"unsupported filter protocol version {version!r}; expected 2"
		)
	writer.write_packet(SERVER_GREETING)
	writer.write_packet(f"version={PROTOCOL_VERSION}".encode("ascii"))
	writer.write_flush()
	writer.flush()

	requested: set[str] = set()
	while True:
		packet = reader.read_packet()
		if packet is None:
			break
		text = _packet_text(packet)
		if text.startswith("capability="):
			requested.add(text.split("=", 1)[1])
	agreed = sorted(requested & capabilities) if requested else sorted(capabilities)
	if not agreed:
		raise FilterProtocolError(
			"git did not request any capability this filter supports"
		)
	for capability in agreed:
		writer.write_packet(f"capability={capability}".encode("ascii"))
	writer.write_flush()
	writer.flush()


def _read_request(reader: PacketReader) -> FilterRequest | None:
	"""Read one request (metadata, flush, content, flush).

	Returns ``None`` for a stray flush packet, which is ignored.
	"""
	command: str | None = None
	pathname = ""
	packet = reader.read_packet()
	while packet is not None:
		text = _packet_text(packet)
		if text.startswith("command="):
			command = text.split("=", 1)[1]
		elif text.startswith("pathname="):
			pathname = text.split("=", 1)[1]
		packet = reader.read_packet()
	if command is None:
		return None

	chunks: list[bytes] = []
	while True:
		packet = reader.read_packet()
		if packet is None:
			break
		chunks.append(packet)
	return FilterRequest(command=command, pathname=pathname, data=b"".join(chunks))


def serve(
	reader: PacketReader,
	writer: PacketWriter,
	*,
	stderr: object | None = None,
	clean: Callable[[bytes], bytes] = envelope.clean_bytes,
	smudge: Callable[[bytes], bytes] = envelope.smudge_bytes,
) -> int:
	"""Serve filter requests until git closes the stream.

	Args:
		reader: Packet source (git's stdout end).
		writer: Packet sink (git's stdin end).
		stderr: Diagnostic stream (defaults to ``sys.stderr``).
		clean: Plaintext -> envelope transform.
		smudge: Envelope -> plaintext transform.

	Returns:
		Process exit status.
	"""
	err = stderr if stderr is not None else sys.stderr
	handlers = {"clean": clean, "smudge": smudge}
	try:
		_handshake(reader, writer, frozenset(handlers))
	except EOFError:
		return 0
	except FilterProtocolError as exc:
		print(f"mkdocs-note: filter handshake failed: {exc}", file=err)
		return 1

	while True:
		try:
			request = _read_request(reader)
		except EOFError:
			return 0
		except FilterProtocolError as exc:
			print(f"mkdocs-note: filter protocol error: {exc}", file=err)
			return 1
		if request is None:
			continue

		handler = handlers.get(request.command)
		if handler is None:
			message = f"unsupported filter command {request.command!r}"
			print(f"mkdocs-note: {message}", file=err)
			_write_error(writer, message)
			continue
		try:
			output = handler(request.data)
		except Exception as exc:  # noqa: BLE001 - report every failure to git
			prefix = f"{request.pathname}: " if request.pathname else ""
			message = f"{prefix}{exc}"
			print(f"mkdocs-note: {message}", file=err)
			_write_error(writer, message)
			continue

		writer.write_packet(b"status=success")
		writer.write_flush()
		writer.write_content(output)
		writer.write_flush()
		# An empty second status list keeps "status=success" unchanged.
		writer.write_flush()
		writer.flush()


def _write_error(writer: PacketWriter, message: str) -> None:
	"""Report a per-file failure; git aborts the operation and prints it."""
	writer.write_packet(b"status=error")
	writer.write_packet(message.encode("utf-8", "replace"))
	writer.write_flush()
	writer.flush()


def run_filter_process() -> int:
	"""Run the long-running filter process on stdin/stdout."""
	return serve(
		PacketReader(sys.stdin.buffer),
		PacketWriter(sys.stdout.buffer),
	)


def run_single(
	kind: str,
	*,
	stdin: BinaryIO | None = None,
	stdout: BinaryIO | None = None,
	stderr: object | None = None,
) -> int:
	"""Run a single-shot ``clean`` or ``smudge`` transform.

	Returns:
		Process exit status.
	"""
	source = stdin if stdin is not None else sys.stdin.buffer
	sink = stdout if stdout is not None else sys.stdout.buffer
	err = stderr if stderr is not None else sys.stderr
	data = source.read()
	try:
		output = (
			envelope.clean_bytes(data)
			if kind == "clean"
			else envelope.smudge_bytes(data)
		)
	except Exception as exc:  # noqa: BLE001 - the CLI turns this into stderr + exit 1
		print(f"mkdocs-note {kind}: {exc}", file=err)
		return 1
	sink.write(output)
	sink.flush()
	return 0
