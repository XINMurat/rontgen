#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- Java / Kotlin: `import` statements resolved to files of the repository.

WHY THIS EXISTS
---------------
After Go, the same gap was checked for the JVM family: an import names a
class by its package path (`import com.acme.billing.Invoice;`), which lives in
`.../com/acme/billing/Invoice.java` under some source root (`src/main/java`,
`app/src/main/kotlin`, ...). The root is not guessed: any repository file whose
path ends with the package path counts, and an import that matches two
files is ambiguous and drawn to neither. `import a.b.*` reaches every file of
that package directory. Same-package references need no import and are not
seen: that is the blind spot this module leaves.
"""
from __future__ import annotations

import posixpath
import re
import sys

IMPORT = re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)(\.\*)?\s*;?\s*(?:as\s+\w+)?\s*$", re.M)
COMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)
EXT = (".java", ".kt", ".kts")


def edges(files: dict, known, _manifests=None):
    """files = {path: text} of .java/.kt files -> (edges set, counts, source roots seen)."""
    by_suffix, by_dir = {}, {}
    for p in known:
        if p.endswith(EXT):
            stem = p.rsplit(".", 1)[0]
            parts = stem.split("/")
            for i in range(len(parts)):
                by_suffix.setdefault("/".join(parts[i:]), []).append(p)
            by_dir.setdefault(posixpath.dirname(p), []).append(p)
    out, counts, missed, roots = set(), {"K": 0, "dis": 0, "cozulemeyen": 0, "belirsiz": 0}, [], set()
    for p, text in files.items():
        for name, star in IMPORT.findall(COMMENT.sub(" ", text)):
            path = name.replace(".", "/")
            if star:
                dirs = [d for d in by_dir if d == path or d.endswith("/" + path)]
                hits = [q for d in dirs for q in by_dir[d]] if len(dirs) == 1 else []
            else:
                key = path if path in by_suffix else path.rsplit("/", 1)[0]   # static import / nested class: last segment off
                hits = by_suffix.get(key, [])
            hits = [q for q in hits if q != p]
            if len(set(hits)) == 1 or (star and hits):
                counts["K"] += 1
                out |= {(p, q) for q in set(hits)}
                roots |= {q.rsplit(".", 1)[0][: -len(key) - 1] or "." for q in hits if not star}
            elif len(set(hits)) > 1:
                counts["belirsiz"] += 1
            elif path.split("/")[0] in ("java", "javax", "kotlin", "kotlinx", "android", "androidx", "org", "com", "io", "net"):
                counts["dis"] += 1
            else:
                counts["cozulemeyen"] += 1
                missed.append(f"{p}: {name}")
    counts["ornek"] = sorted(missed)[:10]
    return out, counts, sorted(roots)


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    known = {"app/src/main/java/com/acme/bill/Invoice.java", "app/src/main/java/com/acme/bill/Tax.java",
             "core/src/main/kotlin/com/acme/core/Money.kt", "app/src/main/java/com/acme/App.java",
             "x/com/acme/dup/A.java", "y/com/acme/dup/A.java"}
    src = ("package com.acme;\n// import com.acme.sahte.Yok;\nimport com.acme.bill.Invoice;\nimport static com.acme.core.Money.of;\n"
           "import com.acme.bill.*;\nimport java.util.List;\nimport com.acme.dup.A;\nimport acme.gone.X;\n")
    e, c, roots = edges({"app/src/main/java/com/acme/App.java": src}, known)
    a = "app/src/main/java/com/acme/App.java"
    check("tekli import dosyaya; static import sinifa; * paketin her dosyasina",
          e == {(a, "app/src/main/java/com/acme/bill/Invoice.java"), (a, "core/src/main/kotlin/com/acme/core/Money.kt"),
                (a, "app/src/main/java/com/acme/bill/Tax.java")} and c["K"] == 3)
    check("iki dosyaya uyan import belirsiz, cizilmez; java.* dis; yorum sayilmaz",
          c["belirsiz"] == 1 and c["dis"] == 1 and c["cozulemeyen"] == 1 and c["ornek"] == [f"{a}: acme.gone.X"])
    check("kaynak koku cikarilir", "app/src/main/java" in roots and "core/src/main/kotlin" in roots)
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else 0)
