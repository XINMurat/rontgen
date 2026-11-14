#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- Go: `import` paths resolved against the repository's go.mod files.

WHY THIS EXISTS
---------------
On a Go repository of about 150 thousand lines the core drew 2 `[K]` edges
and 113 `[H]` ones: Go imports a *package* by its full module path
(`github.com/owner/repo/internal/parser`), which the generic resolver never
matched to a directory. A package is a directory; this module maps an import
path to it through the `module` line of the nearest go.mod and adds an edge
from the importing file to each file of that package. Standard library and
third-party imports are counted, never drawn.

A `replace ... => ./local` in go.mod is honoured. Build tags are not read:
a file excluded on one platform still counts as part of its package.
"""
from __future__ import annotations

import posixpath
import re
import sys

MODULE = re.compile(r"^\s*module\s+(\S+)", re.M)
REPLACE = re.compile(r"^\s*(?:replace\s+)?(\S+)(?:\s+\S+)?\s*=>\s*(\.{1,2}/\S*)", re.M)
IMPORT_ONE = re.compile(r'^\s*import\s+(?:[\w.]+\s+)?"([^"]+)"', re.M)
IMPORT_BLOCK = re.compile(r"^\s*import\s*\(([^)]*)\)", re.M | re.S)
IN_BLOCK = re.compile(r'^\s*(?:[\w.]+\s+)?"([^"]+)"', re.M)
COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)


def modules(gomods: dict) -> dict:
    """{go.mod path: text} -> {module path: dir} (replace targets included)."""
    out = {}
    for path, text in gomods.items():
        d = posixpath.dirname(path) or "."
        m = MODULE.search(text)
        if m:
            out[m.group(1)] = d
        for name, target in REPLACE.findall(text):
            out.setdefault(name, posixpath.normpath(posixpath.join(d, target)))
    return out


def imports(text: str) -> list:
    t = COMMENT.sub(" ", text)
    out = IMPORT_ONE.findall(t)
    for block in IMPORT_BLOCK.findall(t):
        out += IN_BLOCK.findall(block)
    return out


def edges(files: dict, known, gomods: dict):
    """files = {path: text} of .go files -> (edges set, counts, module paths)."""
    mods = modules(gomods)
    by_dir = {}
    for p in known:
        if p.endswith(".go"):
            by_dir.setdefault(posixpath.dirname(p) or ".", []).append(p)
    out, counts, missed = set(), {"K": 0, "dis": 0, "cozulemeyen": 0}, []
    for p, text in files.items():
        for imp in imports(text):
            best = max((m for m in mods if imp == m or imp.startswith(m + "/")), key=len, default=None)
            if best is None:
                counts["dis"] += 1
                continue
            rest = imp[len(best):].lstrip("/")
            d = posixpath.normpath(posixpath.join(mods[best], rest)) if rest else mods[best]
            d = "." if d in ("", ".") else d
            targets = [q for q in by_dir.get(d, []) if q != p]
            if targets:
                counts["K"] += 1
                out |= {(p, q) for q in targets}
            else:
                counts["cozulemeyen"] += 1
                missed.append(f"{p}: {imp}")
    counts["ornek"] = sorted(missed)[:10]
    return out, counts, sorted(mods)


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    gomods = {"go.mod": "module github.com/x/app\n\nreplace github.com/x/lib => ./third/lib\n",
              "tools/go.mod": "module github.com/x/app/tools\n"}
    m = modules(gomods)
    check("go.mod: modul yolu ve yerel replace", m == {"github.com/x/app": ".", "github.com/x/lib": "third/lib",
                                                      "github.com/x/app/tools": "tools"})
    src = ('package main\n// import "github.com/x/app/sahte"\nimport (\n  "fmt"\n  p "github.com/x/app/internal/parser"\n'
           '  _ "github.com/x/lib/ext"\n  "github.com/x/app/yok"\n)\nimport "github.com/x/app/tools/gen"\n')
    check("import: tekli, blok, takma ad, alt cizgi; yorum sayilmaz",
          imports(src) == ["github.com/x/app/tools/gen", "fmt", "github.com/x/app/internal/parser", "github.com/x/lib/ext", "github.com/x/app/yok"])
    known = {"main.go", "internal/parser/a.go", "internal/parser/b.go", "third/lib/ext/e.go", "tools/gen/g.go"}
    e, c, _ = edges({"main.go": src}, known, gomods)
    check("paket = dizin: her dosyaya bag; en uzun modul eslesir; std dis",
          e == {("main.go", "internal/parser/a.go"), ("main.go", "internal/parser/b.go"), ("main.go", "third/lib/ext/e.go"),
                ("main.go", "tools/gen/g.go")} and c["K"] == 3 and c["dis"] == 1)
    check("depoda olmayan ic paket cozulemeyen olarak sayilir, ornegi yazilir",
          c["cozulemeyen"] == 1 and c["ornek"] == ["main.go: github.com/x/app/yok"])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else 0)
