import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from live_translate_subtitles.contracts import TranslationRequest
from live_translate_subtitles.ollama_engine import _translation_prompt


class TranslateGemmaPromptTests(unittest.TestCase):
    def test_korean_to_traditional_chinese_prompt_uses_explicit_language_codes(self) -> None:
        prompt = _translation_prompt(
            TranslationRequest(
                text="오늘은 정말 재미있었어요.",
                source_language="ko",
                target_language="zh-TW",
            )
        )

        self.assertIn("Korean (ko)", prompt)
        self.assertIn("Traditional Chinese (zh-TW)", prompt)
        self.assertTrue(prompt.endswith("오늘은 정말 재미있었어요."))

    def test_rejects_unsupported_source_language(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported translation language"):
            _translation_prompt(
                TranslationRequest(
                    text="Bonjour",
                    source_language="fr",
                    target_language="zh-TW",
                )
            )


if __name__ == "__main__":
    unittest.main()
