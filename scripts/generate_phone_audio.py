#!/usr/bin/env python3
"""Regenerate the page-two phone number as naturally grouped digits."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
TEXT_ID = "pg002_n0011"
SPOKEN = (
    "Phone. Plus two five five, seven three five, zero four one, one seven zero. "
    "Or, plus two five five, seven three five, zero four one, one six eight."
)


def main() -> None:
    output = I18N / "audio" / f"{TEXT_ID}.mp3"
    with tempfile.TemporaryDirectory(prefix="adt-phone-audio-") as temp:
        wav_path = Path(temp) / f"{TEXT_ID}.wav"
        subprocess.run(
            [
                "/usr/bin/say", "-v", "Tessa", "-r", "145",
                "-o", str(wav_path), "--data-format=LEI16@24000", SPOKEN,
            ],
            check=True,
        )
        encode_mp3(wav_path, output)

    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    audios[TEXT_ID] = output.name
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    timecodes.pop(TEXT_ID, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    report = {
        "textId": TEXT_ID,
        "visibleText": "Phone: +255 735 041 170 / +255 735 041 168",
        "spokenText": SPOKEN,
        "voice": "Tessa",
        "locale": "en_ZA",
        "speakingRateWordsPerMinute": 145,
        "format": "MP3",
        "sampleRateHz": 24000,
        "bitRateKbps": 128,
        "channels": 1,
    }
    (ROOT / "phone-audio-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated grouped phone-number narration for {TEXT_ID}")


if __name__ == "__main__":
    main()
