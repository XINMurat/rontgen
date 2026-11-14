#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- package manifests: what each package declares it depends on,
which of those are in the repository, and which are switched on by a feature.

WHY THIS EXISTS
---------------
On a large repository five runs never found that a "frontend-agnostic" layer
was tied to the terminal. No source file imported the terminal library by a
path the core resolves; the tie was in the package manifest: an optional
dependency behind a feature (`term = ["termina", "crossterm"]`). Imports show
what the code uses; manifests show what the build is allowed to use, and
which layer was meant to stay free of what. This script reads them.

Read, never executed: Cargo.toml, package.json, *.csproj / *.fsproj /
*.vbproj, pyproject.toml, requirements*.txt, go.mod, pom.xml,
build.gradle(.kts). A manifest that cannot be parsed is listed as such.

OUTPUT
------
  paket.md / paket.json   per package: name, ecosystem, internal
                          dependencies (another package of this repository),
                          external ones, and those that are optional, behind a
                          feature, or for tests / builds only. All are [K]:
                          declared, not inferred.

USAGE
-----
    python paket.py --repo . --out rontgen-out
    python paket.py --self-test
Exit codes: 0 written / tests pass · 1 a test failed · 2 nothing to read
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ortak import list_files  # noqa: E402

KINDS = ("normal", "dev", "build", "peer", "optional")
NAMES = re.compile(r"(?:^|/)(Cargo\.toml|package\.json|pyproject\.toml|go\.mod|pom\.xml|build\.gradle(?:\.kts)?"
                   r"|requirements[^/]*\.txt|[^/]+\.(?:cs|fs|vb)proj)$")
REQ = re.compile(r"^\s*([A-Za-z0-9_.\-]+)")


def dep(name, kind="normal", local=None, feature=None, target=None):
    return {"name": name, "kind": kind, "local": local, "feature": feature, "target": target}


def cargo(text):
    t = tomllib.loads(text)
    out, feats = [], {}
    tables = [("dependencies", "normal"), ("dev-dependencies", "dev"), ("build-dependencies", "build")]
    for scope, tt in [("", t)] + [(k, v) for k, v in (t.get("target") or {}).items()]:
        for key, kind in tables:
            for n, v in (tt.get(key) or {}).items():
                v = v if isinstance(v, dict) else {}
                local = v.get("path")   # `workspace = true` inherits a version, it does not make a crate internal
                out.append(dep(n, "optional" if v.get("optional") and kind == "normal" else kind, local, None, scope or None))
    for f, members in (t.get("features") or {}).items():
        feats[f] = [m.split("/")[0].removeprefix("dep:") for m in members]
    name = (t.get("package") or {}).get("name") or ("(workspace)" if "workspace" in t else None)
    members = ((t.get("workspace") or {}).get("members")) or []
    return name, out, feats, members


def npm(text):
    t = json.loads(text)
    out = []
    for key, kind in (("dependencies", "normal"), ("devDependencies", "dev"), ("peerDependencies", "peer"),
                      ("optionalDependencies", "optional")):
        for n, v in (t.get(key) or {}).items():
            v = str(v)
            out.append(dep(n, kind, v if v.startswith(("workspace:", "file:", "link:")) else None))
    ws = t.get("workspaces") or []
    return t.get("name"), out, {}, ws.get("packages", []) if isinstance(ws, dict) else ws


def dotnet(text):
    root = ET.fromstring(text)
    out = []
    for el in root.iter():
        tag = el.tag.split("}")[-1]
        inc = el.get("Include")
        if tag == "PackageReference" and inc:
            out.append(dep(inc, "dev" if (el.get("PrivateAssets") or "").lower() == "all" else "normal"))
        elif tag == "ProjectReference" and inc:
            out.append(dep(os.path.splitext(os.path.basename(inc.replace("\\", "/")))[0], "normal", inc.replace("\\", "/")))
    return None, out, {}, []


def pyproject(text):
    t = tomllib.loads(text)
    p, out, feats = t.get("project") or {}, [], {}
    for r in p.get("dependencies") or []:
        m = REQ.match(r)
        if m:
            out.append(dep(m.group(1)))
    for f, rs in (p.get("optional-dependencies") or {}).items():
        names = [REQ.match(r).group(1) for r in rs if REQ.match(r)]
        feats[f] = names
        out += [dep(n, "optional", None, f) for n in names]
    poetry = ((t.get("tool") or {}).get("poetry") or {})
    for n, v in (poetry.get("dependencies") or {}).items():
        if n.lower() != "python":
            out.append(dep(n, "optional" if isinstance(v, dict) and v.get("optional") else "normal",
                           v.get("path") if isinstance(v, dict) else None))
    return p.get("name") or poetry.get("name"), out, feats, []


def requirements(text):
    out = []
    for line in text.splitlines():
        s = line.split("#")[0].strip()
        if not s or s.startswith("-"):
            out.append(dep(s.split()[-1], "normal", s.split()[-1])) if s.startswith(("-e ", "--editable")) else None
            continue
        m = REQ.match(s)
        if m:
            out.append(dep(m.group(1)))
    return None, out, {}, []


def gomod(text):
    name, out, local = None, [], {}
    block = False
    for line in text.splitlines():
        s = line.split("//")[0].strip()
        if s.startswith("module "):
            name = s.split()[1]
        elif s.startswith("replace ") and "=>" in s:
            a, b = s[8:].split("=>")
            if b.strip().startswith((".", "/")):
                local[a.split()[0]] = b.strip().split()[0]
        elif s == "require (":
            block = True
        elif s == ")":
            block = False
        elif block or s.startswith("require "):
            parts = s.removeprefix("require ").split()
            if parts:
                out.append(dep(parts[0], "normal" if "// indirect" not in line else "dev"))
    for d in out:
        d["local"] = local.get(d["name"])
    return name, out, {}, []


def maven(text):
    root = ET.fromstring(re.sub(r'\sxmlns="[^"]+"', "", text, count=1))
    out = []
    for d in root.findall("./dependencies/dependency"):
        scope = (d.findtext("scope") or "compile").strip()
        n = f"{(d.findtext('groupId') or '').strip()}:{(d.findtext('artifactId') or '').strip()}"
        out.append(dep(n, {"test": "dev", "provided": "peer"}.get(scope, "optional" if d.findtext("optional") == "true" else "normal")))
    mods = [m.text.strip() for m in root.findall("./modules/module") if m.text]
    return (root.findtext("artifactId") or "").strip() or None, out, {}, mods


GRADLE = re.compile(r"\b(implementation|api|compileOnly|runtimeOnly|testImplementation|kapt|annotationProcessor)\s*\(?\s*"
                    r"(?:project\(\s*[\"']:?([^\"']+)[\"']\s*\)|[\"']([^\"']+)[\"'])")


def gradle(text):
    out = []
    for conf, proj, coord in GRADLE.findall(text):
        kind = "dev" if conf.startswith("test") else "build" if conf in ("kapt", "annotationProcessor", "compileOnly") else "normal"
        out.append(dep(proj or ":".join(coord.split(":")[:2]), kind, f":{proj}" if proj else None))
    return None, out, {}, []


PARSERS = {"Cargo.toml": ("rust", cargo), "package.json": ("npm", npm), "pyproject.toml": ("python", pyproject),
           "go.mod": ("go", gomod), "pom.xml": ("maven", maven), "build.gradle": ("gradle", gradle),
           "build.gradle.kts": ("gradle", gradle)}


def parser_for(path):
    base = os.path.basename(path)
    if base in PARSERS:
        return PARSERS[base]
    if base.startswith("requirements") and base.endswith(".txt"):
        return ("python", requirements)
    if base.endswith(("proj",)):
        return ("dotnet", dotnet)
    return None


def collect(repo: str):
    paths = [p for p in list_files(repo)[0] if NAMES.search(p) and "node_modules/" not in p]
    pkgs, errors = [], []
    for p in sorted(paths):
        eco, fn = parser_for(p)
        try:
            with io.open(os.path.join(repo, p), encoding="utf-8", errors="replace") as f:
                name, deps, feats, members = fn(f.read())
        except (ValueError, ET.ParseError, tomllib.TOMLDecodeError, AttributeError, IndexError) as e:
            errors.append(f"{p}: okunamadi ({type(e).__name__})")
            continue
        d = os.path.dirname(p)
        pkgs.append({"path": p, "dir": d, "ecosystem": eco, "name": name or os.path.basename(d) or os.path.basename(p),
                     "deps": deps, "features": feats, "members": members})
    names = {x["name"] for x in pkgs} | {os.path.basename(x["dir"]) for x in pkgs if x["dir"]}
    for x in pkgs:
        for d in x["deps"]:
            d["internal"] = bool(d["local"]) or d["name"] in names
        gated = {m for ms in x["features"].values() for m in ms}
        for d in x["deps"]:
            if d["kind"] == "optional" and not d["feature"]:
                d["feature"] = ", ".join(sorted(f for f, ms in x["features"].items() if d["name"] in ms)) or None
            elif d["name"] in gated and not d["feature"]:
                d["feature"] = ", ".join(sorted(f for f, ms in x["features"].items() if d["name"] in ms))
    return {"packages": pkgs, "errors": errors}


def render(r, repo_name):
    pk = [x for x in r["packages"] if x["deps"] or x["features"]]
    o = [f"# Paket bildirimleri — {repo_name}", "",
         "Kaynak: paket dosyalari (okunur, calistirilmaz). Hepsi `[K]`: beyan, cikarim degil. Ic = bu depodaki baska bir paket.", ""]
    if not r["packages"]:
        o += ["Taninan paket dosyasi yok: **olculmedi**.", ""]
    o += [f"- Okunamayan: {e}" for e in r["errors"]] + ([""] if r["errors"] else [])
    o += ["| Paket | Ekosistem | Ic bagimliliklar | Dis | Yalniz test/derleme ic | Ozellige bagli / istege bagli |", "|---|---|---|---|---|---|"]
    for x in pk:
        internal = sorted({d["name"] for d in x["deps"] if d["internal"] and d["kind"] in ("normal", "optional", "peer")})
        devint = sorted({d["name"] for d in x["deps"] if d["internal"] and d["kind"] in ("dev", "build")})
        ext = len({d["name"] for d in x["deps"] if not d["internal"]})
        gated = sorted({f"{d['name']} ({d['feature']})" if d["feature"] else d["name"]
                        for d in x["deps"] if d["kind"] == "optional" or d["feature"]})
        o.append(f"| `{x['name']}` `{x['path']}` | {x['ecosystem']} | {', '.join(internal) or '-'} | {ext} | "
                 f"{', '.join(devint) or '-'} | {', '.join(gated[:8]) + (' …' if len(gated) > 8 else '') or '-'} |")
    o += ["", "Okurken: bir katmanin **ozellige bagli** dis bagimliliklari, o katmanin neye bagli kalmamasi gerektigini ya da "
          "fiilen neye bagli oldugunu gosterir; **yalniz test** ic bagimliliklari kodda gorunmeyen katman iliskileridir. "
          "Ikisi de import'tan cikmaz.", ""]
    return "\n".join(o) + "\n"


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as d:
        def w(rel, text):
            os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        w("Cargo.toml", '[workspace]\nmembers = ["core", "view"]\n')
        w("core/Cargo.toml", '[package]\nname = "core"\n[dependencies]\nropey = "1"\n')
        w("view/Cargo.toml", '[package]\nname = "view"\n[features]\nterm = ["crossterm", "dep:termina"]\n'
          '[dependencies]\ncore = { path = "../core" }\ntermina = { version = "1", optional = true }\n'
          '[target.\'cfg(windows)\'.dependencies]\ncrossterm = { version = "0.28", optional = true }\n'
          '[dev-dependencies]\ntui = { path = "../tui" }\nropey = { workspace = true }\n')
        w("web/package.json", json.dumps({"name": "web", "dependencies": {"core-js": "workspace:*", "react": "18"},
                                          "devDependencies": {"jest": "29"}}))
        w("api/Api.csproj", '<Project><ItemGroup><PackageReference Include="Dapper" Version="2" />'
          '<ProjectReference Include="..\\Lib\\Lib.csproj" /></ItemGroup></Project>')
        w("py/pyproject.toml", '[project]\nname = "svc"\ndependencies = ["requests>=2"]\n[project.optional-dependencies]\npg = ["psycopg"]\n')
        w("go/go.mod", "module ex.com/a\nrequire (\n  ex.com/b v1.0.0\n  golang.org/x/text v0.3.0 // indirect\n)\nreplace ex.com/b => ../b\n")
        w("j/pom.xml", '<project xmlns="http://maven.apache.org/POM/4.0.0"><artifactId>app</artifactId><dependencies>'
          '<dependency><groupId>junit</groupId><artifactId>junit</artifactId><scope>test</scope></dependency>'
          '</dependencies></project>')
        w("k/build.gradle.kts", 'dependencies {\n implementation(project(":core"))\n testImplementation("junit:junit:4.13")\n}\n')
        w("bad/Cargo.toml", "[package\nname=")
        r = collect(d)
        by = {x["path"]: x for x in r["packages"]}
        v = {x["name"]: x for x in by["view/Cargo.toml"]["deps"]}
        check("cargo: yol bagimliligi ic, istege bagli dis ozellik adiyla", v["core"]["internal"] and v["termina"]["kind"] == "optional"
              and v["termina"]["feature"] == "term" and not v["termina"]["internal"])
        check("cargo: hedefe ozgu tablo da okunur, ozellige baglanir", v["crossterm"]["feature"] == "term")
        check("cargo: yalniz test ic bagimliligi ayri tur; workspace = true ic yapmaz", v["tui"]["kind"] == "dev" and v["tui"]["internal"]
              and not v["ropey"]["internal"])
        n = {x["name"]: x for x in by["web/package.json"]["deps"]}
        check("npm: workspace: ic, dev ayri", n["core-js"]["internal"] and n["jest"]["kind"] == "dev" and not n["react"]["internal"])
        c = {x["name"]: x for x in by["api/Api.csproj"]["deps"]}
        check("dotnet: ProjectReference ic, PackageReference dis", c["Lib"]["internal"] and not c["Dapper"]["internal"])
        p = {x["name"]: x for x in by["py/pyproject.toml"]["deps"]}
        check("python: istege bagli grup ozellik olur", p["psycopg"]["feature"] == "pg" and p["requests"]["kind"] == "normal")
        g = {x["name"]: x for x in by["go/go.mod"]["deps"]}
        check("go: replace ile yerel ic; indirect ayri", g["ex.com/b"]["internal"] and g["golang.org/x/text"]["kind"] == "dev")
        m = by["j/pom.xml"]["deps"]
        check("maven: test kapsamli dev", m and m[0]["name"] == "junit:junit" and m[0]["kind"] == "dev")
        k = {x["name"]: x for x in by["k/build.gradle.kts"]["deps"]}
        check("gradle: project() ic, testImplementation dev", k["core"]["internal"] and k["junit:junit"]["kind"] == "dev")
        check("bozuk bildirim: hata satiri, cokmez", any("bad/Cargo.toml" in e for e in r["errors"]))
        md = render(r, "x")
        check("rapor: ozellige bagli ve yalniz test sutunlari", "termina (term)" in md and "| tui |" in md.replace("`", "")
              or ("tui" in md and "termina (term)" in md))
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--repo", default=".")
    ap.add_argument("--out", default="rontgen-out")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    r = collect(a.repo)
    os.makedirs(a.out, exist_ok=True)
    with io.open(os.path.join(a.out, "paket.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(r, f, ensure_ascii=False, indent=2); f.write("\n")
    with io.open(os.path.join(a.out, "paket.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write(render(r, os.path.basename(os.path.abspath(a.repo))))
    print(f"yazildi: {os.path.join(a.out, 'paket.md')} — {len(r['packages'])} paket, {len(r['errors'])} okunamayan")
    return 0 if r["packages"] else 2


if __name__ == "__main__":
    sys.exit(main())
