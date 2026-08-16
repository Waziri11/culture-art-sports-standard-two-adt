#!/usr/bin/env python3
"""Generate audio-duration metadata used by the accessibility media synchronizer."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"


def duration(ffprobe: str, path: Path) -> float:
    result = subprocess.run(
        [
            ffprobe,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return round(float(result.stdout.strip()), 3)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()

    audio_map = json.loads((I18N / "audios.json").read_text(encoding="utf-8"))
    filenames = sorted(set(audio_map.values()))
    durations: dict[str, float] = {}
    missing: list[str] = []

    for filename in filenames:
        path = I18N / "audio" / filename
        if not path.is_file():
            missing.append(filename)
            continue
        durations[filename] = duration(args.ffprobe, path)

    output = {
        "version": 1,
        "audioDurations": durations,
        "missingAudioFiles": missing,
    }
    target = I18N / "media-sync.json"
    target.write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {target.relative_to(ROOT)} with {len(durations)} audio durations")
    if missing:
        print(f"Warning: {len(missing)} mapped audio files were missing")


if __name__ == "__main__":
    main()
