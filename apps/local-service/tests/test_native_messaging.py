import io
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from live_translate_subtitles.native_messaging import MessageWriter, read_message


class NativeMessagingTests(unittest.TestCase):
    def test_message_round_trip(self) -> None:
        stream = io.BytesIO()
        MessageWriter(stream).write({"protocolVersion": 1, "type": "test", "text": "繁中"})
        stream.seek(0)

        self.assertEqual(
            read_message(stream),
            {"protocolVersion": 1, "type": "test", "text": "繁中"},
        )

    def test_end_of_stream_returns_none(self) -> None:
        self.assertIsNone(read_message(io.BytesIO()))


if __name__ == "__main__":
    unittest.main()
