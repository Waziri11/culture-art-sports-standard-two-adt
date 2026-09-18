#!/usr/bin/env python3
"""Install the Writing Standard 1 reader's responsive dock and mobile drawers.

The reference runtime, matching compiled UI stylesheet, and drawer helpers are
copied unchanged. Keep this book's compiled stylesheet first so its additional
lesson utilities remain available; the matching reader styles take precedence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REFERENCE = ROOT.parent.parent / "WRITING STD 1 PB/Writing-Pupil-s-Book-Standard-1-adt"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, default=DEFAULT_REFERENCE)
    parser.add_argument("--version", default="60")
    args = parser.parse_args()
    files = {
        "assets/base.bundle.local.js": "assets/base.bundle.local.js",
        "content/tailwind_output.css": "assets/reader-toolbar.css",
        "assets/mobile-sheet-drag.js": "assets/mobile-sheet-drag.js",
        "assets/mobile-sheet-drag.css": "assets/mobile-sheet-drag.css",
    }
    for source in files:
        assert (args.reference / source).is_file(), source
    copied = []
    for source, target in files.items():
        shutil.copyfile(args.reference / source, ROOT / target)
        copied.append({"source": source, "target": target,
                       "sha256": hashlib.sha256((ROOT / target).read_bytes()).hexdigest()})

    pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
    for page in pages:
        path = ROOT / page["href"]
        source = path.read_text(encoding="utf-8")
        if "./assets/reader-toolbar.css" not in source:
            source, count = re.subn(
                r'(<link\b[^>]*href="\./content/tailwind_output\.css(?:\?[^"]*)?"[^>]*>)',
                r'\1\n    <link href="./assets/reader-toolbar.css?v=' + args.version + '" rel="stylesheet">',
                source,
            )
            assert count == 1, path
        for css in ("mobile-sheet-drag.css", "reader-toolbar-layout.css"):
            if "./assets/" + css not in source:
                source = source.replace("</head>", f'<link href="./assets/{css}?v={args.version}" rel="stylesheet">\n</head>')
        if "./assets/mobile-sheet-drag.js" not in source:
            source = source.replace("</body>", f'<script src="./assets/mobile-sheet-drag.js?v={args.version}"></script>\n</body>')
        source = re.sub(r'(\./assets/(?:base\.bundle\.local\.js|offline-preloader\.js|book-covers\.css|reader-toolbar(?:-layout)?\.css|mobile-sheet-drag\.(?:js|css))\?v=)\d+',
                        lambda match: match[1] + args.version, source)
        path.write_text(source, encoding="utf-8")

    config_path = ROOT / "assets/config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["bundleVersion"] = args.version
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    subprocess.run([sys.executable, "-B", str(ROOT / "scripts/rebuild_offline_preloader.py")], check=True)

    manifest_path = ROOT / "imsmanifest.xml"
    manifest = manifest_path.read_text(encoding="utf-8")
    for name in [*files.values(), "assets/reader-toolbar-layout.css"]:
        if f'href="{name}"' not in manifest:
            manifest = manifest.replace("</resource>", f'      <file href="{name}" />\n    </resource>')
    manifest_path.write_text(manifest, encoding="utf-8")
    report = {
        "referenceBook": args.reference.name,
        "bundleVersion": args.version,
        "pagesUpdated": len(pages),
        "mobileBreakpoint": "max-width: 767.98px",
        "files": copied,
    }
    (ROOT / "responsive-toolbar-report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Installed the reference toolbar on {len(pages)} pages; bundle version {args.version}.")


if __name__ == "__main__":
    main()
