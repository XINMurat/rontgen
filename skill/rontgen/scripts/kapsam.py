#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- the coverage ledger: how much of the code the written documents
actually rest on, and which slice to read next.

WHY THIS EXISTS
---------------
On the first real run one reader covered about a fifth of the largest module
in one sitting and wrote notes for 2 of 12 modules. That is normal -- and it
was only visible because the reader wrote it down by hand. A map that does
not say how much ground it covers reads as a map of everything.

So the coverage statement is computed, and it doubles as the plan for the
next session: a large repository is read in slices, one module per sitting,
and this ledger is the memory between sittings.

INPUTS (all in the documents directory)
---------------------------------------
  rontgen.json, yapi.json   the measurement (sizes, churn, module depth)
  okunan.tsv                what was read: `path<TAB>from<TAB>to`, kept by the
                            reader as they go. Without it the ledger falls
                            back to counting anchored citations and says so:
                            a citation proves one line was seen, not a file.
                            A row for a file that exists in the repository
                            but is not measured source (CMakeLists.txt, a
                            table, a test) is counted apart and never enters
                            the share; a row for a file that does not exist
                            is an error. The repository is found through
                            rontgen.json's `repo`, or --repo.
  atiflar.tsv               anchored citations (see atif.py)
  any *.md starting with "# Kor denetim"
                            the second reader's checklist (atif.py --ornek).
                            Its filled verdicts are counted; no list, or a
                            list nobody filled, is printed as "second reader:
                            not done" -- in a run where the step was only
                            offered, it was skipped and nothing said so.

OUTPUT
------
  kapsam.md / kapsam.json   per module: source lines, lines read, share,
                            citations, state (okundu / kismen / okunmadi);
                            per hotspot: share read; the next slice to read,
                            chosen by unread heat (commits x lines).

A module counts as `okundu` at 60% of its non-test source lines. That number
is a convention, printed with the result; it is not a claim that 60% is
enough to understand a module.

USAGE
-----
    python kapsam.py --docs rontgen-out
    python kapsam.py --self-test

Exit codes: 0 written · 2 could not (measurement missing, unreadable ledger row)
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile

import dil

READ_SHARE = 0.6
ORNEK_HEAD = "# Kor denetim"   # first line of atif.py --ornek


def second_reader(docs: str):
    """-> {file, items, done, tuttu, tutmadi, cikmiyor} for the checklist in docs, or None when there is none."""
    found = None
    for root, _, files in os.walk(docs):
        for n in sorted(files):
            if not n.endswith(".md"):
                continue
            p = os.path.join(root, n)
            with io.open(p, encoding="utf-8", errors="replace") as f:
                text = f.read()
            if text.startswith(ORNEK_HEAD):
                found = (os.path.relpath(p, docs).replace(os.sep, "/"), text)
                break
        if found:
            break
    if not found:
        return None
    rel, text = found
    k = {"file": rel, "items": 0, "done": 0, "tuttu": 0, "tutmadi": 0, "cikmiyor": 0}
    fold = str.maketrans("ıİçÇşŞğĞüÜöÖ", "iiccssgguuoo")
    for line in text.splitlines():
        s = line.strip()
        if s.startswith(("- [ ]", "- [x]", "- [X]")):
            k["items"] += 1
        if s.lower().startswith(("- [x]",)):
            k["done"] += 1
        if s.startswith("sonuc:") or s.startswith("sonuç:"):
            v = s.split(":", 1)[1].strip().lower().translate(fold)
            if v.startswith("tutmadi"):
                k["tutmadi"] += 1
            elif v.startswith("satirdan cikmiyor") or v.startswith("cikmiyor"):
                k["cikmiyor"] += 1
            elif v.startswith("tuttu"):
                k["tuttu"] += 1
    return k


def module_of(path: str, depth: int) -> str:
    return "/".join(path.split("/")[:-1][:depth]) or "."


def file_lines(repo, rel: str):
    """Line count of a file in the repository, or None when there is no such file (or no repository)."""
    try:
        with io.open(os.path.join(repo, rel), encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in f)
    except (OSError, TypeError):
        return None


def load_ranges(path: str, sizes: dict, repo=None):
    """okunan.tsv -> ({file: set(lines)}, {outside file: set(lines)}, errors[]). A file that exists in the
    repository but is not measured source (a build script, a table, a test) is read too: counted apart, never in the share."""
    read, outside, errors, first = {}, {}, [], True
    with io.open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            line = raw.strip("\r\n")
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("\t")
            if first and len(parts) == 3 and not parts[1].isdigit() and not parts[2].isdigit():
                first = False                # a header row (`path<TAB>from<TAB>to`) is not a reading
                continue
            first = False
            if len(parts) != 3 or not parts[1].isdigit() or not parts[2].isdigit():
                errors.append(f"okunan.tsv:{n} okunamadi (yol<TAB>bas<TAB>son bekleniyor)")
                continue
            p, a, b = parts[0].replace("\\", "/"), int(parts[1]), int(parts[2])
            p = p[2:] if p.startswith("./") else p
            size, into = (sizes[p], read) if p in sizes else (file_lines(repo, p), outside)
            if size is None:
                errors.append(f"okunan.tsv:{n} depoda olmayan dosya: {p}" + ("" if repo else " (depo yolu bilinmiyor)"))
            elif not 1 <= a <= b:
                errors.append(f"okunan.tsv:{n} gecersiz aralik {a}-{b}")
            else:
                into.setdefault(p, set()).update(range(a, min(b, size) + 1))
    return read, outside, errors


def load_anchors(path: str):
    out = {}
    if not os.path.exists(path):
        return out
    with io.open(path, encoding="utf-8") as f:
        for raw in f:
            parts = raw.rstrip("\r\n").split("\t")
            if len(parts) >= 3 and parts[1].isdigit():
                p = parts[0].replace("\\", "/")
                out.setdefault(p[2:] if p.startswith("./") else p, set()).add(int(parts[1]))
    return out


def build(docs: str, repo=None):
    try:
        with io.open(os.path.join(docs, "rontgen.json"), encoding="utf-8") as f:
            r = json.load(f)
        with io.open(os.path.join(docs, "yapi.json"), encoding="utf-8") as f:
            y = json.load(f)
    except (OSError, ValueError) as e:
        return None, [f"olcum okunamadi: {e}"]
    if "files" not in r:
        return None, ["rontgen.json eski surum: dosya basina veri yok; rontgen.py'yi yeniden calistirin"]
    src = {p: v for p, v in r["files"].items() if not v["test"]}
    sizes = {p: v["lines"] for p, v in src.items()}
    ranges_path = os.path.join(docs, "okunan.tsv")
    repo = repo or r.get("repo")
    read, outside, errors = load_ranges(ranges_path, sizes, repo) if os.path.exists(ranges_path) else ({}, {}, [])
    if errors:
        return None, errors
    has_ranges = os.path.exists(ranges_path)
    anchors = load_anchors(os.path.join(docs, "atiflar.tsv"))
    depth = y.get("depth", 3)

    mods = {}
    for p, v in src.items():
        m = mods.setdefault(module_of(p, depth), {"lines": 0, "read": 0, "files": 0, "files_touched": 0, "anchors": 0, "unread_heat": 0})
        got = len(read.get(p, ()))
        m["lines"] += v["lines"]; m["read"] += got; m["files"] += 1
        m["anchors"] += len(anchors.get(p, ()))
        m["files_touched"] += 1 if (got or anchors.get(p)) else 0
        m["unread_heat"] += max(1, v["commits"] or 0) * (v["lines"] - got)   # no history: size alone
    for m in mods.values():
        share = m["read"] / m["lines"] if m["lines"] else 0.0
        m["share"] = round(share, 3)
        if has_ranges:
            m["state"] = "okundu" if share >= READ_SHARE else "kismen" if m["read"] else "okunmadi"
        else:
            m["state"] = "atifli" if m["anchors"] else "okunmadi"
    hot = [{"path": h["path"], "lines": h["lines"], "read": len(read.get(h["path"], ())),
            "share": round(len(read.get(h["path"], ())) / max(1, h["lines"]), 2), "anchors": len(anchors.get(h["path"], ()))}
           for h in r.get("hotspots") or []]
    todo = sorted((m for m in mods.items() if m[1]["state"] != "okundu"), key=lambda x: -x[1]["unread_heat"])
    total, got = sum(sizes.values()), sum(len(v) for v in read.values())
    notes = sorted(os.path.splitext(n)[0] for n in os.listdir(os.path.join(docs, "moduller"))) if os.path.isdir(os.path.join(docs, "moduller")) else []
    flows = sorted(os.path.splitext(n)[0] for n in os.listdir(os.path.join(docs, "akislar"))) if os.path.isdir(os.path.join(docs, "akislar")) else []
    return {"has_ranges": has_ranges, "read_share_rule": READ_SHARE, "source_lines": total, "read_lines": got,
            "share": round(got / total, 3) if total else 0.0, "anchored_lines": sum(len(v) for p, v in anchors.items() if p in src),
            "anchors_total": sum(len(v) for v in anchors.values()),
            "modules": dict(sorted(mods.items(), key=lambda x: -x[1]["lines"])), "hotspots": hot,
            "next": [m for m, _ in todo[:3]], "module_notes": notes, "flows": flows,
            "outside_read": {p: len(v) for p, v in sorted(outside.items(), key=lambda x: -len(x[1]))},
            "second_reader": second_reader(docs),
            # a cited line that no recorded range contains: cited without being read in context (or the range was not written)
            "cited_unread": None if not has_ranges else
            sorted(f"{p}:{n}" for p, ns in anchors.items() for n in ns if n not in read.get(p, ()) and n not in outside.get(p, ()))}, []


def render(k: dict, repo_name: str) -> str:
    o = [f"# Kapsam defteri — {repo_name}", ""]
    sr = k.get("second_reader")
    judged = (sr["tuttu"] + sr["tutmadi"] + sr["cikmiyor"]) if sr else 0
    if not sr or not judged:
        o += ["**Ikinci okuyucu: yapilmadi.** " + (f"`{sr['file']}` var ama hic sonuc yazilmamis. " if sr else "Kor denetim listesi yok. ")
              + "Atiflari yalniz yazar denetledi; belgeyle birlikte bunu soyleyin.", ""]
    else:
        o += [f"**Ikinci okuyucu** (`{sr['file']}`): {sr['items']} cumleden {judged} yargilandi — tuttu {sr['tuttu']}, "
              f"tutmadi {sr['tutmadi']}, satirdan cikmiyor {sr['cikmiyor']}."
              + (f" {sr['items'] - judged} cumle bos." if sr["items"] > judged else ""), ""]
    if k["has_ranges"]:
        o += [f"Yazili belgeler, test olmayan {k['source_lines']} kaynak satirin **{k['read_lines']} tanesinin** "
              f"(**%{round(k['share'] * 100, 1)}**) okunmasina dayaniyor (`okunan.tsv`); bunlarin {k['anchored_lines']} satiri capali "
              f"(`atiflar.tsv`'deki {k['anchors_total']} farkli capali satirin {k['anchors_total'] - k['anchored_lines']}'i test ya da "
              "kaynak disi dosyada; `atif.py` ayni satira iki kez yazilmis capayi iki kez sayar).",
              f"Bir modul satirlarinin %{int(k['read_share_rule'] * 100)}'i okununca `okundu` sayilir: bu bir uzlasimdir, yeterlilik iddiasi degil.", ""]
        cu = k["cited_unread"]
        o += [f"**Atifli ama okunmamis {len(cu)} satir** (capasi var, hicbir `okunan.tsv` araliginda degil: ya baglami okunmadan "
              "atiflandi ya araligi yazilmadi): " + ", ".join(f"`{x}`" for x in cu[:12]) + (" …" if len(cu) > 12 else ""), ""] if cu else \
             ["Her capali satir bir okuma araliginin icinde.", ""]
        if k["outside_read"]:
            o += [f"Ayrica **kaynak sayilmayan {len(k['outside_read'])} dosyadan {sum(k['outside_read'].values())} satir** okundu "
                  "(derleme betigi, tablo, test ...); paya girmez: "
                  + ", ".join(f"`{p}` ({n})" for p, n in list(k["outside_read"].items())[:8])
                  + (" …" if len(k["outside_read"]) > 8 else ""), ""]
    else:
        o += ["**`okunan.tsv` yok: okuma araligi olculmedi.** Asagidaki durum yalniz capali atiflardan cikar; bir atif tek bir satirin",
              "goruldugunu gosterir, dosyanin okundugunu degil. Okurken `yol<TAB>bas<TAB>son` satirlarini tutun.", ""]

    def table(head, rows):
        o.append("| " + " | ".join(head) + " |"); o.append("|" + "---|" * len(head))
        o.extend("| " + " | ".join(str(c) for c in x) + " |" for x in rows)
        o.append("")

    table(["Modul", "Durum", "Kaynak satir", "Okunan", "Pay", "Dokunulan dosya", "Capa"],
          [(m, v["state"], v["lines"], v["read"], f"%{round(v['share'] * 100)}", f"{v['files_touched']} / {v['files']}", v["anchors"])
           for m, v in k["modules"].items()])
    if k["hotspots"]:
        o += ["## Sicak noktalar ne kadar okundu", ""]
        table(["Dosya", "Satir", "Okunan", "Pay", "Capa"],
              [(h["path"], h["lines"], h["read"], f"%{round(h['share'] * 100)}", h["anchors"]) for h in k["hotspots"]])
    states = [v["state"] for v in k["modules"].values()]
    o += ["## Belge kapsami", "",
          f"- Modul: {len(states)}; okundu {states.count('okundu')}, kismen {states.count('kismen')}, "
          f"okunmadi {states.count('okunmadi')}" + (f", yalniz atifli {states.count('atifli')}" if not k["has_ranges"] else "") + ".",
          f"- Modul notu: {len(k['module_notes'])}" + (f" ({', '.join(k['module_notes'])})" if k["module_notes"] else "") + ".",
          f"- Akis belgesi: {len(k['flows'])}" + (f" ({', '.join(k['flows'])})" if k["flows"] else "") + ".", "",
          "## Siradaki dilim", "",
          "Okunmamis isiya gore (commit x okunmamis satir). Bir oturumda bir dilim; oturum bu defteri ve belgeleri okuyup devam eder.", ""]
    o += [f"{i}. `{m}` — {k['modules'][m]['lines'] - k['modules'][m]['read']} okunmamis satir"
          for i, m in enumerate(k["next"], 1)] or ["Butun moduller `okundu`."]
    return "\n".join(o) + "\n"


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as d:
        def write(rel, text):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        files = {"a/x.cs": {"lines": 100, "test": False, "commits": 10}, "a/y.cs": {"lines": 100, "test": False, "commits": 1},
                 "b/z.cs": {"lines": 50, "test": False, "commits": 2}, "t/t.cs": {"lines": 500, "test": True, "commits": 9}}
        write("out/rontgen.json", json.dumps({"files": files, "hotspots": [{"path": "a/x.cs", "lines": 100}]}))
        write("out/yapi.json", json.dumps({"depth": 3}))
        docs = os.path.join(d, "out")
        k, e = build(docs)
        check("aralik yoksa: olculmedi der, okundu demez", e == [] and not k["has_ranges"] and "olculmedi" in render(k, "x")
              and k["cited_unread"] is None
              and all(v["state"] == "okunmadi" for v in k["modules"].values()))
        write("out/atiflar.tsv", "# commit: abc\nb/z.cs\t3\tx\n")
        check("aralik yoksa: capali modul 'atifli', 'okundu' degil", build(docs)[0]["modules"]["b"]["state"] == "atifli")
        write("out/okunan.tsv", "# yol\tbas\tson\na/x.cs\t1\t100\na/x.cs\t50\t120\na/y.cs\t1\t30\n")
        k, e = build(docs)
        check("ortusen araliklar bir kez sayilir, dosya boyunu asmaz", k["modules"]["a"]["read"] == 130)
        check("test dosyalari paydaya girmez", k["source_lines"] == 250)
        check("durum: %60 ustu okundu, sifir okunmadi", k["modules"]["a"]["state"] == "okundu" and k["modules"]["b"]["state"] == "okunmadi")
        check("siradaki dilim: okunmamis modul", k["next"] == ["b"])
        check("sicak nokta payi", k["hotspots"][0]["share"] == 1.0)
        write("out/okunan.tsv", "olmayan.cs\t1\t5\n")
        check("olcumde olmayan dosya hatadir", build(docs)[1] != [])
        write("depo/CMakeLists.txt", "a\nb\n")
        write("out/okunan.tsv", "a/x.cs\t1\t60\n./CMakeLists.txt\t1\t9\n")
        k, e = build(docs, os.path.join(d, "depo"))
        check("kaynak disi okuma: hata degil, ayri sayilir, paya girmez",
              e == [] and k["outside_read"] == {"CMakeLists.txt": 2} and k["read_lines"] == 60
              and "kaynak sayilmayan 1 dosyadan 2 satir" in render(k, "x"))
        write("out/rontgen.json", json.dumps({"files": files, "hotspots": [], "repo": os.path.join(d, "depo")}))
        check("depo yolu verilmezse rontgen.json'daki 'repo' kullanilir", (build(docs)[0] or {}).get("outside_read") == {"CMakeLists.txt": 2})
        write("out/okunan.tsv", "path\tfrom\tto\na/x.cs\t1\t10\n")
        k, e = build(docs)
        write("out/okunan.tsv", "a/x.cs\t1\t10\npath\tfrom\tto\n")
        e2 = build(docs)[1]
        write("out/okunan.tsv", "path\tfrom\tto\npath\tfrom\tto\n")
        check("okunan.tsv: ilk satirdaki baslik okuma degil; sonraki sayisiz satir yine hata",
              e == [] and k["read_lines"] == 10 and e2 != [] and build(docs)[1] != [])
        write("out/atiflar.tsv", "# commit: abc\na/x.cs\t3\tx\n./a/y.cs\t4\ty\nCMakeLists.txt\t2\tz\nt/t.cs\t1\tw\n")
        write("out/okunan.tsv", "a/x.cs\t1\t10\n")
        k = build(docs)[0]
        check("capa sayisi: kaynaktaki ve toplam ayri, './' oneki atilir",
              k["anchored_lines"] == 2 and k["anchors_total"] == 4 and "4 farkli capali satirin 2'i" in render(k, "x"))
        write("out/atiflar.tsv", "# commit: abc\na/x.cs\t5\tx\nb/z.cs\t3\ty\n./CMakeLists.txt\t2\tz\n")
        write("out/okunan.tsv", "a/x.cs\t1\t60\n./CMakeLists.txt\t1\t9\n")
        k = build(docs, os.path.join(d, "depo"))[0]
        check("atifli ama okunmamis satir listelenir; kaynak disi aralik da sayilir",
              k["cited_unread"] == ["b/z.cs:3"] and "Atifli ama okunmamis 1 satir" in render(k, "x"))
        write("out/okunan.tsv", "yok.txt\t1\t2\n")
        check("depoda olmayan dosya yine hatadir", "depoda olmayan" in " ".join(build(docs, os.path.join(d, "depo"))[1]))
        write("out/okunan.tsv", "a/x.cs\t9\t3\n")
        check("ters aralik hatadir", build(docs)[1] != [])
        nohist = {p: dict(v, commits=None) for p, v in files.items()}
        write("out/rontgen.json", json.dumps({"files": nohist, "hotspots": None}))
        write("out/okunan.tsv", "a/x.cs\t1\t100\n")
        k, e = build(docs)
        check("gecmissiz olcum: dilim okunmamis boyla secilir, cokmez", e == [] and k["next"] == ["a", "b"] and k["hotspots"] == [])
        check("ikinci okuyucu listesi yoksa: yapilmadi", k["second_reader"] is None and "Ikinci okuyucu: yapilmadi" in render(k, "x"))
        lst = "# Kor denetim — 3 / 9\n\n- [x] `a.md:1` — c\n      sonuc: tuttu — g\n- [x] `a.md:2` — c\n      sonuc: Satırdan çıkmıyor\n" \
              "- [ ] `a.md:3` — c\n      sonuc: \n"
        write("out/kontrol.md", lst.replace("sonuc: tuttu", "sonuc: ").replace("Satırdan çıkmıyor", ""))
        check("bos liste: yine yapilmadi", "var ama hic sonuc" in render(build(docs)[0], "x"))
        write("out/kontrol.md", lst)
        sr = build(docs)[0]["second_reader"]
        check("doldurulmus liste sayilir (Turkce harf, bos satir)", sr == {"file": "kontrol.md", "items": 3, "done": 2, "tuttu": 1,
              "tutmadi": 0, "cikmiyor": 1} and "2 yargilandi" in render(build(docs)[0], "x") and "1 cumle bos" in render(build(docs)[0], "x"))
        write("out/rontgen.json", json.dumps({"hotspots": []}))
        check("eski olcum dosyasi reddedilir", build(docs)[1] != [])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--docs", help="rontgen.json, yapi.json, okunan.tsv ve atiflar.tsv'nin dizini")
    p.add_argument("--repo", help="kaynak disi okumalar icin depo kok dizini (verilmezse rontgen.json'daki yol)")
    p.add_argument("--lang", help="rapor dili: tr-ascii (varsayilan), tr, en")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if not a.docs:
        p.error("--docs gerekli")
    k, errors = build(a.docs, a.repo)
    if errors:
        print("\n".join("olculmedi: " + e for e in errors)); return 2
    name = "?"
    try:
        with io.open(os.path.join(a.docs, "rontgen.json"), encoding="utf-8") as f:
            name = os.path.basename(json.load(f).get("repo", "?"))
    except (OSError, ValueError):
        pass
    with io.open(os.path.join(a.docs, "kapsam.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(k, f, ensure_ascii=False, indent=2); f.write("\n")
    with io.open(os.path.join(a.docs, "kapsam.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(dil.cevir(render(k, name), a.lang or "tr-ascii"))
    print(f"yazildi: {os.path.join(a.docs, 'kapsam.md')} — pay %{round(k['share'] * 100, 1)}, siradaki: {', '.join(k['next']) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
