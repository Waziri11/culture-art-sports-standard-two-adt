#!/usr/bin/env python3
"""One-time insertion of the supplied covers around the 114-page reader.

Source-page text IDs stay stable: several reader pages share a printed page.
Reader positions (page-section-id) and sign-video filenames are renumbered.
New cover audio filenames explicitly identify reader pages 1 and 116.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content/i18n/en"
SOURCE = ROOT.parent / "CULTURE STUDENT  NOT FOR SALE.pdf"
VIDEOS = ROOT.parent / "CULTURE ARTS AND SPORTS - Compressed"


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sha(path):
    return hashlib.file_digest(path.open("rb"), "sha256").hexdigest()


def main():
    pages = read_json(ROOT / "content/pages.json")
    videos = read_json(I18N / "videos.json")
    if len(pages) != 114 or pages[0]["section_id"] != "pg001_sec001":
        raise SystemExit("This migration expects the original 114-page reader; covers may already be installed.")
    assert not (ROOT / "pg001_sec001.html").exists()
    assert not (ROOT / "pg073_sec001.html").exists()
    assert SOURCE.is_file()
    assert (VIDEOS / "FRONT.mp4").is_file() and (VIDEOS / "BACK.mp4").is_file()
    assert len(videos) == 114 and len(set(videos.values())) == 114
    for name in videos.values():
        assert (I18N / "video" / name).is_file(), name

    original_audios = read_json(I18N / "audios.json")
    original_index = (ROOT / "index.html").read_text(encoding="utf-8")
    migration = []
    for index, page in enumerate(pages, 1):
        migration.append({
            "sectionId": page["section_id"], "oldReaderPage": index, "readerPage": index + 1,
            "oldHref": page["href"], "href": "pg001_sec001.html" if index == 1 else page["href"],
            "oldVideo": videos[f"video-{index}"], "video": f"page_{index + 1}.mp4",
            "videoSha256": sha(I18N / "video" / videos[f"video-{index}"]),
        })

    # Coordinates are measured on the publisher's 1800 x 1313 cover proof.
    # Each illustration is a separate image, with its own description/audio ID.
    doc = pymupdf.open(SOURCE)
    page = doc[0]
    def crop(name, box):
        x0, y0, x1, y1 = box
        clip = pymupdf.Rect(x0 * page.rect.width / 1800, y0 * page.rect.height / 1313,
                            x1 * page.rect.width / 1800, y1 * page.rect.height / 1313)
        page.get_pixmap(matrix=pymupdf.Matrix(2.5, 2.5), clip=clip, alpha=False).save(ROOT / name)

    crops = {
        "cover.png": (900, 60, 1741, 1254),
        "images/page_1_drummers.png": (999, 428, 1375, 689),
        "images/page_1_traditional_house.png": (1384, 431, 1714, 693),
        "images/page_1_target_game.png": (987, 773, 1308, 990),
        "images/page_1_modelling_clay.png": (1338, 728, 1698, 997),
        "images/cover_tie_logo.png": (674, 168, 805, 304),
        "images/page_116_writing.png": (223, 414, 378, 638),
        "images/page_116_kusoma.png": (419, 409, 563, 638),
        "images/page_116_arithmetic.png": (596, 409, 747, 638),
        "images/page_116_learn_english.png": (319, 654, 463, 874),
        "images/page_116_health_and_environment.png": (491, 654, 639, 874),
        "images/page_116_barcode.png": (625, 998, 766, 1125),
    }
    for name, box in crops.items():
        crop(name, box)

    clips = []
    def text(tid, filename, value):
        clips.append({"textId": tid, "filename": filename + ".mp3", "text": value})
        return html.escape(value)

    def label(tag, tid, name, value, cls=""):
        return f'<{tag} data-id="{tid}" class="{cls}">{text(tid, name, value)}</{tag}>'

    notice = "Property of the Government of the United Republic of Tanzania. Not for Sale."
    publisher = "Tanzania Institute of Education"
    front = '<section role="article" data-section-type="front_cover" data-section-id="pg000_sec001" class="book-cover front-cover" aria-label="Front cover">\n<header class="cover-heading">'
    front += label("h1", "pg000_gp001_tx001", "page_1_title", "Culture, Art and Sports", "cover-title")
    front += label("p", "pg000_gp001_tx002", "page_1_pupils_book", "Pupil’s Book", "cover-subtitle")
    front += label("p", "pg000_gp001_tx003", "page_1_standard_two", "Standard Two", "cover-standard")
    front += '</header>\n<div class="cover-pictures">'
    pictures = [
        ("drummers", "Four people in traditional dress play drums together."),
        ("traditional_house", "A traditional round house has woven walls and a cone-shaped thatched roof."),
        ("target_game", "A pupil throws a ball towards a group of bottles in a target game."),
        ("modelling_clay", "Pupils, including a pupil with a visual impairment, model objects from clay at a table."),
    ]
    for index, (name, description) in enumerate(pictures, 1):
        alt = text(f"pg000_im{index:03}", f"page_1_{name}_description", description)
        front += f'<img data-id="pg000_im{index:03}" src="images/page_1_{name}.png" alt="{alt}">\n'
    front += '</div>\n<div class="cover-publisher">'
    front += label("p", "pg000_gp002_tx001", "page_1_publisher", publisher)
    front += '<img class="cover-logo" src="images/cover_tie_logo.png" alt="Tanzania Institute of Education logo"></div>'
    front += '<footer class="cover-footer">' + label("p", "pg000_gp003_tx001", "page_1_not_for_sale", notice, "cover-notice") + '</footer></section>'

    back = '<section role="article" data-section-type="back_cover" data-section-id="pg073_sec001" class="book-cover back-cover" aria-label="Back cover">\n<header class="cover-heading"><div>'
    back += label("h1", "pg073_gp001_tx001", "page_116_other_books", "Other Books by")
    back += label("p", "pg073_gp001_tx002", "page_116_publisher", publisher, "cover-by")
    back += '</div><img class="cover-logo" src="images/cover_tie_logo.png" alt="Tanzania Institute of Education logo"></header>'
    back += label("h2", "pg073_gp001_tx003", "page_116_standard_two", "Standard Two", "cover-standard")
    back += '<div class="cover-books">'
    books = [("writing", "Writing"), ("kusoma", "Kusoma"), ("arithmetic", "Arithmetic"),
             ("learn_english", "Learn English"), ("health_and_environment", "Health and Environment")]
    for index, (name, title) in enumerate(books, 1):
        back += f'<figure><img src="images/page_116_{name}.png" alt="{title}, Standard Two book cover">'
        back += label("figcaption", f"pg073_gp002_tx{index:03}", f"page_116_{name}", title) + '</figure>'
    back += '</div><figure class="cover-isbn"><img src="images/page_116_barcode.png" alt="Book barcode">'
    back += label("figcaption", "pg073_gp003_tx001", "page_116_isbn", "ISBN: 978-9912-753-72-3") + '</figure>'
    back += '<footer class="cover-footer">' + label("p", "pg073_gp004_tx001", "page_116_not_for_sale", notice, "cover-notice") + '</footer></section>'

    def document(section, content, position, title):
        head = original_index.split('<body', 1)[0]
        head = re.sub(r'<title>.*?</title>', f'<title>{title}</title>', head)
        head = re.sub(r'(name="title-id" content=")[^"]+', r'\g<1>' + section, head)
        head = re.sub(r'(name="page-section-id" content=")[^"]+', r'\g<1>' + str(position), head)
        head = head.replace('</head>', '<link rel="stylesheet" href="./assets/book-covers.css?v=59">\n</head>')
        scripts = original_index[original_index.index('    <div class="relative z-50" id="interface-container"'):]
        return head + '<body class="book-cover-page">\n<main><div id="content" class="opacity-0">\n' + content + '\n</div></main>\n' + scripts

    (ROOT / "pg001_sec001.html").write_text(original_index.replace('data-section-type="front_cover"', 'role="article" data-section-type="title_page"'), encoding="utf-8")
    (ROOT / "index.html").write_text(document("pg000_sec001", front, 1, "Front cover - Culture, Art and Sports Standard Two"), encoding="utf-8")
    (ROOT / "pg073_sec001.html").write_text(document("pg073_sec001", back, 116, "Back cover - Culture, Art and Sports Standard Two"), encoding="utf-8")
    pages[0]["href"] = "pg001_sec001.html"
    pages = [{"section_id": "pg000_sec001", "href": "index.html"}] + pages + [{"section_id": "pg073_sec001", "href": "pg073_sec001.html"}]
    for position, entry in enumerate(pages, 1):
        path = ROOT / entry["href"]
        source = path.read_text(encoding="utf-8")
        source = re.sub(r'(name="page-section-id" content=")[^"]+', r'\g<1>' + str(position), source)
        source = source.replace('?v=58', '?v=59')
        path.write_text(source, encoding="utf-8")
    write_json(ROOT / "content/pages.json", pages)

    toc = read_json(ROOT / "content/toc.json")
    toc[:0] = [
        {"section_id": "pg000_sec001", "href": "index.html", "title": "Front cover", "chapter_id": "pg000_gp001_tx001", "level": 1},
        {"section_id": "pg001_sec001", "href": "pg001_sec001.html", "title": "Title and approval", "chapter_id": "pg001_n0002", "level": 1},
    ]
    toc.append({"section_id": "pg073_sec001", "href": "pg073_sec001.html", "title": "Back cover", "chapter_id": "pg073_gp001_tx001", "level": 1})
    write_json(ROOT / "content/toc.json", toc)

    # Descending moves cannot overwrite an earlier video's original contents.
    video_dir = (I18N / "video").resolve()
    for entry in reversed(migration):
        source = (video_dir / entry["oldVideo"]).resolve()
        target = (video_dir / entry["video"]).resolve()
        assert source.parent == video_dir and target.parent == video_dir
        assert not target.exists(), target
        source.rename(target)
    shutil.copyfile(VIDEOS / "FRONT.mp4", video_dir / "page_1.mp4")
    shutil.copyfile(VIDEOS / "BACK.mp4", video_dir / "page_116.mp4")
    write_json(I18N / "videos.json", {f"video-{n}": f"page_{n}.mp4" for n in range(1, 117)})

    texts = read_json(I18N / "texts.json")
    audios = original_audios.copy()
    for clip in clips:
        texts[clip["textId"]] = clip["text"]
        audios[clip["textId"]] = clip["filename"]
    texts["pg000_sec001"] = "Front cover"
    texts["pg073_sec001"] = "Back cover"
    write_json(I18N / "texts.json", texts)
    write_json(I18N / "audios.json", audios)
    write_json(ROOT / "cover-audio-report.json", {"voice": "en-TZ-ImaniNeural", "rate": "-8%", "pitch": "+0Hz", "clips": clips})
    config = read_json(ROOT / "assets/config.json")
    config["bundleVersion"] = "59"
    write_json(ROOT / "assets/config.json", config)
    write_json(ROOT / "cover-page-media-report.json", {
        "readerPagesBefore": 114, "readerPagesAfter": 116,
        "frontCover": {"readerPage": 1, "href": "index.html", "video": "page_1.mp4", "source": "FRONT.mp4", "videoSha256": sha(VIDEOS / "FRONT.mp4")},
        "backCover": {"readerPage": 116, "href": "pg073_sec001.html", "video": "page_116.mp4", "source": "BACK.mp4", "videoSha256": sha(VIDEOS / "BACK.mp4")},
        "existingNarrationIdsPreserved": len(original_audios), "shiftedPages": migration,
    })
    print(f"Inserted covers; {len(pages)} pages, {len(clips)} new narration clips queued.")


if __name__ == "__main__":
    main()
