#!/usr/bin/env python3
"""Validate sign video, narration, and highlighting synchronization inputs."""

from __future__ import annotations

import argparse
import json
import subprocess
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"


class DataIdParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        text_id = values.get("data-id")
        if text_id:
            self.items.append((tag.lower(), text_id))


def media_duration(ffprobe: str, path: Path) -> float:
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
    return float(result.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()

    pages = json.loads((ROOT / "content" / "pages.json").read_text(encoding="utf-8"))
    audios = json.loads((I18N / "audios.json").read_text(encoding="utf-8"))
    videos = json.loads((I18N / "videos.json").read_text(encoding="utf-8"))
    sync = json.loads((I18N / "media-sync.json").read_text(encoding="utf-8"))
    timecodes = json.loads(
        (I18N / "timecode" / "timecode_output.json").read_text(encoding="utf-8")
    )
    durations = sync["audioDurations"]
    errors: list[str] = []
    audio_rates: list[tuple[float, int]] = []
    playable = 0
    precise = 0

    if len(pages) != len(videos):
        errors.append(f"pages/videos mismatch: {len(pages)} pages, {len(videos)} videos")

    for index, page in enumerate(pages, start=1):
        html_path = ROOT / page["href"]
        html = html_path.read_text(encoding="utf-8")
        sync_pos = html.find("./assets/sign-language-sync.js")
        runtime_pos = html.find("./assets/base.bundle.local.js")
        if sync_pos < 0 or runtime_pos < 0 or sync_pos > runtime_pos:
            errors.append(f"page {index}: synchronization script is missing or loaded too late")

        video_name = videos.get(f"video-{index}")
        video_path = I18N / "video" / str(video_name)
        if not video_name or not video_path.is_file():
            errors.append(f"page {index}: missing mapped video")
            continue

        data_ids = DataIdParser()
        data_ids.feed(html)
        page_audio = []
        for tag, text_id in data_ids.items:
            if tag == "img":
                continue
            filename = audios.get(text_id)
            if not filename:
                continue
            audio_duration = durations.get(filename)
            if not isinstance(audio_duration, (int, float)) or audio_duration <= 0:
                errors.append(f"page {index}: missing duration for {filename}")
                continue
            page_audio.append(float(audio_duration))
            playable += 1
            if text_id in timecodes:
                precise += 1

        total_audio = sum(page_audio)
        if total_audio <= 0:
            errors.append(f"page {index}: no playable narration")
            continue
        video_duration = media_duration(args.ffprobe, video_path)
        audio_rate = total_audio / video_duration
        audio_rates.append((audio_rate, index))
        if audio_rate < 0.25 or audio_rate > 4:
            errors.append(
                f"page {index}: required narration rate {audio_rate:.3f} is outside browser limits"
            )

    missing_duration_files = sorted(set(audios.values()) - set(durations))
    if missing_duration_files:
        errors.append(f"{len(missing_duration_files)} mapped audio files lack durations")

    if errors:
        print("Media synchronization validation FAILED")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    low = min(audio_rates)
    high = max(audio_rates)
    print("Media synchronization validation passed")
    print(f"- pages/videos: {len(pages)}")
    print(f"- narration tracks: {playable}")
    print(f"- tracks with precise word timing: {precise}")
    print("- sign video rate: 1.000x at the default reading speed")
    print(
        f"- synchronized narration range: {low[0]:.3f}x (page {low[1]}) "
        f"to {high[0]:.3f}x (page {high[1]})"
    )


if __name__ == "__main__":
    main()
