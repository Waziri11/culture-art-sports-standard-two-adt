#!/usr/bin/env python3
"""Generate narration for the rebuilt accessible table on PDF page 39."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
BASE_IDS = tuple(f"pg039_n{number:04d}" for number in range(16, 26))
IDS = BASE_IDS + tuple(f"{text_id}_easy_read" for text_id in BASE_IDS)
SPOKEN = {
    "pg039_n0016": "Number one. Painting.",
    "pg039_n0017": "Letter A. Sewing.",
    "pg039_n0018": "Number two. Making a pot.",
    "pg039_n0019": "Letter B. Moulding.",
    "pg039_n0020": "Number three. Stitching two pieces of fabric together.",
    "pg039_n0021": "Letter C. Decorating.",
    "pg039_n0022": "Number four. Making masks, wooden spoons and combs.",
    "pg039_n0023": "Letter D. Weaving.",
    "pg039_n0024": "Number five. Making sweaters, hats and socks.",
    "pg039_n0025": "Letter E. Carving.",
}


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    clips = []
    with tempfile.TemporaryDirectory(prefix="adt-page39-table-") as temp:
        temp_dir = Path(temp)
        for text_id in IDS:
            base_id = text_id.removesuffix("_easy_read")
            visible = str(texts[text_id])
            spoken = SPOKEN[base_id]
            wav_path = temp_dir / f"{text_id}.wav"
            subprocess.run(["/usr/bin/say", "-v", "Tessa", "-r", "145", "-o", str(wav_path), "--data-format=LEI16@24000", spoken], check=True)
            filename = f"{text_id}.mp3"
            output = I18N / "audio" / filename
            encode_mp3(wav_path, output)
            if output.stat().st_size <= 768:
                raise RuntimeError(f"Invalid table narration: {text_id}")
            audios[text_id] = filename
            clips.append({
                "textId": text_id,
                "visibleTextSha256": hashlib.sha256(visible.encode("utf-8")).hexdigest(),
                "spokenText": spoken,
                "audioBytes": output.stat().st_size,
            })
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (ROOT / "page39-accessible-table-audio-report.json").write_text(
        json.dumps({"voice": "Tessa", "speakingRateWordsPerMinute": 145, "clips": clips}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Generated {len(clips)} accessible table narration clips")


if __name__ == "__main__":
    main()
