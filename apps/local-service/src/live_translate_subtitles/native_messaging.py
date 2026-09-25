"""Chrome/Firefox Native Messaging framing helpers."""

from __future__ import annotations

import json
import struct
import threading
from collections.abc import Mapping
from typing import Any, BinaryIO

MAX_INBOUND_MESSAGE_BYTES = 4 * 1024 * 1024


class NativeMessagingError(RuntimeError):
    """Raised when a native message is malformed or unsafe to process."""


def read_message(stream: BinaryIO) -> dict[str, Any] | None:
    length_bytes = stream.read(4)
    if not length_bytes:
        return None
    if len(length_bytes) != 4:
        raise NativeMessagingError("Truncated native message header")

    (length,) = struct.unpack("=I", length_bytes)
    if length > MAX_INBOUND_MESSAGE_BYTES:
        raise NativeMessagingError(f"Native message exceeds {MAX_INBOUND_MESSAGE_BYTES} bytes")

    payload = stream.read(length)
    if len(payload) != length:
        raise NativeMessagingError("Truncated native message payload")

    value = json.loads(payload.decode("utf-8"))
    if not isinstance(value, dict):
        raise NativeMessagingError("Native message must be a JSON object")
    return value


class MessageWriter:
    """Thread-safe writer for framed native messages."""

    def __init__(self, stream: BinaryIO) -> None:
        self._stream = stream
        self._lock = threading.Lock()

    def write(self, message: Mapping[str, object]) -> None:
        payload = json.dumps(
            message,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        frame = struct.pack("=I", len(payload)) + payload
        with self._lock:
            self._stream.write(frame)
            self._stream.flush()
