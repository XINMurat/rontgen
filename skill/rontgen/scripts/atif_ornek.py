#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- the second reader's checklist (`atif.py --ornek`), split out of atif.py at its 600-line budget.

Table rows get at least a third of the sample: in one run every sentence a blind reader faulted was a table
cell saying more than its cited line, and a plain random sample had drawn too few of them to catch it.
"""
from __future__ import annotations

import random
import sys

from atif import ORNEK_HEAD, doc_citations


def ornek(docs: str, n: int, seed: int, out=sys.stdout) -> int:
    cites = doc_citations(docs)
    seen, rows = set(), []
    for doc, line, *_rest, sentence in cites:
        if (doc, line) not in seen:
            seen.add((doc, line)); rows.append((doc, line, sentence))
    if not rows:
        print("olculmedi: belgelerde atifli cumle yok", file=out)
        return 2
    rnd = random.Random(seed)   # tables get >= 1/3: once, every faulted sentence was a cell saying more than its line
    tab = [r for r in rows if r[2].lstrip().startswith("|")]
    txt = [r for r in rows if not r[2].lstrip().startswith("|")]
    rnd.shuffle(tab); rnd.shuffle(txt)
    nt = min(len(tab), max(-(-n // 3), round(n * len(tab) / len(rows))))
    picked = tab[:nt] + txt[:n - nt]
    picked = sorted(picked + tab[nt:nt + n - len(picked)])
    np_ = sum(r[2].lstrip().startswith("|") for r in picked)
    print(f"{ORNEK_HEAD} — {len(picked)} / {len(rows)} atifli cumle (tohum {seed}; {np_} tablo satiri)\n\n"
          "Bu listeyi belgeleri YAZMAYAN biri (ya da yazarin notlarini gormeyen taze bir oturum) doldurur. Her cumle icin\n"
          "atif yapilan satiri acin ve cumlenin o satirdan cikip cikmadigina bakin: satirin orada olmasi yetmez.\n"
          "Tablo satirinda her hucre bir iddiadir: atif yapilan satir ya da aralik hucrenin hepsini gostermiyorsa sonuc\n"
          "`satirdan cikmiyor`.\n"
          "Sonuc: `tuttu` / `tutmadi` / `satirdan cikmiyor` ve bir cumle gerekce. Oran belgenin kapsam beyanina yazilir.\n", file=out)
    for doc, line, sentence in picked:
        print(f"- [ ] `{doc}:{line}` — {sentence[:700]}" + (" …" if len(sentence) > 700 else "") + "\n      sonuc: ", file=out)
    return 0
