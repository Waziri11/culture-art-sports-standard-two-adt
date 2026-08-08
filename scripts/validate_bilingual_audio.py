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
print(json.dumps({"mapped":len(by),"kiswahiliClips":sw,"errors":errors[:20]},indent=2))
raise SystemExit(bool(errors))
