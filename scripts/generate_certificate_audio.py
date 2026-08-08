#!/usr/bin/env python3
"""Regenerate only certificate narration changed by the PDF-faithful replica."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3, speech_text


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
TEXT_IDS = ("pg001_n0019", "pg001_n0019_easy_read")


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audio_path = I18N / "audios.json"
    audios = json.loads(audio_path.read_text(encoding="utf-8"))
    output = I18N / "audio"
    with tempfile.TemporaryDirectory(prefix="adt-certificate-audio-") as temp:
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
    audio_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in TEXT_IDS:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(TEXT_IDS)} certificate narration clips with Tessa")


if __name__ == "__main__":
    main()
