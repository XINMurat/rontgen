#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- C / C++ for yapi.py: #include edges and an outline.

INCLUDE EDGES [K]
-----------------
`#include "x.h"` is looked up first next to the including file, then under
every include root; `#include <x.h>` under the include roots only. Include
roots are not guessed: they are directories named `include`, and the
directories named in `include_directories(...)` / `target_include_directories(...)`
of a CMakeLists.txt. Each root is reported with where it came from.

  found next to the including file  -> a [K] file edge
  exactly one root holds it         -> a [K] file edge
  several roots hold it             -> NO edge; counted as "belirsiz"
  none, quoted                      -> counted as "cozulemeyen"
  none, angled                      -> an outside dependency; counted, no edge

${PROJECT_SOURCE_DIR} and ${CMAKE_SOURCE_DIR} are taken as the repository
root; a root that uses any other variable or generator expression is skipped
and counted.

OUTLINE [H]
-----------
Function definitions and struct / enum / union / class / typedef struct
declarations with line numbers, found by pattern. Definitions produced by
macros are not chased; files with no mark are counted as such.
"""
from __future__ import annotations

import posixpath
import re

C_EXT = (".c", ".h", ".cpp", ".hpp")
INCLUDE = re.compile(r'^[ \t]*#[ \t]*include[ \t]*([<"])([^>"\n]+)[>"]', re.M)
CMAKE_INC = re.compile(r"\b(target_include_directories|include_directories)\s*\(([^)]*)\)", re.I)
CMAKE_WORDS = {"PUBLIC", "PRIVATE", "INTERFACE", "SYSTEM", "BEFORE", "AFTER"}
HERE_VAR = re.compile(r"^\$\{(?:CMAKE_CURRENT_SOURCE_DIR|CMAKE_CURRENT_LIST_DIR)\}/?")
TOP_VAR = re.compile(r"^\$\{(?:PROJECT_SOURCE_DIR|CMAKE_SOURCE_DIR)\}/?")
NOT_A_FUNCTION = {"if", "for", "while", "switch", "return", "sizeof", "else", "do", "case", "defined", "catch"}
FUNC = re.compile(r"^([ \t]*)(?:[A-Za-z_][\w:<>,*& \t]*[ \t*&])?(~?\w+(?:::~?\w+)*)[ \t]*\(([^;{}()]*(?:\([^()]*\)[^;{}()]*)*)\)"
                  r"\s*(?:const\s*)?(?:noexcept\s*)?(?:override\s*)?\{", re.M)
TYPE = re.compile(r"^([ \t]*)(typedef[ \t]+)?(struct|enum|union|class)[ \t]+(?:class[ \t]+)?(?:[A-Z_][A-Z0-9_]*[ \t]+)*?(\w*)\s*(?::[^{;]*)?\{", re.M)
COMMENT = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)


def _norm(path: str) -> str:
    p = posixpath.normpath(path)
    return "." if p in ("", ".") else p


def include_roots(known, cmake: dict):
    """-> ([(root, source)], skipped). cmake = {CMakeLists path: text}. A root must hold a known file."""
    dirs = {"."}
    for p in known:
        parts = p.split("/")[:-1]
        dirs.update("/".join(parts[:i]) for i in range(1, len(parts) + 1))
    roots, skipped = {}, 0
    for d in sorted(dirs):
        if d.split("/")[-1] == "include":
            roots.setdefault(d, "'include' adli dizin")
    for cm, text in sorted(cmake.items()):
        here = posixpath.dirname(cm) or "."
        for verb, args in CMAKE_INC.findall(re.sub(r"#[^\n]*", "", text)):
            words = [w.strip('"') for w in args.split()]
            for w in words[1:] if verb.lower() == "target_include_directories" else words:
                if not w or w.upper() in CMAKE_WORDS:
                    continue
                if HERE_VAR.match(w):
                    r = posixpath.join(here, HERE_VAR.sub("", w))
                elif TOP_VAR.match(w):
                    r = TOP_VAR.sub("", w)
                elif "$" in w or w.startswith("/") or ":" in w:
                    skipped += 1
                    continue
                else:
                    r = posixpath.join(here, w)
                r = _norm(r)
                if r in dirs:
                    roots.setdefault(r, cm)
    return sorted(roots.items()), skipped


def resolve(src: str, quote: str, name: str, roots, known):
    """-> ('K', path) | ('belirsiz', [paths]) | ('cozulemeyen', None) | ('dis', None)."""
    if quote == '"':
        near = _norm(posixpath.join(posixpath.dirname(src), name))
        if near in known:
            return "K", near
    hits = sorted({c for c in (_norm(posixpath.join(r, name)) for r, _ in roots) if c in known})
    if len(hits) == 1:
        return "K", hits[0]
    if hits:
        return "belirsiz", hits
    return ("cozulemeyen" if quote == '"' else "dis"), None


def include_edges(files: dict, roots, known):
    """files = {path: text} of C files -> (edges set, counts, examples{kind: [(src, name)]})."""
    edges, counts, examples = set(), {"K": 0, "belirsiz": 0, "cozulemeyen": 0, "dis": 0}, {"belirsiz": [], "cozulemeyen": []}
    for p, text in files.items():
        for quote, name in INCLUDE.findall(text):
            kind, hit = resolve(p, quote, name.strip(), roots, known)
            counts[kind] += 1
            if kind == "K" and hit != p:
                edges.add((p, hit))
            elif kind in examples and len(examples[kind]) < 10:
                examples[kind].append((p, name.strip()))
    return edges, counts, examples


def render(c: dict) -> list:
    """The C / C++ section of yapi.md."""
    n = c["includes"]
    o = ["## C / C++ include baglari", "",
         f"{c['files']} C/C++ dosyasi. Include kokleri (tahmin edilmedi; kaynagiyla): "
         + (", ".join(f"`{x['root']}` ({x['source']})" for x in c["roots"]) or "bulunamadi")
         + (f"; degisken iceren {c['roots_skipped']} CMake girdisi atlandi" if c["roots_skipped"] else "") + ".", "",
         f"- `[K]` cozulen include: {n['K']} (dosya bagi {c['file_edges']})",
         f"- **belirsiz** (birden cok kokte ayni ad; bag uretilmedi): {n['belirsiz']}",
         f"- **cozulemeyen tirnakli include** (kor nokta): {n['cozulemeyen']}",
         f"- depoda bulunmayan `<...>` (dis bagimlilik; bag yok): {n['dis']}",
         f"- iskeletinde hic bildirim bulunamayan C/C++ dosyasi (makro ya da kalip disi): {len(c['no_outline'])}", ""]
    for kind in ("belirsiz", "cozulemeyen"):
        if c["examples"][kind]:
            o += [f"Ornek {kind}: " + "; ".join(f"`{a}` → `{b}`" for a, b in c["examples"][kind][:6]), ""]
    return o


def _blank(text: str) -> str:
    """Comments become spaces of the same length, so positions and line numbers stay."""
    return COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)


def outline(text: str, line_of) -> list:
    """-> [(line, depth, kind, name)]  [H]"""
    t, marks = _blank(text), []
    for m in FUNC.finditer(t):
        name = m.group(2)
        if name.split("::")[-1] not in NOT_A_FUNCTION:
            marks.append((line_of(t, m.start(2)), len(m.group(1).replace("\t", "    ")) // 4, "islev", name))
    for m in TYPE.finditer(t):
        kind, name, pos = ("typedef " if m.group(2) else "") + m.group(3), m.group(4), m.start(4)
        if m.group(2):
            depth, i = 0, m.end() - 1
            while i < len(t):
                depth += {"{": 1, "}": -1}.get(t[i], 0)
                if depth == 0:
                    break
                i += 1
            alias = re.match(r"\s*(\w+)", t[i + 1:])
            if alias:
                name, pos = alias.group(1), i + 1 + alias.start(1)
        if name:
            marks.append((line_of(t, pos), len(m.group(1).replace("\t", "    ")) // 4, kind, name))
    return sorted(set(marks))


if __name__ == "__main__":
    # A module of yapi.py, not a script of its own: its checks run inside yapi.py's self-test.
    # Said out loud, because a silent exit reads like a pass.
    import subprocess
    import sys
    print("c_dili.py yapi.py'nin modulu; sinamalari yapi.py --self-test icinde kosuyor:", flush=True)
    sys.exit(subprocess.call([sys.executable, __file__.replace("c_dili.py", "yapi.py"), "--self-test"]))
