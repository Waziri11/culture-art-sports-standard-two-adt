#!/usr/bin/env python3
"""Check cover insertion, media identity, narration links and offline packaging."""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET

from mutagen.mp3 import MP3
from mutagen.mp4 import MP4

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content/i18n/en"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


class PageParser(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.ids, self.references, self.meta = [], [], {}
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-id" in attrs:
            self.ids.append(attrs["data-id"])
        if tag == "meta":
            self.meta[attrs.get("name")] = attrs.get("content")
        for attr in ("src", "href"):
            if attrs.get(attr):
                self.references.append(attrs[attr])


def main():
    pages = read(ROOT / "content/pages.json")
    videos = read(I18N / "videos.json")
    audios = read(I18N / "audios.json")
    texts = read(I18N / "texts.json")
    timing = read(I18N / "timecode/timecode_output.json")
    sync = read(I18N / "media-sync.json")
    report = read(ROOT / "cover-page-media-report.json")
    narration = read(ROOT / "cover-audio-report.json")
    assert len(pages) == len(videos) == 116
    assert len({page["href"] for page in pages}) == 116
    assert len({page["section_id"] for page in pages}) == 116
    assert pages[0]["href"] == "index.html" and pages[1]["href"] == "pg001_sec001.html"
    assert pages[-1]["href"] == "pg073_sec001.html"
    assert set(p.name for p in (I18N / "video").glob("*.mp4")) == {f"page_{i}.mp4" for i in range(1, 117)}
    page_ids = {}
    for position, page in enumerate(pages, 1):
        parser = PageParser((ROOT / page["href"]).read_text(encoding="utf-8"))
        assert parser.meta["page-section-id"] == str(position), page
        assert parser.meta["title-id"] == page["section_id"], page
        assert videos[f"video-{position}"] == f"page_{position}.mp4", page
        assert MP4(I18N / "video" / videos[f"video-{position}"]).info.length > 0
        page_ids[position] = parser.ids
        for ref in parser.references:
            if re.match(r"(?:[a-z]+:|#|//)", ref, re.I):
                continue
            assert (ROOT / re.split(r"[?#]", ref)[0]).is_file(), (page["href"], ref)
    for moved in report["shiftedPages"]:
        assert pages[moved["readerPage"] - 1]["section_id"] == moved["sectionId"]
        assert sha(I18N / "video" / moved["video"]) == moved["videoSha256"], moved
    for cover in (report["frontCover"], report["backCover"]):
        assert sha(I18N / "video" / cover["video"]) == cover["videoSha256"], cover
    original_audios = json.loads(subprocess.check_output(
        ["git", "show", "HEAD:content/i18n/en/audios.json"], cwd=ROOT, encoding="utf-8"))
    assert all(audios[key] == name for key, name in original_audios.items())
    for key, name in audios.items():
        assert (I18N / "audio" / name).is_file(), (key, name)
        assert name in sync["audioDurations"], name
    for clip in narration["clips"]:
        tid, filename = clip["textId"], clip["filename"]
        position = 1 if filename.startswith("page_1_") else 116
        assert tid in page_ids[position], clip
        assert audios[tid] == filename and texts[tid] == clip["text"]
        length = MP3(I18N / "audio" / filename).info.length
        assert abs(length - sync["audioDurations"][filename]) < 0.002
        words = timing[tid]["timecodes"][1]["word_timestamps"]
        assert words and 0 <= words[0]["start"] < words[-1]["end"] <= length + 0.1
    for entry in read(ROOT / "content/toc.json"):
        assert any(p["href"] == entry["href"] and p["section_id"] == entry["section_id"] for p in pages), entry
    package = ET.parse(ROOT / "imsmanifest.xml")
    resources = {e.attrib["href"] for e in package.iter() if e.tag.endswith("}file")}
    assert all((ROOT / ref).is_file() for ref in resources)
    for folder in ("assets", "content", "images"):
        assert all(p.relative_to(ROOT).as_posix() in resources for p in (ROOT / folder).rglob("*") if p.is_file())
    inline = json.loads(re.search(r"var INLINE = (\{.*?\});\n", (ROOT / "assets/offline-preloader.js").read_text(encoding="utf-8"), re.S)[1])
    for ref, value in inline.items():
        path = ROOT / ref.removeprefix("./")
        expected = read(path) if path.suffix == ".json" else path.read_text(encoding="utf-8")
        assert value == expected, ("stale offline data", ref)
    print(f"PASS: 116 page positions, 116 playable videos, 114 preserved video checksums.")
    print(f"PASS: {len(original_audios)} existing narration mappings preserved; 19 Imani cover clips attached and timed.")
    print(f"PASS: all HTML resource links, {len(resources)} SCORM files and {len(inline)} offline resources.")


if __name__ == "__main__":
    main()
