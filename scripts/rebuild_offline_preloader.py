#!/usr/bin/env python3
"""Rebuild the reader's inline/offline content snapshot from canonical files."""

from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "assets" / "offline-preloader.js"


def load(path: str):
    source = ROOT / path.removeprefix("./")
    if path.endswith(".json"):
        return json.loads(source.read_text(encoding="utf-8"))
    return source.read_text(encoding="utf-8")


def main() -> None:
    source = TARGET.read_text(encoding="utf-8")
    match = re.search(r"var INLINE = (\{.*?\});\n", source, re.S)
    if not match:
        raise SystemExit("Could not locate INLINE snapshot")

    pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
    paths = [
        "./assets/config.json",
        "./content/pages.json",
        "./content/toc.json",
        "./content/navigation/nav.html",
    ]
    paths.extend("./" + page["href"] for page in pages)
    paths.extend([
        "./assets/interface_translations/en/interface_translations.json",
        "./content/i18n/en/texts.json",
        "./content/i18n/en/audios.json",
        "./content/i18n/en/videos.json",
        "./content/i18n/en/media-sync.json",
        "./content/i18n/en/images.json",
        "./content/i18n/en/glossary.json",
        "./content/i18n/en/timecode/timecode_output.json",
    ])

    inline = {path: load(path) for path in paths}
    replacement = "var INLINE = " + json.dumps(inline, ensure_ascii=False, separators=(",", ":")) + ";\n"
    TARGET.write_text(source[: match.start()] + replacement + source[match.end() :], encoding="utf-8")
    print(f"Rebuilt {TARGET.relative_to(ROOT)} with {len(inline)} resources")


if __name__ == "__main__":
    main()
