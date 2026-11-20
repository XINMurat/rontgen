#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Leak check that never ships the words it looks for.

The shared leak_check.py needs the forbidden terms in clear text, and in CI that
means uploading private project names to the host as a secret. This check
needs only a random salt there. The repository carries HMAC-SHA256(salt, term)
for each term, lowercased, and the set of term lengths; without the salt the
digests are random-looking strings, and a dictionary attack needs the salt.

  --make     read terms (one per line) from --terms, write tools/leak-hashes.json
             with a fresh salt; the salt is written to --salt-out (never commit it)
  (default)  scan the tracked files and rontgen.skill: every substring of every
             alphanumeric run whose length is a term length is hashed and looked
             up. The salt comes from RONTGEN_LEAK_SALT. No salt: "unmeasured",
             exit 0 with a note, so a fork without the secret is not red.

    python tools/leak_hash.py --make --terms .forbidden-terms --salt-out .leak-salt
    RONTGEN_LEAK_SALT=$(cat .leak-salt) python tools/leak_hash.py
    python tools/leak_hash.py --self-test
"""
from __future__ import annotations

import hashlib
import hmac
import io
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ROOT, "tools", "leak-hashes.json")
RUN = re.compile(r"[A-Za-z0-9ÇĞİÖŞÜçğıöşü]+")


def mac(salt: str, word: str) -> str:
    return hmac.new(salt.encode(), word.lower().encode("utf-8"), hashlib.sha256).hexdigest()


def terms_of(path):
    """Terms as plain words: a regex-ish line like `C:.YEREL` yields its alphanumeric runs (`yerel`), 3+ chars."""
    out = set()
    for line in io.open(path, encoding="utf-8"):
        out |= {w.lower() for w in RUN.findall(line) if len(w) >= 3 and w.lower() not in ("c",)}
    return sorted(out)


def make(terms, salt):
    return {"_note": "HMAC-SHA256(salt, lowercased term); the salt is the CI secret RONTGEN_LEAK_SALT, never committed.",
            "lengths": sorted({len(t) for t in terms}), "digests": sorted(mac(salt, t) for t in terms)}


def hits(text: str, salt: str, db) -> list:
    want, lengths, found = set(db["digests"]), db["lengths"], []
    for m in RUN.finditer(text):
        w = m.group(0).lower()
        for n in lengths:
            for i in range(0, len(w) - n + 1):
                if mac(salt, w[i:i + n]) in want:
                    found.append((m.start(), w[i:i + n]))
    return found


def scan(root, salt, db):
    files = subprocess.run(["git", "-C", root, "ls-files"], capture_output=True, text=True).stdout.split()
    if not files:                                   # a copy without .git (the --can-fail proof): walk it
        skip = {".git", "__pycache__", ".forbidden-terms", ".leak-salt"}
        files = [os.path.relpath(os.path.join(r, f), root).replace(os.sep, "/") for r, ds, fs in os.walk(root)
                 for f in fs if not (set(os.path.relpath(os.path.join(r, f), root).split(os.sep)) & skip)]
    bad = []
    for rel in files:
        if rel in ("tools/leak-hashes.json",):
            continue
        try:
            t = io.open(os.path.join(root, rel), encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        for pos, w in hits(t, salt, db):
            bad.append(f"{rel}:{t.count(chr(10), 0, pos) + 1}")
    pkg = os.path.join(root, "rontgen.skill")
    if os.path.exists(pkg):
        with zipfile.ZipFile(pkg) as z:
            for n in z.namelist():
                if hits(z.read(n).decode("utf-8", "replace"), salt, db):
                    bad.append(f"rontgen.skill:{n}")
    return bad


def self_test() -> int:
    ok = []

    def t(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    with tempfile.TemporaryDirectory() as d:
        tp = os.path.join(d, "terms")
        io.open(tp, "w", encoding="utf-8").write("GizliProje\nC:.YEREL\n")
        terms = terms_of(tp)
        t("terimler: duzenli ifade satiri sozcuklere ayrilir", terms == ["gizliproje", "yerel"])
        salt = secrets.token_hex(16)
        db = make(terms, salt)
        t("ozet dosyasi terimi acik tasimaz", "gizli" not in json.dumps(db).lower() and "yerel" not in json.dumps(db).lower())
        t("yakalar: alt dize, buyuk-kucuk harf, yol icinde", hits("bkz. GizliProjeApi ve C:\\YEREL\\x", salt, db) != []
          and len(hits("C:\\YEREL\\x", salt, db)) == 1)
        t("temiz metinde bulgu yok", hits("helix ve esbuild belgeleri", salt, db) == [])
        t("yanlis tuzla bulunmaz (tuz olmadan ozet ise yaramaz)", hits("GizliProje", secrets.token_hex(16), db) == [])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if "--self-test" in a:
        return self_test()
    if "--make" in a:
        terms = terms_of(a[a.index("--terms") + 1])
        salt = secrets.token_hex(32)
        io.open(DB, "w", encoding="utf-8", newline="\n").write(json.dumps(make(terms, salt), indent=2) + "\n")
        io.open(a[a.index("--salt-out") + 1], "w", encoding="utf-8", newline="\n").write(salt + "\n")
        print(f"yazildi: tools/leak-hashes.json ({len(terms)} ozet); tuz {a[a.index('--salt-out') + 1]} dosyasinda (commit etmeyin)")
        return 0
    salt = (os.environ.get("RONTGEN_LEAK_SALT") or "").strip()
    if not salt:
        print("olculmedi: RONTGEN_LEAK_SALT yok; sizinti ozet denetimi bu ortamda yapilmadi")
        return 0
    db = json.load(io.open(DB, encoding="utf-8"))
    bad = scan(ROOT, salt, db)
    print("\n".join("SIZINTI  " + b for b in bad) or f"ok  {len(db['digests'])} ozet, izlenen dosyalar ve paket temiz")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
