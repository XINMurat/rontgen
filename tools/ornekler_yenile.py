#!/usr/bin/env python3
"""Rebuild the example pages in docs/ornekler/ from one list.

The list lives outside git (default plan/ornekler.json, gitignored) because it holds local paths:

    [{"name": "helix", "repo": "C:/src/helix", "docs": "C:/tmp/rontgen-helix", "lang": "en"},
     {"name": "riemann-lean", "repo": "C:/src/riemann-lean/lean", "docs": "C:/src/riemann-lean/rontgen-out"}]

For each entry: rontgen.py and yapi.py measure `repo` into `docs` (skipped with --pano-only, which reuses what
is there: a 175k-file Lean release takes about 17 minutes to measure), then pano.py writes
docs/ornekler/<name>.html. A page is refused, and the old one kept, if two consecutive folders of a local path
("Users/ad", "kod/riemann-lean") appear in it: a page that is published must not carry the machine. One folder
name alone is not a leak; "lean" is also a language and a file extension.

Usage:
    python tools/ornekler_yenile.py [--list plan/ornekler.json] [--pano-only] [--only helix]
    python tools/ornekler_yenile.py --self-test
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skill", "rontgen", "scripts")
OUT = os.path.join(ROOT, "docs", "ornekler")
PY = sys.executable
SEP = re.compile(r"[/\\]")


def local_pairs(entry: dict) -> set:
    """Two consecutive folders of each local path; the drive letter is left out."""
    pairs = set()
    for key in ("repo", "docs"):
        parts = [p for p in SEP.split(str(entry.get(key, ""))) if p and not p.endswith(":")]
        pairs |= set(zip(parts, parts[1:]))
    return pairs


def leaks(text: str, entry: dict) -> list:
    found = []
    for a, b in local_pairs(entry):
        if re.search(re.escape(a) + r"[/\\]{1,2}" + re.escape(b) + r"(?![\w-])", text):
            found.append(f"{a}/{b}")
    return sorted(found)


def run(args: list) -> int:
    print("  $ " + " ".join(os.path.basename(a) if a.endswith(".py") else a for a in args[1:]))
    return subprocess.call(args)


def rebuild(entry: dict, pano_only: bool) -> bool:
    name, repo, docs = entry["name"], entry["repo"], entry["docs"]
    print(f"== {name}")
    if not pano_only:
        os.makedirs(docs, exist_ok=True)
        for script in ("rontgen.py", "yapi.py"):
            if run([PY, os.path.join(SCRIPTS, script), "--repo", repo, "--out", docs]) != 0:
                print(f"  durdu: {script} basarisiz; eski sayfa korundu")
                return False
    tmp = os.path.join(tempfile.mkdtemp(), name + ".html")
    if run([PY, os.path.join(SCRIPTS, "pano.py"), "--docs", docs, "--lang", entry.get("lang", "en"),
            "--name", name, "--out", tmp]) != 0:
        print("  durdu: pano.py basarisiz; eski sayfa korundu")
        return False
    with io.open(tmp, encoding="utf-8") as f:
        text = f.read()
    bad = leaks(text, entry)
    if bad:
        print(f"  REDDEDILDI: sayfada yerel yol var: {', '.join(bad)}; eski sayfa korundu")
        return False
    os.makedirs(OUT, exist_ok=True)
    with io.open(os.path.join(OUT, name + ".html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"  yazildi: docs/ornekler/{name}.html")
    return True


def self_test() -> int:
    ok = []

    def check(label, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + label)

    e = {"name": "riemann-lean", "repo": "C:/Users/ad/kod/riemann-lean/lean", "docs": "D:/gecici/cikti"}
    check("yerel ciftler: ardisik iki klasor, surucu harfi haric",
          local_pairs(e) == {("Users", "ad"), ("ad", "kod"), ("kod", "riemann-lean"), ("riemann-lean", "lean"),
                             ("gecici", "cikti")})
    check("sizinti bulunur, / ya da \\ ile", leaks("x C:/Users/ad y", e) == ["Users/ad"]
          and leaks("z gecici\\cikti", e) == ["gecici/cikti"])
    check("tek kelime sizinti sayilmaz: dil adi, uzanti, proje adi",
          leaks("<h1>riemann-lean</h1> Lean 4, src/Main.lean, kod", e) == [])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--list", default=os.path.join(ROOT, "plan", "ornekler.json"))
    ap.add_argument("--pano-only", action="store_true")
    ap.add_argument("--only", default=None)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    try:
        with io.open(a.list, encoding="utf-8") as f:
            entries = json.load(f)
    except OSError:
        print(f"liste yok: {a.list} (bicim bu dosyanin basinda)", file=sys.stderr)
        return 2
    entries = [x for x in entries if not a.only or x["name"] == a.only]
    done = [rebuild(x, a.pano_only) for x in entries]
    print(f"\n{sum(done)}/{len(done)} sayfa yenilendi")
    return 0 if all(done) else 1


if __name__ == "__main__":
    sys.exit(main())
