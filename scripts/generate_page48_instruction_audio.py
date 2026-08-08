#!/usr/bin/env python3
"""Regenerate the corrected page 48 instruction in both reading modes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
IDS = ("pg030_n0023", "pg030_n0023_easy_read")


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    clips = []
    with tempfile.TemporaryDirectory(prefix="adt-page48-instruction-") as temp:
        temp_dir = Path(temp)
        for text_id in IDS:
            visible = texts[text_id]
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run([
                "/usr/bin/say", "-v", "Tessa", "-r", "145", "-o", str(wav_path),
                "--data-format=LEI16@24000", visible,
            ], check=True)
            filename = f"{text_id}.mp3"
            path = I18N / "audio" / filename
            encode_mp3(wav_path, path)
            if path.stat().st_size <= 768:
                raise RuntimeError(f"Invalid generated audio: {text_id}")
            audios[text_id] = filename
            clips.append({
                "textId": text_id,
                "visibleTextSha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(),
                "spokenText": visible,
                "audioBytes": path.stat().st_size,
            })
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in IDS:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "page48-instruction-audio-report.json").write_text(json.dumps({
        "voice": "Tessa", "speakingRateWordsPerMinute": 145, "clips": clips,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Generated 2 corrected page 48 instruction clips")


if __name__ == "__main__":
    main()
