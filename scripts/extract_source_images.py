#!/usr/bin/env python3
"""Replace reported image assets with exact embedded images from the approved PDF."""

from pathlib import Path

from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF = Path("/Users/waziri/Desktop/ADT/Core Files/CULTURE ART AND SPORTS STD 2/CULTURE BOOK TWO FINAL LATEST CONFERENECE 4 AUGUST MANYAMA.pdf")
OUT = ROOT / "images"


def save(page_number: int, image_index: int, filename: str) -> None:
    image = list(reader.pages[page_number - 1].images)[image_index].image.convert("RGB")
    image.save(OUT / filename, quality=95)


reader = PdfReader(str(PDF))

# Page 17: restore all four crop photographs, including the missing rice farm.
for index in range(4):
    save(17, index, f"pg017_im{index + 1:03d}.jpg")

# Pages explicitly reported as inverted or unclear.
save(34, 0, "pg034_im001.jpg")
carving = list(reader.pages[33].images)[1].image.convert("RGB").rotate(-90, expand=True)
carving.save(OUT / "pg034_im002.jpg", quality=95)

zebra = list(reader.pages[41].images)[0].image.convert("RGB").rotate(180, expand=True)
zebra.save(OUT / "pg042_im001.jpg", quality=95)
save(42, 1, "pg042_im002.jpg")
giraffe = list(reader.pages[41].images)[2].image.convert("RGB").rotate(180, expand=True)
giraffe.save(OUT / "pg042_im003.jpg", quality=95)
save(64, 0, "pg064_im001.jpg")
source_pitch = list(reader.pages[63].images)[1].image.convert("RGBA")
source_pitch.save(OUT / "pg064_im002.png")

# Page 69: recrop the clean source strip into the three displayed stages.
penalty = list(reader.pages[68].images)[0].image.convert("RGB")
width, height = penalty.size
cuts = [0, width // 3, (2 * width) // 3, width]
for index in range(3):
    penalty.crop((cuts[index], 0, cuts[index + 1], height)).save(
        OUT / f"pg069_im001_seg{index + 1:03d}_v1.png"
    )

# Preserve the signed approval from the supplied official cover without the
# surrounding diagonal watermark. The signature itself is outside the mark.
cover = Image.open(ROOT / "cover.png").convert("RGBA")
cw, ch = cover.size
signature = cover.crop((int(cw * 0.37), int(ch * 0.748), int(cw * 0.63), int(ch * 0.815)))
signature.save(OUT / "pg001_signature.png")
