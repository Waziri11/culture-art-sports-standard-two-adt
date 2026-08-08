#!/usr/bin/env python3
"""Regenerate page-three contents narration with explicit Roman numerals."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
SPOKEN = {
    "pg003_n0026": "Acknowledgments",
    "pg003_n0006": "Roman four",
    "pg003_n0027": "Introduction",
    "pg003_n0008": "Roman six",
    "pg003_n0028": "Our culture",
    "pg003_n0012": "Page one",
    "pg003_n0029": "and ethics",
    "pg003_n0017": "Page sixteen",
    "pg003_n0030": "Creating works of art",
    "pg003_n0021": "Page twenty two",
    "pg003_n0031": "Playing simple games",
    "pg003_n0025": "Page forty six",
}


def main() -> None:
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    output = I18N / "audio"
    generated: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="adt-toc-audio-") as temp:
        temp_dir = Path(temp)
        for base_id, spoken in SPOKEN.items():
            for text_id in (base_id, f"{base_id}_easy_read"):
                wav_path = temp_dir / f"{text_id}.wav"
                subprocess.run(
                    [
                        "/usr/bin/say", "-v", "Tessa", "-r", "155",
                        "-o", str(wav_path), "--data-format=LEI16@24000", spoken,
                    ],
                    check=True,
                )
                filename = f"{text_id}.mp3"
                encode_mp3(wav_path, output / filename)
                audios[text_id] = filename
                timecodes.pop(text_id, None)
                generated[text_id] = spoken
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "voice": "Tessa",
        "locale": "en_ZA",
        "speakingRateWordsPerMinute": 155,
        "romanNumerals": {"iv": "Roman four", "vi": "Roman six"},
        "clips": generated,
    }
    (ROOT / "toc-audio-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {len(generated)} table-of-contents narration clips")


if __name__ == "__main__":
    main()
