import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from live_translate_subtitles.contracts import (
    TranscriptSegment,
    TranslationRequest,
)


class ContractTests(unittest.TestCase):
    def test_translation_context_defaults_to_empty(self) -> None:
        request = TranslationRequest(
            text="Hello",
            source_language="en",
            target_language="zh-TW",
        )
        self.assertEqual(request.context, ())

    def test_final_transcript_keeps_timing(self) -> None:
        segment = TranscriptSegment(
            segment_id="segment-1",
            source_language="en",
            text="Hello",
            start_time_ms=100,
            end_time_ms=900,
            is_final=True,
        )
        self.assertGreater(segment.end_time_ms, segment.start_time_ms)
        self.assertTrue(segment.is_final)


if __name__ == "__main__":
    unittest.main()
