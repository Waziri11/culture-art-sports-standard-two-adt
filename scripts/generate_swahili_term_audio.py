#!/usr/bin/env python3
"""Rebuild page 41 and recurring Kiswahili/Tanzanian-term narration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3
from swahili_pronunciations import PRONUNCIATIONS, apply_pronunciations, terms_in

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
PAGE41 = ROOT / "pg025_sec001.html"


def narration_text(text: str) -> str:
    spoken = text.replace("\n- ", "; ").replace("\n", ". ")
    spoken = apply_pronunciations(spoken)
    spoken = spoken.replace(":", ".").replace("“", "").replace("”", "").replace('"', "")
    return re.sub(r"\s+", " ", spoken).strip()


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    page_ids = list(dict.fromkeys(re.findall(r'data-id="(pg025_[^"]+)"', PAGE41.read_text(encoding="utf-8"))))
    page_ids += [f"{i}_easy_read" for i in page_ids if str(texts.get(f"{i}_easy_read", "")).strip()]
    detected = [
        text_id for text_id, value in texts.items()
        if text_id in audios and str(value).strip() and terms_in(str(value)) and not text_id.startswith("pg023_")
    ]
    text_ids = list(dict.fromkeys(page_ids + detected))
    output = I18N / "audio"
    clips = []

    with tempfile.TemporaryDirectory(prefix="adt-swahili-audio-") as temp:
        temp_dir = Path(temp)
        for index, text_id in enumerate(text_ids, 1):
            visible = str(texts[text_id])
            spoken = narration_text(visible)
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run([
                "/usr/bin/say", "-v", "Tessa", "-r", "145", "-o", str(wav_path),
                "--data-format=LEI16@24000", spoken,
            ], check=True)
            filename = f"{text_id}.mp3"
            mp3_path = output / filename
            encode_mp3(wav_path, mp3_path)
            if mp3_path.stat().st_size <= 768:
                raise RuntimeError(f"Speech synthesis produced an invalid clip: {text_id}")
            audios[text_id] = filename
            clips.append({
                "textId": text_id,
                "scope": "complete-page-41" if text_id in page_ids else "book-wide-term-scan",
                "detectedTerms": terms_in(visible),
                "visibleTextSha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(),
                "spokenText": spoken,
                "audioBytes": mp3_path.stat().st_size,
            })
            if index % 25 == 0:
                print(f"Generated {index}/{len(text_ids)}")

    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in text_ids:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "voice": "Tessa", "locale": "en_ZA", "speakingRateWordsPerMinute": 145,
        "pronunciations": PRONUNCIATIONS,
        "completePage41ClipCount": len(page_ids),
        "bookWideDetectedClipCount": len(set(detected) - set(page_ids)),
        "clips": clips,
    }
    (ROOT / "swahili-pronunciation-audio-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {len(text_ids)} clips: {len(page_ids)} for page 41 and {len(set(detected) - set(page_ids))} elsewhere")


if __name__ == "__main__":
    main()
