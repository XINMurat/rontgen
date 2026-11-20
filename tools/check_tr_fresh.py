#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A Turkish page must say which version of its English source it translates.

The language-parity gate checks that every page has a counterpart; it cannot
see that the counterpart is a translation of an older text. After a day of
changes to SKILL.md the Turkish methodology page still translated the version
before them, and every gate was green. So each Turkish page carries, in its
first lines, the content hash of the source it was translated from:

    > Kaynak: skill/rontgen/SKILL.md · sha256:0123abcd4567

and this gate fails when the source's hash today is different.

    python tools/check_tr_fresh.py            # exit 1 on a stale or unmarked page
    python tools/check_tr_fresh.py --hashes   # print the hash each page must carry
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARK = re.compile(r"sha256:([0-9a-f]{12})")


def digest(rel: str) -> str:
    with io.open(os.path.join(ROOT, rel), "rb") as f:
        return hashlib.sha256(f.read().replace(b"\r\n", b"\n")).hexdigest()[:12]


def main() -> int:
    pages = json.load(io.open(os.path.join(ROOT, "docs", "en-mirror.json"), encoding="utf-8"))["pages"]
    bad = []
    for p in pages:
        src, tr = p["sources"][0], p.get("tr")
        if not tr:
            continue
        want = digest(src)
        if "--hashes" in sys.argv:
            print(f"{tr}\t{src}\tsha256:{want}")
            continue
        try:
            head = "".join(io.open(os.path.join(ROOT, tr), encoding="utf-8").readlines()[:5])
        except OSError:
            bad.append(f"{tr}: yok"); continue
        m = MARK.search(head)
        if not m:
            bad.append(f"{tr}: kaynak isareti yok (ilk satirlarda 'sha256:' bekleniyor)")
        elif m.group(1) != want:
            bad.append(f"{tr}: {src} degismis (sayfa {m.group(1)}, kaynak bugun {want}) — yeniden cevrilmeli")
    if "--hashes" in sys.argv:
        return 0
    print("\n".join(bad) or f"ok  {len([p for p in pages if p.get('tr')])} TR sayfa kaynaginin bugunku surumunu cevirir")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
