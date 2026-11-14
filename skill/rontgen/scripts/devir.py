#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- hand-off files for the siblings: a backlog for iskele, a
registry for mizan. Rontgen finds; it does not fix and it does not judge.

WHY THIS EXISTS
---------------
Step 7 said "each finding becomes a task" and "each doubted claim goes to an
audit", but a finding copied by hand into another kit's format is a finding
re-worded, and re-wording is where a measured number turns into an opinion.
This script writes the hand-off straight from the measurement and the
second reader's checklist, in the formats the siblings' own parsers accept.

  --iskele   backlog (Markdown: phase -> epic -> task, each with an
             acceptance criterion the measurement can check) and a `review`
             block whose baseline is today's files over budget.
  --mizan    registry (YAML): each checklist sentence the second reader did
             not mark `tuttu`, and each `[H]` sentence sampled, becomes an
             open hypothesis whose arbiter is the cited line.

USAGE
-----
    python devir.py --docs rontgen-out --iskele out/devir-iskele.md
    python devir.py --docs rontgen-out --mizan  out/devir-mizan.yaml
    python devir.py --self-test
"""
from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys
import tempfile

ITEM = re.compile(r"^- \[[ xX]\] (?:`(?P<doc>[^`]+)` — |\*\*X\d+\*\* — )(?P<text>.+)$")
VERDICT = re.compile(r"^\s+sonu[cç]:\s*(?P<v>.*)$", re.I)
CITE = re.compile(r"`([\w./\\-]+\.\w+):(\d+)(?:[-–](\d+))?`")


def load(docs, name):
    with io.open(os.path.join(docs, name), encoding="utf-8") as f:
        return json.load(f)


def iskele_backlog(docs, today=None):
    r, y = load(docs, "rontgen.json"), load(docs, "yapi.json")
    th = r.get("thresholds", {})
    maxl = int((th.get("max_file_lines") or {}).get("value", 600)) if isinstance(th.get("max_file_lines"), dict) else 600
    big = sorted(((p, v["lines"]) for p, v in r["files"].items() if not v["test"] and v["lines"] > maxl), key=lambda x: -x[1])
    hot = [h for h in (r.get("hotspots") or [])][:5]
    cyc = y.get("cycles") or []
    blind = {k: v for k, v in (y.get("blind_spots") or {}).items() if isinstance(v, (int, float)) and v}
    tasks, n = [], 0

    def task(epic, size, title, accept, dep="—"):
        nonlocal n
        n += 1
        tasks.append((epic, f"- [ ] **F1-RNT-{n:02d}** ({size}) {title} **Bağ.:** {dep}\n  - *Kabul:* {accept}"))

    for p, lines in big[:8]:
        task("Boyut", "M", f"`{p}` ({lines} satır) bölünür.",
             f"`rontgen.py` yeniden koşunca `{p}` {maxl} satırın altında ya da `review` taban çizgisinde gerekçesiyle duruyor.")
    for h in hot:
        task("Sıcak noktalar", "S", f"Sıcak nokta `{h['path']}` için modül notu ve test adı eşleşmesi.",
             f"`moduller/` altında bu dosyayı anlatan not var ve `rontgen.md` test örtüsünde dosyanın adı bir test dosyasında geçiyor.")
    for g in cyc[:5]:
        task("Döngüler", "M", f"`[K]` döngüsü kırılır: {' ↔ '.join(g)}.",
             "`yapi.py` yeniden koşunca bu modüller arasında `[K]` döngüsü listelenmiyor.")
    for k, v in sorted(blind.items(), key=lambda x: -x[1])[:3]:
        task("Kör noktalar", "S", f"Kör nokta `{k}` ({v} isabet) için sonda ya da derleyici aracı.",
             "Sonuç `probe_results` ile yüklenir ve blok şemada en az bir `[H]` bağ `[K]` olur.")
    if not tasks:
        task("Gözlem", "S", "Ölçümde eşik aşan bulgu yok; bir sonraki faz kapanışında yeniden ölç.",
             "`rontgen.py` ve `yapi.py` yeniden koşar, çıktılar `dogrula.py`'den geçer.")
    epics, out = [], ["# Görev Listesi (Backlog) — Rontgen devri", "",
                      f"Kaynak: `rontgen.json`, `yapi.json` ({today or datetime.date.today().isoformat()}). Görevler ölçümden üretildi; "
                      "kabul ölçütü yeniden ölçümle denetlenir.", "", "---", "", "## F1 — Rontgen bulguları", ""]
    for i, (e, t) in enumerate(tasks):
        if e not in epics:
            epics.append(e)
            out += ["", f"### Epik F1.{len(epics)} — {e}"]
        out.append(t)
    review = {"review": {"id_pattern": r"F\d+-[A-Z]+-\d+", "max_file_lines": maxl,
                         "max_line_length": int((th.get("max_line_length") or {}).get("value", 160))
                         if isinstance(th.get("max_line_length"), dict) else 160,
                         "max_changed_lines": 400, "baseline": [p for p, _ in big]}}
    return "\n".join(out) + "\n", review


def checklist(docs):
    for root, _, files in os.walk(docs):
        for fn in sorted(files):
            if fn.endswith(".md"):
                p = os.path.join(root, fn)
                with io.open(p, encoding="utf-8", errors="replace") as f:
                    t = f.read()
                if t.startswith("# Kor denetim"):
                    return t
    return None


def mizan_registry(docs, project, today=None):
    today = today or datetime.date.today().isoformat()
    review_by = (datetime.date.fromisoformat(today) + datetime.timedelta(days=30)).isoformat()
    t = checklist(docs)
    if t is None:
        return None
    rows, cur = [], None
    for line in t.splitlines():
        m = ITEM.match(line)
        if m:
            cur = {"doc": m.group("doc") or "", "text": m.group("text"), "v": ""}
            rows.append(cur)
        elif cur and VERDICT.match(line):
            cur["v"] = VERDICT.match(line).group("v").strip()
    picked = [r for r in rows if not r["v"].lower().startswith("tuttu")]

    def q(s):
        return json.dumps(s, ensure_ascii=False)

    o = ["registry:", f"  project: {q(project)}", '  owner: "rontgen"', '  schema_version: "1.7"',
         '  methodology: "mizan-v2.2"', f'  created: "{today}"',
         "  notes: >", "    Rontgen belgelerinden, ikinci okuyucunun `tuttu` demedigi cumleler. Her biri satirin",
         "    soyledigiyle sinanacak acik bir iddiadir; hakem atif yapilan kaynak satiridir.", "", "hypotheses:"]
    for i, r in enumerate(picked, 1):
        cites = [f"{a}:{b}" + (f"-{c}" if c else "") for a, b, c in CITE.findall(r["text"])] or ["(atif yok)"]
        o += [f'  - id: "H-{i:03d}"', "    version: 1", '    tier: "H"', '    status: "open"', "    preregistered: false", f'    recorded: "{today}"',
              f'    review_by: "{review_by}"', '    data_status: "exists_seen"',
              '    note: "post-hoc: cumle satiri okuyarak yazildi; yeniden okuma bir denetimdir, tahmin degil."',
              f"    title: {q('Belge cumlesi: ' + (r['doc'] or 'kor liste') + ' — ' + r['text'][:80])}",
              f"    formal: {q(r['text'][:600])}", f"    origin: {q('rontgen ikinci okuyucu: ' + (r['v'] or 'sonuc yok'))}",
              "    metric:", '      name: "satir_destegi"', f"      instrument: {q('atif yapilan satir(lar): ' + ', '.join(cites))}",
              "    arbiter:", '      class: "instrument"',
              f"      who: {q('kaynak satiri ' + ', '.join(cites) + ' — yazarin yorumundan gecmez')}",
              "      independent_of_author: true", '      latency: "minutes"',
              '      calibration: "Ayni satiri iki okur ayni yargiya varir; varamazsa sonuc underpowered."',
              "    threshold:", '      support: "satir iddianin her parcasini gosteriyor"', '      refute: "satir iddiayla celisiyor"',
              '      underpowered: "satir celismiyor ama iddianin bir parcasini gostermiyor"',
              '      non_numeric_justification: "Tek bir cumle ile tek bir satir karsilastirilir; olcu ikili (gosteriyor / '
              'celisiyor), sayi uretmez."',
              '    stopping_rule: "Atif yapilan her satir bir kez okunur; ek ornek alinmaz."',
              '    exclusion_rule: "yok — her cumle yargilanir."',
              '    missing_data: "Satir artik yoksa (dosya degisti) sonuc tutmadi sayilir."',
              '    refutation: "Atif yapilan satir iddiayla celisirse cumle duzeltilir ya da silinir."',
              '    two_sided: "Destek: cumle oldugu gibi kalir. Curutme: belge duzeltilir ve kor liste yeniden alinir."',
              '    cost: "Bir satir okumak; dakikalar."', '    prior_art: ["bilinen akraba yok"]',
              '    confounds: ["satir kaymasi (atif.py ile denetlenir)"]']
    if not picked:
        o.append("  []")
    return "\n".join(o) + "\n"


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as d:
        files = {"a/big.rs": {"lines": 900, "test": False}, "a/s.rs": {"lines": 50, "test": False}, "t/x.rs": {"lines": 2000, "test": True}}
        with io.open(os.path.join(d, "rontgen.json"), "w", encoding="utf-8") as f:
            json.dump({"files": files, "hotspots": [{"path": "a/big.rs", "lines": 900}], "thresholds": {}}, f)
        with io.open(os.path.join(d, "yapi.json"), "w", encoding="utf-8") as f:
            json.dump({"cycles": [["a", "b"]], "blind_spots": {"DI": 12, "ORM": 0}}, f)
        md, rv = iskele_backlog(d, "2026-11-14")
        check("iskele: esigi asan kaynak dosya gorev olur, test dosyasi olmaz", "`a/big.rs` (900 satır)" in md and "t/x.rs" not in md)
        check("iskele: dongu ve kor nokta gorevleri, her gorevde kabul", "a ↔ b" in md and "`DI`" in md
              and md.count("*Kabul:*") == md.count("**F1-RNT-"))
        check("iskele: review taban cizgisi bugunku buyuk dosyalar", rv["review"]["baseline"] == ["a/big.rs"])
        with io.open(os.path.join(d, "kor.md"), "w", encoding="utf-8") as f:
            f.write("# Kor denetim — 2\n\n- [x] `m.md:3` — Iddia `src/a.rs:5`.\n      sonuc: tuttu\n"
                    "- [x] `m.md:4` — Genelleme `src/b.rs:9-12`.\n      sonuc: satirdan cikmiyor — x\n")
        y = mizan_registry(d, "p", "2026-11-14")
        check("mizan: yalniz tutmayan cumle hipotez olur, hakem atif satiri", y.count('- id: "H-') == 1 and "src/b.rs:9-12" in y
              and "src/a.rs:5" not in y)
        check("mizan: liste yoksa None", mizan_registry(os.path.join(d, "yok") if os.makedirs(os.path.join(d, "yok")) is None else d, "p") is None)
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--docs", default="rontgen-out")
    ap.add_argument("--iskele")
    ap.add_argument("--mizan")
    ap.add_argument("--project", default="rontgen-devri")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.iskele:
        md, rv = iskele_backlog(a.docs)
        with io.open(a.iskele, "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        with io.open(os.path.splitext(a.iskele)[0] + ".review.json", "w", encoding="utf-8", newline="\n") as f:
            json.dump(rv, f, ensure_ascii=False, indent=2); f.write("\n")
        print(f"yazildi: {a.iskele} (+ .review.json)")
    if a.mizan:
        y = mizan_registry(a.docs, a.project)
        if y is None:
            print("olculmedi: kor denetim listesi yok (atif.py --ornek)"); return 2
        with io.open(a.mizan, "w", encoding="utf-8", newline="\n") as f:
            f.write(y)
        print(f"yazildi: {a.mizan}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
