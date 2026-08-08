#!/usr/bin/env python3
"""Regenerate every instruction changed from 'Study of' to 'Study at'."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3
from swahili_pronunciations import apply_pronunciations

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
BASE_IDS = ("pg013_n0014", "pg029_n0002", "pg033_n0016", "pg035_n0006", "pg037_n0002", "pg038_n0007", "pg048_n0006", "pg050_n0006")
IDS = BASE_IDS + tuple(f"{text_id}_easy_read" for text_id in BASE_IDS)


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    clips = []
    with tempfile.TemporaryDirectory(prefix="adt-study-at-pictures-") as temp:
        temp_dir = Path(temp)
        for text_id in IDS:
            visible = str(texts[text_id])
            spoken = apply_pronunciations(visible)
            spoken = re.sub(r"^1\.\s*", "Number one. ", spoken)
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run(["/usr/bin/say", "-v", "Tessa", "-r", "145", "-o", str(wav_path), "--data-format=LEI16@24000", spoken], check=True)
            filename = f"{text_id}.mp3"
            path = I18N / "audio" / filename
            encode_mp3(wav_path, path)
            if path.stat().st_size <= 768:
                raise RuntimeError(f"Invalid instruction audio: {text_id}")
            audios[text_id] = filename
            clips.append({"textId": text_id, "visibleTextSha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(), "spokenText": spoken, "audioBytes": path.stat().st_size})
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in IDS:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "study-at-pictures-audio-report.json").write_text(json.dumps({"voice": "Tessa", "speakingRateWordsPerMinute": 145, "clips": clips}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(IDS)} corrected instruction clips")


if __name__ == "__main__":
    main()
