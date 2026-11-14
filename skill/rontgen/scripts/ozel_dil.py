#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- a language the project made for itself, described in the config.

WHY THIS EXISTS
---------------
Some repositories carry their logic in a language of their own, a DSL or an
experimental language whose compiler lives in the same repository. The scripts
listed such files as "unclassified" and, with `extra_sources`, could count
them; they could never see what imports what, or what a file declares. The
project's own specs and grammars say how the language imports and declares.
A reader who has read those specs writes it down once, and the measurement
then treats the language like any other:

    "extra_sources": {
      ".path": {"name": "Path",
                "import": "^\\\\s*use\\\\s+([\\\\w.:/]+)",
                "decl":   "^\\\\s*(?:fn|type|cage)\\\\s+(\\\\w+)",
                "comment": "//"}
    }

  import   regex; group 1 is the target. `a.b`, `a::b` and `a/b` all mean
           the path a/b. It resolves to the one repository file of the same
           language whose path, without extension, ends with that path, or to
           the file relative to the importing one. Two candidates: ambiguous,
           no edge. None: unresolved, counted as a blind spot.
  decl     regex; group 1 names a declaration. It feeds the outline and the
           [H] name edges, as for any language.
  comment  line-comment marker; comment text is not scanned.

The tier is [K] for a resolved import: the rule came from the project's own
spec, it is not inferred from the code. The spec is quoted in the session log.
"""
from __future__ import annotations

import posixpath
import re
import sys


def specs(cfg: dict) -> dict:
    """-> {'.ext': {'name', 'import' (compiled), 'decl' (compiled), 'comment'}} for the described languages."""
    out = {}
    for e, v in (cfg.get("_diller") or cfg.get("extra_sources") or {}).items():
        if isinstance(v, dict):
            out[e.lower()] = {"name": v["name"], "comment": v.get("comment"),
                              "import": re.compile(v["import"], re.M) if v.get("import") else None,
                              "decl": re.compile(v["decl"], re.M) if v.get("decl") else None}
    return out


def validate(value) -> list:
    """Errors for one extra_sources value that is an object (a string value is checked elsewhere)."""
    if not isinstance(value.get("name"), str) or not value["name"].strip():
        return ["'name' metin olmali"]
    errs = []
    for k in ("import", "decl"):
        if value.get(k) is not None:
            try:
                rx = re.compile(value[k])
                if rx.groups < 1:
                    errs.append(f"'{k}' bir yakalama grubu icermeli")
            except (re.error, TypeError) as e:
                errs.append(f"'{k}' gecersiz duzenli ifade: {e}")
    unknown = set(value) - {"name", "import", "decl", "comment"}
    return errs + ([f"bilinmeyen alan: {', '.join(sorted(unknown))}"] if unknown else [])


def _strip(text, spec):
    c = spec.get("comment")
    return re.sub(re.escape(c) + r"[^\n]*", "", text) if c else text


def outline(text: str, spec: dict, line_of) -> list:
    rx = spec.get("decl")
    t = _strip(text, spec)
    return [(line_of(t, m.start(1)), 0, "bildirim", m.group(1)) for m in rx.finditer(t)] if rx else []


def edges(files: dict, known, cfg: dict):
    """files = {path: text} of described-language files -> (edges set, counts, language names)."""
    sp = specs(cfg)
    by_ext = {}
    for p in known:
        e = posixpath.splitext(p)[1].lower()
        if e in sp:
            by_ext.setdefault(e, []).append(p)
    out, counts, missed = set(), {"K": 0, "dis": 0, "cozulemeyen": 0, "belirsiz": 0}, []
    for p, text in files.items():
        e = posixpath.splitext(p)[1].lower()
        spec = sp.get(e)
        if not spec or not spec["import"]:
            continue
        for raw in spec["import"].findall(_strip(text, spec)):
            raw = raw if isinstance(raw, str) else raw[0]
            target = re.sub(r"::|\.(?=\w)", "/", raw.strip("\"'")).strip("/")
            target = posixpath.splitext(target)[0] if posixpath.splitext(target)[1].lower() == e else target
            rel = posixpath.normpath(posixpath.join(posixpath.dirname(p), target))
            hits = [q for q in by_ext.get(e, []) if posixpath.splitext(q)[0] == rel] or \
                   [q for q in by_ext.get(e, []) if (posixpath.splitext(q)[0] + "/").endswith("/" + target + "/")
                    or posixpath.splitext(q)[0] == target]
            hits = [q for q in hits if q != p]
            if len(hits) == 1:
                counts["K"] += 1; out.add((p, hits[0]))
            elif len(hits) > 1:
                counts["belirsiz"] += 1
            else:
                counts["cozulemeyen"] += 1; missed.append(f"{p}: {raw}")
    counts["ornek"] = sorted(missed)[:10]
    return out, counts, sorted({s["name"] for s in sp.values()})


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    cfg = {"extra_sources": {".pth": {"name": "Path", "import": r"^\s*use\s+([\w.:/]+)", "decl": r"^\s*(?:fn|cage)\s+(\w+)",
                                      "comment": "//"}, ".tbl": "Tablo"}}
    check("dogrulama: grupsuz desen ve bilinmeyen alan hata", validate({"name": "X", "import": "use", "x": 1}) != []
          and validate({"name": "X", "import": r"use (\w+)"}) == [])
    known = {"os/kernel/main.pth", "os/kernel/sched.pth", "os/lib/mem.pth", "os/drv/mem.pth", "os/net/tcp.pth", "a.tbl"}
    src = ("// use os.sahte\nuse os::kernel::sched\nuse lib.mem\nuse mem\nuse yok.modul\ncage Kafes\nfn main() {}\n")
    e, c, names = edges({"os/kernel/main.pth": src}, known, cfg)
    check("import: :: ve . yol olur; sonek eslesmesi; yorum sayilmaz",
          ("os/kernel/main.pth", "os/kernel/sched.pth") in e and ("os/kernel/main.pth", "os/lib/mem.pth") in e and c["K"] == 2)
    check("iki adaya uyan belirsiz, bulunmayan cozulemeyen ornegiyle", c["belirsiz"] == 1 and c["cozulemeyen"] == 1
          and c["ornek"] == ["os/kernel/main.pth: yok.modul"] and names == ["Path"])
    marks = outline(src, specs(cfg)[".pth"], lambda t, pos: t.count("\n", 0, pos) + 1)
    check("iskelet: bildirim deseni satir numarasiyla", [(ln, n) for ln, _, _, n in marks] == [(6, "Kafes"), (7, "main")])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else 0)
