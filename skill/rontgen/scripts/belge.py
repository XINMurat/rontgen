#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- the project's own map: which code paths its documents name,
whether those paths still exist, and which modules no document names.

WHY THIS EXISTS
---------------
A fresh reader on a foreign repository read 900 lines of code and drew the
command path right, but missed the principle the whole design rests on. A
module map in the project's own docs stated it in its first sentence; the
reader never opened that file. A person would have. The documents are claims,
not facts -- but they are where the authors wrote the axis down, and which of
them is the map is measurable without reading them.

WHAT IT DOES
------------
Every `.md` file the measurement can see is scanned for code paths in
backticks (`src/engine/`, `runtime/evented/connection.rs`, `table.rs:94`).
Each is resolved against the repository: as written, relative to the document,
or as the tail of exactly one path. It is then

  var        resolved to one file or directory
  belirsiz   the tail of more than one path (`mod.rs`)
  yok        nowhere: the document names code that is not there (stale) [H]

Per document: how many distinct existing paths it names -- the documents that
name the most are the navigation-document candidates, opened before the
first hotspot. Per source module (directory): whether any document names it
or a file in it. A large module no document names is where the docs cannot
help; a module named in many is where they must be checked against the code.

Content is not read or judged: a path is a claim that something is there,
nothing more. Naming a parent (`src/`) does not count as naming a module.

USAGE
-----
    python belge.py --repo . --out rontgen-out [--config rontgen.config.json]
    python belge.py --self-test
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tempfile
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # runs under python -I too: siblings are found by path
from ortak import uzun_yol, NOT_SOURCE, list_files, load_config, matches, read_sources, source_map
import dil  # noqa: E402

TICK = re.compile(r"`([^`\s]+)`")
LINK = re.compile(r"\]\(([^)\s#?]+)(?:[#?][^)]*)?\)")    # [text](path#anchor): a link to a file in the repository
SHOW = 15


def candidates(token: str, exts=frozenset({".rs", ".py", ".md"})):
    """A backticked token -> a path-like string, or None (a word, a URL, a glob, a placeholder, `JSON.SET`).
    A name with no `/` counts only with a known file extension (`exts`)."""
    t = re.sub(r":\d+(?:[-–]\d+)?$", "", token.strip().rstrip(".,;)"))
    t = re.sub(r"\(.*$", "", t).replace("\\", "/")
    if "://" in t or any(c in t for c in "*<>{}$|=") or t.startswith(("-", "@")):
        return None
    if "/" not in t and os.path.splitext(t)[1] not in exts:
        return None
    while t.startswith("./"):
        t = t[2:]
    return t.rstrip("/") or None


def resolver(paths):
    files = set(paths)
    dirs = {p.rsplit("/", 1)[0] for p in paths if "/" in p}
    for d in list(dirs):
        while "/" in d:
            d = d.rsplit("/", 1)[0]; dirs.add(d)
    every = files | dirs

    def resolve(name: str, doc_dir: str):
        """-> list of matching repository paths (files or directories)."""
        if name in every:
            return [name]
        rel = os.path.normpath(os.path.join(doc_dir, name)).replace("\\", "/")
        if rel in every:
            return [rel]
        return sorted(p for p in every if p.endswith("/" + name))
    return resolve


def module_named(module: str, named) -> bool:
    return any(p == module or p.startswith(module + "/") and "/" not in p[len(module) + 1:] for p in named)


def build(repo: str, cfg: dict) -> dict:
    paths, _ = list_files(repo)
    resolve = resolver(paths)
    sources = read_sources(repo, cfg)[0]
    exts = (set(source_map(cfg)) | NOT_SOURCE) - {""}
    top = {p.split("/")[0] for p in paths}
    docs, named, counts, stale, ambiguous, broken = [], set(), Counter(), [], Counter(), []
    skipped_docs = [p for p in paths if p.lower().endswith(".md") and matches(p, cfg.get("exclude_globs", []))]
    for doc in sorted(p for p in paths if p.lower().endswith(".md") and p not in skipped_docs):   # archived copies are not the map
        try:
            with io.open(uzun_yol(os.path.join(repo, doc)), encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except OSError:
            continue
        doc_dir, found = os.path.dirname(doc), set()
        for n, line in enumerate(lines, 1):
            for target in LINK.findall(line):
                if "://" in target or target.startswith(("mailto:", "/")):
                    continue
                if not os.path.exists(os.path.join(repo, doc_dir, target)):
                    broken.append(f"{doc}:{n} `{target}`")
            for tok in TICK.findall(line):
                name = candidates(tok, exts)
                if not name:
                    continue
                hits = resolve(name, doc_dir)
                if len(hits) == 1:
                    counts["var"] += 1; found.add(hits[0])
                elif hits:
                    counts["belirsiz"] += 1; ambiguous[name] += 1
                elif any(os.path.exists(os.path.join(repo, x, name)) for x in ("", doc_dir)):
                    counts["olculmeyen"] += 1     # there, in a directory the walk does not enter (.github/)
                elif "/" in name and name.split("/")[0] not in top and not name.startswith("../"):
                    counts["dis"] += 1            # not this repository's path (linux/aarch64, owner/repo)
                else:
                    counts["yok"] += 1; stale.append(f"{doc}:{n} `{name}`")
        named |= found
        if found:
            docs.append({"doc": doc, "paths": len(found), "lines": len(lines)})
    docs.sort(key=lambda d: (-d["paths"], d["doc"]))
    modules = Counter()
    for p, text in sources.items():
        modules[os.path.dirname(p).replace("\\", "/") or "."] += len(text.splitlines())
    unnamed = sorted(((m, n) for m, n in modules.items() if not module_named(m, named)), key=lambda x: (-x[1], x[0]))
    return {"docs": docs, "counts": dict(counts), "stale": stale, "broken_links": broken, "ambiguous": ambiguous.most_common(SHOW),
            "modules": len(modules), "unnamed": unnamed,
            "unnamed_lines": sum(n for _, n in unnamed), "source_lines": sum(modules.values())}


def render(r: dict, name: str) -> str:
    c = r["counts"]
    o = [f"# Belge haritasi — {name}", "",
         "Projenin kendi `.md` belgelerinde ters tirnak icinde gecen kod yollari. Icerik okunmadi ve yargilanmadi: bir yol",
         "yalniz 'orada bir sey var' iddiasidir. Belgeler iddiadir; kodla karsilastirilir.", "",
         f"- Yol: **{c.get('var', 0)} var**, {c.get('belirsiz', 0)} belirsiz (birden cok yola uyan ad), "
         f"**{c.get('yok', 0)} yok** (belge depoda olmayan kodu aniyor) `[H]`; {c.get('olculmeyen', 0)} olcume girmeyen "
         f"dizinde var; {c.get('dis', 0)} depo disi gorunen (ilk parcasi depoda yok)",
         f"- Kaynak modul (dizin): {r['modules']}; hicbir belgede anilmayan: **{len(r['unnamed'])}** "
         f"({r['unnamed_lines']} / {r['source_lines']} kaynak satir)", "",
         "## Gezinme belgesi adaylari", "", "Ilk sicak noktadan once acilir (SKILL.md adim 4).", "",
         "| Belge | Anilan ve var olan yol | Satir |", "|---|---:|---:|"]
    o += [f"| `{d['doc']}` | {d['paths']} | {d['lines']} |" for d in r["docs"][:SHOW]] or ["| - | - | - |"]
    o += ["", "## Hicbir belgenin anmadigi en buyuk moduller", "", "| Modul | Kaynak satir |", "|---|---:|"]
    o += [f"| `{m}` | {n} |" for m, n in r["unnamed"][:SHOW]] or ["| - | - |"]
    o += ["", f"## Kirik baglantilar ({len(r['broken_links'])})", "",
          "Belgenin bag verdigi dosya depoda yok: belge kumesi bir belgeyi kaybetmis ya da tasimis.", ""]
    o += [f"- {s}" for s in r["broken_links"][:SHOW]] or ["- yok"]
    o += ["", "## Depoda olmayan yollar (ilk 15) `[H]`", ""]
    o += [f"- {s}" for s in r["stale"][:SHOW]] or ["- yok"]
    if r["ambiguous"]:
        o += ["", "Belirsiz adlar: " + ", ".join(f"`{n}` ({k})" for n, k in r["ambiguous"])]
    return "\n".join(o) + "\n"


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    check("aday: yol, satirli yol, dosya adi; kelime, URL, glob, yer tutucu degil",
          [candidates(x) for x in ("src/a/", "table.rs:94", "./x/b.py", "Args", "https://a/b", "src/*.rs", "<family>.rs", "f(x)")]
          == ["src/a", "table.rs", "x/b.py", None, None, None, None, None])
    with tempfile.TemporaryDirectory() as d:
        for rel, text in (("src/eng/a.rs", "x\n" * 30), ("src/eng/mod.rs", "m\n"), ("src/net/mod.rs", "n\n"),
                          ("src/store/b.rs", "y\n" * 50), ("src/xeng/a.rs", "q\n"), ("src/store/deep/c.rs", "z\n"),
                          ("docs/DEV.md", "Bkz. `eng/a.rs:3`, `src/net/`, `mod.rs`, `src/gone.rs`, `src/`, `JSON.SET`, `linux/x`, `.ci/a.yml`.\n"),
                          (".ci/a.yml", "c\n"),
                          ("docs/A.md", "`../src/store/deep/c.rs` ve `Args`. [D](DEV.md#x), [Y](ARCH.md), [w](https://a/b.md).\n")):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        cfg = load_config(d, None)[0]
        r = build(d, cfg)
        check("cozum: kuyruk, belge dizinine gore, belirsiz ve yok ayri sayilir",
              r["counts"] == {"var": 4, "belirsiz": 1, "yok": 1, "dis": 1, "olculmeyen": 1} and r["stale"] == ["docs/DEV.md:1 `src/gone.rs`"])
        check("baglanti: kirik yerel bag sayilir; var olan, capali ve dis bag sayilmaz", r["broken_links"] == ["docs/A.md:1 `ARCH.md`"])
        check("belge sirasi: en cok yol anan once", [x["doc"] for x in r["docs"]] == ["docs/DEV.md", "docs/A.md"])
        check("modul: ust dizini anmak modulu anmak degil; alt dizindeki dosya yalniz kendi modulunu anar",
              [m for m, _ in r["unnamed"]] == ["src/store", "src/xeng"] and r["unnamed_lines"] == 51)
        md = render(r, "t")
        check("rapor: sayilar, aday tablosu, anilmayan modul ve bayat yol", "**4 var**" in md and "| `docs/DEV.md` | 3 |" in md
              and "| `src/store` | 50 |" in md and "`src/gone.rs`" in md)
        r2 = build(d, dict(cfg, exclude_globs=["docs/A.md"]))
        check("dislama belgeye de uygulanir: arsiv kopyasi haritada yer almaz", [x["doc"] for x in r2["docs"]] == ["docs/DEV.md"])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--repo", default=".")
    p.add_argument("--out", help="cikti dizini (belge.md, belge.json)")
    p.add_argument("--config", help="rontgen.config.json (verilmezse depo kokunde aranir)")
    p.add_argument("--lang", help="rapor dili: tr-ascii (varsayilan), tr, en; verilmezse config'teki report_lang")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if not a.out:
        p.error("--out gerekli")
    cfg, _, errors = load_config(a.repo, a.config)
    if errors:
        print("\n".join("olculmedi: " + e for e in errors)); return 2
    r = build(a.repo, cfg)
    os.makedirs(a.out, exist_ok=True)
    with io.open(os.path.join(a.out, "belge.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(r, f, ensure_ascii=False, indent=2); f.write("\n")
    with io.open(os.path.join(a.out, "belge.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(dil.cevir(render(r, os.path.basename(os.path.abspath(a.repo))), a.lang or cfg.get("report_lang", "tr-ascii")))
    print(f"yazildi: {os.path.join(a.out, 'belge.md')} — {len(r['docs'])} belge yol aniyor, {len(r['unnamed'])} modul anilmiyor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
