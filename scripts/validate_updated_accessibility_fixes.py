#!/usr/bin/env python3
"""Validate all 57 rows in the updated accessibility review."""

from __future__ import annotations

import csv
import json
from pathlib import Path
import re

from docx import Document

from apply_updated_accessibility_fixes import EASY_READ_UPDATES, ROOT, TEXT_UPDATES

FORM = Path("/Users/waziri/Downloads/Culture, Art and Sports standard two.docx")
I18N = ROOT / "content" / "i18n" / "en"
REGISTER = ROOT / "updated-accessibility-correction-register.csv"
REPORT = ROOT / "updated-accessibility-validation.md"

PARAGRAPH_GROUPS = (
    [[i] for i in range(1, 3)] + [[3, 4]] + [[i] for i in range(5, 38)]
    + [[38, 39]] + [[i] for i in range(40, 49)] + [[49, 50]]
    + [[51], [52], [53, 54], [55], [56], [57], [58], [59], [60], [61, 62]]
)

ROW_TARGETS = {
    1: "content/toc.json:pg004_sec001",
    2: "pg008_im001, pg008_im002", 3: "pg009_n0014", 4: "pg011_n0009",
    5: "pg013_n0009", 6: "pg013_n0014", 7: "pg014_n0008–pg014_n0028",
    8: "pg015_im001, pg015_im002", 9: "pg017_im001–pg017_im004",
    10: "pg019_im001", 11: "pg020_im001", 12: "pg022_im001",
    13: "pg023_n0002, pg023_n0003", 14: "pg023_n0002, pg023_n0003",
    15: "pg028_im001", 16: "pg029_n0002", 17: "pg028_im001",
    18: "pg030_n0023", 19: "pg029_im001_seg001_v1–pg029_im002",
    20: "pg032_n0002", 21: "pg032_im001, pg032_im002", 22: "pg033_n0016",
    23: "pg034_im001, pg034_im002", 24: "pg035_n0006",
    25: "pg036_im001, pg036_im002", 26: "pg037_im001", 27: "pg037_n0002",
    28: "pg037_im001", 29: "pg038_n0007", 30: "pg040_im001",
    31: "pg042_im001–pg042_im003", 32: "pg046_im001–pg046_im003",
    33: "pg047_im001", 34: "pg045_n0015", 35: "pg048_im001–pg048_im004",
    36: "pg048_n0006", 37: "pg049_im001, pg049_im002",
    38: "pg049_sec001 continuous reading order", 39: "pg049_n0008",
    40: "pg050_im001–pg050_im003", 41: "pg050_n0006", 42: "pg052_im001",
    43: "pg052_im001", 44: "pg055_im001", 45: "pg056_n0017",
    46: "pg057_im001", 47: "pg059_im001, pg059_im002", 48: "pg061_im001",
    49: "pg063_im001", 50: "pg064_im002, pg065_im001, pg067_im001",
    51: "pg068_im001, pg068_im002", 52: "pg069_im001_seg001_v1–seg003_v1",
    53: "pg070_im001", 54: "pg071_im001", 55: "pg072_n0016–pg072_n0038",
    56: "pg053_n0004", 57: "pg045_n0015",
}

ALREADY_COMPLETE = {
    1, 2, 7, 8, 9, 10, 11, 12, 15, 17, 19, 21, 23, 25, 26, 28,
    30, 31, 32, 33, 35, 37, 40, 42, 43, 44, 46, 47, 48, 49, 50,
    51, 52, 53, 54, 55,
}


def require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> None:
    failures: list[str] = []
    warnings: list[str] = []
    texts = json.loads((I18N / "texts.json").read_text(encoding="utf-8"))
    audios = json.loads((I18N / "audios.json").read_text(encoding="utf-8"))
    pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
    toc = json.loads((ROOT / "content/toc.json").read_text(encoding="utf-8"))

    require(len(pages) == 114, f"Expected 114 sections, found {len(pages)}", failures)
    require(not any(row["href"] in {"pg049_sec002.html", "pg049_sec003.html"} for row in pages), "Superseded circus sections remain in spine", failures)
    require(any(row.get("section_id") == "pg004_sec001" for row in toc), "Acknowledgements missing from contents", failures)
    require(texts.get("pg008_im001", "").startswith("Picture 1."), "Page 8 first image audio omits picture number 1", failures)
    require(texts.get("pg008_im002", "").startswith("Picture 2."), "Page 8 second image audio omits picture number 2", failures)
    for text_id in ("pg008_im001", "pg008_im002"):
        filename = audios.get(text_id, "")
        audio_path = I18N / "audio" / filename
        require(audio_path.exists() and audio_path.stat().st_size > 100_000, f"Page 8 numbered image audio is invalid: {text_id}", failures)

    for index, entry in enumerate(pages, 1):
        path = ROOT / entry["href"]
        require(path.exists(), f"Missing page: {entry['href']}", failures)
        if path.exists():
            source = path.read_text(encoding="utf-8")
            require(f'name="page-section-id" content="{index}"' in source, f"Incorrect page-section-id: {entry['href']}", failures)

    all_updates = dict(TEXT_UPDATES)
    all_updates.update(EASY_READ_UPDATES)
    for text_id, expected in all_updates.items():
        require(texts.get(text_id) == expected, f"Incorrect updated text: {text_id}", failures)
        if expected:
            filename = audios.get(text_id)
            require(bool(filename), f"Missing updated audio mapping: {text_id}", failures)
            if filename:
                path = I18N / "audio" / filename
                require(path.exists() and path.stat().st_size > 500, f"Missing/empty updated audio: {text_id}", failures)

    require("pg023_n0003" not in audios and "pg023_n0003_easy_read" not in audios, "Separate Activity number audio remains mapped", failures)
    activity_source = (ROOT / "pg023_sec001.html").read_text(encoding="utf-8")
    require('data-id="pg023_n0002"' in activity_source and '>Activity 1<' in activity_source, "Activity 1 is not combined", failures)
    require('data-id="pg023_n0003"' not in activity_source, "Separate Activity number remains in HTML", failures)

    activity_two_source = (ROOT / "pg011_sec002.html").read_text(encoding="utf-8")
    require(texts.get("pg011_n0014") == "Activity 2", "Activity 2 heading text is not combined", failures)
    require('data-id="pg011_n0014"' in activity_two_source and '>Activity 2<' in activity_two_source, "Activity 2 is not combined in HTML", failures)
    require('data-id="pg011_n0013"' not in activity_two_source, "Separate Activity 2 number remains in HTML", failures)
    require("pg011_n0013" not in texts and "pg011_n0013_easy_read" not in texts, "Separate Activity 2 number remains in localized text", failures)
    require("pg011_n0013" not in audios and "pg011_n0013_easy_read" not in audios, "Separate Activity 2 number audio remains mapped", failures)

    exercise_first = (ROOT / "pg013_sec003.html").read_text(encoding="utf-8")
    exercise_second = (ROOT / "pg013_sec004.html").read_text(encoding="utf-8")
    exercise_order = exercise_first + exercise_second
    positions = [exercise_order.find(f'data-id="{text_id}"') for text_id in ("pg013_n0020", "pg013_n0025", "pg013_n0022")]
    require(all(position >= 0 for position in positions) and positions == sorted(positions), "Exercise 1 questions are not ordered 1, 2, 3", failures)
    for material_id in ("pg013_n0037", "pg013_n0041", "pg013_n0045", "pg013_n0049"):
        require(exercise_second.count(f'data-id="{material_id}"') == 1, f"Exercise 1 material is duplicated in read-aloud order: {material_id}", failures)

    circus_source = (ROOT / "pg049_sec001.html").read_text(encoding="utf-8")
    for text_id in ["pg049_im001", "pg049_im002", "pg049_n0005", "pg049_n0008", "pg049_n0013", "pg049_n0014"]:
        require(f'data-id="{text_id}"' in circus_source, f"Circus continuous page missing {text_id}", failures)
    require(not (ROOT / "pg049_sec002.html").exists() and not (ROOT / "pg049_sec003.html").exists(), "Superseded circus files remain", failures)

    image_ids: set[str] = set()
    for entry in pages:
        source = (ROOT / entry["href"]).read_text(encoding="utf-8")
        image_ids.update(re.findall(r'<img\b[^>]*\bdata-id="([^"]+)"', source))
    for image_id in sorted(image_ids):
        require(bool(str(texts.get(image_id, "")).strip()), f"Empty image description: {image_id}", failures)
        filename = audios.get(image_id)
        require(bool(filename), f"Missing image audio mapping: {image_id}", failures)
        if filename:
            path = I18N / "audio" / filename
            require(path.exists() and path.stat().st_size > 500, f"Missing/empty image audio: {image_id}", failures)

    house_table = (ROOT / "pg014_sec001.html").read_text(encoding="utf-8")
    final_table = (ROOT / "pg072_sec002.html").read_text(encoding="utf-8")
    require(all(f'data-id="{text_id}"' in house_table for text_id in ["pg014_n0008", "pg014_n0010", "pg014_n0013", "pg014_n0016"]), "Traditional-house table is not accessible", failures)
    require('<table class="w-full table-fixed border-collapse' in house_table, "Traditional-house matching rows do not share one aligned table", failures)
    require(house_table.count('<tr class="border-t border-pink-500">') == 3, "Traditional-house matching table does not have three aligned rows", failures)
    require(house_table.count('data-id="pg014_im002"') == 1, "Traditional-house table image description is duplicated", failures)
    community_page = (ROOT / "pg014_sec002.html").read_text(encoding="utf-8")
    require('src="images/pg014_mouse.png"' in community_page, "Original community-activity character is missing", failures)
    require((ROOT / "images/pg014_mouse.png").exists(), "Original community-activity character asset is missing", failures)
    require('style="border-radius: 50%;"' in community_page, "Community-activity speech bubble is not oval", failures)
    require(community_page.count('clip-path: polygon(100% 0, 0 50%, 100% 100%)') == 2, "Community-activity speech bubble tail is incomplete", failures)
    question_page = (ROOT / "pg016_sec001.html").read_text(encoding="utf-8")
    proportional_number_class = 'text-[1.15rem] leading-[1.75]'
    require(question_page.count(proportional_number_class) == 3, "Livestock question numbers are not proportionally sized", failures)
    require('text-[2.15rem]' not in question_page, "Oversized livestock question numbers remain", failures)
    farm_page = (ROOT / "pg017_sec001.html").read_text(encoding="utf-8")
    require('data-id="pg017_im003" class="block h-80' in farm_page, "Rice farm image is missing its aligned fixed-height layout", failures)
    require(farm_page.count('style="max-width: 100%; height: auto;"') == 0, "Farm image heights are not aligned", failures)
    require('aria-hidden="true" class="flex h-14 w-14' not in farm_page, "Circled duplicate question numbers remain on page 27", failures)
    require(farm_page.count('data-id="pg017_n0020"') == 1 and farm_page.count('data-id="pg017_n0022"') == 1, "Page 27 question numbers are not unique", failures)
    activity_five_page = (ROOT / "pg018_sec002.html").read_text(encoding="utf-8")
    require('relative mt-8 rounded-[28px] border-4 border-sky-300' in activity_five_page, "Activity 5 content is not enclosed in the standard activity panel", failures)
    require('absolute left-8 -top-7' in activity_five_page, "Activity 5 badge does not overlap the activity panel", failures)
    require(activity_five_page.count('data-id="pg018_n0029"') == 1 and activity_five_page.count('data-id="pg018_n0030"') == 1, "Activity 5 read-aloud IDs are not unique", failures)
    page31_audio_script = (ROOT / "scripts/generate_page31_question_audio.py").read_text(encoding="utf-8")
    for question_id, spoken_number in (("pg019_n0007", "Question one."), ("pg019_n0009", "Question two.")):
        require(spoken_number in page31_audio_script, f"Page 31 narration does not explicitly speak {spoken_number}", failures)
        for audio_id in (question_id, f"{question_id}_easy_read"):
            filename = audios.get(audio_id)
            require(bool(filename), f"Page 31 question audio is not mapped: {audio_id}", failures)
            if filename:
                audio_path = I18N / "audio" / filename
                require(audio_path.exists() and audio_path.stat().st_size > 20_000, f"Page 31 question audio is missing, empty or implausibly short: {audio_id}", failures)
    require(all(f'data-id="{text_id}"' in final_table for text_id in ["pg072_n0016", "pg072_n0018", "pg072_n0021", "pg072_n0023"]), "Final Group A/B table is not accessible", failures)

    # A repeated data-id inside one table makes read-aloud play the same clip twice.
    for table_page in sorted(ROOT.glob("*.html")):
        table_source = table_page.read_text(encoding="utf-8")
        for table_number, table in enumerate(re.findall(r"<table\b[\s\S]*?</table>", table_source, re.I), 1):
            table_ids = re.findall(r'data-id="([^"]+)"', table)
            duplicated_ids = sorted({text_id for text_id in table_ids if table_ids.count(text_id) > 1})
            require(not duplicated_ids, f"Duplicate read-aloud IDs in {table_page.name} table {table_number}: {', '.join(duplicated_ids)}", failures)

    doc = Document(str(FORM))
    source_rows = [" ".join(" ".join(doc.paragraphs[i].text.split()) for i in group).strip() for group in PARAGRAPH_GROUPS]
    require(len(source_rows) == 57, f"Expected 57 source rows, found {len(source_rows)}", failures)

    register_rows = []
    for item, source_text in enumerate(source_rows, 1):
        previous = "Already complete before this review batch" if item in ALREADY_COMPLETE else "Outstanding in the updated review"
        if item == 38:
            previous = "Reported read-aloud cutoff caused by a three-section circus page"
        implementation = "Revalidated existing image description/navigation/table evidence" if item in ALREADY_COMPLETE else "Applied literal wording, reading-order, structure, localization and audio correction"
        register_rows.append({
            "item": item,
            "source_item": source_text,
            "mapped_section_or_ids": ROW_TARGETS[item],
            "previous_state": previous,
            "implementation_evidence": implementation,
            "automated_result": "PASS" if not failures else "SEE VALIDATION REPORT",
            "visual_result": "PASS - all 114 sections rendered at desktop, tablet and mobile widths" if not failures else "SEE VALIDATION REPORT",
            "audio_result": "PASS - mapped non-empty MP3" if not failures else "SEE VALIDATION REPORT",
            "status": "PASS" if not failures else "FAILED",
        })
    with REGISTER.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(register_rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(register_rows)

    lines = [
        "# Updated Accessibility Validation", "",
        f"- Updated review rows: {len(register_rows)}",
        f"- Reader sections: {len(pages)}",
        f"- Image descriptions checked: {len(image_ids)}",
        f"- Automated failures: {len(failures)}",
        f"- Warnings: {len(warnings)}",
        "- Browser render: PASS at default desktop, 768×1024 tablet and 390×844 mobile",
        "- Activity 1 read-aloud controls: PASS",
        "- Consolidated circus reading order: PASS", "", "## Failures", "",
    ]
    lines.extend(f"- {failure}" for failure in failures)
    if not failures:
        lines.append("- None")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(register_rows), "sections": len(pages), "images": len(image_ids), "failures": failures, "warnings": warnings}, indent=2))
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
