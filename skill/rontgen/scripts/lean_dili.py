#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- Lean 4: `import` graph, declaration outline, trust inventory.

WHY THIS EXISTS
---------------
A Lean library is read the way a proof is read: which module rests on which,
what each file declares, and where the kernel is asked to take something on
faith. The generic resolver saw none of it: `import Foo.Bar.Baz` names a
*module*, which is the file `Foo/Bar/Baz.lean` under a package source root.

Roots are the directory of every lakefile (`lakefile.lean` / `lakefile.toml`),
its `srcDir` when one is declared, and the repository root. An import that
resolves to a file in the repository is a `[K]` edge; one whose first
component is not a local top-level module (Mathlib, Std, Lean, Init...) is
counted as external; a local-looking one that resolves nowhere is a blind spot.

The trust inventory lists, by line, the places a reviewer must look at first:
`sorry` / `admit` (unfinished proof), `axiom` (assumed without proof),
`opaque`, `unsafe`, `native_decide` (trusts the compiler, not the kernel),
`@[implemented_by]` / `@[extern]` (runtime code the kernel never sees).
It is lexical `[H]`: `#print axioms` in Lean is the authority; this is a map.
Comments are stripped (nested `/- -/` included); strings are not parsed.
"""
from __future__ import annotations

import posixpath
import re
import sys

IMPORT = re.compile(r"^\s*import\s+(.+)$", re.M)
SRC_DIR_LEAN = re.compile(r"srcDir\s*:=\s*\"([^\"]+)\"")
SRC_DIR_TOML = re.compile(r"^\s*srcDir\s*=\s*\"([^\"]+)\"", re.M)
MODS = r"(?:(?:private|protected|noncomputable|partial|unsafe|nonrec|scoped|local)\s+)*"
DECL = re.compile(r"^([ \t]*)(?:@\[[^\]]*\]\s*)?" + MODS +
                  r"(theorem|lemma|def|abbrev|structure|class|inductive|instance|axiom|opaque|example)\b[ \t]*([^\s:({\[]*)", re.M)
SCOPE = re.compile(r"^\s*(namespace|section|end)\b[ \t]*(\S*)", re.M)
TRUST = [("sorry", re.compile(r"\bsorry\b")), ("admit", re.compile(r"\badmit\b")),
         ("axiom", re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?" + MODS + r"axiom\b", re.M)),
         ("opaque", re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?" + MODS + r"opaque\b", re.M)),
         ("unsafe", re.compile(r"\bunsafe\b")), ("native_decide", re.compile(r"\bnative_decide\b")),
         ("implemented_by", re.compile(r"@\[[^\]]*\bimplemented_by\b")), ("extern", re.compile(r"@\[[^\]]*\bextern\b"))]


def strip_comments(text: str) -> str:
    """Remove `--` and nested `/- -/` comments, keeping every newline so line numbers hold."""
    out, i, depth, n = [], 0, 0, len(text)
    while i < n:
        two = text[i:i + 2]
        if two == "/-":
            depth += 1; i += 2; continue
        if depth and two == "-/":
            depth -= 1; i += 2; continue
        if depth:
            out.append("\n" if text[i] == "\n" else " "); i += 1; continue
        if two == "--":
            j = text.find("\n", i)
            j = n if j < 0 else j
            out.append(" " * (j - i)); i = j; continue
        out.append(text[i]); i += 1
    return "".join(out)


def imports(text: str) -> list:
    out = []
    for line in IMPORT.findall(strip_comments(text)):
        out += [w for w in line.split() if w not in ("runtime",)]
    return out


def roots(manifests: dict) -> list:
    out = {"."}
    for path, text in manifests.items():
        d = posixpath.dirname(path) or "."
        out.add(d)
        for m in SRC_DIR_LEAN.findall(text) + SRC_DIR_TOML.findall(text):
            out.add(posixpath.normpath(posixpath.join(d, m)))
    return sorted(out)


def edges(files: dict, known, manifests: dict):
    """files = {path: text} of .lean files -> (edges set, counts, source roots)."""
    rs = roots(manifests)
    index, local_tops = {}, set()
    for p in known:
        if not p.endswith(".lean"):
            continue
        for r in rs:
            rel = p if r == "." else (p[len(r) + 1:] if p.startswith(r + "/") else None)
            if rel:
                mod = rel[:-5].replace("/", ".")
                index.setdefault(mod, p); local_tops.add(mod.split(".")[0])
    out, counts, missed, trust = set(), {"K": 0, "dis": 0, "cozulemeyen": 0}, [], {}
    for p, text in files.items():
        for imp in imports(text):
            hit = index.get(imp)
            if hit and hit != p:
                counts["K"] += 1; out.add((p, hit))
            elif imp.split(".")[0] in local_tops:
                counts["cozulemeyen"] += 1; missed.append(f"{p}: import {imp}")
            elif not hit:
                counts["dis"] += 1
        for kind, ln in inventory(text):
            trust.setdefault(kind, []).append(f"{p}:{ln}")
    counts["ornek"] = sorted(missed)[:10]
    counts["guven"] = {k: {"say": len(v), "ornek": sorted(v)[:10]} for k, v in sorted(trust.items())}
    return out, counts, rs


def inventory(text: str) -> list:
    t = strip_comments(text)
    found = []
    for kind, rx in TRUST:
        for m in rx.finditer(t):
            found.append((kind, t.count("\n", 0, m.start()) + 1))
    return sorted(found, key=lambda x: (x[1], x[0]))


def outline(text: str, line_of) -> list:
    """(line, depth, kind, name): declarations, nested by namespace / section."""
    t = strip_comments(text)
    events = [(m.start(), "scope", m) for m in SCOPE.finditer(t)] + [(m.start(), "decl", m) for m in DECL.finditer(t)]
    depth, marks = 0, []
    for pos, kind, m in sorted(events, key=lambda e: e[0]):
        if kind == "scope":
            if m.group(1) == "end":
                depth = max(0, depth - 1)
            else:
                if m.group(1) == "namespace":
                    marks.append((line_of(t, pos), depth, "namespace", m.group(2)))
                depth += 1
        else:
            marks.append((line_of(t, pos), depth, m.group(2), m.group(3) or "(adsiz)"))
    return marks


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    src = ("import Mathlib.Analysis.Complex.Basic\nimport Proj.Lemmas Proj.Yok\n-- import Proj.Sahte\n"
           "/- dis /- ic -/ import Proj.Sahte2 -/\n"
           "namespace Proj\n/-- belge -/\ntheorem ana (s : Nat) : s = s := by\n  sorry\n"
           "private lemma yard : True := trivial\naxiom varsayim : False\n"
           "@[implemented_by hizli] def yavas : Nat := 0\ninstance : Inhabited Nat := ⟨0⟩\nend Proj\n")
    check("import: coklu ad, ic ice yorum sayilmaz", imports(src) == ["Mathlib.Analysis.Complex.Basic", "Proj.Lemmas", "Proj.Yok"])
    check("lakefile srcDir koku eklenir", roots({"lakefile.lean": 'package p where\n  srcDir := "src"\n'}) == [".", "src"])
    known = {"src/Proj/Main.lean", "src/Proj/Lemmas.lean"}
    e, c, _ = edges({"src/Proj/Main.lean": src}, known, {"lakefile.toml": 'name = "p"\nsrcDir = "src"\n'})
    check("modul -> dosya [K]; Mathlib dis; yerel ama yok cozulemeyen",
          e == {("src/Proj/Main.lean", "src/Proj/Lemmas.lean")} and c["K"] == 1 and c["dis"] == 1
          and c["ornek"] == ["src/Proj/Main.lean: import Proj.Yok"])
    g = c["guven"]
    check("guven envanteri: sorry, axiom, implemented_by satiriyla",
          g["sorry"]["ornek"] == ["src/Proj/Main.lean:8"] and g["axiom"]["say"] == 1 and "implemented_by" in g)
    lo = lambda t, p: t.count("\n", 0, p) + 1
    o = outline(src, lo)
    check("iskelet: namespace altinda bildirimler, adsiz instance",
          [(k, n, d) for _, d, k, n in o] == [("namespace", "Proj", 0), ("theorem", "ana", 1), ("lemma", "yard", 1),
                                               ("axiom", "varsayim", 1), ("def", "yavas", 1), ("instance", "(adsiz)", 1)])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else 0)
