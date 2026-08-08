#!/usr/bin/env python3
"""Regenerate the corrected original-PDF instruction on reader page 10."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3, speech_text


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
TEXT_IDS = ("pg009_n0014", "pg009_n0014_easy_read")


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    output = I18N / "audio"
    with tempfile.TemporaryDirectory(prefix="adt-page10-audio-") as temp:
        temp_dir = Path(temp)
        for text_id in TEXT_IDS:
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run(
                [
                    "/usr/bin/say", "-v", "Tessa", "-r", "155",
                    "-o", str(wav_path), "--data-format=LEI16@24000",
                    speech_text(text_id, texts[text_id]),
                ],
                check=True,
            )
            encode_mp3(wav_path, output / f"{text_id}.mp3")
    print("Generated page 10 standard and easy-read narration with Tessa")


if __name__ == "__main__":
    main()
