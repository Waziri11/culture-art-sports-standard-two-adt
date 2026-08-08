#!/usr/bin/env python3
"""Apply source-backed teacher corrections to the Standard Two ADT bundle."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content/i18n/en"


TEXT_UPDATES = {
    "pg009_n0014": "1. Observe the pictures or watch video clips about Msonge houses in Tanzanian communities.",
    "pg009_n0014_easy_read": "1. Observe the pictures.\nOr watch video clips about Msonge houses in Tanzanian communities.",
    "pg011_n0009": "3. Which areas have banda houses?",
    "pg011_n0009_easy_read": "3. Which areas have banda houses?",
    "pg011_n0015": "1. Observe the pictures or watch video clips about banda houses in Tanzanian communities.",
    "pg011_n0015_easy_read": "1. Observe the pictures.\nOr watch video clips about banda houses in Tanzanian communities.",
    "pg013_n0009": "Which areas have tembe houses?",
    "pg013_n0009_easy_read": "Which areas have tembe houses?",
    "pg013_n0014": "Observe the pictures or watch video clips about tembe houses in Tanzanian communities.",
    "pg013_n0014_easy_read": "Observe the pictures.\nOr watch video clips about tembe houses in Tanzanian communities.",
    "pg013_n0018": "Exercise 1",
    "pg017_im003": "A green rice field grows in neat rows across a wet farm.",
    "pg018_n0039": "Wanyasa, Wapemba, Wadigo, Wajita and Waha are some of the communities that engage in fishing activities.",
    "pg018_n0039_easy_read": "Some communities that fish are:\n- Wanyasa\n- Wapemba\n- Wadigo\n- Wajita\n- Waha",
    "pg019_n0015": "1. Observe the pictures or watch video clips that show how fishing is done.",
    "pg019_n0015_easy_read": "1. Observe the pictures.\nOr watch video clips that show how fishing is done.",
    "pg020_n0006": "Wachaga, Wakinga and Wapemba are some of the well-known communities involved in business.",
    "pg020_n0006_easy_read": "Wachaga, Wakinga, and Wapemba are some well-known communities involved in business.",
    "pg020_n0013": "1. What products do you observe in the picture?",
    "pg020_n0013_easy_read": "1. What products do you observe in the picture?",
    "pg029_n0002": "Observe the pictures and answer the questions that follow:",
    "pg029_n0002_easy_read": "Observe the pictures.\nThen answer the questions that follow:",
    "pg030_n0023": "Observe the picture and answer the questions that follow:",
    "pg032_n0002": "Observe the pictures and answer the questions that follow:",
    "pg033_n0016": "Observe the pictures and answer the questions that follow:",
    "pg033_n0016_easy_read": "Observe the pictures.\nThen answer the questions that follow:",
    "pg035_n0006": "1. Observe pictures 1 and 2.",
    "pg035_n0006_easy_read": "1. Observe pictures 1 and 2.",
    "pg035_n0013": "Activity 4",
    "pg035_n0014": "Carve one item you like by using a piece of wood found in your surroundings.",
    "pg035_n0021": "Observe the shapes and answer the questions that follow:",
    "pg035_n0021_easy_read": "Observe the shapes.\nThen answer the questions that follow:",
    "pg037_n0002": "Observe the picture and answer the questions that follow:",
    "pg037_n0002_easy_read": "Observe the picture.\nThen answer the questions.",
    "pg037_n0015": "Activity",
    "pg037_n0016": "6",
    "pg038_n0007": "Observe this picture and answer the questions that follow:",
    "pg038_n0007_easy_read": "Observe this picture.\nThen answer the questions that follow.",
    "pg039_n0002": "Exercise 1",
    "pg045_n0015": "1. Change your facial expression and tell what you mean.",
    "pg045_n0016": "",
    "pg045_n0016_easy_read": "",
    "pg046_n0014": "Observe the pictures and answer the following questions:",
    "pg046_n0014_easy_read": "Observe the pictures.\nThen answer the questions.",
    "pg048_n0006": "Observe the pictures and answer the following questions:",
    "pg048_n0006_easy_read": "Observe the pictures.\nThen answer the following questions:",
    "pg049_n0008": "What type of performing art involving body movement do you observe in these pictures?",
    "pg049_n0008_easy_read": "What type of performing art that uses body movement do you observe in these pictures?",
    "pg050_n0006": "Observe the pictures and answer the following questions:",
    "pg051_n0016": "3.",
    "pg056_n0008": "Mention the steps for running with a stick game.",
    "pg056_n0010": "What are the benefits of running with a stick game?",
    "pg056_n0012": "To win this game, what do you need to do?",
    "pg067_n0010": "The player behind the opposing team is known as __________.",
    "pg070_n0002": "The football game",
    "pg070_n0004": "The football game",
}


FRONT_MATTER = {
    "pg002_sec001": {
        "title": "Copyright",
        "texts": [
            ("pg002_n0002", "© Tanzania Institute of Education 2024"),
            ("pg002_n0003", "First Edition 2018"),
            ("pg002_n0004", "Second Edition 2024"),
            ("pg002_n0005", "ISBN: 978-9912-753-72-3"),
            ("pg002_n0006", "Tanzania Institute of Education"),
            ("pg002_n0007", "132 Ali Hassan Mwinyi Road"),
            ("pg002_n0008", "Mikocheni Area"),
            ("pg002_n0009", "P.O. Box 35094"),
            ("pg002_n0010", "14112 Dar es Salaam"),
            ("pg002_n0011", "Phone: +255 735 041 170 / +255 735 041 168"),
            ("pg002_n0012", "Email: director.general@tie.go.tz"),
            ("pg002_n0013", "Website: www.tie.go.tz"),
            ("pg002_n0014", "All rights reserved. No part of this book may be reproduced, stored in any retrieval system, or transmitted in any form or by any means, whether electronic, mechanical, photocopying, recording or otherwise, without the prior written permission of the Tanzania Institute of Education."),
        ],
    },
    "pg004_sec001": {
        "title": "Acknowledgements",
        "texts": [
            ("pg004_n0002", "Acknowledgements"),
            ("pg004_n0003", "The Tanzania Institute of Education (TIE) acknowledges and appreciates the valuable contribution of the participants who successfully contributed to translating this Pupil’s Book. In particular, TIE wishes to thank the University of Dar es Salaam (UDSM) and Open University of Tanzania (OUT). Besides, the following experts are acknowledged:"),
            ("pg004_n0004", "Translators: Ms Joyce C. Chamuhulo (TIE), Mr Charles Manyama (TIE) and Mr Given A. Mbakilwa (TIE)"),
            ("pg004_n0005", "Editors: Dr Cyprian N. Maro (UDSM) and Mr Beatus J. Nsiima (OUT)"),
            ("pg004_n0006", "Illustrators: Mr Fikiri A. Msimbe (TIE), Mr Yohana P. Mwenda and Mr Gwakisa U. Mwandoloma"),
            ("pg004_n0007", "Designer: Ms Mariam Matotola"),
            ("pg004_n0008", "Coordinators: Ms Joyce C. Chamuhulo (TIE) and Mr Charles Manyama (TIE)"),
        ],
    },
    "pg005_sec001": {
        "title": "Acknowledgements continued",
        "texts": [
            ("pg005_n0002", "Additionally, TIE extends its thanks to the teachers and Standard Two pupils who participated in testing the content of this book. Finally, TIE gives special thanks to the Government of the United Republic of Tanzania for overseeing and facilitating the writing of this textbook."),
            ("pg005_n0003", "Dr Aneth A. Komba"),
            ("pg005_n0004", "Director General"),
            ("pg005_n0005", "Tanzania Institute of Education"),
        ],
    },
}


WATERMARK_IDS = {
    "pg001_n0008", "pg007_n0022", "pg008_n0005", "pg012_n0005",
    "pg015_n0005", "pg018_n0040", "pg023_n0022", "pg039_n0016",
    "pg053_n0017", "pg058_n0011", "pg062_n0024", "pg066_n0029",
    "pg068_n0013", "pg072_n0007",
}


STATIC_ACTIVITY_PAGES = {
    "pg009_sec002.html", "pg011_sec002.html", "pg013_sec001.html",
    "pg013_sec002.html", "pg013_sec003.html", "pg013_sec004.html",
    "pg014_sec001.html", "pg016_sec001.html", "pg016_sec002.html",
    "pg018_sec001.html", "pg018_sec002.html", "pg019_sec002.html",
    "pg021_sec001.html", "pg021_sec002.html", "pg021_sec003.html",
    "pg024_sec002.html", "pg026_sec002.html", "pg026_sec003.html",
    "pg027_sec001.html", "pg031_sec002.html", "pg033_sec001.html",
    "pg033_sec002.html", "pg035_sec001.html", "pg036_sec001.html",
    "pg036_sec002.html", "pg037_sec001.html", "pg037_sec002.html",
    "pg038_sec001.html", "pg038_sec002.html", "pg039_sec001.html",
    "pg039_sec002.html", "pg041_sec002.html", "pg043_sec002.html",
    "pg045_sec002.html", "pg045_sec003.html", "pg046_sec001.html",
    "pg047_sec002.html",
    "pg051_sec001.html", "pg051_sec002.html", "pg051_sec003.html",
    "pg059_sec001.html", "pg063_sec001.html", "pg063_sec002.html",
    "pg067_sec002.html", "pg071_sec002.html", "pg072_sec001.html",
    "pg072_sec002.html",
}


def dump_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def replace_inline_text(source: str, text_id: str, value: str) -> str:
    encoded = html.escape(value, quote=False).replace("\n", "<br>")
    pattern = re.compile(
        rf'(<(?P<tag>[a-zA-Z][\w:-]*)\b[^>]*\bdata-id=["\']{re.escape(text_id)}["\'][^>]*>)(.*?)(</(?P=tag)>)',
        re.DOTALL,
    )
    return pattern.sub(lambda m: m.group(1) + encoded + m.group(4), source)


def remove_data_id_element(source: str, text_id: str) -> str:
    pattern = re.compile(
        rf'\s*<(?P<tag>[a-zA-Z][\w:-]*)\b[^>]*\bdata-id=["\']{re.escape(text_id)}["\'][^>]*>.*?</(?P=tag)>',
        re.DOTALL,
    )
    return pattern.sub("", source)


def staticize_activity(source: str) -> str:
    # Keep printed activities as ordinary readable content. The runtime adds
    # Submit/Reset controls to every activity_* section, even without inputs.
    source = re.sub(r'data-section-type="activity_[^"]+"', 'data-section-type="text"', source)
    source = re.sub(r'\s*<textarea\b[^>]*>.*?</textarea>', '', source, flags=re.DOTALL)
    source = re.sub(r'\s*<input\b[^>]*>', ' <span class="inline-block min-w-32 border-b-2 border-slate-500" aria-hidden="true">&nbsp;</span>', source)
    source = re.sub(r'\s*<script\b[^>]*>\s*window\.correctAnswers\s*=.*?</script>', '', source, flags=re.DOTALL)
    source = re.sub(r'\sdata-activity-item="[^"]*"', '', source)
    source = re.sub(r'\sdraggable="true"', '', source)
    source = re.sub(r'\srole="button"', '', source)
    source = re.sub(r'\stabindex="0"', '', source)
    source = re.sub(r'\s*<span\b[^>]*class="sr-only"[^>]*data-id="[^"]+"[^>]*>\s*</span>', '', source)
    return source


def update_localization() -> None:
    texts_path = I18N / "texts.json"
    audios_path = I18N / "audios.json"
    texts = json.loads(texts_path.read_text(encoding="utf-8"))
    audios = json.loads(audios_path.read_text(encoding="utf-8"))
    texts.update(TEXT_UPDATES)
    for page in FRONT_MATTER.values():
        texts.update(dict(page["texts"]))
    for key in list(texts):
        if key.startswith("qz") or "_ans_" in key or key in WATERMARK_IDS or key.removesuffix("_easy_read") in WATERMARK_IDS:
            texts.pop(key, None)
    for key in list(audios):
        if key.startswith("qz") or "_ans_" in key or key in WATERMARK_IDS:
            audios.pop(key, None)
    dump_json(texts_path, texts)
    dump_json(audios_path, audios)

    timecode_path = I18N / "timecode/timecode_output.json"
    if timecode_path.exists():
        timecodes = json.loads(timecode_path.read_text(encoding="utf-8"))
        for key in list(timecodes):
            if key.startswith("qz") or "_ans_" in key or key in WATERMARK_IDS:
                timecodes.pop(key, None)
        dump_json(timecode_path, timecodes)


def create_front_matter() -> None:
    for section_id, page in FRONT_MATTER.items():
        blocks = []
        for index, (text_id, value) in enumerate(page["texts"]):
            tag = "h1" if index == 0 and "Acknowledgements" in page["title"] else "p"
            classes = (
                "text-4xl font-bold text-purple-900 mb-8 max-sm:text-3xl"
                if tag == "h1"
                else "text-2xl leading-relaxed text-slate-800 mb-5 max-lg:text-xl max-sm:text-lg"
            )
            blocks.append(f'      <{tag} data-id="{text_id}" class="{classes}">{html.escape(value)}</{tag}>')
        document = f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Culture, Art and Sports Pupil’s Book Standard Two</title>
  <meta name="title-id" content="{section_id}" />
  <meta name="page-section-id" content="0" />
  <link href="./content/tailwind_output.css" rel="stylesheet">
  <link href="./assets/libs/fontawesome/css/all.min.css" rel="stylesheet">
  <link href="./assets/fonts.css" rel="stylesheet">
</head>
<body class="min-h-screen flex items-center justify-center">
  <main class="w-full">
    <div id="content" class="container mx-auto max-w-5xl bg-white px-12 py-12 max-lg:px-8 max-sm:px-5 opacity-0">
      <section role="article" data-section-type="text_only" data-section-id="{section_id}" class="rounded-3xl border-2 border-sky-200 bg-sky-50/30 px-12 py-10 shadow-sm max-lg:px-8 max-sm:px-5 max-sm:py-7">
{chr(10).join(blocks)}
      </section>
    </div>
  </main>
  <div class="relative z-50" id="interface-container"></div>
  <div class="relative z-50" id="nav-container"></div>
  <script src="./assets/offline-preloader.js"></script>
  <script src="./assets/scorm.js"></script>
  <script src="./assets/base.bundle.local.js"></script>
</body>
</html>
'''
        (ROOT / f"{section_id}.html").write_text(document, encoding="utf-8")


def update_html() -> None:
    standard_updates = {k: v for k, v in TEXT_UPDATES.items() if not k.endswith("_easy_read")}
    for path in ROOT.glob("*.html"):
        if path.name.startswith("qz"):
            continue
        source = path.read_text(encoding="utf-8")
        for text_id, value in standard_updates.items():
            if text_id.startswith(path.stem.split("_sec")[0]) or path.name == "index.html":
                source = replace_inline_text(source, text_id, value)
        for text_id in WATERMARK_IDS:
            source = remove_data_id_element(source, text_id)
        if path.name in STATIC_ACTIVITY_PAGES:
            source = staticize_activity(source)
        path.write_text(source, encoding="utf-8")


def source_specific_html_fixes() -> None:
    path = ROOT / "pg017_sec001.html"
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        '<div class="h-80 w-full rounded-[1rem] bg-[linear-gradient(180deg,#b8e3ff_0%,#d9f3b1_45%,#a3f000_100%)] max-lg:h-64 max-sm:h-52"></div>',
        '<img src="images/pg017_im003.jpg" alt="A green rice field grows in neat rows across a wet farm." data-id="pg017_im003" class="block h-80 max-w-full w-full rounded-[1rem] object-cover max-lg:h-64 max-sm:h-52" style="max-width: 100%; height: auto;">',
    )
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg029_sec001.html"
    source = path.read_text(encoding="utf-8").replace(
        'class="grid grid-cols-2 gap-1 bg-white"',
        'class="grid grid-cols-2 gap-0 bg-white"',
    )
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg043_sec002.html"
    source = path.read_text(encoding="utf-8")
    source = re.sub(
        r'\s*<div class="-ml-3 mb-1 rounded-\[1rem\][^"]*">9</div>',
        '',
        source,
    )
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg049_sec004.html"
    source = path.read_text(encoding="utf-8")
    if 'data-id="pg050_n0002"' not in source:
        source = source.replace(
            '<span data-id="pg049_n0020">It can be performed during cultural ceremonies such</span>',
            '<span data-id="pg049_n0020">It can be performed during cultural ceremonies such</span> '
            '<span data-id="pg050_n0002">as festivals, religious events or social gatherings.</span> '
            '<span data-id="pg050_n0003">Traditional dances reflect the history, values, beliefs and social customs.</span> '
            '<span data-id="pg050_n0004">These dances are usually specific to the culture they represent and may vary widely from one community to another.</span>',
        )
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg050_sec001.html"
    source = path.read_text(encoding="utf-8")
    source = re.sub(
        r'\s*<div class="relative z-10 mb-10[^>]*>\s*<span data-id="pg050_n0002">.*?</div>',
        '',
        source,
        flags=re.DOTALL,
    )
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg067_sec001.html"
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        'class="mx-auto mt-6 w-full rounded-[1.5rem] border-2 border-orange-200 bg-orange-50 px-8 py-5 max-lg:px-6 max-sm:mt-5 max-sm:rounded-[1.25rem] max-sm:px-4 max-sm:py-4"',
        'class="mx-auto mt-6 w-full px-2 py-2 max-sm:mt-5"',
    )
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg067_sec002.html"
    source = path.read_text(encoding="utf-8")
    source = source.replace(
        'class="min-w-0 flex-1 rounded-[24px] border-2 border-blue-200 bg-white/35 px-5 py-4 max-sm:px-4 max-sm:py-3"',
        'class="min-w-0 flex-1"',
    )
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg072_sec002.html"
    source = path.read_text(encoding="utf-8")
    for text_id in ["pg072_n0021", "pg072_n0026", "pg072_n0031", "pg072_n0036"]:
        marker = f'data-id="{text_id}"'
        if f'data-answer-line-for="{text_id}"' not in source:
            source = re.sub(
                rf'(<span {marker}[^>]*>.*?</span>)',
                rf'\1<span data-answer-line-for="{text_id}" class="mt-3 block w-24 border-b-2 border-neutral-700" aria-label="Answer line">&nbsp;</span>',
                source,
                count=1,
                flags=re.DOTALL,
            )
    # This is a printed matching exercise: keep its choices and requested
    # writing lines, but remove digital drag/drop affordances.
    for item_no, text_id in enumerate(["pg072_n0023", "pg072_n0028", "pg072_n0033", "pg072_n0038"], 1):
        source = re.sub(
            rf'<div class="dropzone[^>]*"[^>]*id="target{item_no}"><div id="dropzone-{item_no}"[^>]*></div><div data-id="{text_id}"[^>]*>(.*?)</div></div>',
            rf'<span data-id="{text_id}" class="block text-left text-[0.95rem] leading-relaxed text-neutral-900 max-sm:text-[0.88rem]">\1</span>',
            source,
            count=1,
            flags=re.DOTALL,
        )
    source = re.sub(r'<div class="mt-5 text-center"><span id="feedback".*?</span></div>', '', source, flags=re.DOTALL)
    path.write_text(source, encoding="utf-8")

    path = ROOT / "pg039_sec002.html"
    source = path.read_text(encoding="utf-8")
    source = source.replace(" rounded-md shadow-sm activity-item", " rounded-md shadow-sm")
    source = source.replace('class="dropzone border border-gray-300', 'class="border border-gray-300')
    source = re.sub(r'<div id="dropzone-1"[^>]*></div>', '', source)
    path.write_text(source, encoding="utf-8")

    path = ROOT / "index.html"
    source = path.read_text(encoding="utf-8")
    if 'images/pg001_signature.png' not in source:
        source = source.replace(
            '<div data-id="pg001_n0019"',
            '<img src="images/pg001_signature.png" alt="Signature of the Commissioner for Education" class="mb-2 h-auto w-48 max-sm:w-32">\n            <div data-id="pg001_n0019"',
        )
    path.write_text(source, encoding="utf-8")


def update_manifest() -> None:
    pages_path = ROOT / "content/pages.json"
    pages = json.loads(pages_path.read_text(encoding="utf-8"))
    pages = [entry for entry in pages if not entry["href"].startswith("qz")]
    existing = {entry["section_id"] for entry in pages}
    additions = [
        {"section_id": "pg002_sec001", "href": "pg002_sec001.html"},
        {"section_id": "pg004_sec001", "href": "pg004_sec001.html"},
        {"section_id": "pg005_sec001", "href": "pg005_sec001.html"},
    ]
    if not all(item["section_id"] in existing for item in additions):
        pages = [pages[0], additions[0], pages[1], additions[1], additions[2], *pages[2:]]
    dump_json(pages_path, pages)
    for index, entry in enumerate(pages, 1):
        page = ROOT / entry["href"]
        source = page.read_text(encoding="utf-8")
        source = re.sub(
            r'(<meta\s+name="page-section-id"\s+content=")[^"]*("\s*/?>)',
            rf'\g<1>{index}\2',
            source,
        )
        page.write_text(source, encoding="utf-8")
    manifest = ROOT / "imsmanifest.xml"
    source = manifest.read_text(encoding="utf-8")
    source = re.sub(r'^\s*<file href="qz00[1-8]\.html"/>\s*\n', '', source, flags=re.MULTILINE)
    for href in ["pg002_sec001.html", "pg004_sec001.html", "pg005_sec001.html"]:
        if f'<file href="{href}"/>' not in source:
            source = source.replace('      <file href="pg003_sec001.html"/>', f'      <file href="{href}"/>\n      <file href="pg003_sec001.html"/>', 1)
    manifest.write_text(source, encoding="utf-8")


def update_toc() -> None:
    path = ROOT / "content/toc.json"
    toc = json.loads(path.read_text(encoding="utf-8"))
    if not any(row.get("section_id") == "pg004_sec001" for row in toc):
        toc.insert(0, {"section_id": "pg004_sec001", "href": "pg004_sec001.html", "title": "Acknowledgements", "chapter_id": "pg004_n0002", "level": 1})
    for row in toc:
        if row.get("chapter_id") in TEXT_UPDATES:
            row["title"] = TEXT_UPDATES[row["chapter_id"]]
    dump_json(path, toc)


def main() -> None:
    update_localization()
    create_front_matter()
    update_html()
    source_specific_html_fixes()
    update_manifest()
    update_toc()
    # Catch any already-static activity pages outside the teacher-target list.
    for path in ROOT.glob("pg*.html"):
        source = path.read_text(encoding="utf-8")
        updated = source.replace('data-section-type="activity_other"', 'data-section-type="text"')
        updated = re.sub(r'src="\./assets/offline-preloader\.js(?:\?v=\d+)?"', 'src="./assets/offline-preloader.js?v=4"', updated)
        if updated != source:
            path.write_text(updated, encoding="utf-8")
    index_path = ROOT / "index.html"
    source = index_path.read_text(encoding="utf-8")
    source = re.sub(r'src="\./assets/offline-preloader\.js(?:\?v=\d+)?"', 'src="./assets/offline-preloader.js?v=4"', source)
    index_path.write_text(source, encoding="utf-8")


if __name__ == "__main__":
    main()
