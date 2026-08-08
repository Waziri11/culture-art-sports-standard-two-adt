#!/usr/bin/env python3
"""Regenerate narration for every text changed by either correction batch."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from apply_teacher_corrections import TEXT_UPDATES as TEACHER_TEXT_UPDATES
from apply_updated_accessibility_fixes import (
    EASY_READ_UPDATES,
    TEXT_UPDATES as ACCESSIBILITY_TEXT_UPDATES,
)
from generate_corrected_audio import encode_mp3, speech_text


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
NUMBER_WORDS = {
    "1": "One", "2": "Two", "3": "Three", "4": "Four", "5": "Five",
    "6": "Six", "7": "Seven", "8": "Eight", "9": "Nine", "10": "Ten",
}


def narration_text(text_id: str, visible_text: str) -> str:
    spoken = speech_text(text_id, visible_text)
    match = re.match(r"^(10|[1-9])\.\s*", spoken)
    if match:
        spoken = NUMBER_WORDS[match.group(1)] + ". " + spoken[match.end():]
    return spoken


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    changed_ids = sorted(
        text_id
        for text_id in set(TEACHER_TEXT_UPDATES) | set(ACCESSIBILITY_TEXT_UPDATES) | set(EASY_READ_UPDATES)
        if str(texts.get(text_id, "")).strip() and text_id in audios
    )
    output = I18N / "audio"
    report_items = []

    with tempfile.TemporaryDirectory(prefix="adt-all-changed-text-audio-") as temp:
        temp_dir = Path(temp)
        for text_id in changed_ids:
            visible_text = texts[text_id]
            spoken = narration_text(text_id, visible_text)
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run(
                [
                    "/usr/bin/say", "-v", "Tessa", "-r", "155",
                    "-o", str(wav_path), "--data-format=LEI16@24000", spoken,
                ],
                check=True,
            )
            filename = f"{text_id}.mp3"
            mp3_path = output / filename
            encode_mp3(wav_path, mp3_path)
            if mp3_path.stat().st_size <= 768:
                raise RuntimeError(f"Speech synthesis produced an invalid clip: {text_id}")
            audios[text_id] = filename
            report_items.append({
                "textId": text_id,
                "visibleTextSha256": hashlib.sha256(visible_text.encode("utf-8")).hexdigest(),
                "spokenTextSha256": hashlib.sha256(spoken.encode("utf-8")).hexdigest(),
                "audioBytes": mp3_path.stat().st_size,
            })

    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "voice": "Tessa",
        "locale": "en_ZA",
        "speakingRateWordsPerMinute": 155,
        "clips": report_items,
    }
    (ROOT / "changed-text-audio-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(changed_ids)} corrected narration clips from current visible text")


if __name__ == "__main__":
    main()
