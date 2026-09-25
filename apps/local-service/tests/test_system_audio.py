import sys
import unittest
from pathlib import Path

import numpy as np

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))

from live_translate_subtitles.system_audio import _float_audio_to_pcm_s16le


class SystemAudioTests(unittest.TestCase):
    def test_stereo_float_audio_is_mixed_to_mono_pcm(self) -> None:
        stereo = np.array([[1.0, -1.0], [0.5, 0.5]], dtype=np.float32)

        pcm = np.frombuffer(_float_audio_to_pcm_s16le(stereo), dtype="<i2")

        np.testing.assert_array_equal(pcm, np.array([0, 16383], dtype=np.int16))

    def test_samples_are_clipped_to_pcm_range(self) -> None:
        audio = np.array([-2.0, 2.0], dtype=np.float32)

        pcm = np.frombuffer(_float_audio_to_pcm_s16le(audio), dtype="<i2")

        np.testing.assert_array_equal(pcm, np.array([-32767, 32767], dtype=np.int16))


if __name__ == "__main__":
    unittest.main()
