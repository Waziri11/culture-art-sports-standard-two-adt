#!/usr/bin/env python3
"""Render the Kabula/Mzee Masanja passage as a two-voice dialogue."""

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
PAGES = (ROOT / "pg025_sec001.html", ROOT / "pg026_sec001.html")
KABULA_BASE_IDS = {
    "pg025_n0002", "pg025_n0003", "pg025_n0004", "pg025_n0009", "pg025_n0010", "pg025_n0011",
    "pg025_n0016", "pg025_n0017", "pg025_n0024", "pg025_n0025",
    "pg026_n0003", "pg026_n0004", "pg026_n0005", "pg026_n0010", "pg026_n0011", "pg026_n0012", "pg026_n0013",
}
PRONUNCIATIONS = (
    (r"\bMzee Masanja\b", "em-ZEH-eh mah-SAHN-jah"),
    (r"\bMzee\b", "em-ZEH-eh"),
    (r"\bMasanja\b", "mah-SAHN-jah"),
    (r"\bKabula\b", "kah-BOO-lah"),
    (r"\bAdhana\b", "ah-THAA-nah"),
)


def narration(text: str) -> str:
    spoken = text.replace("\n", ". ").replace(":", ".")
    for pattern, replacement in PRONUNCIATIONS:
        spoken = re.sub(pattern, replacement, spoken, flags=re.I)
    return re.sub(r"\s+", " ", spoken).strip()


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    base_ids = []
    for page in PAGES:
        base_ids.extend(re.findall(r'data-id="(pg02[56]_[^"]+)"', page.read_text(encoding="utf-8")))
    base_ids = list(dict.fromkeys(base_ids))
    ids = base_ids + [f"{text_id}_easy_read" for text_id in base_ids if str(texts.get(f"{text_id}_easy_read", "")).strip()]
    clips = []
    with tempfile.TemporaryDirectory(prefix="adt-adhana-dialogue-") as temp:
        temp_dir = Path(temp)
        for index, text_id in enumerate(ids, 1):
            base_id = text_id.removesuffix("_easy_read")
            speaker = "Kabula" if base_id in KABULA_BASE_IDS else "Mzee Masanja"
            voice = "Tessa" if speaker == "Kabula" else "Daniel"
            visible = str(texts[text_id])
            spoken = narration(visible)
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run([
                "/usr/bin/say", "-v", voice, "-r", "142", "-o", str(wav_path),
                "--data-format=LEI16@24000", spoken,
            ], check=True)
            filename = f"{text_id}.mp3"
            path = I18N / "audio" / filename
            encode_mp3(wav_path, path)
            if path.stat().st_size <= 768:
                raise RuntimeError(f"Invalid dialogue audio: {text_id}")
            audios[text_id] = filename
            clips.append({
                "textId": text_id, "speaker": speaker, "voice": voice,
                "visibleTextSha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(),
                "spokenText": spoken, "audioBytes": path.stat().st_size,
            })
            if index % 20 == 0:
                print(f"Generated {index}/{len(ids)}")
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in ids:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "adhana-dialogue-audio-report.json").write_text(json.dumps({
        "speakingRateWordsPerMinute": 142,
        "voices": {"Kabula": "Tessa", "Mzee Masanja": "Daniel"},
        "adhanaPronunciation": "ah-THAA-nah", "clips": clips,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(ids)} two-voice dialogue clips")


if __name__ == "__main__":
    main()
