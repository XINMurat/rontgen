#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- citations: is every `file:line` in the written documents still
pointing at what the writer saw, and has anyone but the writer looked?

WHY THIS EXISTS
---------------
The written documents are trusted because each arrow cites a line. On the
first real run, fifteen of 162 citations were eleven lines off: part of a hot
file had been read before another commit landed. The documents' own safeguard
-- "re-open three arrows per diagram" -- had passed. A line number is a claim
about a moving target, and a sample of three does not find a block shift.

THE SIDECAR
-----------
Next to the documents, `atiflar.tsv`:

    # commit: e9e7ff3
    dotnet/src/Api/Program.cs<TAB>452<TAB>Yetkili(HttpRequest
    dotnet/src/Cekirdek/Odeme.cs<TAB>417<TAB>Hazirlayan<TAB>oto

path, line, a piece of text that must be ON that line (the anchor), and
optionally `oto` for an anchor this script wrote.

WHAT IT REPORTS
---------------
  KAYIK     the anchor is not on the cited line. Found nearby: the new line
            is suggested. Found nowhere: the code changed and the sentence
            has to be re-read, not renumbered.
  CAPASIZ   a `Name.ext:123` citation in a document has no sidecar row
  ARALIK    a `Name.ext:120-134` citation whose END line has no sidecar row:
            the start is checked, the extent is not
  BELIRSIZ  the cited name matches more than one file in the repository
            (`Program.cs`, `index.ts`): write a longer path. A name that is
            itself a full path (`CMakeLists.txt` at the root) is not ambiguous.

Not read as citations: the --ornek list (it quotes the documents) and a
`doc.md:12` pointing at another document in the same directory.
  DEGISTI   a cited file changed since the sidecar's commit
  BAYAT     per document: how many of the files it rests on have changed
  COKLU     (warning) the anchor text is on more than one line of the file:
            it proves the text, not which place was meant. --capala tries
            the whole line instead, and says so when even that repeats

MODES
-----
  (default)   check
  --capala    write sidecar rows for CAPASIZ citations from the file as it is
              now. Refused for any file that differs from the sidecar's
              commit: anchoring a citation to code that has moved since it
              was read would turn a stale citation into a "verified" one.
  --ornek N   print N randomly chosen cited sentences as a checklist for a
              reader who did NOT write the documents. The writer checking
              their own citations proves the line is there, not that the
              sentence about it is true.

EXIT CODES
----------
  0  every anchored citation holds
  1  at least one KAYIK (with --strict also CAPASIZ, ARALIK, BELIRSIZ)
  2  could not check (no sidecar, unreadable row)

USAGE
-----
    python atif.py --repo . --docs rontgen-out
    python atif.py --repo . --docs rontgen-out --capala
    python atif.py --repo . --docs rontgen-out --ornek 12 --seed 7
    python atif.py --self-test
"""
from __future__ import annotations

import argparse
import glob
import io
import os
import random
import re
import subprocess
import sys
import tempfile

from ortak import has_git, list_files

NO_GIT = ("commit'siz capa: git yok. Capalar calisma agacindaki dosyaya bagli; dosyanin capadan sonra degisip "
          "degismedigi (DEGISTI / BAYAT) olculmedi, KAYIK onu yalniz capa metni kayinca yakalar.")
NO_COMMIT = "yok (git yok)"   # the sidecar's commit line when there is no git

SIDECAR = "atiflar.tsv"
CITE = re.compile(r"`([\w./\\-]+\.[A-Za-z0-9]+):(\d+)(?:[–-](\d+))?")
TOKEN = re.compile(r"[A-Za-z_][\w.]{3,}\(?|\"[^\"]{4,}\"")
WINDOW = 80
GENERATED = {"rontgen.md", "yapi.md", "belge.md", "kapsam.md"}   # the core's reports in the output folder
ORNEK_HEAD = "# Kor denetim"   # first line of an --ornek list; such a file is skipped when citations are read


def load_sidecar(path: str):
    """-> (commit|None, rows[(path, line, anchor)], errors[])"""
    commit, rows, errors = None, [], []
    with io.open(path, encoding="utf-8") as f:
        for n, raw in enumerate(f, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue
            if line.startswith("#"):
                m = re.match(r"#\s*commit:\s*(\S+)", line)
                if m and m.group(1) != "yok":
                    commit = m.group(1)
                continue
            parts = line.split("\t")
            if len(parts) not in (3, 4) or not parts[1].isdigit() or not parts[2]:
                errors.append(f"{SIDECAR}:{n} okunamadi (yol<TAB>satir<TAB>capa bekleniyor)")
                continue
            rows.append((clean(parts[0]), int(parts[1]), parts[2]))
    return commit, rows, errors


def judge(lines, line_no: int, anchor: str):
    """-> ('ok', None) | ('kayik', [nearby line numbers]) | ('yok', [])"""
    if 1 <= line_no <= len(lines) and anchor in lines[line_no - 1]:
        return "ok", None
    lo, hi = max(0, line_no - 1 - WINDOW), min(len(lines), line_no + WINDOW)
    near = [i + 1 for i in range(lo, hi) if anchor in lines[i]]
    if near:
        return "kayik", sorted(near, key=lambda x: abs(x - line_no))[:3]
    anywhere = [i + 1 for i, text in enumerate(lines) if anchor in text]
    return ("kayik", anywhere[:3]) if anywhere else ("yok", [])


def clean(name: str) -> str:
    name = name.replace("\\", "/")
    return name[2:] if name.startswith("./") else name


def suffix_match(path: str, name: str) -> bool:
    path, name = clean(path), clean(name)
    return path == name or path.endswith("/" + name)


def resolve(name: str, tracked):
    """A cited name -> the tracked files it can mean. A name that is itself a full path (a root file
    such as CMakeLists.txt) means that path, not every file of that name below it."""
    name = clean(name)
    return [name] if name in tracked else [p for p in tracked if suffix_match(p, name)]


def pick_anchor(text: str):
    """The most distinctive token on a line: longest identifier-like run, else the stripped line."""
    found = TOKEN.findall(text)
    if found:
        return max(found, key=len)
    stripped = text.strip()
    return stripped[:40] if len(stripped) >= 3 else None


BLOCK_START = re.compile(r"^\s*(#|\||[-*+]\s|\d+[.)]\s|```)")
SENTENCE_END = re.compile(r"[.!?][)\"'`*]*\s*$")


def context(lines, i: int) -> str:
    """What a second reader needs to judge the citation on line i (0-based): the whole sentence, which may start
    lines earlier (a file named on the line above) and end lines later; for a table row, the header row too."""
    if lines[i].lstrip().startswith("|"):
        top = i
        while top > 0 and lines[top - 1].lstrip().startswith("|"):
            top -= 1
        return lines[i].strip() if top == i else f"{lines[top].strip()} … {lines[i].strip()}"
    start = i                                # back to the sentence start; a list item or paragraph start ends it
    while start > 0 and not BLOCK_START.match(lines[start]):
        prev = lines[start - 1]
        if not prev.strip() or prev.lstrip().startswith(("#", "|", "```")) or SENTENCE_END.search(prev):
            break
        start -= 1
    end = i
    while (not SENTENCE_END.search(lines[end]) and end + 1 < len(lines) and lines[end + 1].strip()
           and not BLOCK_START.match(lines[end + 1])):
        end += 1
    return " ".join(x.strip() for x in lines[start:end + 1])


def doc_citations(docs_dir: str):
    """-> [(doc, doc_line, name, start, end|None, sentence)]. Two things in the documents directory are not
    citations of the code: this script's own --ornek list (it quotes the documents), and a `doc.md:12` that
    points at another document there. Nor are the core's own reports (`yapi.md` lists entries by line; nobody
    wrote those as claims), nor a quoted line (`> ...`: a log quoting a script's message)."""
    out = []
    for md in sorted(glob.glob(os.path.join(docs_dir, "**", "*.md"), recursive=True)):
        if os.path.dirname(os.path.abspath(md)) == os.path.abspath(docs_dir) and os.path.basename(md) in GENERATED:
            continue
        with io.open(md, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
        if lines and lines[0].startswith(ORNEK_HEAD):
            continue
        for n, text in enumerate(lines, 1):
            if text.lstrip().startswith(">"):
                continue
            for name, start, end in CITE.findall(text):
                if os.path.isfile(os.path.join(docs_dir, clean(name))):
                    continue
                out.append((os.path.relpath(md, docs_dir).replace("\\", "/"), n, clean(name),
                            int(start), int(end) if end else None, context(lines, n - 1)))
    return out


def changed_since(repo: str, commit: str, paths):
    out = []
    for p in sorted(set(paths)):
        r = subprocess.run(["git", "-C", repo, "diff", "--quiet", commit, "--", p], capture_output=True)
        if r.returncode == 1:
            out.append(p)
        elif r.returncode != 0:
            return None
    return out


def tracked_files(repo: str):
    """Git's tracked files; without git, the files of a directory walk (build and hidden directories not entered)."""
    if not has_git(repo):
        return list_files(repo)[0]
    r = subprocess.run(["git", "-C", repo, "-c", "core.quotepath=off", "ls-files"], capture_output=True)
    return r.stdout.decode("utf-8", "replace").splitlines() if r.returncode == 0 else []


def classify(cites, rows, tracked):
    """-> loose, range_only, ambiguous: lists of citations; anchored: {doc: set(paths)}"""
    by_line = {}
    for path, n, _ in rows:
        by_line.setdefault(n, []).append(path)
    loose, range_only, ambiguous, rests_on = [], [], [], {}
    for c in cites:
        doc, _, name, start, end, _ = c
        cands = resolve(name, tracked)
        if len(cands) > 1:
            ambiguous.append(c)
        hit = [p for p in by_line.get(start, []) if suffix_match(p, name)]
        if not hit:
            loose.append(c)
            continue
        rests_on.setdefault(doc, set()).update(hit)
        if end and not [p for p in by_line.get(end, []) if suffix_match(p, name)]:
            range_only.append(c)
    return loose, range_only, ambiguous, rests_on


def read_lines(repo: str, path: str, cache: dict):
    if path not in cache:
        try:
            with io.open(os.path.join(repo, path), encoding="utf-8", errors="replace") as f:
                cache[path] = f.read().splitlines()
        except OSError:
            cache[path] = None
    return cache[path]


def run(repo: str, docs: str, strict: bool, verbose: bool, out=sys.stdout) -> int:
    def say(*a):
        print(*a, file=out)

    git = has_git(repo)
    if not git:
        say(NO_GIT)
    side = os.path.join(docs, SIDECAR)
    if not os.path.exists(side):
        say(f"olculmedi: {side} yok. Atiflar capasiz; hicbiri denetlenemez.")
        return 2
    commit, rows, errors = load_sidecar(side)
    for e in errors:
        say("olculmedi: " + e)
    if errors:
        return 2
    cache, bad, gone, multi = {}, 0, 0, 0
    for path, line_no, anchor in rows:
        lines = read_lines(repo, path, cache)
        if lines is None:
            say(f"KAYIK    {path}:{line_no}  dosya yok"); bad += 1; gone += 1
            continue
        verdict, near = judge(lines, line_no, anchor)
        also = [i + 1 for i, t in enumerate(lines) if anchor in t and i + 1 != line_no]
        if verdict == "ok" and also:          # the anchor proves the text, not which of its places was meant
            whole = lines[line_no - 1].strip()[:80]
            fix = (f"; tum satir tek: capayi \"{whole}\" yapin" if sum(whole in t for t in lines) == 1
                   else "; satirin tamami da tekrarliyor — cumle yeri (islevi) adlandirsin")
            say(f"COKLU    {path}:{line_no}  \"{anchor}\" dosyada {len(also)} yerde daha var ({', '.join(map(str, also[:4]))}): "
                "capa ayirt edici degil" + fix); multi += 1
        if verdict == "kayik":
            say(f"KAYIK    {path}:{line_no}  \"{anchor}\" -> simdi {', '.join(map(str, near))}"); bad += 1
        elif verdict == "yok":
            say(f"KAYIK    {path}:{line_no}  \"{anchor}\" dosyada hic yok: kod degisti, cumleyi yeniden oku"); bad += 1; gone += 1

    cites = doc_citations(docs)
    loose, range_only, ambiguous, rests_on = classify(cites, rows, tracked_files(repo))
    if verbose:
        for label, group in (("CAPASIZ ", loose), ("ARALIK  ", range_only), ("BELIRSIZ", ambiguous)):
            for doc, n, name, start, end, _ in group:
                say(f"{label} {doc}:{n}  {name}:{start}" + (f"-{end}" if end else ""))

    changed = None
    if not git:
        pass                                  # said at the top: no commit to compare with
    elif commit:
        changed = changed_since(repo, commit, [p for p, _, _ in rows])
        if changed is None:
            say(f"olculmedi: commit {commit} cozulemedi; hangi dosyalarin degistigi bilinmiyor")
        else:
            for p in changed:
                say(f"DEGISTI  {p}  ({commit} sonrasi)")
            for doc, paths in sorted(rests_on.items()):
                stale = sorted(paths & set(changed))
                if stale:
                    say(f"BAYAT    {doc}: dayandigi {len(paths)} dosyadan {len(stale)} tanesi degisti — yeniden okunmali: {', '.join(stale[:4])}")
    else:
        say("olculmedi: yan dosyada '# commit:' satiri yok; hangi surume ait oldugu bilinmiyor")

    say(f"\n{len(rows)} capali atif{'' if git else ' (commit siz)'}: {len(rows) - bad} yerinde, {bad} kayik ({gone} tanesi artik yok). "
        f"Belgelerde {len(cites)} atif: {len(loose)} capasiz, {len(range_only)} aralik sonu capasiz, {len(ambiguous)} belirsiz ad. "
        f"Capasi dosyada birden cok yerde gecen (uyari): {multi}.")
    if bad or (strict and (loose or range_only or ambiguous)):
        return 1
    return 0


def capala(repo: str, docs: str, out=sys.stdout) -> int:
    def say(*a):
        print(*a, file=out)

    git = has_git(repo)
    side = os.path.join(docs, SIDECAR)
    if not git:
        say(NO_GIT)
        if not os.path.exists(side):
            with io.open(side, "w", encoding="utf-8", newline="\n") as f:
                f.write(f"# commit: {NO_COMMIT}\n")
    if not os.path.exists(side):
        say(f"olculmedi: {side} yok. Once '# commit: <sha>' satiriyla olusturun: capa, okunan surume baglanir.")
        return 2
    commit, rows, errors = load_sidecar(side)
    if errors or (git and not commit):
        say("olculmedi: " + ("; ".join(errors) if errors else "yan dosyada '# commit:' yok; hangi surume capalanacagi bilinmiyor"))
        return 2
    tracked = tracked_files(repo)
    have = {(p, n) for p, n, _ in rows}
    wanted = {}
    for doc, _, name, start, end, _ in doc_citations(docs):
        cands = resolve(name, tracked)
        for line_no in filter(None, (start, end)):
            if any(suffix_match(p, name) and n == line_no for p, n in have):
                continue
            wanted.setdefault((name, line_no), cands)
    added, cache, refused = [], {}, 0
    moved = set(changed_since(repo, commit, {c[0] for c in wanted.values() if len(c) == 1}) or []) if git else set()
    for (name, line_no), cands in sorted(wanted.items()):
        if len(cands) != 1:
            say(f"BELIRSIZ {name}:{line_no}  {'eslesen dosya yok' if not cands else str(len(cands)) + ' dosya eslesiyor'}: capalanmadi"); refused += 1
            continue
        path = cands[0]
        if path in moved:
            say(f"REDDEDILDI {path}:{line_no}  dosya {commit} sonrasi degisti: bugunku satira capalamak bayat atfi aklar. Yeniden okuyun."); refused += 1
            continue
        lines = read_lines(repo, path, cache)
        anchor = pick_anchor(lines[line_no - 1]) if lines and 1 <= line_no <= len(lines) else None
        if not anchor:
            near = next((k for k in range(min(line_no, len(lines or [])), max(0, line_no - 10), -1) if pick_anchor(lines[k - 1])), None)
            say(f"REDDEDILDI {path}:{line_no}  satir bos ya da dosya disinda: capa cikarilamadi"
                + (f"; en yakin dolu satir {near} — atfi (ya da araligin sonunu) {near}'e cekin" if near else "")); refused += 1
            continue
        if sum(anchor in t for t in lines) > 1:     # try the whole line before giving up on a unique anchor
            whole = lines[line_no - 1].strip()[:80]
            if sum(whole in t for t in lines) == 1:
                anchor = whole
            else:
                say(f"COKLU    {path}:{line_no}  satir dosyada birebir baska yerde de var; ayirt edici capa yok — "
                    "cumle yeri (islevi, bolumu) adlandirsin")
        added.append((path, line_no, anchor.replace("\t", " ")))
    if added:
        with io.open(side, "a", encoding="utf-8", newline="\n") as f:
            f.writelines(f"{p}\t{n}\t{a}\toto\n" for p, n, a in added)
    say(f"\n{len(added)} capa yazildi (oto), {refused} atif capalanamadi.")
    return 0


def ornek(docs: str, n: int, seed: int, out=sys.stdout) -> int:
    cites = doc_citations(docs)
    seen, rows = set(), []
    for doc, line, *_rest, sentence in cites:
        if (doc, line) not in seen:
            seen.add((doc, line)); rows.append((doc, line, sentence))
    if not rows:
        print("olculmedi: belgelerde atifli cumle yok", file=out)
        return 2
    rnd = random.Random(seed)   # tables get >= 1/3: once, every faulted sentence was a cell saying more than its line
    tab = [r for r in rows if r[2].lstrip().startswith("|")]
    txt = [r for r in rows if not r[2].lstrip().startswith("|")]
    rnd.shuffle(tab); rnd.shuffle(txt)
    nt = min(len(tab), max(-(-n // 3), round(n * len(tab) / len(rows))))
    picked = tab[:nt] + txt[:n - nt]
    picked = sorted(picked + tab[nt:nt + n - len(picked)])
    np_ = sum(r[2].lstrip().startswith("|") for r in picked)
    print(f"{ORNEK_HEAD} — {len(picked)} / {len(rows)} atifli cumle (tohum {seed}; {np_} tablo satiri)\n\n"
          "Bu listeyi belgeleri YAZMAYAN biri (ya da yazarin notlarini gormeyen taze bir oturum) doldurur. Her cumle icin\n"
          "atif yapilan satiri acin ve cumlenin o satirdan cikip cikmadigina bakin: satirin orada olmasi yetmez.\n"
          "Tablo satirinda her hucre bir iddiadir: atif yapilan satir ya da aralik hucrenin hepsini gostermiyorsa sonuc\n"
          "`satirdan cikmiyor`.\n"
          "Sonuc: `tuttu` / `tutmadi` / `satirdan cikmiyor` ve bir cumle gerekce. Oran belgenin kapsam beyanina yazilir.\n", file=out)
    for doc, line, sentence in picked:
        print(f"- [ ] `{doc}:{line}` — {sentence[:700]}" + (" …" if len(sentence) > 700 else "") + "\n      sonuc: ", file=out)
    return 0


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    lines = ["a", "b = Yetkili(x)", "c", "d"]
    check("capa satirda: ok", judge(lines, 2, "Yetkili(") == ("ok", None))
    check("capa kaymis: yeni satir onerilir", judge(lines, 4, "Yetkili(") == ("kayik", [2]))
    check("capa hic yok", judge(lines, 2, "Silindi(") == ("yok", []))
    check("satir dosya disinda: cokmez", judge(lines, 99, "Yetkili(")[0] == "kayik")
    check("atif deseni: aralik sonu da okunur",
          CITE.findall("bkz. `Odeme.cs:333–345` ve `sql/20-odeme.sql:60`") == [("Odeme.cs", "333", "345"), ("sql/20-odeme.sql", "60", "")])
    check("atif deseni: yalniz :608 sayilmaz", CITE.findall("(`:608`)") == [])
    check("ad eslesmesi: yol kuyrugu, alt dize degil", suffix_match("a/Program.cs", "Program.cs") and not suffix_match("a/XProgram.cs", "Program.cs"))
    check("capa secimi: en ayirt edici belirtec", pick_anchor("    var x = odeme.FaturaKaydet(s);") == "odeme.FaturaKaydet(")
    md = ["# Baslik", "", "Commit `abc`. Okunan: `a.c:1-60`;", "`b.c:2-5` ve `:9-12`; `c.h:3-4`.", "",
          "- Ilk madde `a.c:7` tek satir.", "- Ikinci madde `a.c:8` iki", "  satira tasar.", "",
          "| Ad | Yer |", "|---|---|", "| X | `a.c:9` |", "", "Yarim cumle `a.c:10` burada", "ve burada biter. Sonraki cumle.",
          "", "- Noktasiz madde `a.c:11`", "- Sonraki madde `a.c:12`"]
    check("cumle baglami: noktasiz onceki madde alinmaz", context(md, 17) == "- Sonraki madde `a.c:12`")
    check("cumle baglami: onceki satirdaki dosya adi gorunur", context(md, 3).startswith("Commit `abc`.") and "`c.h:3-4`." in context(md, 3))
    check("cumle baglami: madde basindan geri gidilmez, devami alinir",
          context(md, 5) == "- Ilk madde `a.c:7` tek satir." and context(md, 6) == "- Ikinci madde `a.c:8` iki satira tasar.")
    check("cumle baglami: tablo satiri basligiyla", context(md, 11) == "| Ad | Yer | … | X | `a.c:9` |")
    check("cumle baglami: cumle sonuna kadar ileri", context(md, 13) == "Yarim cumle `a.c:10` burada ve burada biter. Sonraki cumle.")
    check("capa secimi: bos satirdan capa cikmaz", pick_anchor("   ") is None and pick_anchor("}") is None)
    with tempfile.TemporaryDirectory() as d:
        def g(*a):
            subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)

        def write(rel, text):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        docs = os.path.join(d, "out")
        try:
            g("init", "-q"); g("config", "user.email", "t@example.invalid"); g("config", "user.name", "t"); g("config", "commit.gpgsign", "false")
            write("src/A.cs", "bir\niki Yetkili(\nuc Kaydet()\ndort\n")
            write("api/Program.cs", "x\ny\n"); write("arac/Program.cs", "p\nq\n")
            g("add", "-A"); g("commit", "-q", "-m", "ilk")
            sha = subprocess.run(["git", "-C", d, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
            write("out/not.md", "Bkz. `A.cs:2–3` ve `A.cs:4`; ayrica `Program.cs:1`.\n")
            check("uctan uca: yan dosya yoksa 2", run(d, docs, False, False, io.StringIO()) == 2)
            write("out/atiflar.tsv", f"# commit: {sha}\nsrc/A.cs\t2\tYetkili(\n")
            buf = io.StringIO()
            rc = run(d, docs, False, True, buf)
            check("uctan uca: capasiz, aralik sonu ve belirsiz ad ayri sayilir",
                  rc == 0 and "2 capasiz, 1 aralik sonu capasiz, 1 belirsiz ad" in buf.getvalue())
            check("uctan uca: --strict bunlarda duser", run(d, docs, True, False, io.StringIO()) == 1)
            buf = io.StringIO()
            capala(d, docs, buf)
            side = io.open(os.path.join(docs, SIDECAR), encoding="utf-8").read()
            check("uctan uca: --capala aralik sonunu ve capasizi yazar", "src/A.cs\t3\tKaydet(\toto" in side and "src/A.cs\t4\tdort\toto" in side)
            check("uctan uca: --capala belirsiz adi capalamaz", "BELIRSIZ Program.cs:1" in buf.getvalue() and "Program.cs\t1" not in side)
            buf = io.StringIO()
            check("uctan uca: capalamadan sonra aralik temiz", run(d, docs, False, False, buf) == 0 and "0 aralik sonu capasiz" in buf.getvalue())
            write("src/A.cs", "yeni\nbir\niki Yetkili(\nuc Kaydet()\ndort\n")
            buf = io.StringIO()
            rc = run(d, docs, False, False, buf)
            check("uctan uca: kayan satir yakalanir ve yeni yer onerilir", rc == 1 and "simdi 3" in buf.getvalue())
            check("uctan uca: degisen dosya ve bayat belge bildirilir", "DEGISTI  src/A.cs" in buf.getvalue() and "BAYAT    not.md" in buf.getvalue())
            write("out/ek.md", "Yeni: `A.cs:5`.\n")
            buf = io.StringIO()
            capala(d, docs, buf)
            check("uctan uca: degismis dosyaya capa reddedilir", "REDDEDILDI src/A.cs:5" in buf.getvalue())
            buf = io.StringIO()
            check("uctan uca: kor denetim listesi uretilir, tohumla ayni", ornek(docs, 1, 3, buf) == 0 and "- [ ] `" in buf.getvalue()
                  and (lambda b2: ornek(docs, 1, 3, b2) == 0 and b2.getvalue() == buf.getvalue())(io.StringIO()))
            write("out/kor.md", buf.getvalue())
            write("out/ref.md", "Bkz. `not.md:1` ve `CMakeLists.txt:1`, `./CMakeLists.txt:2`.\n")
            write("CMakeLists.txt", "a\nb\n"); write("alt/CMakeLists.txt", "c\n"); g("add", "-A")
            names = [(doc, name) for doc, _, name, *_ in doc_citations(docs)]
            check("kendi --ornek listesi ve belgeye gonderme atif sayilmaz", not any(doc == "kor.md" for doc, _ in names)
                  and ("ref.md", "not.md") not in names and ("ref.md", "CMakeLists.txt") in names)
            buf = io.StringIO()
            run(d, docs, False, True, buf)
            check("kokteki tam yol belirsiz degil, './' oneki atilir", resolve("./CMakeLists.txt", tracked_files(d)) == ["CMakeLists.txt"]
                  and (lambda b: not any("CMakeLists" in x for x in b) and any("Program.cs" in x for x in b))(
                      [x for x in buf.getvalue().splitlines() if x.startswith("BELIRSIZ")]))
            write("out/iki.md", "Okunan dosya src/A.cs icinde\n`A.cs:2` ve `A.cs:3`.\n")
            check("uctan uca: liste cumleyi onceki satiriyla verir",
                  any(c[0] == "iki.md" and c[-1].startswith("Okunan dosya") for c in doc_citations(docs)))
            write("out/yapi.md", "Giris `A.cs:1`.\n"); write("out/alt/yapi.md", "Not `A.cs:1`.\n")
            write("out/gunluk.md", "> KAYIK `A.cs:4` dosyada yok\nAma `A.cs:2` yazildi.\n")
            cs = [(c[0], c[1]) for c in doc_citations(docs)]
            check("cekirdegin kendi raporu ve '>' alinti satiri atif sayilmaz; alt dizindeki ayni ad sayilir",
                  ("yapi.md", 1) not in cs and ("alt/yapi.md", 1) in cs and ("gunluk.md", 1) not in cs and ("gunluk.md", 2) in cs)
            write("out/atiflar.tsv", "src/A.cs\tiki\tx\n")
            check("uctan uca: bozuk yan dosya 2", run(d, docs, False, False, io.StringIO()) == 2)
        except (OSError, subprocess.CalledProcessError) as e:
            check(f"uctan uca: git calistirilamadi ({e})", False)
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "out")
        for rel, text in (("src/a.rs", "fn bir() {}\nfn iki() { hesapla(); }\nfn uc() { hesapla(); }\n"),
                          ("x/b.rs", "z\n"), ("y/b.rs", "z\n"), (".gizli/c.rs", "c\n"),
                          ("out/not.md", "Bkz. `a.rs:1-2`, `a.rs:3`, `b.rs:1`, `c.rs:1`.\n")):
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            with io.open(os.path.join(d, rel), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        b1, b2 = io.StringIO(), io.StringIO()
        capala(d, out, b1)
        side = io.open(os.path.join(out, SIDECAR), encoding="utf-8").read()
        check("git yok: --capala yan dosyayi commit'siz acar, capalari yazar, belirsizi ve gizliyi capalamaz",
              side.startswith(f"# commit: {NO_COMMIT}") and "src/a.rs\t1\tfn bir() {}\toto" in side and "src/a.rs\t3\tfn uc() { hesapla(); }\toto" in side
              and "BELIRSIZ b.rs:1" in b1.getvalue() and "c.rs\t1" not in side and "commit'siz capa" in b1.getvalue())
        check("git yok: 'commit: yok' satiri commit sayilmaz (sonra git gelirse 'yok' cozulmeye calisilmaz)",
              load_sidecar(os.path.join(out, SIDECAR))[0] is None)
        rc = run(d, out, False, False, b2)
        check("git yok: denetim calisir, commit'siz der, DEGISTI / commit uyarisi vermez",
              rc == 0 and "3 capali atif (commit siz): 3 yerinde" in b2.getvalue() and "commit'siz capa" in b2.getvalue()
              and "DEGISTI  " not in b2.getvalue() and "'# commit:' satiri yok" not in b2.getvalue())
        with io.open(os.path.join(d, "src/a.rs"), "w", encoding="utf-8", newline="\n") as f:
            f.write("// yeni\nfn bir() {}\nfn iki() { hesapla(); }\nfn uc() { hesapla(); }\n")
        b3 = io.StringIO()
        check("git yok: kayan satir yine yakalanir", run(d, out, False, False, b3) == 1 and "simdi 2" in b3.getvalue())
    with tempfile.TemporaryDirectory() as d:
        try:
            run_git = lambda *a: subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)  # noqa: E731
            run_git("init", "-q"); run_git("config", "user.email", "t@example.invalid"); run_git("config", "user.name", "t")
            run_git("config", "commit.gpgsign", "false")
            os.makedirs(os.path.join(d, "out"))
            with io.open(os.path.join(d, "b.c"), "w", encoding="utf-8", newline="\n") as f:
                f.write("int bir(void);\n\n")
            with io.open(os.path.join(d, "c.c"), "w", encoding="utf-8", newline="\n") as f:
                f.write("int f(void) {\n    if (!x) return true;\n}\nint g(void) {\n    if (!x) return true;\n}\n"
                        "b = hesapla(2);\na = hesapla(1);\n")
            run_git("add", "-A"); run_git("commit", "-q", "-m", "x")
            sha = subprocess.run(["git", "-C", d, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
            with io.open(os.path.join(d, "out", "not.md"), "w", encoding="utf-8") as f:
                f.write("Bkz. `b.c:1-2`. Kapi `c.c:2` ve `c.c:8`.\n")
            with io.open(os.path.join(d, "out", SIDECAR), "w", encoding="utf-8") as f:
                f.write(f"# commit: {sha}\n")
            buf = io.StringIO()
            capala(d, os.path.join(d, "out"), buf)
            check("--capala: bos satirdaki aralik sonu icin en yakin dolu satiri soyler", "en yakin dolu satir 1" in buf.getvalue())
            side = io.open(os.path.join(d, "out", SIDECAR), encoding="utf-8").read()
            check("--capala: tekrar eden belirtec yerine tum satir; satir da tekrarliyorsa COKLU der",
                  "c.c\t8\ta = hesapla(1);\toto" in side and "COKLU    c.c:2" in buf.getvalue() and "COKLU    c.c:8" not in buf.getvalue())
            buf = io.StringIO()
            run(d, os.path.join(d, "out"), False, False, buf)
            check("denetim: capa dosyada birden cok yerde gecerse COKLU uyarir, hata vermez",
                  "COKLU    c.c:2" in buf.getvalue() and "COKLU    c.c:8" not in buf.getvalue() and "birden cok yerde gecen (uyari): 1" in buf.getvalue())
            with io.open(os.path.join(d, "out", SIDECAR), "a", encoding="utf-8") as f:
                f.write("c.c\t7\thesapla(\n")
            buf = io.StringIO()
            run(d, os.path.join(d, "out"), False, False, buf)
            check("denetim: COKLU satirin tamami tekse onu onerir, degilse islevi adlandirmayi",
                  "capayi \"b = hesapla(2);\" yapin" in buf.getvalue() and "satirin tamami da tekrarliyor" in buf.getvalue())
        except (OSError, subprocess.CalledProcessError) as e:
            check(f"--capala bos satir: git calistirilamadi ({e})", False)
    with tempfile.TemporaryDirectory() as d:
        with io.open(os.path.join(d, "not.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write("".join(f"Cumle {i} `a.c:{i}`.\n\n" for i in range(1, 11)))
            f.write("| Ad | Yer |\n|---|---|\n| X | `a.c:20` |\n| Y | `a.c:21` |\n")
        buf = io.StringIO()
        ornek(d, 6, 1, buf)
        items = [x for x in buf.getvalue().splitlines() if x.startswith("- [ ]")]
        check("ornek: tablo satirlari orneklemin en az ucte birini alir (varsa)",
              len(items) == 6 and sum("| X |" in x or "| Y |" in x for x in items) == 2 and "2 tablo satiri" in buf.getvalue())
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
    p.add_argument("--docs", help=f"yazili belgelerin dizini ({SIDECAR} burada)")
    p.add_argument("--strict", action="store_true", help="capasiz, aralik sonu capasiz ve belirsiz atif da hata sayilir")
    p.add_argument("--verbose", action="store_true", help="capasiz / aralik / belirsiz atiflari tek tek listele")
    p.add_argument("--capala", action="store_true", help="capasiz atiflara bugunku satirdan capa yaz (dosya degismediyse)")
    p.add_argument("--ornek", type=int, metavar="N", help="yazar olmayan biri icin N atifli cumlelik kor denetim listesi")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args()
    if a.self_test:
        return self_test()
    if not a.docs:
        p.error("--docs gerekli")
    if a.capala:
        return capala(a.repo, a.docs)
    if a.ornek:
        return ornek(a.docs, a.ornek, a.seed)
    return run(a.repo, a.docs, a.strict, a.verbose)


if __name__ == "__main__":
    sys.exit(main())
