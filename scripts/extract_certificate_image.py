#!/usr/bin/env python3
"""Reassemble the exact certificate image embedded across PDF page-one strips."""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "/Users/waziri/Desktop/ADT/Core Files/CULTURE ART AND SPORTS STD 2/"
    "CULTURE BOOK TWO FINAL LATEST CONFERENECE 4 AUGUST MANYAMA.pdf"
)
OUTPUT = ROOT / "images" / "pg001_certificate.png"


def main() -> None:
    strips: dict[int, Image.Image] = {}
    for image_file in PdfReader(str(SOURCE)).pages[0].images:
        number = int(image_file.name.removeprefix("Im").split(".")[0])
        strips[number] = Image.open(BytesIO(image_file.data)).convert("RGB")
    ordered = [strips[number] for number in sorted(strips)]
    if len(ordered) != 15 or len({image.width for image in ordered}) != 1:
        raise RuntimeError("Unexpected certificate strip structure in source PDF")
    certificate = Image.new("RGB", (ordered[0].width, sum(image.height for image in ordered)))
    y = 0
    for image in ordered:
        certificate.paste(image, (0, y))
        y += image.height
    # The embedded strips span the full PDF page width. Remove only the white
    # page margin around the certificate; do not resample or alter its pixels.
    certificate = certificate.crop((25, 60, 520, 788))
    certificate.save(OUTPUT, optimize=True)
    print(f"Extracted exact certificate image: {certificate.width}x{certificate.height}")


if __name__ == "__main__":
    main()
