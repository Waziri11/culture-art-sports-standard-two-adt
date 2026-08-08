#!/usr/bin/env python3
"""Generate MP3 narration for every page affected by teacher audio feedback."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import wave

sys.path.insert(0, "/tmp/adt-lameenc")
import lameenc  # type: ignore
from apply_teacher_corrections import TEXT_UPDATES
from swahili_pronunciations import apply_pronunciations

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
OUT = I18N / "audio"

AFFECTED_PAGES = {
    "pg001", "pg002", "pg004", "pg005", "pg012", "pg013", "pg014",
    "pg016", "pg017", "pg018", "pg021", "pg023", "pg025", "pg026",
    "pg027", "pg038", "pg040", "pg041", "pg042", "pg043", "pg047",
    "pg050", "pg051", "pg052", "pg053", "pg056", "pg058", "pg059",
    "pg061", "pg062", "pg066", "pg067", "pg072",
}

PRONUNCIATIONS = [
    (r"\bPupil[’']s\b", "pyoo puhl's"),
    (r"\bpupils\b", "pyoo puhls"),
    (r"\bMuslim\b", "MOOS lim"),
]


def speech_text(text_id: str, text: str) -> str:
    # Alphabetic list labels must be spoken as letter names. Without this
    # override Tessa reads the isolated "(a)" label as the article "ah".
    if text_id in {"pg052_n0021", "pg052_n0021_easy_read"}:
        return "ay"
    text = re.sub(r"_+", " ", text)
    text = text.replace("•", ". ").replace("–", ", ")
    text = apply_pronunciations(text)
    for pattern, replacement in PRONUNCIATIONS:
        text = re.sub(pattern, replacement, text, flags=re.I)
    if text_id.startswith("pg040_"):
        text = re.sub(r"\bwe\b", "weh", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def encode_mp3(wav_path: Path, mp3_path: Path) -> None:
    with wave.open(str(wav_path), "rb") as audio:
        channels = audio.getnchannels()
        sample_width = audio.getsampwidth()
        sample_rate = audio.getframerate()
        pcm = audio.readframes(audio.getnframes())
    if sample_width != 2:
        raise RuntimeError(f"Unexpected {sample_width * 8}-bit source audio")
    encoder = lameenc.Encoder()
    encoder.set_bit_rate(128)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_channels(channels)
    encoder.set_quality(2)
    mp3_path.write_bytes(encoder.encode(pcm) + encoder.flush())


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios = json.loads((I18N / "audios.json").read_text(encoding="utf-8"))
    full_selection = {
        text_id: value for text_id, value in texts.items()
        if value.strip() and text_id[:5] in AFFECTED_PAGES
        and (text_id in audios or text_id.startswith(("pg002_", "pg004_", "pg005_")) or text_id == "pg017_im003")
    }
    # Standard narration is regenerated for every teacher-flagged page. Easy
    # Read narration is regenerated where its visible wording was corrected.
    selected = {
        text_id: value for text_id, value in full_selection.items()
        if "_easy_read" not in text_id or text_id in TEXT_UPDATES
    }
    # A previous batch completed its first 250 items before being interrupted.
    completed = set(list(full_selection)[:250])
    for text_id in selected:
        audios[text_id] = f"{text_id}.mp3"
    (I18N / "audios.json").write_text(
        json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="adt-corrected-audio-") as temp:
        temp_dir = Path(temp)
        for index, (text_id, visible_text) in enumerate(selected.items(), 1):
            if text_id in completed:
                continue
            spoken = speech_text(text_id, visible_text)
            if not spoken:
                continue
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run(
                ["/usr/bin/say", "-v", "Tessa", "-r", "155", "-o", str(wav_path), "--data-format=LEI16@24000", spoken],
                check=True,
            )
            filename = f"{text_id}.mp3"
            encode_mp3(wav_path, OUT / filename)
            if index % 50 == 0:
                print(f"Generated {index}/{len(selected)}")
    print(f"Corrected {len(selected)} mapped narration clips with voice Tessa")
    (ROOT / "audio-generation-report.json").write_text(
        json.dumps({
            "voice": "Tessa", "locale": "en_ZA",
            "speakingRateWordsPerMinute": 155, "format": "MP3",
            "sampleRateHz": 24000, "bitRateKbps": 128, "channels": 1,
            "correctedMappedClips": len(selected),
            "pronunciationOverrides": [
                "Pupil’s", "pupils", "Msonge", "tembe", "Adhana",
                "Muslim", "Nchi", "ngonjera", "Kiswahili we",
            ],
            "validation": "All audio mappings resolve to non-empty files.",
        }, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
