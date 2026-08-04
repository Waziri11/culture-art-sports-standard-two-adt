#!/usr/bin/env python3
"""Regenerate only narration changed by the updated accessibility review."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile

from apply_updated_accessibility_fixes import EASY_READ_UPDATES, I18N, ROOT, TEXT_UPDATES
from generate_corrected_audio import encode_mp3, speech_text


def main() -> None:
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    changed_ids = sorted(
        text_id for text_id in set(TEXT_UPDATES) | set(EASY_READ_UPDATES)
        if texts.get(text_id, "").strip()
    )
    output = I18N / "audio"
    with tempfile.TemporaryDirectory(prefix="adt-updated-accessibility-audio-") as temp:
        temp_dir = Path(temp)
        for text_id in changed_ids:
            spoken = speech_text(text_id, texts[text_id])
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
    audios.pop("pg023_n0003", None)
    audios.pop("pg023_n0003_easy_read", None)
    audios_path.write_text(json.dumps(audios, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "voice": "Tessa",
        "locale": "en_ZA",
        "speakingRateWordsPerMinute": 155,
        "format": "MP3",
        "sampleRateHz": 24000,
        "bitRateKbps": 128,
        "channels": 1,
        "updatedAccessibilityClips": len(changed_ids),
        "textIds": changed_ids,
        "validation": "Pending updated accessibility validation",
    }
    (ROOT / "updated-accessibility-audio-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Generated {len(changed_ids)} updated accessibility clips")


if __name__ == "__main__":
    main()
