#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- pano: one self-contained, bilingual HTML page of the measurement.

WHY THIS EXISTS
---------------
The Markdown reports are read top to bottom; a 175,187-file Lean release showed
that a structure this size is understood by pointing at it: which block leans
on which, where the lines are, which files everything imports. This page draws
that from `yapi.json` (and `rontgen.json`, when there is history), with no
network: no CDN, no fonts, the data inside the file. It opens from disk, in
light or dark, at phone width.

LANGUAGE
--------
Both languages ship in the page; a TR / EN switch flips every label, and the
choice is remembered in the browser. The first view follows `report_lang`
(`--lang`, else the repository's config): `tr` and `tr-ascii` open in Turkish,
`en` in English. Module and file names are data and are never translated.

WHAT IT DOES NOT DO
-------------------
It adds no measurement. Every number on the page is in the JSON it read, and a
section whose input is missing says "not measured" instead of drawing zero.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import time
from html import escape
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # runs under python -I too
from ortak import load_config  # noqa: E402

TOP_BLOCK, TOP_MATRIX, MAX_MODULES = 16, 12, 400


def group_of(module: str) -> str:
    """Top-level group for colour and filter: the first path part, or the second under src/."""
    p = [x for x in module.split("/") if x]
    if not p:
        return "."
    return p[1] if p[0] in ("src", "lib", "app", "pkg", "internal") and len(p) > 1 else p[0]


def page_lang(lang: str) -> str:
    return "en" if lang == "en" else "tr"


def block_of(y: dict, mods: dict, per_row: int = 4, keep: int = 40) -> dict:
    """The heaviest modules in reading order, `per_row` to a row; the strongest links only.

    Layering by longest path put a dense 16-module graph in one column of 13 rows with every back link in a
    lane of its own (a 175k-file Lean release). Here the order is topological once cycles are broken, rows
    wrap that order, and a link is drawn if it is among the `keep` strongest and carries 1% of the largest."""
    edges = [e for e in y.get("edges", []) if not e.get("weak")]
    weight = Counter()
    for e in edges:
        weight[e["from"]] += e["files"]; weight[e["to"]] += e["files"]
    top = [m for m, _ in weight.most_common(TOP_BLOCK)]
    inner = [e for e in edges if e["from"] in top and e["to"] in top and e["from"] != e["to"]]
    biggest = max((e["files"] for e in inner), default=0)
    inner = sorted((e for e in inner if e["files"] * 100 >= biggest), key=lambda e: -e["files"])[:keep]
    out = {m: [e["to"] for e in inner if e["from"] == m and e["tier"] == "K"] for m in top}
    state, back = {}, set()

    def dfs(m):
        state[m] = 1
        for n in sorted(out[m], key=lambda n: -weight[n]):
            if state.get(n) == 1:
                back.add((m, n))
            elif n not in state:
                dfs(n)
        state[m] = 2
    for m in top:
        if m not in state:
            dfs(m)
    level = {m: 0 for m in top}
    for _ in top:
        moved = False
        for e in inner:
            a, b = e["from"], e["to"]
            if e["tier"] == "K" and (a, b) not in back and level[b] < level[a] + 1:
                level[b] = level[a] + 1; moved = True
        if not moved:
            break
    order = sorted(top, key=lambda m: (level[m], -weight[m]))
    return {"nodes": [{"m": m, "o": i, "row": i // per_row, "col": i % per_row, "g": group_of(m),
                       "lines": mods.get(m, {}).get("lines", 0)} for i, m in enumerate(order)],
            "per_row": per_row, "edges": [{"a": e["from"], "b": e["to"], "t": e["tier"], "n": e["files"]} for e in inner],
            "dropped": len([e for e in edges if e["from"] in top and e["to"] in top]) - len(inner)}


GENERIC_ROOTS = {"lean", "src", "lib", "app", "code", "source", "repo", "project", "main", "packages"}


def project_name(path: str) -> str:
    """The folder that was measured, with its parent when the folder alone says nothing (`riemann-lean/lean`).
    No other part of the path reaches the page: a shared page must not carry the machine's folders."""
    parts = [x for x in str(path).replace("\\", "/").split("/") if x and not x.endswith(":")]
    if not parts:
        return "."
    return "/".join(parts[-2:]) if parts[-1].lower() in GENERIC_ROOTS and len(parts) > 1 else parts[-1]


def data_of(y: dict, r: dict | None, name: str | None = None, measured: str | None = None) -> dict:
    mods, fan = y.get("modules", {}), y.get("fan", {})
    rows = sorted(({"m": m, "g": group_of(m), "files": v.get("files", 0), "lines": v.get("lines", 0),
                    "fi": fan.get(m, {}).get("in_k", 0), "fo": fan.get(m, {}).get("out_k", 0)} for m, v in mods.items()),
                  key=lambda x: -x["lines"])
    hard = [e for e in y.get("edges", []) if e.get("tier") == "K"]
    weight = Counter()
    for e in hard:
        weight[e["from"]] += e["files"]; weight[e["to"]] += e["files"]
    block = block_of(y, mods)
    mtop = [m for m, _ in weight.most_common(TOP_MATRIX)]
    matrix = {"mods": mtop, "cells": [{"a": e["from"], "b": e["to"], "n": e["files"]} for e in hard
                                      if e["from"] in mtop and e["to"] in mtop]}
    langs = {k: {"files": v["files"], "K": v["uses"]["K"], "dis": v["uses"]["dis"], "miss": v["uses"]["cozulemeyen"]}
             for k, v in ((k, y.get(k)) for k in ("rust", "go", "java", "lean", "ozel")) if v}
    trust = ((y.get("lean") or {}).get("uses") or {}).get("guven")
    hot = None if not r or r.get("hotspots") is None else [
        {"p": h["path"], "c": h.get("commits"), "l": h.get("lines"), "ch": h.get("changed"), "pp": h.get("people")} for h in r["hotspots"][:15]]
    return {
        "repo": name or project_name(y.get("repo", "")), "measured": measured,
        "summary": {"files": sum(x["files"] for x in rows), "lines": sum(x["lines"] for x in rows), "modules": len(rows),
                    "edges_k": y.get("edge_counts", {}).get("K", 0), "edges_h": y.get("edge_counts", {}).get("H", 0),
                    "cycles": len(y.get("cycles", [])), "excluded": sum(len(v) for v in y.get("excluded", {}).values())},
        "modules": rows[:MAX_MODULES], "modules_cut": max(0, len(rows) - MAX_MODULES),
        "block": block, "matrix": matrix,
        "used": [{"p": x["path"], "n": x["used_by"]} for x in y.get("most_used_files", [])[:15]],
        "langs": langs, "trust": {k: v["say"] for k, v in trust.items()} if trust is not None else None,
        "hot": hot,
    }


ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


def asset(name: str) -> str:
    """CSS, JS and the two-language text table live beside the scripts; the page embeds them, so it stays one file."""
    with io.open(os.path.join(ASSETS, name), encoding="utf-8") as f:
        return f.read()


STRINGS = json.loads(asset("pano-metin.json"))





def embed(obj) -> str:
    """JSON inside <script>: '</' and U+2028/9 escaped so no data value can close the tag."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


def static_body(d: dict, lang: str) -> str:
    """The page with its words and summary written in, so a viewer that runs no script (an app's file
    preview, a mail client) shows text and numbers instead of a blank page; the script redraws the same."""
    s = STRINGS[page_lang(lang)]
    body = re.sub(r'data-t="(\w+)"></', lambda m: f'data-t="{m.group(1)}">{escape(s.get(m.group(1), ""))}</',
                  asset("pano-govde.html"))
    sm = d["summary"]
    tiles = "".join(f'<div class="tile"><b>{sm[k]:,}</b><span>{escape(s[t])}</span></div>'.replace(",", "." if page_lang(lang) == "tr" else ",")
                    for k, t in (("files", "files"), ("lines", "lines"), ("modules", "modules"), ("edges_k", "edges"),
                                 ("cycles", "cycles"), ("excluded", "excluded")))
    body = body.replace('<div class="tiles" id="tiles"></div>', f'<div class="tiles" id="tiles">{tiles}</div>', 1)
    body = body.replace('<h1 id="repo"></h1>', f'<h1 id="repo">{escape(d["repo"])}</h1>', 1)
    where = f'{escape(s["measured"])} {escape(d["measured"])}' if d.get("measured") else ""
    body = body.replace('<span id="where"></span>', f'<span id="where">{where}</span>', 1)
    note = escape(STRINGS["tr"]["noscript"]) + " / " + escape(STRINGS["en"]["noscript"])
    return body.replace("<main>", f'<main><noscript><p class="muted">{note}</p></noscript>', 1)


def html(y: dict, r: dict | None, lang: str, name: str | None = None, measured: str | None = None) -> str:
    d = data_of(y, r, name, measured)
    return ("<!doctype html>\n" f'<html lang="{page_lang(lang)}"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f"<title>Röntgen · {escape(d['repo'])}</title>"
            f"<style>{asset('pano.css')}</style></head><body>"
            f'{static_body(d, lang)}<script type="application/json" id="pano-data">{embed(d)}</script>'
            f'<script type="application/json" id="pano-strings">{embed(STRINGS)}</script>'
            f"<script>\n{asset('pano.js')}</script>"
            "</body></html>\n")


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    y = {"repo": "/x/demo", "modules": {"src/A/core": {"files": 3, "lines": 900}, "src/A/util": {"files": 1, "lines": 50},
                                        "src/B/api": {"files": 2, "lines": 300}, "src/C/x</script>": {"files": 1, "lines": 10}},
         "fan": {"src/A/core": {"in_k": 2, "out_k": 1}},
         "edges": [{"from": "src/A/core", "to": "src/B/api", "tier": "K", "files": 4, "weak": False},
                   {"from": "src/B/api", "to": "src/A/core", "tier": "K", "files": 2, "weak": False},
                   {"from": "src/A/util", "to": "src/A/core", "tier": "H", "files": 3, "weak": False}],
         "edge_counts": {"K": 2, "H": 1}, "cycles": [["src/A/core", "src/B/api"]], "excluded": {},
         "most_used_files": [{"path": "src/A/core/a.lean", "used_by": 5}],
         "lean": {"files": 7, "uses": {"K": 9, "dis": 2, "cozulemeyen": 0, "guven": {}}}}
    h = html(y, None, "tr")
    net = h.replace("http://www.w3.org/2000/svg", "")
    check("tek dosya: dis betik, stil veya font yok", not any(x in net for x in ("<script src", "<link", "@import", "http://", "https://")))
    check("iki dil de gomulu; ilk dil report_lang'den",
          'lang="tr"' in h and "Blok şeması" in h and "Block diagram" in h and 'lang="en"' in html(y, None, "en"))
    check("proje adi: genel klasorde ust klasorle, --name ustun",
          project_name("C:/x/riemann-lean/lean") == "riemann-lean/lean" and project_name("/a/helix") == "helix"
          and '<h1 id="repo">demo</h1>' in h and '<h1 id="repo">Benim</h1>' in html(y, None, "tr", "Benim", "2026-11-26")
          and "2026-11-26" in html(y, None, "tr", None, "2026-11-26"))
    yerel = html(dict(y, repo="C:/Users/ad/is/proje"), None, "tr")
    check("yerel yol sayfaya girmez: yalniz proje adi",
          "Users" not in yerel and "is/proje" not in yerel and '<h1 id="repo">proje</h1>' in yerel)
    check("betiksiz gorunum: baslik, ozet sayilari ve noscript notu HTML'de",
          '<p class="eyebrow" data-t="title">Röntgen panosu</p>' in h and "<b>7</b>" in h and "<noscript>" in h
          and 'data-t="title">Röntgen dashboard<' in html(y, None, "en"))
    check("varliklar gomuldu: stil, govde, betik", "--c0:" in h and 'id="block"' in h and "function squarify" in h)
    check("tr-ascii Turkce acilir", 'lang="tr"' in html(y, None, "tr-ascii"))
    d = data_of(y, None)
    check("veri: ozet, grup, dongulu blok cizilir", d["summary"]["files"] == 7 and d["summary"]["cycles"] == 1
          and {n["g"] for n in d["block"]["nodes"]} >= {"A", "B"} and len(d["block"]["edges"]) == 3)
    check("veri adi script etiketini kapatamaz", "x</script>" not in h and "x<\\/script>" in h)
    check("gecmis yok: sicak nokta None (olculmedi), sifir degil", d["hot"] is None)
    r = {"hotspots": [{"path": "src/A/core/a.lean", "commits": 4, "lines": 900, "changed": 120, "people": 2}]}
    check("gecmis var: sicak noktalar tasinir", data_of(y, r)["hot"][0]["c"] == 4)
    check("Lean guven envanteri: bos sozluk 'bulunmadi', None degil", d["trust"] == {})
    check("grup: src/ altinda ikinci parca", data_of(y, None)["modules"][0]["g"] == "A" and "." == group_of(""))
    for lang in STRINGS:
        check(f"metin tablosu esit: {lang}", set(STRINGS[lang]) == set(STRINGS["tr"]))
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--docs", default="rontgen-out", help="yapi.json'un (ve varsa rontgen.json'un) oldugu dizin")
    ap.add_argument("--repo", default=None, help="report_lang icin config'in okunacagi depo")
    ap.add_argument("--name", default=None, help="sayfada gorunecek proje adi; yoksa olculen klasorden")
    ap.add_argument("--lang", choices=("tr-ascii", "tr", "en"), default=None, help="ilk acilis dili; yoksa config'teki report_lang")
    ap.add_argument("--out", default=None, help="varsayilan: <docs>/pano.html")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    lang = a.lang
    if lang is None and a.repo:
        cfg, _, errors = load_config(a.repo, None)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 2
        lang = cfg["report_lang"]
    lang = lang or "tr"
    try:
        with io.open(os.path.join(a.docs, "yapi.json"), encoding="utf-8") as f:
            y = json.load(f)
    except OSError:
        print("olculmedi: yapi.json yok; once yapi.py calistirin", file=sys.stderr)
        return 2
    r = None
    try:
        with io.open(os.path.join(a.docs, "rontgen.json"), encoding="utf-8") as f:
            r = json.load(f)
    except OSError:
        print("rontgen.json yok: sicak noktalar 'olculmedi' yazilir")
    out = a.out or os.path.join(a.docs, "pano.html")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        stamp = time.strftime("%Y-%m-%d", time.localtime(os.path.getmtime(os.path.join(a.docs, "yapi.json"))))
        f.write(html(y, r, lang, a.name, stamp))
    print(f"yazildi: {out} (ilk dil {page_lang(lang)}; TR/EN dugmesiyle degisir)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
