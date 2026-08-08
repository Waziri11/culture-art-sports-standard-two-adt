#!/usr/bin/env python3
"""Apply the August updated accessibility review to the ADT bundle."""

from __future__ import annotations

import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content" / "i18n" / "en"

TEXT_UPDATES = {
    "pg009_n0014": "1. Look at the pictures or watch video clips about Msonge houses in Tanzanian communities.",
    "pg011_n0009": "3. In which areas have you observe banda houses?",
    "pg013_n0009": "Which areas have you identify a tembe house?",
    "pg013_n0014": "Study of the pictures or watch video clips about tembe houses in Tanzanian communities.",
    "pg023_n0002": "Activity 1",
    "pg023_n0003": "",
    "pg029_n0002": "Study of the pictures and answer the questions that follow:",
    "pg030_n0023": "Study at the picture and answer the questions that follow:",
    "pg032_n0002": "Study at the pictures and answer the questions that follow:",
    "pg033_n0016": "Study of the pictures and answer the questions that follow:",
    "pg035_n0006": "1. Study of pictures 1 and 2.",
    "pg037_n0002": "Study of the picture and answer the questions that follow:",
    "pg038_n0007": "Study of this picture and answer the questions that follow:",
    "pg045_n0015": "1. Take a mirror or use an accessible application while changing your facial expression. What do you observe?",
    "pg048_n0006": "Study of the pictures and answer the following questions:",
    "pg049_n0008": "What type of performing art involving body movement do you identify in these pictures?",
    "pg050_n0006": "Study of the pictures and answer the following questions:",
    "pg053_n0004": "Mention or use cones to make a circle on the ground with a diameter of 25 steps;",
    "pg056_n0017": "Mention a circle for running with a stick game.",
}

EASY_READ_UPDATES = {
    key + "_easy_read": value for key, value in TEXT_UPDATES.items()
    if key not in {"pg023_n0003"}
}
EASY_READ_UPDATES["pg023_n0003_easy_read"] = ""


def dump(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_inline(source: str, text_id: str, value: str) -> str:
    pattern = re.compile(
        rf'(<(?P<tag>[a-zA-Z0-9]+)\b[^>]*\bdata-id="{re.escape(text_id)}"[^>]*>)(.*?)(</(?P=tag)>)',
        re.DOTALL,
    )
    return pattern.sub(lambda match: match.group(1) + value + match.group(4), source)


def update_text_and_html() -> None:
    texts_path = I18N / "texts.json"
    texts = json.loads(texts_path.read_text(encoding="utf-8"))
    texts.update(TEXT_UPDATES)
    texts.update(EASY_READ_UPDATES)
    dump(texts_path, texts)

    for path in ROOT.glob("pg*.html"):
        source = path.read_text(encoding="utf-8")
        updated = source
        for text_id, value in TEXT_UPDATES.items():
            if f'data-id="{text_id}"' in updated:
                updated = replace_inline(updated, text_id, value)
        if path.name == "pg023_sec001.html":
            updated = updated.replace('<h1 class="sr-only" id="page-heading">Activity</h1>', '<h1 class="sr-only" id="page-heading">Activity 1</h1>')
            updated = re.sub(
                r'<div data-id="pg023_n0003"[^>]*>.*?</div>',
                '',
                updated,
                count=1,
                flags=re.DOTALL,
            )
            updated = updated.replace('rounded-l-[1.4rem] rounded-r-[1rem]', 'rounded-[1.4rem]')
        updated = re.sub(
            r'src="\./assets/offline-preloader\.js(?:\?v=\d+)?"',
            'src="./assets/offline-preloader.js?v=4"',
            updated,
        )
        if updated != source:
            path.write_text(updated, encoding="utf-8")

    index = ROOT / "index.html"
    source = index.read_text(encoding="utf-8")
    source = re.sub(
        r'src="\./assets/offline-preloader\.js(?:\?v=\d+)?"',
        'src="./assets/offline-preloader.js?v=4"',
        source,
    )
    index.write_text(source, encoding="utf-8")


def merge_circus_sections() -> None:
    destination = ROOT / "pg049_sec001.html"
    source = destination.read_text(encoding="utf-8")
    if 'data-id="pg049_n0005"' not in source:
        additions = []
        for filename in ["pg049_sec002.html", "pg049_sec003.html"]:
            section_source = (ROOT / filename).read_text(encoding="utf-8")
            match = re.search(r'<section\b[^>]*>(.*?)</section>', section_source, re.DOTALL)
            if not match:
                raise RuntimeError(f"Could not extract section from {filename}")
            additions.append('<div class="mt-8">' + match.group(1).strip() + '</div>')
        source = source.replace(
            '  </section>\n</div>',
            '\n'.join(additions) + '\n  </section>\n</div>',
            1,
        )
        destination.write_text(source, encoding="utf-8")


def update_spine_and_metadata() -> None:
    pages_path = ROOT / "content" / "pages.json"
    pages = json.loads(pages_path.read_text(encoding="utf-8"))
    removed = {"pg049_sec002.html", "pg049_sec003.html"}
    pages = [entry for entry in pages if entry["href"] not in removed]
    if len(pages) != 114:
        raise RuntimeError(f"Expected 114 reader sections, found {len(pages)}")
    dump(pages_path, pages)

    for index, entry in enumerate(pages, 1):
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        source = re.sub(
            r'(<meta\s+name="page-section-id"\s+content=")[^"]*("\s*/?>)',
            rf'\g<1>{index}\2',
            source,
        )
        path.write_text(source, encoding="utf-8")

    toc_path = ROOT / "content" / "toc.json"
    toc = json.loads(toc_path.read_text(encoding="utf-8"))
    toc = [row for row in toc if row.get("section_id") not in {"pg049_sec002", "pg049_sec003"}]
    dump(toc_path, toc)

    manifest = ROOT / "imsmanifest.xml"
    source = manifest.read_text(encoding="utf-8")
    source = re.sub(r'^\s*<file href="pg049_sec00[23]\.html"/>\s*\n', '', source, flags=re.MULTILINE)
    manifest.write_text(source, encoding="utf-8")


def update_audio_metadata() -> None:
    audios_path = I18N / "audios.json"
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    audios.pop("pg023_n0003", None)
    audios.pop("pg023_n0003_easy_read", None)
    dump(audios_path, audios)

    timecodes_path = I18N / "timecode" / "timecode_output.json"
    timecodes = json.loads(timecodes_path.read_text(encoding="utf-8"))
    for text_id in set(TEXT_UPDATES) | set(EASY_READ_UPDATES):
        timecodes.pop(text_id, None)
    dump(timecodes_path, timecodes)


def update_config() -> None:
    path = ROOT / "assets" / "config.json"
    config = json.loads(path.read_text(encoding="utf-8"))
    config["bundleVersion"] = "4"
    dump(path, config)


def main() -> None:
    update_text_and_html()
    merge_circus_sections()
    update_spine_and_metadata()
    update_audio_metadata()
    update_config()


if __name__ == "__main__":
    main()
