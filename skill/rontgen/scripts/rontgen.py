#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- the measuring rig: what is in this repository, where the risk
sits, and where a newcomer should start reading.

WHY THIS EXISTS
---------------
"Is this codebase understandable?" is usually answered by whoever read the
most of it, from memory. This script answers the part that can be counted,
from two sources that cannot flatter anyone: the files as they are and the git
history as it happened. Everything it prints carries a tier:

  [K]  counted directly (lines, commits, files changed together, a coverage
       report the project produced itself)
  [H]  a proxy that is usually right and can be wrong (nesting depth from
       indentation, "this is a test file" from its path)

It does not judge design, naming or correctness. Those need a reader; this
tells the reader where to look first and how much there is.

WHAT IT MEASURES
----------------
  inventory     files and lines per language and per top-level directory;
                what was left out and why; what was not classified
  size          the largest source files, and how many lines run past a width
  depth         deepest indentation per file (a nesting proxy)
  churn         commits and changed lines per file
  hotspots      churn x size: files that are both big and often changed
  knowledge     how many people have touched each file; share of the top author
  coupling      pairs of files that keep changing in the same commit
  change shape  files and lines per commit: can the history be reviewed at all
  tests         a coverage report if the project has one (config:
                coverage_reports, Cobertura XML or lcov) [K]; otherwise test
                lines against source lines and source files whose name no
                test file's name contains [H]

NO SILENT DEFAULTS
------------------
Thresholds come from the config and are printed with their source. Excluded
files are listed with the reason. An extension the script does not know is
shown as "siniflanmadi", not as zero lines of code.

USAGE
-----
    python rontgen.py --repo . --out rontgen-out
    python rontgen.py --repo . --config rontgen.config.json --since 2026-01-01
    python rontgen.py --self-test

Without git the files are read from the directory (build and hidden directories
are not entered, and are listed); every history section says "olculmedi", never 0.

Exit codes: 0 measured · 2 could not measure (no source, bad config, git failed)
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
from itertools import combinations

from ortak import excluded_lines, source_map, ext, git, has_history, is_test, load_config, read_sources, thresholds_line

COUPLING_MAX_FILES = 30


def depth_of(lines) -> int:
    """Deepest indentation in units of 4 columns (tab = 4). A proxy, not a parse."""
    deepest = 0
    for ln in lines:
        if not ln.strip():
            continue
        lead = len(ln) - len(ln.lstrip(" \t"))
        deepest = max(deepest, sum(4 if c == "\t" else 1 for c in ln[:lead]) // 4)
    return deepest


def pct(values, q: float):
    if not values:
        return None
    v = sorted(values)
    return v[min(len(v) - 1, int(round(q * (len(v) - 1))))]


def inline_tests(path: str, lines) -> int:
    """Rust keeps unit tests inside the source file: lines from the first `#[cfg(test)]` to the end. [H]: the
    module is usually last, not always."""
    if not path.endswith(".rs"):
        return 0
    at = next((i for i, x in enumerate(lines) if x.strip().startswith("#[cfg(test)]")), None)
    return 0 if at is None else len(lines) - at


def measure_files(texts: dict, width: int, langs: dict) -> dict:
    files = {}
    for p, text in texts.items():
        lines = text.splitlines()
        files[p] = {"lang": langs[ext(p)], "lines": len(lines), "long": sum(1 for x in lines if len(x) > width),
                    "depth": depth_of(lines), "test": is_test(p), "inline_test": inline_tests(p, lines)}
    return files


def measure_history(repo: str, since, tracked):
    """-> per-file churn/authors, per-commit shape, coupling pairs."""
    args = ["log", "--no-merges", "--numstat", "--format=%x01%H%x02%ae%x02%ad", "--date=short"]
    if since:
        args.append(f"--since={since}")
    churn = defaultdict(lambda: {"commits": 0, "changed": 0, "authors": Counter()})
    shape, authors, pairs, dates = [], Counter(), Counter(), []
    for block in git(repo, *args).split("\x01")[1:]:
        head, _, body = block.partition("\n")
        parts = head.split("\x02")
        if len(parts) < 3:
            continue
        author, date = parts[1], parts[2].strip()
        touched, total = [], 0
        for row in body.splitlines():
            c = row.split("\t")
            if len(c) != 3 or not c[0].isdigit() or not c[1].isdigit():
                continue
            path, n = c[2], int(c[0]) + int(c[1])
            if path not in tracked:          # deleted, renamed away, excluded or not source
                continue
            total += n
            touched.append(path)
            ch = churn[path]
            ch["commits"] += 1; ch["changed"] += n; ch["authors"][author] += 1
        authors[author] += 1
        dates.append(date)
        shape.append({"files": len(touched), "lines": total})
        if 2 <= len(touched) <= COUPLING_MAX_FILES:
            pairs.update(combinations(sorted(touched), 2))
    return churn, shape, authors, pairs, dates


def read_coverage(repo: str, reports) -> dict:
    """Cobertura XML or lcov -> {"reports": [...], "files": {path: rate}, "errors": [...]}. No report configured = None."""
    if not reports:
        return None
    out = {"reports": [], "files": {}, "errors": []}
    for rel in reports:
        try:
            with io.open(os.path.join(repo, rel), encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError as e:
            out["errors"].append(f"{rel}: okunamadi ({e})")
            continue
        found = {}
        if "<coverage" in text[:2000]:
            for name, rate in re.findall(r'<class\b[^>]*\bfilename="([^"]+)"[^>]*\bline-rate="([0-9.]+)"', text):
                found[name.replace("\\", "/")] = min(found.get(name.replace("\\", "/"), 1.0), float(rate))
        else:
            name, lf = None, None
            for line in text.splitlines():
                if line.startswith("SF:"):
                    name, lf = line[3:].replace("\\", "/"), None
                elif line.startswith("LF:"):
                    lf = int(line[3:] or 0)
                elif line.startswith("LH:") and name and lf:
                    found[name] = int(line[3:] or 0) / lf
        if not found:
            out["errors"].append(f"{rel}: taninan bicimde degil ya da bos (Cobertura XML / lcov bekleniyor)")
            continue
        out["reports"].append(rel)
        out["files"].update(found)
    return out


def build(repo: str, since, top: int, cfg: dict) -> dict:
    texts, excluded, unclassified = read_sources(repo, cfg)
    files = measure_files(texts, cfg["max_line_length"], source_map(cfg))
    hist = has_history(repo)
    churn, shape, authors, pairs, dates = (measure_history(repo, since, set(files)) if hist
                                           else ({}, [], Counter(), Counter(), []))
    src = {p: m for p, m in files.items() if not m["test"]}
    tst = {p: m for p, m in files.items() if m["test"]}

    by_lang = defaultdict(lambda: {"files": 0, "lines": 0})
    by_dir = defaultdict(lambda: {"files": 0, "lines": 0})
    for p, m in files.items():
        by_lang[m["lang"]]["files"] += 1; by_lang[m["lang"]]["lines"] += m["lines"]
        d = p.split("/")[0] if "/" in p else "."
        by_dir[d]["files"] += 1; by_dir[d]["lines"] += m["lines"]

    def row(p):
        m, ch, z = files[p], churn.get(p), (0 if hist else None)
        return {"path": p, "lines": m["lines"], "depth": m["depth"], "long": m["long"],
                "commits": ch["commits"] if ch else z, "changed": ch["changed"] if ch else z,
                "people": len(ch["authors"]) if ch else z}

    largest = sorted(src, key=lambda p: -src[p]["lines"])[:top]
    hot = sorted((p for p in src if p in churn), key=lambda p: -(churn[p]["commits"] * src[p]["lines"]))[:top]
    deepest = sorted(src, key=lambda p: (-src[p]["depth"], -src[p]["lines"]))[:top]
    solo = [p for p in src if p in churn and len(churn[p]["authors"]) == 1]
    coupled = [{"a": a, "b": b, "together": n,
                "share": round(n / max(1, min(churn[a]["commits"], churn[b]["commits"])), 2)}
               for (a, b), n in pairs.most_common(top * 4) if n >= 3][:top]

    # A source file counts as "named by a test" when its stem occurs in some
    # test file's name (Odeme.cs <-> OdemeTestleri.cs, a.ts <-> a.test.ts).
    test_names = " ".join(os.path.basename(p).lower() for p in tst)
    unnamed = sorted(((p, m["lines"]) for p, m in src.items()
                      if m["lines"] >= 100 and os.path.splitext(os.path.basename(p))[0].lower() not in test_names),
                     key=lambda x: -x[1])
    cov = read_coverage(repo, cfg["coverage_reports"])
    if cov and cov["files"]:
        # report paths are rarely repo-relative: match on the longest shared path tail
        matched = {}
        for name, rate in cov["files"].items():
            hits = [p for p in src if p.endswith(name) or name.endswith(p)]
            if len(hits) == 1:
                matched[hits[0]] = rate
        cov["matched"] = len(matched)
        cov["unmatched"] = len(cov["files"]) - len(matched)
        cov["line_rate"] = round(sum(matched[p] * src[p]["lines"] for p in matched) / max(1, sum(src[p]["lines"] for p in matched)), 3)
        cov["lowest"] = [{"path": p, "rate": round(r_, 2), "lines": src[p]["lines"]}
                         for p, r_ in sorted(matched.items(), key=lambda x: (x[1], -src[x[0]]["lines"]))[:top]]
        cov["not_in_report"] = sum(1 for p in src if p not in matched)
        del cov["files"]

    commit_lines = [s["lines"] for s in shape if s["files"]]
    commit_files = [s["files"] for s in shape if s["files"]]
    n_commits = sum(authors.values())
    return {
        "repo": os.path.abspath(repo), "since": since, "history": hist,
        "thresholds": {k: cfg[k] for k in ("max_file_lines", "max_line_length", "max_commit_lines")},
        "classified_as_source": sorted(set(ext(p) for p in files)),
        "extra_sources": {e: sum(1 for p in files if ext(p) == e) for e in sorted(cfg["extra_sources"])},
        "unclassified_extensions": dict(unclassified.most_common()),
        "excluded": {k: sorted(v) for k, v in excluded.items()},
        "inventory": {"source_files": len(src), "source_lines": sum(m["lines"] for m in src.values()),
                      "test_files": len(tst), "test_lines": sum(m["lines"] for m in tst.values()),
                      "by_language": dict(sorted(by_lang.items(), key=lambda x: -x[1]["lines"])),
                      "by_directory": dict(sorted(by_dir.items(), key=lambda x: -x[1]["lines"]))},
        "size": {"median_lines": pct([m["lines"] for m in src.values()], 0.5),
                 "p90_lines": pct([m["lines"] for m in src.values()], 0.9),
                 "files_over_budget": sum(1 for m in src.values() if m["lines"] > cfg["max_file_lines"]),
                 "lines_over_width": sum(m["long"] for m in src.values()),
                 "largest": [row(p) for p in largest]},
        "depth": {"deepest": [row(p) for p in deepest]},
        "hotspots": [row(p) for p in hot] if hist else None,
        "knowledge": {"commits": n_commits, "people": len(authors),
                      "top_author_share": round(max(authors.values()) / n_commits, 2) if n_commits else None,
                      "source_files_with_history": sum(1 for p in src if p in churn),
                      "touched_by_one_person": len(solo),
                      "first_commit": min(dates) if dates else None, "last_commit": max(dates) if dates else None} if hist else None,
        "coupling": coupled if hist else None,
        "change_shape": {"commits_touching_source": len(commit_lines),
                         "median_lines": pct(commit_lines, 0.5), "p90_lines": pct(commit_lines, 0.9),
                         "max_lines": max(commit_lines) if commit_lines else None,
                         "median_files": pct(commit_files, 0.5), "p90_files": pct(commit_files, 0.9),
                         "over_budget": sum(1 for n in commit_lines if n > cfg["max_commit_lines"])} if hist else None,
        "tests": {"inline_test_lines": sum(m["inline_test"] for m in src.values()),
                  "test_to_source_lines": round(sum(m["lines"] for m in tst.values()) / max(1, sum(m["lines"] for m in src.values())), 2),
                  "unnamed_by_tests_files": len(unnamed), "unnamed_by_tests_lines": sum(n for _, n in unnamed),
                  "largest_unnamed_by_tests": [{"path": p, "lines": n} for p, n in unnamed[:top]],
                  "coverage": cov},
        "files": {p: {"lines": m["lines"], "test": m["test"], "commits": churn[p]["commits"] if p in churn else (0 if hist else None)}
                  for p, m in sorted(files.items())},
    }


def render(r: dict, sources: dict, cfg: dict) -> str:
    o = []
    inv, size, th = r["inventory"], r["size"], r["thresholds"]

    def table(head, rows):
        o.append("| " + " | ".join(head) + " |"); o.append("|" + "---|" * len(head))
        o.extend("| " + " | ".join(str(c) for c in x) + " |" for x in rows)
        o.append("")

    o += [f"# Rontgen — {os.path.basename(r['repo'])}", "",
          "Katmanlar: `[K]` dogrudan sayildi · `[H]` vekil olcu (yanilabilir). Bu rapor tasarimi, adlandirmayi",
          "ya da dogrulugu yargilamaz; okuyana nereden baslayacagini ve ne kadar oldugunu soyler.", "",
          "- Esikler: " + thresholds_line(cfg, sources, ("max_file_lines", "max_line_length", "max_commit_lines")), "",
          "## Envanter `[K]`", "",
          f"- Kaynak: **{inv['source_files']} dosya, {inv['source_lines']} satir** · test: {inv['test_files']} dosya, "
          f"{inv['test_lines']} satir (test dosyasi ayrimi yola gore `[H]`)",
          f"- Kaynak sayilan uzantilar: {', '.join(r['classified_as_source']) or '-'}",
          "- Config'le kaynak sayilan (`extra_sources`; sayilir, ayristirilmaz): "
          + (", ".join(f"{e} x{n}" for e, n in r["extra_sources"].items()) or "yok"),
          "- Siniflanmayan uzantilar (sifir sayilmadi, **olculmedi**): "
          + (", ".join(f"{k or '(uzantisiz)'} x{v}" for k, v in r["unclassified_extensions"].items()) or "yok"), "",
          "Olcume girmeyen kaynak dosyalari:", ""] + excluded_lines(r["excluded"]) + [""]
    table(["Dil", "Dosya", "Satir"], [(k, v["files"], v["lines"]) for k, v in inv["by_language"].items()])
    table(["Ust dizin", "Dosya", "Satir"], [(k, v["files"], v["lines"]) for k, v in list(inv["by_directory"].items())[:12]])

    o += ["## Boyut `[K]`", "",
          f"- Kaynak dosya basina medyan {size['median_lines']} satir, p90 {size['p90_lines']}; "
          f"**{th['max_file_lines']} satiri asan {size['files_over_budget']} dosya**; "
          f"{th['max_line_length']} karakteri asan {size['lines_over_width']} satir.", ""]
    na = lambda v: "—" if v is None else v  # noqa: E731  -- not measured is not zero
    if not r["history"]:
        o += ["Commit ve Kisi sutunlari **olculmedi: git gecmisi yok** (— sifir degildir).", ""]
    table(["Dosya", "Satir", "Uzun satir", "Derinlik [H]", "Commit", "Kisi"],
          [(x["path"], x["lines"], x["long"], x["depth"], na(x["commits"]), na(x["people"])) for x in size["largest"]])
    if not r["history"]:
        for t in ("Sicak noktalar", "Bilgi dagilimi", "Birlikte degisenler", "Degisiklik bicimi"):
            o += [f"## {t}", "", "**olculmedi: git gecmisi yok.** Bu bolum commit gecmisinden sayilir; gecmis olmadan sifir yazilmaz.", ""]
    else:
        render_history(r, o, table)
    render_tests(r, o, table)
    return "\n".join(o) + "\n"


def render_history(r: dict, o: list, table) -> None:
    kn, cs, th = r["knowledge"], r["change_shape"], r["thresholds"]
    o += ["## Sicak noktalar `[K]` — cok degisen VE buyuk", "",
          "Sira: commit sayisi x satir. Ust siralar hem en cok okunmasi gereken hem en pahali okunan dosyalardir.", ""]
    table(["Dosya", "Commit", "Degisen satir", "Satir", "Kisi"],
          [(x["path"], x["commits"], x["changed"], x["lines"], x["people"]) for x in r["hotspots"]] or [("-",) * 5])

    o += ["## Bilgi dagilimi `[K]`", "",
          f"- {kn['commits']} commit, {kn['people']} kisi ({kn['first_commit']} → {kn['last_commit']}); "
          f"en cok commit atan kisinin payi **{kn['top_author_share']}**.",
          f"- Gecmisi olan {kn['source_files_with_history']} kaynak dosyanin **{kn['touched_by_one_person']}** tanesine tek kisi dokunmus.",
          "- Yazar kimligi e-posta adresidir; ayni kisinin iki adresi iki kisi sayilir `[H]`.", ""]

    o += ["## Birlikte degisenler `[K]` — gorunmeyen baglar", "",
          "Ayni commit'te en az 3 kez birlikte degisen ciftler. Pay: birlikte / (ikisinden az degisenin commit sayisi).",
          f"{COUPLING_MAX_FILES} dosyadan genis commit'ler sayilmadi (her seyi her seye baglarlar).", ""]
    table(["A", "B", "Birlikte", "Pay"], [(x["a"], x["b"], x["together"], x["share"]) for x in r["coupling"]] or [("-",) * 4])

    o += ["## Degisiklik bicimi `[K]` — gecmis incelenebilir mi", "",
          f"- Kaynaga dokunan {cs['commits_touching_source']} commit: satir medyan {cs['median_lines']}, p90 {cs['p90_lines']}, "
          f"en buyuk {cs['max_lines']}; dosya medyan {cs['median_files']}, p90 {cs['p90_files']}.",
          f"- **{th['max_commit_lines']} satiri asan commit: {cs['over_budget']}** — bunlar buyuk olasilikla okunmadan onaylandi `[H]`.", ""]


def render_tests(r: dict, o: list, table) -> None:
    ts = r["tests"]
    cov = ts["coverage"]
    if cov and cov.get("matched"):
        o += ["## Test ortusu `[K]` — projenin kendi kapsam raporundan", "",
              f"- Rapor: {', '.join(f'`{x}`' for x in cov['reports'])}. Eslesen {cov['matched']} kaynak dosyada satir kapsami "
              f"**{cov['line_rate']}**; raporda olup depoda eslesmeyen {cov['unmatched']} giris; **raporda hic olmayan "
              f"{cov['not_in_report']} kaynak dosya** (olculmedi, sifir degil).", ""]
        table(["En dusuk kapsamli dosya", "Kapsam", "Satir"], [(x["path"], x["rate"], x["lines"]) for x in cov["lowest"]])
    else:
        why = ("config'te `coverage_reports` yok" if cov is None else "; ".join(cov["errors"]) or "rapor depodaki dosyalarla eslesmedi")
        o += ["## Test ortusu `[H]` — vekil olcu", "",
              f"Kapsam raporu kullanilamadi ({why}). Projenin kapsam araci varsa calistirip raporu config'e yazin; asagidaki vekilin yerini alir.", "",
              f"- Test / kaynak satir orani {ts['test_to_source_lines']}."
              + (f" Kaynak dosyalarin icinde {ts['inline_test_lines']} satir Rust testi (`#[cfg(test)]`'den dosya sonuna `[H]`)"
                 " kaynak sayildi; oran bu kadar dusuk gorunur." if ts.get("inline_test_lines") else ""),
              f"- Adi hicbir test dosyasinin adinda gecmeyen kaynak dosyalari (100+ satir): **{ts['unnamed_by_tests_files']} dosya, "
              f"{ts['unnamed_by_tests_lines']} satir**. Ad eslesmesidir: test baska adla yaziyorsa yanlis alarm, ad gecip davranis",
              "  sinanmiyorsa yanlis guvence.", ""]
        table(["Dosya", "Satir"], [(x["path"], x["lines"]) for x in ts["largest_unnamed_by_tests"]] or [("-", "-")])


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    check("derinlik: sekme 4 sutun", depth_of(["\t\tx", "    y"]) == 2)
    check("derinlik: bos satir sayilmaz", depth_of(["", "        "]) == 0)
    check("yuzdelik: bos liste None", pct([], 0.5) is None)
    rs = ["fn a() {}", "", "#[cfg(test)]", "mod tests {", "    #[test] fn b() {}", "}"]
    check("Rust satir ici test: #[cfg(test)]'den sona; baska dil ve testsiz dosya 0",
          inline_tests("src/a.rs", rs) == 4 and inline_tests("src/a.c", rs) == 0 and inline_tests("src/b.rs", rs[:2]) == 0)
    with tempfile.TemporaryDirectory() as d:
        def g(*a):
            subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)

        def write(rel, n, body="        satir {i}\n"):
            os.makedirs(os.path.dirname(os.path.join(d, rel)) or d, exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(body.format(i=i) for i in range(n)))

        def commit(msg, who):
            g("add", "-A"); g("-c", f"user.email={who}@example.invalid", "-c", f"user.name={who}", "commit", "-q", "-m", msg)
        try:
            g("init", "-q"); g("config", "commit.gpgsign", "false")
            write("src/buyuk.cs", 700); write("src/kucuk.cs", 10); write("tests/kucuk_test.cs", 5); write("x.zig", 3)
            write("web/dist/index-AbCd1234.js", 50)
            commit("ilk", "a")
            for i in range(3):
                write("src/buyuk.cs", 701 + i); write("src/kucuk.cs", 11 + i); commit(f"degisiklik {i}", "a")
            write("src/kucuk.cs", 40); commit("ikinci kisi", "b")
            cfg, src, errs = load_config(d, None)
            r = build(d, None, 5, cfg)
            check("uctan uca: envanter kaynak ve testi ayirir", r["inventory"]["source_files"] == 2 and r["inventory"]["test_files"] == 1)
            check("uctan uca: bilinmeyen uzanti siniflanmadi diye gorunur", r["unclassified_extensions"] == {".zig": 1})
            check("uctan uca: paketlenmis dosya dislanir, nedeniyle", r["excluded"] == {"paketlenmis dosya adi": ["web/dist/index-AbCd1234.js"]}
                  or r["excluded"] == {"derleme dizini": ["web/dist/index-AbCd1234.js"]})
            check("uctan uca: butceyi asan dosya sayilir", r["size"]["files_over_budget"] == 1)
            check("uctan uca: sicak nokta buyuk ve cok degisen dosya", r["hotspots"][0]["path"] == "src/buyuk.cs")
            check("uctan uca: birlikte degisen cift bulunur", any({x["a"], x["b"]} == {"src/buyuk.cs", "src/kucuk.cs"} for x in r["coupling"]))
            check("uctan uca: tek kisinin dokundugu dosya", r["knowledge"]["touched_by_one_person"] == 1 and r["knowledge"]["people"] == 2)
            check("uctan uca: butceyi asan commit sayilir", r["change_shape"]["over_budget"] == 1)
            check("uctan uca: dosya basina veri kapsam defteri icin yazilir", r["files"]["src/buyuk.cs"]["commits"] == 4)
            md = render(r, src, cfg)
            check("uctan uca: rapor esik kaynagini ve vekil ortuyu soyler", "(varsayilan)" in md and "vekil olcu" in md)
            cfg2 = dict(cfg, max_file_lines=1000)
            check("uctan uca: esik config'ten gelir", build(d, None, 5, cfg2)["size"]["files_over_budget"] == 0)
            with io.open(os.path.join(d, "cov.xml"), "w", encoding="utf-8") as f:
                f.write('<coverage><class name="a" filename="src/buyuk.cs" line-rate="0.25"></class></coverage>')
            r3 = build(d, None, 5, dict(cfg, coverage_reports=["cov.xml"]))
            c3 = r3["tests"]["coverage"]
            check("uctan uca: Cobertura raporu [K] ortu verir", c3["line_rate"] == 0.25 and c3["not_in_report"] == 1 and "[K]" in render(r3, src, cfg))
            with io.open(os.path.join(d, "lcov.info"), "w", encoding="utf-8") as f:
                f.write("SF:src/kucuk.cs\nLF:10\nLH:5\nend_of_record\n")
            check("uctan uca: lcov raporu okunur", build(d, None, 5, dict(cfg, coverage_reports=["lcov.info"]))["tests"]["coverage"]["line_rate"] == 0.5)
            r4 = build(d, None, 5, dict(cfg, coverage_reports=["yok.xml"]))
            check("uctan uca: okunamayan rapor sessizce atlanmaz", r4["tests"]["coverage"]["errors"] != [] and "okunamadi" in render(r4, src, cfg))
        except (OSError, subprocess.CalledProcessError) as e:
            check(f"uctan uca: git calistirilamadi ({e})", False)
    with tempfile.TemporaryDirectory() as d:
        for rel, n in (("src/ana.rs", 700), ("src/bin/arac.rs", 10), ("target/debug/x.rs", 5)):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8") as f:
                f.write("x\n" * n)
        cfg, src, _ = load_config(d, None)
        r = build(d, None, 5, cfg)
        check("git yok: dosyalar dizinden okunur, derleme dizini dislanir",
              r["inventory"]["source_files"] == 2 and "target/" in sum(r["excluded"].values(), []))
        check("git yok: gecmis bolumleri sifir degil olculmedi",
              not r["history"] and r["hotspots"] is None and r["knowledge"] is None and r["coupling"] is None
              and r["change_shape"] is None and r["files"]["src/ana.rs"]["commits"] is None
              and r["size"]["largest"][0]["commits"] is None)
        md = render(r, src, cfg)
        check("git yok: rapor dort bolumde 'olculmedi' der", md.count("olculmedi: git gecmisi yok") >= 4 and "| — | — |" in md)
        with io.open(os.path.join(d, "src", "akis.spath"), "w", encoding="utf-8") as f:
            f.write("CALL :a\nEMIT b\n")
        r5 = build(d, None, 5, dict(cfg, extra_sources={".spath": "S-Path"}))
        check("extra_sources: envantere dil adiyla girer, raporda config diye gorunur",
              r5["inventory"]["by_language"].get("S-Path") == {"files": 1, "lines": 2} and r5["extra_sources"] == {".spath": 1}
              and ".spath x1" in render(r5, src, cfg) and "src/akis.spath" in r5["files"])
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
    p.add_argument("--out", help="rontgen.json ve rontgen.md buraya yazilir; verilmezse rapor ekrana")
    p.add_argument("--since", help="gecmisi bu tarihten itibaren oku (YYYY-AA-GG)")
    p.add_argument("--top", type=int, default=15)
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    cfg, sources, errors = load_config(a.repo, a.config)
    if errors:
        print("\n".join("olculmedi: " + e for e in errors)); return 2
    try:
        r = build(a.repo, a.since, a.top, cfg)
    except RuntimeError as e:
        print(f"olculmedi: git ({e})"); return 2
    if not r["inventory"]["source_files"]:
        print("olculmedi: kaynak sayilan dosya yok; siniflanmayan uzantilar: " + json.dumps(r["unclassified_extensions"]))
        return 2
    md = render(r, sources, cfg)
    if a.out:
        os.makedirs(a.out, exist_ok=True)
        with io.open(os.path.join(a.out, "rontgen.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(r, f, ensure_ascii=False, indent=2); f.write("\n")
        with io.open(os.path.join(a.out, "rontgen.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(md)
        print(f"yazildi: {os.path.join(a.out, 'rontgen.md')} ve rontgen.json")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
