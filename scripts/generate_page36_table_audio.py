#!/usr/bin/env python3
"""Regenerate page 36 table rows with explicit spoken letter names."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
ROW_IDS = ("pg021_n0022", "pg021_n0026", "pg021_n0030", "pg021_n0034")
LETTERS = {"a": "A", "b": "B", "c": "C", "d": "D"}


def spoken_row(visible_text: str) -> str:
    match = re.match(r"^\(([a-d])\)\s*(.*)$", visible_text, re.I)
    if not match:
        raise ValueError(f"Expected a parenthesized row letter: {visible_text}")
    return f"Letter {LETTERS[match.group(1).lower()]}. {match.group(2)}"


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    output = I18N / "audio"
    text_ids = ROW_IDS + tuple(f"{text_id}_easy_read" for text_id in ROW_IDS)

    with tempfile.TemporaryDirectory(prefix="adt-page36-table-audio-") as temp:
        temp_dir = Path(temp)
        for text_id in text_ids:
            spoken = spoken_row(texts[text_id])
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

    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in text_ids:
        timecodes.pop(text_id, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Generated eight page 36 table clips with explicit letter names")


if __name__ == "__main__":
    main()
