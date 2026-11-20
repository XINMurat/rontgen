#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen CI gates, runnable locally and from the workflow.

    python tools/ci.py              # run every gate; exit 1 on the first failure
    python tools/ci.py --can-fail   # prove each gate CAN fail: break a copy, expect red

A gate that cannot fail is decoration. `--can-fail` copies the repository to a
temporary folder, applies one breaking change per gate, and requires that gate
to go red on the copy (and only that change, so a red gate is that gate's red).
"""
from __future__ import annotations

import glob
import io
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def gates(root):
    scripts = sorted(glob.glob(os.path.join(root, "skill", "rontgen", "scripts", "*.py")))
    g = [(f"oz-test {os.path.basename(s)}", [PY, s, "--self-test"]) for s in scripts]
    g += [("paket esligi", [PY, "tools/build_skill.py", "--check"]),
          ("token butcesi", [PY, "tools/token_budget.py"]),
          ("ortak araclar", [PY, "tools/check_shared_tools.py"]),
          ("EN sayfa esligi", [PY, "tools/sync_en_docs.py", "--check"]),
          ("dil esligi", [PY, "tools/check_lang_parity.py"]),
          ("TR tazeligi", [PY, "tools/check_tr_fresh.py"]),
          ("satir ve dosya butcesi", [PY, "tools/ci.py", "--budget"]),
          ("sizinti ozet", [PY, "tools/leak_hash.py"])]   # salted digests: the CI secret is a salt, never the terms
    terms = os.environ.get("RONTGEN_FORBIDDEN_TERMS") or (".forbidden-terms" if os.path.exists(os.path.join(root, ".forbidden-terms")) else None)
    if terms:
        g.append(("sizinti", [PY, "tools/leak_check.py", "--terms", terms, "--package", "rontgen.skill", "--require"]))
    return g


def budget(root):
    bad = []
    for p in glob.glob(os.path.join(root, "skill", "rontgen", "scripts", "*.py")):
        lines = io.open(p, encoding="utf-8").read().splitlines()
        bad += [f"{os.path.basename(p)}: {len(lines)} satir > 600"] if len(lines) > 600 else []
        bad += [f"{os.path.basename(p)}:{i} > 160 karakter" for i, l in enumerate(lines, 1) if len(l) > 160]
    print("\n".join(bad) or "ok  betikler 600 satir / 160 karakter icinde")
    return 1 if bad else 0


def run(root, quiet=False, env=None):
    for name, cmd in gates(root):
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        if r.returncode != 0:
            if not quiet:
                print(f"KIRMIZI  {name}\n{(r.stdout + r.stderr)[-800:]}")
            return name
        if not quiet:
            print(f"yesil    {name}")
    return None


def can_fail():
    s = "skill/rontgen/SKILL.md"
    breaks = {
        "oz-test kapsam.py": ("skill/rontgen/scripts/kapsam.py", "READ_SHARE = 0.6", "READ_SHARE = 0.9"),
        "paket esligi": (s, "## Red lines", "## Red lines\n\nbozuk"),
        "token butcesi": (s, "## Red lines", "## Red lines\n\n" + "x " * 20000),
        "satir ve dosya butcesi": ("skill/rontgen/scripts/belge.py", "import argparse", "import argparse  # " + "y" * 170),
        "ortak araclar": ("tools/rule_hits.py", "\n", "\n# kopya bozuldu\n"),
        "EN sayfa esligi": ("docs/en/methodology.md", "\n", "\nelle eklenmis satir\n"),
        "dil esligi": ("docs/_config.yml", '/tr/kanit" }', '/tr/kanit-yok" }'),
        "TR tazeligi": ("skill/rontgen/references/okuma.md", "\n", "\nkaynak degisti, ceviri eskidi\n"),
    }
    if os.path.exists(os.path.join(ROOT, ".forbidden-terms")):
        first = io.open(os.path.join(ROOT, ".forbidden-terms"), encoding="utf-8").readline().strip()
        breaks["sizinti"] = ("skill/rontgen/scripts/belge.py", "import argparse", f"import argparse  # {first}")   # no TR page
        breaks["sizinti ozet"] = breaks["sizinti"]
    salt_file = os.path.join(ROOT, ".leak-salt")
    salt = io.open(salt_file, encoding="utf-8").read().strip() if os.path.exists(salt_file) else None
    ok = True
    for gate, (rel, a, b) in breaks.items():
        with tempfile.TemporaryDirectory() as d:
            dst = os.path.join(d, "r")
            shutil.copytree(ROOT, dst, ignore=shutil.ignore_patterns(".git", "__pycache__"))
            p = os.path.join(dst, rel)
            t = io.open(p, encoding="utf-8").read()
            assert a in t, (gate, a)
            io.open(p, "w", encoding="utf-8", newline="\n").write(t.replace(a, b, 1))
            if gate not in ("paket esligi", "EN sayfa esligi"):   # derived files in step: only the gate under test goes red
                for c in (["tools/build_skill.py"], ["tools/sync_en_docs.py"]):
                    subprocess.run([PY] + c, cwd=dst, capture_output=True)
            env = dict(os.environ)
            env.pop("RONTGEN_LEAK_SALT", None)
            if gate == "sizinti ozet":               # only the salted gate sees the term: the clear-text list is not in the copy
                if not salt:
                    continue
                os.remove(os.path.join(dst, ".forbidden-terms")); env["RONTGEN_LEAK_SALT"] = salt
            red = run(dst, quiet=True, env=env)
            good = red == gate
            ok &= good
            print(f"{'ok  ' if good else 'FAIL'} {gate}: bozulunca {'bu kapi' if good else red or 'hicbir kapi'} kirmizi")
    return 0 if ok else 1


def main():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    if "--budget" in sys.argv:
        return budget(ROOT)
    if "--can-fail" in sys.argv:
        return can_fail()
    red = run(ROOT)
    print("tum kapilar yesil" if red is None else f"durdu: {red}")
    return 0 if red is None else 1


if __name__ == "__main__":
    sys.exit(main())
