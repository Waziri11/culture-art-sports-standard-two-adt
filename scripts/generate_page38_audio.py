#!/usr/bin/env python3
"""Regenerate all page 38 narration with tuned Tanzanian-name pronunciation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
PAGE = ROOT / "pg023_sec001.html"
PRONUNCIATIONS = (
    (r"\bAmani\b", "Ah-mah-nee"),
    (r"\bFuraha\b", "Foo-rah-ha"),
    (r"\bTumaini\b", "Too-mah-ee-nee"),
    (r"\bBaraka\b", "Bah-rah-kah"),
    (r"\bpupils\b", "pyoo-puhls"),
)


def narration_text(text_id: str, visible_text: str) -> str:
    spoken = visible_text.replace("\n- ", "; ").replace("\n", ". ")
    spoken = re.sub(r"\b3\b", "three", spoken)
    if text_id.endswith("n0002") or text_id.endswith("n0002_easy_read"):
        spoken = "Activity one."
    for pattern, replacement in PRONUNCIATIONS:
        spoken = re.sub(pattern, replacement, spoken, flags=re.I)
    spoken = spoken.replace(":", ".").replace("“", "").replace("”", "").replace('"', "")
    spoken = re.sub(r"\s+", " ", spoken).strip()
    return spoken


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    page_source = PAGE.read_text(encoding="utf-8")
    visible_ids = list(dict.fromkeys(re.findall(r'data-id="(pg023_[^"]+)"', page_source)))
    text_ids = visible_ids + [
        f"{text_id}_easy_read" for text_id in visible_ids
        if str(texts.get(f"{text_id}_easy_read", "")).strip()
    ]
    output = I18N / "audio"
    report_items = []

    with tempfile.TemporaryDirectory(prefix="adt-page38-audio-") as temp:
        temp_dir = Path(temp)
        for text_id in text_ids:
            visible_text = str(texts[text_id])
            spoken = narration_text(text_id, visible_text)
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run(
                [
                    "/usr/bin/say", "-v", "Tessa", "-r", "145",
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
                "spokenText": spoken,
                "audioBytes": mp3_path.stat().st_size,
            })

    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in text_ids:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "voice": "Tessa",
        "locale": "en_ZA",
        "speakingRateWordsPerMinute": 145,
        "pronunciations": {
            "Amani": "Ah-mah-nee",
            "Furaha": "Foo-rah-ha",
            "Tumaini": "Too-mah-ee-nee",
            "Baraka": "Bah-rah-kah",
        },
        "clips": report_items,
    }
    (ROOT / "page38-audio-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(text_ids)} complete page 38 narration clips")


if __name__ == "__main__":
    main()
