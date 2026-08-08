#!/usr/bin/env python3
"""Shared speech-friendly renderings for Kiswahili and Tanzanian names."""

from __future__ import annotations

import re


# Keep longer names before shorter words. Hyphens guide Tessa's syllable stress
# without adding the long pauses produced by space-separated spellings.
PRONUNCIATIONS = {
    "Mzee Masanja": "m-ZEH-eh mah-SAHN-jah",
    "Mzee": "m-ZEH-eh",
    "Masanja": "mah-SAHN-jah",
    "Adhana": "ah-THAA-nah",
    "Kabula": "kah-BOO-lah",
    "Msonge": "m-SOHN-geh",
    "Tembe": "TEM-beh",
    "Banda": "BAHN-dah",
    "Nchi": "n-CHEE",
    "ngonjera": "ngohn-JEH-rah",
    "Kiswahili": "kee-swah-HEE-lee",
    "Kilimanjaro": "kee-lee-mahn-JAH-roh",
    "Mawenzi": "mah-WEHN-zee",
    "Kibo": "KEE-boh",
    "Wanyiramba": "wah-nyee-RAHM-bah",
    "Wanyaturu": "wah-nyah-TOO-roo",
    "Wanyamwezi": "wah-nyah-MWEH-zee",
    "Wanyakyusa": "wah-nyah-KYOO-sah",
    "Wasukuma": "wah-soo-KOO-mah",
    "Wamasai": "wah-mah-SIGH",
    "Wachaga": "wah-CHAH-gah",
    "Wagogo": "wah-GOH-goh",
    "Wahaya": "wah-HAH-yah",
    "Wasafwa": "wah-SAH-fwah",
    "Wanyasa": "wah-NYAH-sah",
    "Wanyambo": "wah-NYAHM-boh",
    "Wapemba": "wah-PEHM-bah",
    "Wapogoro": "wah-poh-GOH-roh",
    "Wakinga": "wah-KEEN-gah",
    "Wakurya": "wah-KOOR-yah",
    "Wanyisanzu": "wah-nyee-SAHN-zoo",
    "Wasandawe": "wah-sahn-DAH-weh",
    "Wazigua": "wah-ZEE-gwah",
    "Wadigo": "wah-DEE-goh",
    "Wahehe": "wah-HEH-heh",
    "Wajita": "wah-JEE-tah",
    "Wamwera": "wah-MWEH-rah",
    "Wayao": "wah-YAH-oh",
    "Samaki": "sah-MAH-kee",
    "Tuungane": "too-oon-GAH-neh",
    "Tuwakemee": "too-wah-keh-MEH-eh",
    "Ufukara": "oo-foo-KAH-rah",
    "Utajiri": "oo-tah-JEE-ree",
}


def terms_in(text: str) -> list[str]:
    return [term for term in PRONUNCIATIONS if re.search(rf"\b{re.escape(term)}\b", text, re.I)]


def apply_pronunciations(text: str) -> str:
    for term, spoken in PRONUNCIATIONS.items():
        text = re.sub(rf"\b{re.escape(term)}\b", spoken, text, flags=re.I)
    return text
