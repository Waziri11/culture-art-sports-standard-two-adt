#!/usr/bin/env python3
"""Regenerate numbered items so every visible leading number is spoken."""

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
NUMBER_WORDS = {
    "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
}
LEADING_NUMBER = re.compile(r"^\s*(10|[1-9])[.)]\s+")


def spoken_text(visible: str) -> str:
    match = LEADING_NUMBER.match(visible)
    if not match:
        return visible
    body = visible[match.end():].replace("\n", ". ")
    body = re.sub(r"\s*_+\s*", ". ", body)
    body = apply_pronunciations(body)
    return re.sub(r"\s+", " ", f"Number {NUMBER_WORDS[match.group(1)]}. {body}").strip()


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    # Page 38 has a complete, separately approved story narration batch.
    ids = [
        text_id for text_id, visible in texts.items()
        if text_id in audios and LEADING_NUMBER.match(str(visible)) and not text_id.startswith("pg023_")
    ]
    clips = []
    with tempfile.TemporaryDirectory(prefix="adt-numbered-items-") as temp:
        temp_dir = Path(temp)
        for index, text_id in enumerate(ids, 1):
            visible = str(texts[text_id])
            spoken = spoken_text(visible)
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run([
                "/usr/bin/say", "-v", "Tessa", "-r", "145", "-o", str(wav_path),
                "--data-format=LEI16@24000", spoken,
            ], check=True)
            filename = f"{text_id}.mp3"
            path = I18N / "audio" / filename
            encode_mp3(wav_path, path)
            if path.stat().st_size <= 768:
                raise RuntimeError(f"Invalid numbered-item audio: {text_id}")
            audios[text_id] = filename
            clips.append({
                "textId": text_id,
                "visibleTextSha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(),
                "spokenText": spoken,
                "audioBytes": path.stat().st_size,
            })
            if index % 25 == 0:
                print(f"Generated {index}/{len(ids)}")
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in ids:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "numbered-item-audio-report.json").write_text(json.dumps({
        "voice": "Tessa", "speakingRateWordsPerMinute": 145,
        "selectionRule": "Mapped visible text beginning with 1.-10. or 1)-10), excluding complete page 38 batch",
        "clips": clips,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(ids)} numbered-item narration clips")


if __name__ == "__main__":
    main()
