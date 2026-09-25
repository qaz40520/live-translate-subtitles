"""Native Messaging host entry point."""

from __future__ import annotations

import os
import sys
from typing import Any

from .native_messaging import MessageWriter, NativeMessagingError, read_message
from .nllb_engine import NllbTranslationEngine
from .session import TranscriptionSession


def _configure_binary_stdio() -> None:
    if os.name != "nt":
        return
    import msvcrt

    msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
    msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)


def run() -> int:
    _configure_binary_stdio()
    reader = sys.stdin.buffer
    writer = MessageWriter(sys.stdout.buffer)
    active: TranscriptionSession | None = None

    try:
        while True:
            message = read_message(reader)
            if message is None:
                break
            if message.get("protocolVersion") != 1:
                raise NativeMessagingError("Unsupported protocol version")

            message_type = message.get("type")
            if message_type == "session.start":
                if active is not None:
                    active.stop()
                session_id = _required_string(message, "sessionId")
                target_language = _required_string(message, "targetLanguage")
                active = TranscriptionSession(
                    session_id,
                    writer.write,
                    translator=NllbTranslationEngine(),
                    target_language=target_language,
                )
                active.start()
            elif message_type == "audio.chunk":
                session_id = _required_string(message, "sessionId")
                if active is not None and active.session_id == session_id:
                    active.submit_base64(message)
            elif message_type == "session.stop":
                if active is not None:
                    active.stop()
                    active = None
            else:
                raise NativeMessagingError(f"Unsupported message type: {message_type!r}")
    except (NativeMessagingError, ValueError) as error:
        print(f"Native messaging error: {error}", file=sys.stderr)
        return 2
    finally:
        if active is not None:
            active.stop()
    return 0


def _required_string(message: dict[str, Any], key: str) -> str:
    value = message.get(key)
    if not isinstance(value, str) or not value:
        raise NativeMessagingError(f"{key} must be a non-empty string")
    return value


def main() -> None:
    raise SystemExit(run())


if __name__ == "__main__":
    main()
