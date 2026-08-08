#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; I=ROOT/"content/i18n/en"
texts=json.loads((I/"texts.json").read_text()); audios=json.loads((I/"audios.json").read_text()); reg=json.loads((ROOT/"bilingual-audio-register.json").read_text())
by={x["textId"]:x for x in reg["clips"]}; errors=[]
for tid,name in audios.items():
    if not str(texts.get(tid," ")).strip(): continue
    p=I/"audio"/name
    if not p.exists() or p.stat().st_size<768: errors.append(f"missing/short {tid}")
    if tid not in by: errors.append(f"unregistered {tid}")
    elif by[tid]["visibleTextSha256"] != __import__('hashlib').sha256(str(texts[tid]).encode()).hexdigest(): errors.append(f"stale {tid}")
tc=json.loads((I/"timecode/timecode_output.json").read_text())
for tid in by:
    if tid not in tc: errors.append(f"missing timecode {tid}")
sw=sum(any(s["language"]=="sw" for s in x["spans"]) for x in by.values())
if sw<173: errors.append(f"only {sw} Kiswahili clips")
roman_ids={
    tid for tid,item in by.items()
    if "Roman " in " ".join(span["text"] for span in item["spans"])
}
expected_roman_ids={
    "pg003_n0006", "pg003_n0008",
    "pg003_n0006_easy_read", "pg003_n0008_easy_read",
}
if roman_ids != expected_roman_ids:
    errors.append(
        "Roman numeral scope mismatch: "
        f"unexpected={sorted(roman_ids-expected_roman_ids)} "
        f"missing={sorted(expected_roman_ids-roman_ids)}"
    )
print(json.dumps({"mapped":len(by),"kiswahiliClips":sw,"errors":errors[:20]},indent=2))
raise SystemExit(bool(errors))
