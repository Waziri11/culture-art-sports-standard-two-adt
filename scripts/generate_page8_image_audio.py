#!/usr/bin/env python3
"""Regenerate the two numbered image descriptions on reader page 8."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3, speech_text


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
TEXT_IDS = ("pg008_im001", "pg008_im002")


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    output = I18N / "audio"

    with tempfile.TemporaryDirectory(prefix="adt-page8-image-audio-") as temp:
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
            filename = f"{text_id}.mp3"
            encode_mp3(wav_path, output / filename)
            audios[text_id] = filename

    audios_path.write_text(
        json.dumps(audios, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print("Generated two numbered page 8 image-description clips with Tessa")


if __name__ == "__main__":
    main()
