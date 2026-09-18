#!/usr/bin/env python3
"""Generate only the new cover clips using the book's existing Imani settings."""
from __future__ import annotations

import asyncio
from collections import Counter
import hashlib
import json
from pathlib import Path

import edge_tts
from mutagen.mp3 import MP3

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content/i18n/en"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def main():
    report = read(ROOT / "cover-audio-report.json")
    timecodes = read(I18N / "timecode/timecode_output.json")
    sync = read(I18N / "media-sync.json")
    register = read(ROOT / "bilingual-audio-register.json")
    semaphore = asyncio.Semaphore(3)

    async def generate(clip):
        target = I18N / "audio" / clip["filename"]
        async with semaphore:
            for attempt in range(4):
                audio = bytearray()
                words = []
                try:
                    speech = edge_tts.Communicate(clip["text"], report["voice"], rate=report["rate"],
                                                   pitch=report["pitch"], boundary="WordBoundary")
                    async for event in speech.stream():
                        if event["type"] == "audio":
                            audio.extend(event["data"])
                        elif event["type"] == "WordBoundary":
                            words.append({"text": event["text"], "start": round(event["offset"] / 10_000_000, 3),
                                          "end": round((event["offset"] + event["duration"]) / 10_000_000, 3)})
                    if not words or len(audio) < 768:
                        raise ValueError("Empty narration or word timing")
                    target.write_bytes(audio)
                    break
                except Exception:
                    if attempt == 3:
                        raise
                    await asyncio.sleep(2 * (attempt + 1))
        duration = round(MP3(target).info.length, 3)
        timecodes[clip["textId"]] = {"timecodes": [None, {"word_timestamps": words}]}
        sync["audioDurations"][clip["filename"]] = duration
        clip.update({"duration": duration, "wordCount": len(words), "fileSize": len(audio), "status": "passed"})
        print(f'Generated {clip["filename"]}: {duration}s', flush=True)
        return {
            "textId": clip["textId"], "visibleTextSha256": hashlib.sha256(clip["text"].encode()).hexdigest(),
            "spans": [{"language": "en", "voice": report["voice"], "text": clip["text"]}],
            "duration": duration, "fileSize": len(audio), "status": "passed",
        }

    new_clips = await asyncio.gather(*(generate(clip) for clip in report["clips"]))
    new_ids = {clip["textId"] for clip in new_clips}
    register["clips"] = [clip for clip in register["clips"] if clip["textId"] not in new_ids] + new_clips
    register["clipCount"] = len(register["clips"])
    register["voiceSpanCounts"] = dict(Counter(span["voice"] for clip in register["clips"] for span in clip["spans"]))
    write(ROOT / "bilingual-audio-register.json", register)
    write(I18N / "timecode/timecode_output.json", timecodes)
    write(I18N / "media-sync.json", sync)
    write(ROOT / "cover-audio-report.json", report)
    print(f"Generated and registered {len(new_clips)} Imani cover clips.")


if __name__ == "__main__":
    asyncio.run(main())
