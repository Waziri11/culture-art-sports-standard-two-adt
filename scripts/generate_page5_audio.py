#!/usr/bin/env python3
"""Regenerate narration for the corrected page-five acknowledgement text."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from generate_corrected_audio import encode_mp3


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"
TEXT_ID = "pg005_n0002"


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    output = I18N / "audio" / f"{TEXT_ID}.mp3"
    with tempfile.TemporaryDirectory(prefix="adt-page5-audio-") as temp:
        wav_path = Path(temp) / f"{TEXT_ID}.wav"
        subprocess.run(
            [
                "/usr/bin/say", "-v", "Tessa", "-r", "155",
                "-o", str(wav_path), "--data-format=LEI16@24000", texts[TEXT_ID],
            ],
            check=True,
        )
        encode_mp3(wav_path, output)

    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    timecodes.pop(TEXT_ID, None)
    timecodes_path.write_text(json.dumps(timecodes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Generated corrected narration for {TEXT_ID}")


if __name__ == "__main__":
    main()
