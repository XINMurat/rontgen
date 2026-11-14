#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- structure: which parts exist, what leans on what, where the
outside world comes in and where the data lives. Drawn from the code, not
from anyone's memory of the code.

WHAT IT EXTRACTS
----------------
  modules      a module is a directory of source files (depth from config)
  edges [K]    declared dependencies that resolve inside the repository:
               Python `import`, relative `import ... from` in TS/JS,
               `<ProjectReference>` between C# projects, C/C++ `#include` that resolves
               to one file (c_dili.py), Rust mod/use and Go import through the manifest
               (rust_dili.py, go_dili.py), and any probe result that earned [K] (sonda.py)
  edges [H]    a name declared in exactly ONE file and used in another file
               of the same language family. A proxy: a common word used as a
               type name gives a false edge; reflection and DI give none.
               An [H] edge carried by fewer file pairs than `weak_edge` is
               ZAYIF: listed, never drawn, never used to find a cycle.
  cycles       from [K] edges alone; cycles that need [H] edges are listed
               separately as candidates, with their thinnest edge
  blind spots  how often the code uses a mechanism these scripts cannot
               follow (DI, reflection, ORM, built-up SQL ...): the list a
               probe is written from, produced before anyone reads the code
  entry points routes and mains recognised by pattern [H]
  stores       tables declared in SQL or an ORM (orm_dili.py); files that WRITE (INSERT/UPDATE/DELETE),
               READ (FROM/JOIN; ORM access, [H]) or quote each. A bare word in prose is no mention.
  outline      declarations and routes of the largest files, with line
               numbers; C# methods and C/C++ functions and types are
               matched by pattern [H]

The first version drew [K] and [H] together, found cycles through edges on three file pairs, counted
bundled build output as source and a word in a spreadsheet script as a table use: hence the lines above.

USAGE
-----
    python yapi.py --repo . --out rontgen-out
    python yapi.py --repo . --config rontgen.config.json --edges 40
    python yapi.py --self-test
Exit codes: 0 extracted · 2 could not (not a git repository, no source, bad config or probe result)
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
from collections import Counter, defaultdict

from ortak import EXTRA, cycles, entry_match, entry_order, excluded_lines, family_of, is_test, list_files, load_config, read_sources, thresholds_line
import dil  # noqa: E402
from sonda import kor_noktalar, load_probes, probe_ends
import c_dili
import go_dili, jvm_dili, orm_dili, ozel_dil  # noqa: E401,E402
import rust_dili
from yapi_rapor import render  # noqa: E402

DECL = {
    "cs": re.compile(r"\b(?:class|record|interface|enum|struct)\s+([A-Z]\w+)"),
    "py": re.compile(r"^(?:class|def)\s+([A-Za-z_]\w+)", re.M),
    "web": re.compile(r"^export\s+(?:default\s+)?(?:async\s+)?(?:function|class|const|let|type|interface|enum)\s+([A-Za-z_]\w+)", re.M),
    "java": re.compile(r"\b(?:class|interface|enum|record|object)\s+([A-Z]\w+)"),
    "go": re.compile(r"^(?:func|type)\s+(?:\([^)]*\)\s*)?([A-Z]\w+)", re.M),
}
CS_MOD = r"(?:public|internal|private|protected|static|async|override|virtual|sealed|abstract|partial|new|readonly|extern)"
OUTLINE = {
    "py": [("", re.compile(r"^([ \t]*)(?:async\s+)?(def|class)\s+(\w+)", re.M))],
    "web": [("", re.compile(r"^([ \t]*)(?:export\s+)?(?:default\s+)?(?:async\s+)?(function|class)\s+(\w+)", re.M))],
    "cs": [("", re.compile(r"^([ \t]*)(?:" + CS_MOD + r"\s+)*(class|record|interface|enum|struct)\s+(\w+)", re.M)),
           ("method", re.compile(r"^([ \t]*)(?:" + CS_MOD + r"\s+)+[\w<>\[\],.? ()]+?\s+()(\w+)\s*(?:<[^>\n]*>)?\(", re.M))],
    "java": [("", re.compile(r"^([ \t]*)(?:(?:public|private|protected|static|final|abstract)\s+)*(class|interface|enum|record)\s+(\w+)", re.M))],
    "go": [("", re.compile(r"^()(func|type)\s+(?:\([^)]*\)\s*)?(\w+)", re.M))],
}
NOT_A_METHOD = {"if", "for", "foreach", "while", "switch", "return", "new", "using", "lock", "catch", "await", "throw",
                "nameof", "typeof", "base", "this"}
TABLE = re.compile(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w.\[\]\"]+)", re.I)
SQL_USE = re.compile(r"\b(DELETE\s+FROM|INSERT\s+INTO|INTO|UPDATE|FROM|JOIN)\s+([\w.\[\]\"]+)", re.I)
QUOTED = re.compile(r"[\"']([A-Za-z_]\w{4,})[\"']")
ROUTES = [re.compile(r"\.Map(Get|Post|Put|Delete|Patch)\(\s*\"([^\"]+)\""),
          re.compile(r"\[Http(Get|Post|Put|Delete|Patch)\(\s*\"([^\"]*)\""),
          re.compile(r"@\w+\.(get|post|put|delete|patch|route)\(\s*[\"']([^\"']+)[\"']"),
          re.compile(r"\b(?:router|app)\.(get|post|put|delete|patch)\(\s*[\"'`](/[^\"'`]*)[\"'`]")]
MAINS = [re.compile(r"if\s+__name__\s*==\s*[\"']__main__[\"']"), re.compile(r"static\s+(?:async\s+)?\w+\s+Main\s*\("),
         re.compile(r"WebApplication\.CreateBuilder"), re.compile(r"createRoot\(|ReactDOM\.render\("),
         re.compile(r"^func\s+main\s*\(", re.M)]
PY_IMPORT = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
WEB_IMPORT = re.compile(r"""(?:from|import)\s+['"](\.{1,2}/[^'"]+)['"]""")
PROJECT_REF = re.compile(r"<ProjectReference\s+Include=\"([^\"]+)\"", re.I)
WORD = re.compile(r"[A-Za-z_]\w+"); NOCOMMENT = re.compile(r"//[^\n]*|/\*.*?\*/", re.S)  # [H]: a name in a comment is no use
MIN_NAME = 5


def ranked(counter):   # most_common breaks ties by insertion, i.e. by hash order: two runs drew different edges
    return sorted(counter.items(), key=lambda x: (-x[1], x[0]))


def module_of(path: str, depth: int) -> str:
    return "/".join(path.split("/")[:-1][:depth]) or "."


def node_id(name: str) -> str:
    return "m_" + re.sub(r"\W", "_", name)


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def resolve_web(src: str, target: str, known):
    base = os.path.normpath(os.path.join(os.path.dirname(src), target)).replace("\\", "/")
    for tail in ("", ".ts", ".tsx", ".js", ".jsx", ".vue", ".mjs", "/index.ts", "/index.tsx", "/index.js"):
        if base + tail in known:
            return base + tail
    return None


def outline_of(fam: str, text: str, routes):
    marks = c_dili.outline(text, line_of) if fam == "c" else rust_dili.outline(text, line_of) if fam == "rs" else []
    for kind, rx in OUTLINE.get(fam, []):
        for m in rx.finditer(text):
            name = m.group(3)
            if kind == "method" and name in NOT_A_METHOD:
                continue
            marks.append((line_of(text, m.start(3)), len(m.group(1).replace("\t", "    ")) // 4, kind or m.group(2), name))
    marks += [(ln, 0, "uc", f"{verb} {path}") for ln, verb, path in routes]
    return sorted(set(marks))


def project_edges(repo: str, depth: int):
    """[K] edges between C# projects, from <ProjectReference>."""
    out = set()
    for p in list_files(repo, "**/*.csproj")[0]:
        try:
            with io.open(os.path.join(repo, p), encoding="utf-8", errors="replace") as f:
                refs = PROJECT_REF.findall(f.read())
        except OSError:
            continue
        for ref in refs:
            target = os.path.normpath(os.path.join(os.path.dirname(p), ref.replace("\\", "/"))).replace("\\", "/")
            a, b = module_of(p, depth), module_of(target, depth)
            if a != b:
                out.add((a, b))
    return out


def build(repo: str, cfg: dict, top: int, probes=()) -> dict:
    depth, weak = cfg["module_depth"], cfg["weak_edge"]
    texts, excluded, _ = read_sources(repo, cfg)
    files = {p: (family_of(p, cfg), t) for p, t in texts.items() if family_of(p, cfg)}
    known = set(files)
    specs = ozel_dil.specs(cfg)
    py_index = defaultdict(list)
    for p, (fam, _) in files.items():
        if fam == "py":
            parts = p[:-3].split("/")
            for i in range(len(parts)):
                py_index[".".join(parts[i:])].append(p)

    declared = defaultdict(set)
    for p, (fam, text) in files.items():
        if fam in DECL:
            for name in set(DECL[fam].findall(text)):
                if len(name) >= MIN_NAME:
                    declared[(fam, name)].add(p)
    owner = {k: next(iter(v)) for k, v in declared.items() if len(v) == 1}

    tables = {}
    for p, (fam, text) in files.items():
        if fam == "sql":
            for raw in TABLE.findall(text):
                name = re.sub(r"[\[\]\"]", "", raw).split(".")[-1]
                if name not in tables or (is_test(tables[name]) and not is_test(p)):
                    tables[name] = p          # a fixture copy of the schema does not own the table
    orm = {t: v for t, v in orm_dili.tables(files).items() if t not in tables}; tables.update({t: v[0] for t, v in orm.items()})
    use = {t: {"write": set(), "read": set(), "quoted": set()} for t in tables}
    for t, us in orm_dili.uses(files, orm).items(): use[t]["read"] |= us

    hard, soft, routes, mains, outlines = set(), set(), defaultdict(list), [], {}
    for p, (fam, text) in files.items():
        if fam == "py":
            for a, b in PY_IMPORT.findall(text):
                hit = py_index.get(a or b, [])
                if len(hit) == 1 and hit[0] != p:
                    hard.add((p, hit[0]))
        elif fam == "web":
            for target in WEB_IMPORT.findall(text):
                hit = resolve_web(p, target, known)
                if hit and hit != p:
                    hard.add((p, hit))
        if fam not in ("sql", EXTRA):   # an extra source is counted, never parsed
            for w in set(WORD.findall(NOCOMMENT.sub(" ", text) if fam in ("cs", "java", "go", "web", "c") else text)):  # no Rust DECL
                o = owner.get((fam, w))
                if o and o != p:
                    soft.add((p, o))
            for verb, raw in SQL_USE.findall(text):
                name = re.sub(r"[\[\]\"]", "", raw).split(".")[-1]
                if name in use:
                    use[name]["read" if verb.upper() in ("FROM", "JOIN") else "write"].add(p)
            for name in set(QUOTED.findall(text)):
                if name in use:
                    use[name]["quoted"].add(p)
            for rx in ROUTES:
                for m in rx.finditer(text):
                    routes[p].append((line_of(text, m.start()), m.group(1).upper(), m.group(2)))
            if any(rx.search(text) for rx in MAINS):
                mains.append(p)
        if fam in OUTLINE or fam in ("c", "rs"):
            outlines[p] = (text.count("\n") + 1, outline_of(fam, text, routes.get(p, [])))
        elif fam == EXTRA and os.path.splitext(p)[1].lower() in specs:      # a language the config describes
            outlines[p] = (text.count("\n") + 1, ozel_dil.outline(text, specs[os.path.splitext(p)[1].lower()], line_of))

    wanted, entry_fns, found = cfg["entry_points"], [], set()     # rules in ortak.entry_match
    for p, (_, marks) in sorted(outlines.items()):
        for ln, _, kind, nm in marks:
            hit = kind != "uc" and entry_match(p, files[p][0], nm, wanted)
            if hit:
                entry_fns.append({"path": p, "line": ln, "name": nm, "source": hit[0]}); found.add(hit[1])
    entry_fns.sort(key=entry_order)
    def read_all(pattern):                  # build files (CMakeLists.txt, Cargo.toml) are read, never measured
        out = {}
        for rel in list_files(repo, pattern)[0]:
            try:
                with io.open(os.path.join(repo, rel), encoding="utf-8", errors="replace") as f:
                    out[rel] = f.read()
            except OSError:
                pass
        return out

    lang = {}                                   # Rust mod/use, Go import: resolved through the manifest, never by name
    for fam, mod, manifest in (("rs", rust_dili, "**/Cargo.toml"), ("go", go_dili, "**/go.mod"), ("java", jvm_dili, "**/pom.xml")):
        lf = {p: t for p, (f, t) in files.items() if f == fam}
        if lf:
            e, cnt, roots = mod.edges(lf, known, read_all(manifest)); hard |= e
            lang[fam] = {"files": len(lf), "crates": roots, "uses": cnt, "file_edges": len(e)}
    of = {p: t for p, (f, t) in files.items() if f == EXTRA and os.path.splitext(p)[1].lower() in specs}
    if of:
        e, cnt, roots = ozel_dil.edges(of, known, cfg); hard |= e
        lang["ozel"] = {"files": len(of), "crates": roots, "uses": cnt, "file_edges": len(e)}
    c_files, c_note = {p: t for p, (fam, t) in files.items() if fam == "c"}, None
    if c_files:
        roots, skipped = c_dili.include_roots(known, read_all("**/CMakeLists.txt"))
        c_edges, counts, examples = c_dili.include_edges(c_files, roots, known)
        hard |= c_edges
        c_note = {"files": len(c_files), "roots": [{"root": a, "source": b} for a, b in roots], "roots_skipped": skipped,
                  "includes": counts, "examples": examples, "file_edges": len(c_edges),
                  "no_outline": sorted(p for p in c_files if not outlines[p][1])}

    probe_notes, present, outside = [], set(list_files(repo)[0]) if probes else set(), set()
    for pr in probes:
        pairs = {(e["from"].replace("\\", "/"), e["to"].replace("\\", "/")) for e in pr["edges"]}
        accepted, kinds = probe_ends(pairs, known, present, cfg)
        (hard if pr["tier"] == "K" else soft).update(accepted)
        outside.update(kinds["kaynak_disi"])
        probe_notes.append({"sonda": pr["sonda"], "tier": pr["tier"], "commit": pr["commit"], "oz_test": pr["oz_test"],
                            "edges": len(pairs), "accepted": len(accepted), "outside_count": len(kinds["kaynak_disi"]),
                            "excluded_files": kinds["dislanan"][:10], "excluded_count": len(kinds["dislanan"]),
                            "unknown_files": kinds["yok"][:10], "unknown_count": len(kinds["yok"])})
    soft -= hard

    def agg(pairs):
        out = Counter()
        for a, b in pairs:
            ma, mb = module_of(a, depth), module_of(b, depth)
            if ma != mb:
                out[(ma, mb)] += 1
        return out

    mod_hard = agg(hard)
    for e in project_edges(repo, depth):
        mod_hard[e] += 1
    mod_soft = Counter({k: v for k, v in agg(soft).items() if k not in mod_hard})
    strong_soft = {k for k, v in mod_soft.items() if v >= weak}
    mods = defaultdict(lambda: {"files": 0, "lines": 0})
    for p, (_, text) in files.items():
        m = mods[module_of(p, depth)]
        m["files"] += 1; m["lines"] += text.count("\n") + 1
    for p in outside:                       # a probe end that is not measured source: shown, never counted as lines
        m = mods[module_of(p, depth)]
        m["kaynak_disi"] = m.get("kaynak_disi", 0) + 1
    fan = {m: {"in_k": 0, "out_k": 0, "in_h": 0, "out_h": 0} for m in mods}
    for (a, b) in mod_hard:
        if a in fan and b in fan:
            fan[a]["out_k"] += 1; fan[b]["in_k"] += 1
    for (a, b) in strong_soft:
        fan[a]["out_h"] += 1; fan[b]["in_h"] += 1
    file_in = Counter(b for _, b in hard | soft)
    cyc_k = cycles(list(mod_hard))
    cyc_h = [{"modules": g, "thinnest": min((mod_soft[(a, b)] for a in g for b in g if (a, b) in strong_soft), default=None)}
             for g in cycles(list(mod_hard) + list(strong_soft)) if g not in cyc_k]
    prefix = Counter()
    for rs in routes.values():
        for _, _, path in rs:
            prefix["/" + "/".join([s for s in path.split("/") if s and not s.startswith("{")][:2])] += 1
    edges = ([{"from": a, "to": b, "files": n, "tier": "K", "weak": False} for (a, b), n in ranked(mod_hard)]
             + [{"from": a, "to": b, "files": n, "tier": "H", "weak": n < weak} for (a, b), n in ranked(mod_soft)])
    biggest = sorted(outlines, key=lambda p: (-outlines[p][0], p))[:top]
    return {
        "repo": os.path.abspath(repo), "depth": depth, "weak_edge": weak,
        "excluded": {k: sorted(v) for k, v in excluded.items()},
        "modules": dict(sorted(mods.items(), key=lambda x: (-x[1]["lines"], x[0]))),
        "edges": edges, "fan": fan,
        "edge_counts": {"K": len(mod_hard), "H": len(strong_soft), "H_weak": len(mod_soft) - len(strong_soft)},
        "cycles": cyc_k, "cycle_candidates": cyc_h,
        "blind_spots": kor_noktalar({p: t for p, (f, t) in files.items() if f not in ("sql", EXTRA) and not is_test(p)}),
        "probes": probe_notes, "c": c_note, "rust": lang.get("rs"), "go": lang.get("go"), "java": lang.get("java"), "ozel": lang.get("ozel"),
        "most_used_files": [{"path": p, "used_by": n} for p, n in ranked(file_in)[:top]],
        "entry": {"mains": sorted(mains), "functions": entry_fns, "missing": sorted(set(wanted) - found - {"main"}),
                  "route_count": sum(len(v) for v in routes.values()),
                  "route_test": sum(len(v) for k, v in routes.items() if is_test(k)),
                  "routes_by_file": {p: len(v) for p, v in sorted(routes.items(), key=lambda x: -len(x[1]))},
                  "routes_by_prefix": dict(ranked(prefix)[:40])},
        "stores": {"tables": len(tables),
                   "unmentioned": sorted(t for t, u in use.items() if not (u["write"] or u["read"] or u["quoted"])),
                   "by_table": {t: {"declared_in": tables[t], "written_by": sorted(u["write"]), "read_by": sorted(u["read"]),
                                    "quoted_in": sorted(u["quoted"] - u["write"] - u["read"])}
                                for t, u in sorted(use.items(), key=lambda x: -(len(x[1]["write"]) + len(x[1]["read"])))}},
        "outline": {p: {"lines": outlines[p][0],
                        "marks": [{"line": a, "depth": b, "kind": c, "name": d} for a, b, c, d in outlines[p][1]]}
                    for p in biggest},
    }


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    check("modul: derinlik keser", module_of("a/b/c/d.py", 2) == "a/b" and module_of("x.py", 2) == ".")
    check("dongu: iki modul", cycles([("a", "b"), ("b", "a"), ("b", "c")]) == [["a", "b"]])
    check("dongu: yoksa bos", cycles([("a", "b"), ("b", "c")]) == [])
    cs = "class Odeme {\n    public void Onayla(int id) { if (x) { } }\n    static async Task<int> Say<T>(T a) => 1;\n}\n"
    names = [(k, n) for _, _, k, n in outline_of("cs", cs, [])]
    check("iskelet: C# tip ve yontemler", names == [("class", "Odeme"), ("method", "Onayla"), ("method", "Say")])
    check("iskelet: 'if (' yontem sayilmaz", all(n != "if" for _, n in names))
    check("iskelet: Go kaliplari", [n for *_, n in outline_of("go", "func Ana() {}\ntype Kayit struct {}\n", [])] == ["Ana", "Kayit"])
    check("iskelet: Rust kaliplari", [n for *_, n in outline_of("rs", "pub fn calis() {}\nstruct Veri;\n", [])] == ["calis", "Veri"])
    check("iskelet: Java sinifi", [n for *_, n in outline_of("java", "public class Servis {\n}\n", [])] == ["Servis"])
    csrc = ("/*\nint yorum(void) {\n*/\nstatic int\nbaslat(struct cihaz *c,\n       int n)\n{\n    if (n) { }\n}\n"
            "struct kuyruk {\n int a;\n};\ntypedef struct {\n int b;\n} Paket;\nenum durum { A };\nint Sinif::Calis() const {\n}\n"
            "typedef struct PAKETLI basl {\n} basl_t;\nstruct KUTU {\n};\n")
    cm = [(ln, k, n) for ln, _, k, n in outline_of("c", csrc, [])]
    check("iskelet: C islev, struct, enum, typedef struct satirli; yorumdaki islev sayilmaz",
          cm == [(5, "islev", "baslat"), (10, "struct", "kuyruk"), (15, "typedef struct", "Paket"), (16, "enum", "durum"),
                 (17, "islev", "Sinif::Calis"), (20, "typedef struct", "basl_t"), (21, "struct", "KUTU")])
    verbs = [v.upper().split()[0] for v, _ in SQL_USE.findall("INSERT INTO Gorev VALUES; SELECT * FROM Gorev g JOIN Kisi k; DELETE FROM Gorev")]
    check("tablo kullanimi: yazma ve okuma ayrilir", verbs == ["INSERT", "FROM", "JOIN", "DELETE"])
    with tempfile.TemporaryDirectory() as d:
        def write(rel, text):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        try:
            subprocess.run(["git", "-C", d, "init", "-q"], check=True, capture_output=True)
            write("api/Api.csproj", '<Project><ItemGroup><ProjectReference Include="..\\cekirdek\\Cekirdek.csproj" /></ItemGroup></Project>')
            write("cekirdek/Cekirdek.csproj", "<Project></Project>")
            write("api/Program.cs", 'app.MapGet("/api/odeme/paket", () => new OdemeServisi());\napp.MapPost("/api/odeme/onay", x);\n'
                                    "services.AddScoped<IKanal, KlasorKanali>();\n")
            write("cekirdek/Odeme.cs", 'public class OdemeServisi { void Yaz() { Calistir("INSERT INTO OdemePaketi VALUES (1)"); } }\n')
            write("cekirdek/Rapor.cs", 'class Rapor { string s = "SELECT * FROM OdemePaketi"; string ad = "Bekleyen"; }\n')
            write("yan/Tek.cs", "class YanModul { OdemeServisi x; }\n")
            write("kanal/Klasor.cs", "class KlasorKanali { }\n")
            write("web/src/a.ts", 'import { yardim } from "./ortak/b";\nexport const sayfa = 1;\n')
            write("web/src/ortak/b.ts", "export function yardim() {}\n")
            write("web/dist/index-DnlIJ73T.js", "var OdemePaketi=1;\n")
            write("arac/x.py", "import yardimci\n# Gorev sutunu\nGorev = 'Gorev'\n\ndef calis():\n    pass\n\nif __name__ == '__main__':\n    calis()\n")
            write("arac/yardimci.py", "def topla():\n    pass\n")
            write("sql/1.sql", "CREATE TABLE odeme.OdemePaketi (Id int);\nCREATE TABLE k.Gorev (Id int);\n"
                               "CREATE TABLE k.Bekleyen (Id int);\nCREATE TABLE k.Olu (Id int);\n")
            write("c/CMakeLists.txt", "include_directories(${CMAKE_CURRENT_SOURCE_DIR}/ortak)\n")
            for h in ("c/include/arac.h", "c/include/cift.h", "c/ortak/cift.h", "c/ortak/kayit.h", "c/surucu/yerel.h"):
                write(h, "struct bos { int x; };\n")
            write("c/surucu/a.c", '#include "kayit.h"\n#include "yerel.h"\n#include <arac.h>\n#include <stdio.h>\n'
                                  '#include "yok.h"\n#include "cift.h"\nint main(void) {\n}\n')
            write("c/makro.c", "TANIMLA_ISLEYICI(ac)\n")
            write("c/cekirdek/giris.c", "void kernel_main(void) {\n}\nint main(int argc);\n")
            write("rsk/Cargo.toml", '[package]\nname = "rsk"\n'); write("rsk/src/lib.rs", "mod depo;\nmod arac;\n")
            write("rsk/src/depo/mod.rs", "pub struct DepoKaydi;\n")
            write("rsk/src/arac/mod.rs", "// DepoKaydi\nfn f() { let x = super::depo::DepoKaydi; }\n")
            subprocess.run(["git", "-C", d, "add", "-A"], check=True, capture_output=True)
            cfg, src, _ = load_config(d, None)
            r = build(d, cfg, 5)
            E = {(e["from"], e["to"]): e for e in r["edges"]}
            check("uctan uca: TS goreli import [K]", E[("web/src", "web/src/ortak")]["tier"] == "K")
            check("uctan uca: C# proje basvurusu [K]", E[("api", "cekirdek")]["tier"] == "K")
            check("uctan uca: tek dosya ciftli [H] bag zayif", E[("yan", "cekirdek")]["tier"] == "H" and E[("yan", "cekirdek")]["weak"])
            check("uctan uca: paketlenmis dosya dislanir ve raporlanir", "web/dist/index-DnlIJ73T.js" in sum(r["excluded"].values(), []))
            t = r["stores"]["by_table"]
            check("uctan uca: yazan ve okuyan ayri",
                  t["OdemePaketi"]["written_by"] == ["cekirdek/Odeme.cs"] and t["OdemePaketi"]["read_by"] == ["cekirdek/Rapor.cs"])
            check("uctan uca: sutun basligi tablo anmasi degil", t["Gorev"]["written_by"] == [] and t["Gorev"]["read_by"] == [])
            check("uctan uca: tirnakli ad ayri sinif", t["Bekleyen"]["quoted_in"] == ["cekirdek/Rapor.cs"])
            check("uctan uca: hic gecmeyen tablo", r["stores"]["unmentioned"] == ["Olu"])
            check("uctan uca: uclar iskelette satir numarali",
                  {"line": 2, "depth": 0, "kind": "uc", "name": "POST /api/odeme/onay"} in r["outline"]["api/Program.cs"]["marks"])
            check("uctan uca: [K] dongusu yok, zayif bag donguye girmez", r["cycles"] == [] and r["cycle_candidates"] == [])
            check("uctan uca: kor nokta DI kaydini sayar", r["blind_spots"]["bagimlilik enjeksiyonu"]["hits"] == 1)
            C = r["c"]
            check("uctan uca: C include [K] (yan dizin, CMake koku, 'include' koku)",
                  E.get(("c/surucu", "c/ortak"), {}).get("tier") == "K" and E.get(("c/surucu", "c/include"), {}).get("tier") == "K"
                  and C["includes"]["K"] == 3)
            check("uctan uca: C include kokleri kaynagiyla", {x["root"]: x["source"] for x in C["roots"]}
                  == {"c/ortak": "c/CMakeLists.txt", "c/include": "'include' adli dizin"})
            check("uctan uca: C belirsiz, cozulemeyen, dis ayri sayilir",
                  (C["includes"]["belirsiz"], C["includes"]["cozulemeyen"], C["includes"]["dis"]) == (1, 1, 1))
            check("uctan uca: C iskeletsiz dosya sayilir", C["no_outline"] == ["c/makro.c"])
            check("Rust: mod [K] bag; yorumdaki ve yol nitelikli ad [H] bag kurmaz", E.get(("rsk/src", "rsk/src/depo"), {}).get("tier") == "K"
                  and ("rsk/src/arac", "rsk/src/depo") not in E and r["rust"]["crates"] == ["rsk"] and "Rust `mod` / `use`" in render(r, 20, src, cfg))
            fn = lambda rr: [(x["path"], x["line"], x["source"]) for x in rr["entry"]["functions"]]  # noqa: E731
            r_ep = build(d, dict(cfg, entry_points=["kernel_main", "yok_islev"]), 5)
            check("giris: C main kalipla, prototip sayilmaz; diger ad yalniz config'ten, bulunamayan yazilir",
                  fn(r) == [("c/surucu/a.c", 7, "main")] and r["entry"]["missing"] == []
                  and fn(r_ep) == [("c/surucu/a.c", 7, "main"), ("c/cekirdek/giris.c", 1, "config")]
                  and r_ep["entry"]["missing"] == ["yok_islev"] and "bulunamayan: yok_islev" in render(r_ep, 20, src, cfg))
            check("giris: config'teki 'main' kalip kuralina gider, bulunamayan diye yazilmaz",
                  build(d, dict(cfg, entry_points=["main"]), 5)["entry"]["missing"] == [])
            r_ep["entry"]["functions"] = r_ep["entry"]["functions"] * 7
            check("giris: 12'den uzun liste kesildigini ve kalanin sayisini soyler", "ve 2 tane daha (`yapi.json`)" in render(r_ep, 20, src, cfg))
            r_ep["rust"]["uses"]["ornek"] = ["a.rs: use crate::yok"]
            check("Rust: cozulemeyenler ornekleriyle yazilir", "Cozulemeyen ornekleri: `a.rs: use crate::yok`" in render(r_ep, 20, src, cfg))
            write("api/App.Tests/T.cs", 'app.MapGet("/t", x);\n')
            subprocess.run(["git", "-C", d, "add", "-A"], check=True, capture_output=True)
            r_t = build(d, cfg, 5)
            check("giris: test projesindeki HTTP ucu ayri sayilir", (r_t["entry"]["route_count"], r_t["entry"]["route_test"]) == (3, 1)
                  and "(1 tanesi test dosyalarinda)" in render(r_t, 20, src, cfg))
            subprocess.run(["git", "-C", d, "rm", "-q", "-f", "api/App.Tests/T.cs"], check=True, capture_output=True)
            md = render(r, 20, src, cfg)
            check("uctan uca: rapor C include sayilarini yazar", "belirsiz** (birden cok" in md and "cozulemeyen tirnakli" in md)
            check("uctan uca: rapor zayif bagi cizmez ama listeler",
                  "-.->" not in md and "Zayif baglar" in md and "Olcume girmeyenler" in md and "Kor noktalar" in md)
            probe = {"sonda": "di", "commit": "abc", "tier": "K", "oz_test": "3/3", "kontrol": "var",
                     "edges": [{"from": "api/Program.cs", "to": "kanal/Klasor.cs"}, {"from": "api/Program.cs", "to": "yok/Dosya.cs"}]}
            r2 = build(d, cfg, 5, [probe])
            E2 = {(e["from"], e["to"]): e for e in r2["edges"]}
            check("uctan uca: [K] sonda kesik oku duz oka cevirir", E2[("api", "kanal")]["tier"] == "K" and ("api", "kanal") in E
                  and E[("api", "kanal")]["tier"] == "H")
            check("uctan uca: sondanin bilinmeyen dosyasi gorunur", r2["probes"][0]["unknown_count"] == 1)
            write("akis/yuk.spath", "CALL OdemeServisi\nservices.AddScoped<IKanal, KlasorKanali>();\nif __name__ == '__main__':\n")
            subprocess.run(["git", "-C", d, "add", "-A"], check=True, capture_output=True)
            pr2 = dict(probe, edges=[{"from": "api/Program.cs", "to": "akis/yuk.spath"}])
            cfg_ek = dict(cfg, extra_sources={".spath": "S-Path"})
            r3, r4 = build(d, cfg_ek, 5, [pr2]), build(d, cfg, 5, [pr2])
            E3 = {(e["from"], e["to"]): e for e in r3["edges"]}
            check("extra_sources: sonda ucu olur, modul kutusuna girer", r3["probes"][0]["unknown_count"] == 0
                  and E3[("api", "akis")]["tier"] == "K" and r3["modules"]["akis"]["files"] == 1 and r4["probes"][0]["unknown_count"] == 0)
            write("KOK.txt", "x\n"); subprocess.run(["git", "-C", d, "add", "-A"], check=True, capture_output=True)
            pr3 = dict(probe, edges=pr2["edges"] + [{"from": "api/Program.cs", "to": "web/dist/index-DnlIJ73T.js"},
                                                    {"from": "api/Program.cs", "to": "KOK.txt"}])
            p4 = build(d, cfg, 5, [pr3])
            E4 = {(e["from"], e["to"]): e for e in p4["edges"]}
            check("sonda ucu: var olan kaynak disi dosya kabul ve kutuda gorunur; dislanan reddedilir",
                  p4["probes"][0]["outside_count"] == 2 and E4.get(("api", "akis"), {}).get("tier") == "K"
                  and p4["modules"]["akis"] == {"files": 0, "lines": 0, "kaynak_disi": 1} and p4["probes"][0]["excluded_count"] == 1
                  and 'satir · 1 kaynak disi"]' in render(p4, 20, src, cfg) and '["(kok dizin)<br/>' in render(p4, 20, src, cfg))
            check("extra_sources: ayristirilmaz (giris, ad bagi, kor nokta yok)", ("akis", "cekirdek") not in E3
                  and "akis/yuk.spath" not in r3["entry"]["mains"]
                  and r3["blind_spots"]["bagimlilik enjeksiyonu"]["hits"] == 1)
        except (OSError, subprocess.CalledProcessError) as e:
            check(f"uctan uca: git calistirilamadi ({e})", False)
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--repo", default=".")
    p.add_argument("--config", help="rontgen.config.json (verilmezse depo kokunde aranir)")
    p.add_argument("--out", help="yapi.md ve yapi.json buraya yazilir; verilmezse ekrana")
    p.add_argument("--edges", type=int, default=40, help="semada cizilecek en guclu bag sayisi")
    p.add_argument("--top", type=int, default=8)
    p.add_argument("--lang", help="rapor dili: tr-ascii (varsayilan), tr, en; verilmezse config'teki report_lang")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    cfg, sources, errors = load_config(a.repo, a.config)
    probes, perr = ([], []) if errors else load_probes(a.repo, cfg)
    if errors or perr:
        print("\n".join("olculmedi: " + e for e in errors + perr)); return 2
    try:
        r = build(a.repo, cfg, a.top, probes)
    except RuntimeError as e:
        print(f"olculmedi: git ({e})"); return 2
    if not r["modules"]:
        print("olculmedi: taninan kaynak dosyasi yok"); return 2
    md = render(r, a.edges, sources, cfg)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        with io.open(os.path.join(a.out, "yapi.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(r, f, ensure_ascii=False, indent=2); f.write("\n")
        with io.open(os.path.join(a.out, "yapi.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(dil.cevir(md, a.lang or cfg.get("report_lang", "tr-ascii")))
        print(f"yazildi: {os.path.join(a.out, 'yapi.md')} ve yapi.json")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
