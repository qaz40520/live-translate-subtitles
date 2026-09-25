import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from live_translate_subtitles.nllb_engine import _language_code


class NllbEngineTests(unittest.TestCase):
    def test_maps_supported_whisper_languages_to_flores_codes(self) -> None:
        self.assertEqual(_language_code("en"), "eng_Latn")
        self.assertEqual(_language_code("ja"), "jpn_Jpan")
        self.assertEqual(_language_code("ko"), "kor_Hang")
        self.assertEqual(_language_code("zh-TW"), "zho_Hant")

    def test_rejects_an_unmapped_language(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported translation language"):
            _language_code("xx")


if __name__ == "__main__":
    unittest.main()
