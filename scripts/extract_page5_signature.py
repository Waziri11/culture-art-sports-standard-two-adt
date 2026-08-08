#!/usr/bin/env python3
"""Extract the authentic Director General signature embedded on PDF page five."""

from pathlib import Path

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(
    "/Users/waziri/Desktop/ADT/Core Files/CULTURE ART AND SPORTS STD 2/"
    "CULTURE BOOK TWO FINAL LATEST CONFERENECE 4 AUGUST MANYAMA.pdf"
)
OUTPUT = ROOT / "images" / "pg005_signature.jpg"


def main() -> None:
    images = PdfReader(str(SOURCE)).pages[4].images
    if len(images) != 1 or images[0].name != "Im0.jpg":
        raise RuntimeError("Unexpected signature image structure on PDF page five")
    OUTPUT.write_bytes(images[0].data)
    print(f"Extracted authentic page-five signature: {OUTPUT.name}")


if __name__ == "__main__":
    main()
