import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from live_translate_subtitles.faster_whisper_engine import _is_final_utterance


class UtteranceFinalizationTests(unittest.TestCase):
    def test_long_trailing_silence_finalizes_without_punctuation(self) -> None:
        self.assertTrue(_is_final_utterance("complete thought", 4.0, 3.1))

    def test_short_pause_keeps_partial_text_provisional(self) -> None:
        self.assertFalse(_is_final_utterance("still speaking", 4.0, 3.7))

    def test_punctuation_allows_a_shorter_sentence_pause(self) -> None:
        self.assertTrue(_is_final_utterance("This is complete.", 4.0, 3.6))


if __name__ == "__main__":
    unittest.main()
