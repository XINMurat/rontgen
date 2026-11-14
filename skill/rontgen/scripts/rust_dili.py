#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- Rust for yapi.py: an outline and `mod` / `use` edges; no name proxy.

WHY THIS EXISTS
---------------
On a Rust repository the scripts had no [K] edge at all, and of ten [H] edges
checked by hand eight were wrong: a name in a comment or a string, an enum
variant (`Kind::SortedSet`), `io::Error`, another crate's method (`db.execute`).
The outline missed half of the definitions in generic code (`unsafe fn`,
`impl<T>`, `const fn`, `type`, `mod`).

EDGES [K]
---------
  `mod x;`                         -> x.rs or x/mod.rs next to the module
  `use crate::a::b` / `self::` / `super::` / `use <crate>::...`
                                   -> the deepest module FILE the path reaches
                                      (an item inside a module points at the
                                      module's file)
Crates come from the repository's Cargo.toml files (`[package] name`, `-` read
as `_`). A path into a crate that is not in the repository (std, serde ...) is
"dis": counted, no edge. A path into a crate here that reaches no file, and a
`mod x;` with no file, are "cozulemeyen".

NO NAME PROXY [H] FOR RUST
--------------------------
The [H] proxy (a name declared in one file, used in another) was first
cleaned for Rust -- comments, strings and names after `::` or `.` skipped. On
the same repository, re-checked with the same seed, the cleaned [H] edges held
0 of 4: the shared name was another file's own `fn reserve`, an associated
`type Error = ...`, an enum variant `BloomAdd(...)`. Rust names its imports
explicitly, so [K] from `use` covers what [H] was guessing at; Rust has no [H]
name edges.
"""
from __future__ import annotations

import posixpath
import re
import sys

MOD = re.compile(r"^[ \t]*(?:pub(?:\([^)]*\))?[ \t]+)?mod[ \t]+(\w+)[ \t]*;", re.M)
USE = re.compile(r"^[ \t]*(?:pub(?:\([^)]*\))?[ \t]+)?use[ \t]+([^;]+);", re.M)
PACKAGE = re.compile(r"^\[package\][^\[]*?^name\s*=\s*\"([^\"]+)\"", re.M | re.S)
COMMENT_OR_STRING = re.compile(r"//[^\n]*|/\*.*?\*/|r(#*)\".*?\"\1|b?\"(?:\\.|[^\"\\])*\"", re.S)
QUALS = r"(?:(?:const|async|unsafe|default|extern(?:[ \t]+\"[^\"]*\")?)[ \t]+)*"
DEF = re.compile(r"^([ \t]*)(?:pub(?:\([^)]*\))?[ \t]+)?" + QUALS + r"(fn|struct|enum|trait|type|mod|union)[ \t]+(\w+)", re.M)
IMPL = re.compile(r"^([ \t]*)" + QUALS + r"impl\b[ \t]*(?:<(?:[^<>]|<[^<>]*>)*>)?[ \t]*([^{\n]*?)\s*(?:where\b[^{]*)?\{", re.M)


def outline(text: str, line_of) -> list:
    """-> [(line, depth, kind, name)]  [H]"""
    t = COMMENT_OR_STRING.sub(lambda m: re.sub(r"[^\n]", " ", m.group()), text)
    marks = [(line_of(t, m.start(3)), len(m.group(1).replace("\t", "    ")) // 4, m.group(2), m.group(3)) for m in DEF.finditer(t)]
    for m in IMPL.finditer(t):
        name = re.sub(r"\s+", " ", m.group(2)).strip()[:60]
        if name:
            marks.append((line_of(t, m.start(2)), len(m.group(1).replace("\t", "    ")) // 4, "impl", name))
    return sorted(set(marks))


def crates(cargo: dict) -> dict:
    """{Cargo.toml path: text} -> {crate_name: crate_dir}"""
    out = {}
    for path, text in cargo.items():
        m = PACKAGE.search(text)
        if m:
            out[m.group(1).replace("-", "_")] = posixpath.dirname(path) or "."
    return out


def _expand(spec: str) -> list:
    """`a::{b, c::{d, e}}` -> [['a','b'], ['a','c','d'], ['a','c','e']]; `as x` and `*` dropped."""
    spec = re.sub(r"\s+", "", spec)
    depth, cut = 0, None
    for i, ch in enumerate(spec):
        depth += ch == "{"
        depth -= ch == "}"
        if ch == "{" and depth == 1 and cut is None:
            cut = i
    if cut is None:
        segs = [s for s in re.sub(r"as\w+$", "", spec).split("::") if s and s not in ("*", "self")]
        return [segs] if segs else []
    head = [s for s in spec[:cut].split("::") if s]
    inner, parts, depth, buf = spec[cut + 1:spec.rindex("}")], [], 0, ""
    for ch in inner:
        depth += ch == "{"
        depth -= ch == "}"
        if ch == "," and depth == 0:
            parts.append(buf); buf = ""
        else:
            buf += ch
    parts.append(buf)
    out = []
    for p in parts:
        if p == "self":
            out.append(head)
        elif p:
            out += [head + tail for tail in _expand(p)]
    return [o for o in out if o]


class Tree:
    """Where each Rust file sits in its crate's module tree."""

    def __init__(self, known, crate_dirs: dict):
        self.known, self.crate_dirs = known, crate_dirs

    def crate_of(self, path: str):
        best = None
        for name, d in self.crate_dirs.items():
            if (d == "." or path.startswith(d + "/")) and (best is None or len(d) > len(self.crate_dirs[best])):
                best = name
        return best

    def src_root(self, name: str):
        d = self.crate_dirs[name]
        src = "src" if d == "." else d + "/src"
        for f in ("lib.rs", "main.rs"):
            if f"{src}/{f}" in self.known:
                return src, f"{src}/{f}"
        return src, None

    def is_root(self, path: str) -> bool:
        name = self.crate_of(path)
        src = self.src_root(name)[0] if name else None
        return (not src or not path.startswith(src + "/") or path.startswith(src + "/bin/")
                or path in (f"{src}/lib.rs", f"{src}/main.rs"))

    def mod_dir(self, path: str) -> str:
        """The directory a `mod x;` in this file looks into."""
        if self.is_root(path) or posixpath.basename(path) == "mod.rs":
            return posixpath.dirname(path)
        return path[:-3]

    def module_file(self, d: str):
        for f in (d + ".rs", d + "/mod.rs"):
            if f in self.known:
                return f
        return None

    def walk(self, d: str, f: str, segs):
        """Descend the module tree from (dir, file) along segs. One segment left over is an item in the module
        reached: an edge to its file. More than one left over means a module that is not here: not resolved."""
        left = list(segs)
        while left:
            nxt = self.module_file(f"{d}/{left[0]}")
            if not nxt:
                break
            d, f, left = f"{d}/{left[0]}", nxt, left[1:]
        return ("K", f) if len(left) <= 1 else ("cozulemeyen", None)

    def resolve_use(self, path: str, segs):
        """-> ('K', file) | ('dis', None) | ('cozulemeyen', None)"""
        first, rest = segs[0], segs[1:]
        own = self.crate_of(path)
        if first == "crate":
            if not own:
                return "cozulemeyen", None
            if self.is_root(path):
                return self.walk(self.mod_dir(path), path, rest)
            src, root = self.src_root(own)
            return self.walk(src, root, rest) if root else ("cozulemeyen", None)
        if first in ("self", "super"):
            d, f = self.mod_dir(path), path
            while segs and segs[0] == "super":
                segs = segs[1:]
                d = posixpath.dirname(d)
                f = (self.module_file(d) or self.src_root(own)[1]) if own else None
                if not f:
                    return "cozulemeyen", None
            return self.walk(d, f, [s for s in segs if s != "self"])
        if first in self.crate_dirs:
            src, root = self.src_root(first)
            return self.walk(src, root, rest) if root else ("cozulemeyen", None)
        return "dis", None


def edges(files: dict, known, cargo: dict):
    """files = {path: text} of .rs files -> (edges set, counts, crate names)"""
    tree = Tree(known, crates(cargo))
    out, counts, missed = set(), {"K": 0, "dis": 0, "cozulemeyen": 0}, []
    for p, text in files.items():
        t = COMMENT_OR_STRING.sub(" ", text)
        for name in MOD.findall(t):
            hit = tree.module_file(f"{tree.mod_dir(p)}/{name}")
            counts["K" if hit else "cozulemeyen"] += 1
            missed += [] if hit else [f"{p}: mod {name}"]
            if hit:
                out.add((p, hit))
        for spec in USE.findall(t):
            for segs in _expand(spec):
                kind, hit = tree.resolve_use(p, segs)
                counts[kind] += 1
                missed += [f"{p}: use {'::'.join(segs)}"] if kind == "cozulemeyen" else []
                if hit and hit != p:
                    out.add((p, hit))
    counts["ornek"] = sorted(missed)[:10]     # which ones: a count alone cannot be checked
    return out, counts, sorted(tree.crate_dirs)


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    def line_of(text, pos):
        return text.count("\n", 0, pos) + 1

    src = ("// fn yorum_islev() {}\npub(crate) unsafe fn ham() {}\nimpl<T: Clone> Kume<T> {\n    pub const fn bos() -> Self { x }\n}\n"
           "impl<'a, K> Iterator for Gezgin<'a, K>\nwhere K: Eq\n{\n}\npub type Takma = u8;\nmod alt;\nasync fn bekle() {}\n"
           "extern \"C\" fn dis() {}\nlet s = \"fn sahte() {\";\n")
    marks = [(ln, k, n) for ln, _, k, n in outline(src, line_of)]
    check("iskelet: unsafe/const/async/extern fn, jenerik impl, type, mod; yorum ve metin sayilmaz",
          marks == [(2, "fn", "ham"), (3, "impl", "Kume<T>"), (4, "fn", "bos"), (6, "impl", "Iterator for Gezgin<'a, K>"),
                    (10, "type", "Takma"), (11, "mod", "alt"), (12, "fn", "bekle"), (13, "fn", "dis")])
    check("use acilimi: ic ice suslu, self, as", _expand("crate::a::{b, c::{d, e as f}, self}") ==
          [["crate", "a", "b"], ["crate", "a", "c", "d"], ["crate", "a", "c", "e"], ["crate", "a"]])
    files = {
        "Cargo.toml": "[package]\nname = \"ana-kut\"\n",
        "istemci/Cargo.toml": "[package]\nname = \"istemci\"\n",
        "src/lib.rs": "pub mod depo;\nmod protokol;\nuse std::io;\npub use crate::depo::Kume;\n",
        "src/depo/mod.rs": "pub mod kume;\nuse super::protokol::Komut;\nuse self::kume::{Kume, Yardim};\n",
        "src/depo/kume.rs": "use crate::protokol;\nuse crate::yok::Bir;\nmod kayip;\n",
        "src/protokol.rs": "pub struct Komut;\n",
        "src/bin/sunucu.rs": "use ana_kut::depo::kume::Kume;\nuse serde::Serialize;\nmod bin_ortak;\n",
        "src/bin/bin_ortak.rs": "pub fn yardim() {}\n",
        "tests/uctan.rs": "use ana_kut::protokol::Komut;\n",
        "istemci/src/lib.rs": "use crate::hata::Hata;\nmod hata;\n",
        "istemci/src/hata.rs": "pub struct Hata;\n",
    }
    rs = {p: t for p, t in files.items() if p.endswith(".rs")}
    e, n, names = edges(rs, set(files), {p: t for p, t in files.items() if p.endswith("Cargo.toml")})
    want = {("src/lib.rs", "src/depo/mod.rs"), ("src/lib.rs", "src/protokol.rs"), ("src/depo/mod.rs", "src/depo/kume.rs"),
            ("src/depo/mod.rs", "src/protokol.rs"), ("src/depo/kume.rs", "src/protokol.rs"), ("src/bin/sunucu.rs", "src/depo/kume.rs"),
            ("tests/uctan.rs", "src/protokol.rs"), ("istemci/src/lib.rs", "istemci/src/hata.rs"), ("src/bin/sunucu.rs", "src/bin/bin_ortak.rs")}
    check("bag [K]: mod, crate::, self::, super::, crate adi (- yerine _), calisma alani uyesi", e == want)
    check("bag: crate'ler ve dis sayimi (std, serde)", names == ["ana_kut", "istemci"] and n["dis"] == 2)
    check("bag: var olmayan modul (`crate::yok::Bir`) ve `mod kayip;` cozulemeyen, kok dosyaya dusmez",
          ("src/depo/kume.rs", "src/lib.rs") not in e and n["cozulemeyen"] == 2)
    check("bag: cozulemeyenler dosyasiyla listelenir", len(n["ornek"]) == 2 and all(": mod " in x or ": use " in x for x in n["ornek"])
          and any("yok" in x for x in n["ornek"]) and any("kayip" in x for x in n["ornek"]))
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv[1:] or len(sys.argv) == 1 else 0)
