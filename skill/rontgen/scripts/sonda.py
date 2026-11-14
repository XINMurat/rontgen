#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- blind spots and probes: where the fixed scripts cannot see, and
how a project-specific measurement is allowed to fill the gap.

WHY THIS EXISTS
---------------
`yapi.py` reads declared imports and name usage. It cannot follow a
dependency that is registered in a container, loaded by reflection, hidden
behind an ORM, or built into a query string at run time. Until now an arrow
simply stopped there. A model can write a small script that resolves exactly
that mechanism for exactly this project -- and turn an [H] into a [K].

That is powerful and it breaks three things if done freely:

  anchoring    a tool written after reading measures what the reader already
               saw. So the GAP comes first, from the fixed scripts, before
               any code is read: `kor_noktalar` below counts the mechanisms
               the fixed scripts are blind to, and a probe is written for a
               listed gap -- never for a hunch.
  the series   a scorecard is only comparable if the instrument is the same.
               So the fixed core never changes per project, and a probe is a
               file kept in the repository with the commit it was run at; its
               numbers form their own series and are never merged into the
               core's.
  silence      an untested script that reports zero looks like a clean
               result. So a probe result is refused unless it says its
               self-test passed in full, and may claim [K] only with a
               control: a known positive it found and a known negative it
               did not.

PROBE RESULT (a JSON file listed under `probe_results` in the config)
---------------------------------------------------------------------
    {
      "sonda": "di-kayitlari",
      "aciklama": "Program.cs'teki servis kayitlarindan arayuz -> gercekleme",
      "commit": "e9e7ff3",
      "tier": "K",
      "oz_test": "9/9",
      "kontrol": "bilinen pozitif IBankaKanali->KlasorKanali bulundu; bilinen negatif bulunmadi",
      "edges": [{"from": "src/Api/Program.cs", "to": "src/Cekirdek/Banka.cs"}]
    }

An edge end may be ANY file that exists in the repository, source or not
(a table, a DSL file, a build script): the mechanism a probe resolves often
lives exactly there. An end the measurement excluded (config, build output)
stays out and is counted; only a path that does not exist is "unknown".

Anything else in the file is carried through untouched. A result that fails
these rules stops the run (exit 2): a probe that is silently ignored and a
probe that is silently trusted are the same mistake.
"""
from __future__ import annotations

import io
import json
import os
import re

from ortak import exclusion

BLIND = {
    "bagimlilik enjeksiyonu": re.compile(
        r"\b(?:AddScoped|AddSingleton|AddTransient|AddHostedService)\s*[<(]|@Inject\b|@Autowired\b|\[FromServices\]|\bcontainer\.(?:register|resolve)\("),
    "yansima / dinamik yukleme": re.compile(
        r"Activator\.CreateInstance|Type\.GetType\(|\.GetMethod\(|importlib\.import_module|__import__\(|getattr\(\w+,\s*[\"']|Class\.forName\("),
    "ORM / sorgu kurucu": re.compile(
        r"\bDbSet<|\bDbContext\b|\.FromSqlRaw\(|\bsession\.query\(|\.objects\.(?:filter|get|all)\("
        r"|createQueryBuilder\(|\bprisma\.\w+\.(?:find|create|update|delete)"),
    "parcalardan kurulan SQL": re.compile(
        r"\$\"[^\"\n]*\b(?:SELECT|INSERT|UPDATE|DELETE)\b[^\"\n]*\{|\bf[\"'][^\"'\n]*\b(?:SELECT|INSERT|UPDATE|DELETE)\b[^\"'\n]*\{", re.I),
    "olay / yayin-abone": re.compile(r"\.Subscribe\(|\.Publish\(|\bEventEmitter\b|\.addEventListener\(|\bemit\(\s*[\"']"),
    "arayuz arkasinda gercekleme": re.compile(r"\binterface\s+I[A-Z]\w+|\babstract\s+class\b|\bProtocol\)|\bABC\)"),
}
REQUIRED = ("sonda", "commit", "tier", "oz_test", "edges")


def kor_noktalar(files: dict) -> dict:
    """files{path: text} -> {mechanism: {"files": n, "hits": n, "top": [(path, hits)]}}; mechanisms with no hit are omitted."""
    out = {}
    for name, rx in BLIND.items():
        per = {p: len(rx.findall(t)) for p, t in files.items()}
        per = {p: n for p, n in per.items() if n}
        if per:
            out[name] = {"files": len(per), "hits": sum(per.values()),
                         "top": sorted(per.items(), key=lambda x: -x[1])[:5]}
    return out


def validate(raw, label: str):
    """-> errors[] for one probe result."""
    if not isinstance(raw, dict):
        return [f"{label}: bir nesne degil"]
    errs = [f"{label}: '{k}' yok" for k in REQUIRED if k not in raw]
    if errs:
        return errs
    if raw["tier"] not in ("K", "H"):
        errs.append(f"{label}: tier K ya da H olmali, {raw['tier']!r} degil")
    m = re.fullmatch(r"(\d+)/(\d+)", str(raw["oz_test"]))
    if not m or m.group(1) != m.group(2) or m.group(1) == "0":
        errs.append(f"{label}: oz_test tam gecmis olmali (N/N), {raw['oz_test']!r} degil")
    if raw["tier"] == "K" and not str(raw.get("kontrol", "")).strip():
        errs.append(f"{label}: [K] iddiasi 'kontrol' ister (bilinen pozitif ve negatif ornek)")
    if not isinstance(raw["edges"], list) or any(
            not isinstance(e, dict) or not isinstance(e.get("from"), str) or not isinstance(e.get("to"), str) for e in raw["edges"]):
        errs.append(f"{label}: edges, {{from, to}} nesnelerinin listesi olmali")
    return errs


def load_probes(repo: str, cfg: dict):
    """-> (probes[], errors[]). A listed result that is missing or malformed is an error, never skipped."""
    probes, errors = [], []
    for rel in cfg.get("probe_results", []):
        # Next to the config file first (a config kept outside a repository you may not write to), then the repository root.
        path = next((p for p in (os.path.join(cfg.get("_dir", repo), rel), os.path.join(repo, rel)) if os.path.exists(p)),
                    os.path.join(repo, rel))
        try:
            with io.open(path, encoding="utf-8") as f:
                raw = json.load(f)
        except (OSError, ValueError) as e:
            errors.append(f"sonda sonucu okunamadi: {rel} ({e})")
            continue
        errs = validate(raw, rel)
        if errs:
            errors += errs
        else:
            probes.append(raw)
    return probes, errors


def probe_ends(pairs, known, present, cfg: dict):
    """Sort the ends of probe edges. -> (accepted pairs, {kind: sorted paths}) where kind is
    'kaynak_disi' (exists, not measured source: accepted), 'dislanan' (excluded: refused), 'yok' (missing: refused)."""
    kinds = {"kaynak_disi": set(), "dislanan": set(), "yok": set()}
    for x in {x for pair in pairs for x in pair if x not in known}:
        kinds["yok" if x not in present else "dislanan" if exclusion(x, None, cfg) else "kaynak_disi"].add(x)
    ok = known | kinds["kaynak_disi"]
    return {p for p in pairs if p[0] in ok and p[1] in ok and p[0] != p[1]}, {k: sorted(v) for k, v in kinds.items()}


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    k = kor_noktalar({"a.cs": "services.AddScoped<IOdeme, Odeme>();\ninterface IOdeme {}", "b.py": "x = 1\n",
                      "c.cs": 'var s = $"SELECT * FROM {tablo}";'})
    check("kor nokta: DI kaydi sayilir", k["bagimlilik enjeksiyonu"]["hits"] == 1)
    check("kor nokta: parcali SQL sayilir", k["parcalardan kurulan SQL"]["files"] == 1)
    check("kor nokta: isabet yoksa mekanizma listelenmez", "ORM / sorgu kurucu" not in k)
    good = {"sonda": "di", "commit": "abc", "tier": "K", "oz_test": "4/4", "kontrol": "pozitif ve negatif", "edges": [{"from": "a", "to": "b"}]}
    check("sonda: gecerli sonuc", validate(good, "x") == [])
    check("sonda: eksik alan reddedilir", validate({k_: v for k_, v in good.items() if k_ != "commit"}, "x") != [])
    check("sonda: gecmeyen oz-test reddedilir", validate(dict(good, oz_test="3/4"), "x") != [])
    check("sonda: 0/0 oz-test sayilmaz", validate(dict(good, oz_test="0/0"), "x") != [])
    check("sonda: kontrolsuz [K] reddedilir", validate(dict(good, kontrol=""), "x") != [])
    check("sonda: kontrolsuz [H] kabul", validate(dict(good, tier="H", kontrol=""), "x") == [])
    check("sonda: bozuk edges reddedilir", validate(dict(good, edges=[{"from": "a"}]), "x") != [])
    cfg = {"exclude_globs": ["_arsiv/**"]}
    acc, kinds = probe_ends({("a.c", "t/x.tsv"), ("a.c", "_arsiv/y.c"), ("a.c", "yok.c"), ("t/x.tsv", "b.c")},
                            {"a.c", "b.c"}, {"a.c", "b.c", "t/x.tsv", "_arsiv/y.c"}, cfg)
    check("sonda ucu: kaynak disi var olan dosya kabul, dislanan ve olmayan reddedilir",
          acc == {("a.c", "t/x.tsv"), ("t/x.tsv", "b.c")}
          and kinds == {"kaynak_disi": ["t/x.tsv"], "dislanan": ["_arsiv/y.c"], "yok": ["yok.c"]})
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "cikti", "sondalar"))
        with io.open(os.path.join(d, "cikti", "sondalar", "s.json"), "w", encoding="utf-8") as f:
            json.dump(good, f)
        found = load_probes(os.path.join(d, "depo"), {"probe_results": ["sondalar/s.json"], "_dir": os.path.join(d, "cikti")})
        check("sonda: yol once config'in dizininde aranir", found[1] == [] and len(found[0]) == 1)
    check("sonda: listelenen dosya yoksa hata", load_probes(".", {"probe_results": ["yok-boyle.json"]})[1] != [])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    import sys
    sys.exit(self_test())
