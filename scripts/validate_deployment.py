#!/usr/bin/env python3
"""Audit the static reader's local links and unused deployment resources."""
from __future__ import annotations

from collections import deque
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
# Build input and required favicon attribution are intentionally not loaded by HTML.
SUPPORT_FILES = {"assets/tailwind_css.css", "assets/favicon_io/about.txt"}


def audit():
    linked, missing, queue = set(), set(), deque()
    exact_paths = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*")
                   if p.is_file() and ".git" not in p.parts}

    def add(ref, source):
        url = urlsplit(ref)
        if url.scheme or url.netloc or not url.path or "${" in ref:
            return
        path = (source.parent / unquote(url.path)).resolve()
        if not path.is_relative_to(ROOT):
            missing.add(f"{source.relative_to(ROOT)}: outside reader root: {ref}")
        elif not path.is_file():
            missing.add(f"{source.relative_to(ROOT)}: {ref}")
        elif path.relative_to(ROOT).as_posix() not in exact_paths:
            missing.add(f"{source.relative_to(ROOT)}: wrong filename case: {ref}")
        elif path not in linked:
            linked.add(path)
            queue.append(path)

    class Links(HTMLParser):
        def handle_starttag(self, tag, attrs):
            for key, value in attrs:
                if key in ("src", "href", "poster") and value:
                    add(value, self.source)

    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    entry = ROOT / "index.html"
    pages = read(ROOT / "content/pages.json")
    roots = [p["href"] for p in pages] + ["cover.png", "assets/config.json",
            "content/pages.json", "content/toc.json", "content/navigation/nav.html"]
    for language in read(ROOT / "assets/config.json")["languages"]["available"]:
        roots.append(f"assets/interface_translations/{language}/interface_translations.json")
        base = ROOT / "content/i18n" / language
        for name in ("texts", "audios", "videos", "images", "glossary", "media-sync"):
            roots.append(f"content/i18n/{language}/{name}.json")
        roots.append(f"content/i18n/{language}/timecode/timecode_output.json")
        for name, folder in (("audios", "audio"), ("videos", "video"), ("images", "images")):
            for value in read(base / f"{name}.json").values():
                if isinstance(value, str):
                    add(value, base / folder / "_")
    # These filenames are selected dynamically by the reader's SOUND_FILES map.
    roots += [f"assets/sounds/{name}.mp3" for name in
              ("drop", "success", "error", "reset", "validate_success")]
    for ref in roots:
        add(ref, entry)
    while queue:
        path = queue.popleft()
        if path.suffix not in (".html", ".css", ".js", ".webmanifest"):
            continue
        source = path.read_text(encoding="utf-8")
        if path.suffix == ".html":
            parser = Links()
            parser.source = path
            parser.feed(source)
        elif path.suffix == ".css":
            for ref in re.findall(r"url\([\s'\"]*([^\s)'\"]+)", source):
                add(ref, path)
        elif path.suffix == ".webmanifest":
            for icon in json.loads(source).get("icons", []):
                add(icon["src"], path)
        elif path.suffix == ".js":
            source = source.split("//# sourceMappingURL=")[0]
            for ref in re.findall(r"[\"'`]((?:\./)?assets/[^\"'`]+)[\"'`]", source):
                add(ref, entry)
    candidates = {p for folder in ("assets", "content", "images")
                  for p in (ROOT / folder).rglob("*") if p.is_file()}
    candidates.update(ROOT.glob("*.html"))
    unused = candidates - linked - {ROOT / name for name in SUPPORT_FILES}
    return linked, missing, unused


def main():
    linked, missing, unused = audit()
    for item in sorted(missing):
        print(f"MISSING: {item}")
    for path in sorted(unused):
        print(f"UNLINKED: {path.relative_to(ROOT).as_posix()}")
    if missing or unused:
        raise SystemExit(1)
    print(f"PASS: {len(linked)} linked reader resources; no broken links or unused runtime files.")


if __name__ == "__main__":
    main()
