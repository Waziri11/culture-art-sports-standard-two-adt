#!/usr/bin/env python3
"""Regenerate page 31 questions with explicit spoken question numbers."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
SPOKEN_TEXT = {
    "pg019_n0007": "Question one. Where do fishing activities take place?",
    "pg019_n0009": "Question two. What tools are used for fishing?",
    "pg019_n0007_easy_read": "Question one. Where does fishing activity take place?",
    "pg019_n0009_easy_read": "Question two. What tools do people use for fishing?",
}


def main() -> None:
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    output = I18N / "audio"

    with tempfile.TemporaryDirectory(prefix="adt-page31-question-audio-") as temp:
        temp_dir = Path(temp)
        for text_id, spoken in SPOKEN_TEXT.items():
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run(
                [
                    "/usr/bin/say", "-v", "Tessa", "-r", "155",
                    "-o", str(wav_path), "--data-format=LEI16@24000", spoken,
                ],
                check=True,
            )
            filename = f"{text_id}.mp3"
            encode_mp3(wav_path, output / filename)
            audios[text_id] = filename

    audios_path.write_text(
        json.dumps(audios, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Generated four numbered page 31 question clips with Tessa")


if __name__ == "__main__":
    main()
