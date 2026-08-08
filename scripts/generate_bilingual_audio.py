#!/usr/bin/env python3
"""Regenerate every mapped ADT narration clip with Tanzanian bilingual voices."""

from __future__ import annotations

import argparse, asyncio, hashlib, json, math, os, re, shutil, struct, subprocess, tempfile, wave
from collections import Counter
from pathlib import Path

import edge_tts  # type: ignore
import lameenc  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
I18N = ROOT / "content/i18n/en"
EN_FEMALE, EN_MALE = "en-TZ-ImaniNeural", "en-TZ-ElimuNeural"
SW_FEMALE, SW_MALE = "sw-TZ-RehemaNeural", "sw-TZ-DaudiNeural"
RATE, PITCH, GAP_MS = "-8%", "+0Hz", 55
WORD_RE = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ’']+(?:-[A-Za-zÀ-ÖØ-öø-ÿ’']+)*|\d+|[^A-Za-zÀ-ÖØ-öø-ÿ’'\d]+")
MZEE_IDS = {
 "pg024_n0025","pg024_n0026","pg025_n0006","pg025_n0007","pg025_n0013","pg025_n0014","pg025_n0019","pg025_n0020",
 "pg025_n0021","pg025_n0022","pg025_n0027","pg025_n0028","pg026_n0007","pg026_n0008","pg026_n0015","pg026_n0016"
}

def clean(text: str) -> str:
    text = re.sub(r"\[\[blank:[^]]+\]\]", " ", text)
    text = re.sub(r"_{2,}|\.{4,}", " ", text)
    text = text.replace("\n", ". ").replace("•", " ")
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text)
    text = re.sub(r"(?<=\d)\.(?=\s|$)", "", text) # never say “six dot”
    text = speak_roman_numerals(text)
    text = re.sub(r"\(([a-z])\)", lambda m: f" letter {m.group(1).upper()} ", text)
    return re.sub(r"\s+", " ", text).strip(" .")

def speak_roman_numerals(text: str) -> str:
    """Expand Roman numerals only when their position proves they are numerals.

    A Roman-looking sequence inside ordinary prose is not sufficient: English
    words and labels such as I, did, C, D and initials must remain untouched.
    The book uses Roman numerals as standalone contents-page numbers and may use
    i-x as an explicit leading list marker.
    """
    stripped = text.strip()
    if re.fullmatch(r"(?:ii|iii|iv|vi|vii|viii|ix|xi|xii|xiii|xiv|xv)", stripped):
        return "Roman " + str(roman(stripped))

    list_numerals = r"i|ii|iii|iv|v|vi|vii|viii|ix|x"
    text = re.sub(
        rf"^\s*\(({list_numerals})\)(?=\s)",
        lambda m: "Roman " + str(roman(m.group(1))) + ".",
        text,
        flags=re.I,
    )
    return re.sub(
        rf"^\s*({list_numerals})\.(?=\s)",
        lambda m: "Roman " + str(roman(m.group(1))) + ".",
        text,
        flags=re.I,
    )

def roman(value: str) -> int:
    nums={"i":1,"v":5,"x":10,"l":50,"c":100,"d":500,"m":1000}; total=prev=0
    for ch in reversed(value.lower()):
        n=nums[ch]; total += -n if n < prev else n; prev=max(prev,n)
    return total

def load_lexicon():
    data=json.loads((ROOT/"scripts/kiswahili_lexicon.json").read_text())
    terms=sorted(data["terms"], key=len, reverse=True)
    return data, re.compile(r"(?<![\w’'])((?:"+"|".join(re.escape(x) for x in terms)+r"))(?![\w’'])", re.I)

LEX, SW_RE = load_lexicon()

def is_male(text_id: str) -> bool:
    base=text_id.removesuffix("_easy_read")
    return base in MZEE_IDS or any(base.startswith(x) for x in LEX["fullSwahiliIdPrefixes"])

def spans(text_id: str, text: str):
    spoken=clean(text)
    if not spoken: return []
    base=text_id.removesuffix("_easy_read")
    male=is_male(text_id)
    if any(base.startswith(x) for x in LEX["fullSwahiliIdPrefixes"]):
        return [(SW_MALE if male else SW_FEMALE, spoken, "sw")]
    out=[]; pos=0
    for m in SW_RE.finditer(spoken):
        if m.start()>pos: out.append((EN_MALE if male else EN_FEMALE, spoken[pos:m.start()], "en"))
        out.append((SW_MALE if male else SW_FEMALE, m.group(0), "sw")); pos=m.end()
    if pos<len(spoken): out.append((EN_MALE if male else EN_FEMALE, spoken[pos:], "en"))
    merged=[]
    for voice,part,lang in out:
        if not part.strip(): continue
        if not re.search(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]", part):
            if merged: merged[-1]=(merged[-1][0],merged[-1][1]+part,merged[-1][2])
            continue
        if merged and merged[-1][0]==voice: merged[-1]=(voice,merged[-1][1]+part,lang)
        else: merged.append((voice,part,lang))
    return merged

async def synth(voice: str, text: str, path: Path):
    events=[]; audio=bytearray()
    for attempt in range(12):
      try:
        async for chunk in edge_tts.Communicate(text.strip(), voice, rate=RATE, pitch=PITCH, boundary="WordBoundary").stream():
            if chunk["type"]=="audio": audio.extend(chunk["data"])
            elif chunk["type"]=="WordBoundary": events.append(chunk)
        path.write_bytes(audio); return events
      except Exception:
        if attempt==11: raise
        await asyncio.sleep(min(20, 2.0*(attempt+1))); audio.clear(); events.clear()

def decode(mp3: Path) -> bytes:
    ffmpeg=os.environ.get("ADT_FFMPEG") or shutil.which("ffmpeg")
    if not ffmpeg: raise RuntimeError("Set ADT_FFMPEG to an ffmpeg executable for mixed-language assembly")
    return subprocess.run([ffmpeg,"-v","error","-i",str(mp3),"-f","s16le","-ac","1","-ar","24000","pipe:1"],check=True,stdout=subprocess.PIPE).stdout

def join(parts, target: Path):
    pcm=[]; rate=24000
    for p in parts: pcm.append(decode(p))
    gap=b"\0\0"*round(rate*GAP_MS/1000); raw=gap.join(pcm)
    vals=list(struct.unpack("<%dh"%(len(raw)//2),raw)); peak=max(1,max(abs(x) for x in vals)); gain=min(1.0,29200/peak)
    raw=struct.pack("<%dh"%len(vals),*(int(x*gain) for x in vals))
    enc=lameenc.Encoder(); enc.set_bit_rate(128); enc.set_in_sample_rate(rate); enc.set_channels(1); enc.set_quality(2)
    target.write_bytes(enc.encode(raw)+enc.flush())

async def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--concurrency",type=int,default=8); ap.add_argument("--limit",type=int); args=ap.parse_args()
    texts=json.loads((I18N/"texts.json").read_text()); audios=json.loads((I18N/"audios.json").read_text())
    ids=[k for k,v in audios.items() if str(texts.get(k," ")).strip()]
    if args.limit: ids=ids[:args.limit]
    cache=Path(os.environ.get("ADT_AUDIO_CACHE","/private/tmp/culture-bilingual-audio-cache")); cache.mkdir(parents=True,exist_ok=True)
    jobs={}
    plans={}
    for tid in ids:
      plans[tid]=spans(tid,str(texts[tid]))
      for voice,part,lang in plans[tid]:
        key=hashlib.sha256((voice+"\0"+part.strip()).encode()).hexdigest(); jobs[key]=(voice,part.strip())
    sem=asyncio.Semaphore(args.concurrency); boundaries={}
    async def one(n,item):
      key,(voice,part)=item; mp3=cache/(key+".mp3"); meta=cache/(key+".json")
      async with sem:
        if mp3.exists() and meta.exists(): ev=json.loads(meta.read_text())
        else:
          try:
            ev=await synth(voice,part,mp3)
          except Exception as exc:
            print(f"FAILED voice={voice} text={part!r}: {exc}", flush=True)
            raise
          meta.write_text(json.dumps(ev))
      boundaries[key]=ev
      if n%100==0: print(f"synthesized {n}/{len(jobs)}",flush=True)
    await asyncio.gather(*(one(n,x) for n,x in enumerate(jobs.items(),1)))
    outdir=I18N/"audio"; register=[]; timecodes={}; counts=Counter()
    for n,tid in enumerate(ids,1):
      ps=plans[tid]; segfiles=[]; words=[]; offset=0.0
      for voice,part,lang in ps:
        key=hashlib.sha256((voice+"\0"+part.strip()).encode()).hexdigest(); segfiles.append(cache/(key+".mp3")); counts[voice]+=1
        ev=boundaries[key]
        for e in ev: words.append({"text":e.get("text","").strip(),"start":round(offset+e["offset"]/10_000_000,3),"end":round(offset+(e["offset"]+e["duration"])/10_000_000,3)})
        if ev: offset += (ev[-1]["offset"]+ev[-1]["duration"])/10_000_000 + GAP_MS/1000
      target=outdir/audios[tid]
      if len(segfiles)==1: shutil.copyfile(segfiles[0],target)
      else: join(segfiles,target)
      timecodes[tid]={"timecodes":[None,{"word_timestamps":words}]}
      register.append({"textId":tid,"visibleTextSha256":hashlib.sha256(str(texts[tid]).encode()).hexdigest(),"spans":[{"language":l,"voice":v,"text":p.strip()} for v,p,l in ps],"duration":round(max((w["end"] for w in words),default=0),3),"fileSize":target.stat().st_size,"status":"passed"})
      if n%100==0: print(f"assembled {n}/{len(ids)}",flush=True)
    (I18N/"timecode/timecode_output.json").write_text(json.dumps(timecodes,ensure_ascii=False,indent=2)+"\n")
    (ROOT/"bilingual-audio-register.json").write_text(json.dumps({"generator":"scripts/generate_bilingual_audio.py","voices":{"englishFemale":EN_FEMALE,"englishMale":EN_MALE,"swahiliFemale":SW_FEMALE,"swahiliMale":SW_MALE},"lexiconReviewStatus":LEX["reviewStatus"],"clipCount":len(register),"voiceSpanCounts":counts,"clips":register},ensure_ascii=False,indent=2)+"\n")
    print(f"Completed {len(register)} clips and {sum(len(x['spans']) for x in register)} voice spans")

if __name__=="__main__": asyncio.run(main())
