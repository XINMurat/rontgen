#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- output schemas and their validator.

WHY THIS EXISTS
---------------
Iskele and Mizan read Rontgen's JSON. A field renamed in one script would
reach them as a silent gap. The schemas in `schemas/` freeze what each output
promises; this validator refuses a file that breaks it, and names the path.

A subset of JSON Schema, standard library only: type (a name or a list, so
"null" can be allowed), required, properties, items, enum,
additionalProperties (only `false` is acted on).

USAGE
-----
    python dogrula.py rontgen-out/rontgen.json            # schema chosen by file name
    python dogrula.py --schema yapi path/to/file.json
    python dogrula.py --self-test
Exit codes: 0 valid · 1 invalid · 2 no schema / unreadable
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMAS = os.path.join(HERE, "..", "schemas")
PY = {"object": dict, "array": list, "string": str, "integer": int, "number": (int, float), "boolean": bool, "null": type(None)}


def type_ok(value, t):
    for name in ([t] if isinstance(t, str) else t):
        want = PY[name]
        if isinstance(value, bool) and name in ("integer", "number"):
            continue
        if isinstance(value, want):
            return True
    return False


def check(value, schema, path="$"):
    """-> [error strings]."""
    errs = []
    if "type" in schema and not type_ok(value, schema["type"]):
        return [f"{path}: {schema['type']} bekleniyordu, {type(value).__name__} geldi"]
    if "enum" in schema and value not in schema["enum"]:
        errs.append(f"{path}: {value!r} izinli degerlerden degil {schema['enum']}")
    if isinstance(value, dict):
        for k in schema.get("required", []):
            if k not in value:
                errs.append(f"{path}: zorunlu alan yok: {k}")
        props = schema.get("properties", {})
        for k, v in value.items():
            if k in props:
                errs += check(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}: beklenmeyen alan: {k}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errs += check(v, schema["additionalProperties"], f"{path}.{k}")
    if isinstance(value, list) and "items" in schema:
        for i, v in enumerate(value):
            errs += check(v, schema["items"], f"{path}[{i}]")
    return errs


def load_schema(name):
    p = os.path.join(SCHEMAS, f"{name}.schema.json")
    with io.open(p, encoding="utf-8") as f:
        return json.load(f)


def validate_file(path, name=None):
    name = name or os.path.splitext(os.path.basename(path))[0]
    try:
        schema = load_schema(name)
    except OSError:
        return None, [f"sema yok: {name}"]
    try:
        with io.open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return None, [f"okunamadi: {e}"]
    return schema, check(data, schema)


def self_test() -> int:
    ok = []

    def t(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    s = {"type": "object", "required": ["a", "e"], "properties": {
        "a": {"type": "integer"}, "b": {"type": ["string", "null"]},
        "e": {"type": "array", "items": {"type": "object", "required": ["tier"], "properties": {"tier": {"enum": ["K", "H"]}}}}}}
    t("gecerli belge: hata yok", check({"a": 1, "b": None, "e": [{"tier": "K"}]}, s) == [])
    t("eksik zorunlu alan yolu ile", any("zorunlu alan yok: a" in x for x in check({"e": []}, s)))
    t("yanlis tur: bool sayi sayilmaz", check({"a": True, "e": []}, s) != [])
    t("dizi ogesi icinde enum ihlali yolu ile", any("$.e[1].tier" in x for x in check({"a": 1, "e": [{"tier": "K"}, {"tier": "X"}]}, s)))
    t("additionalProperties false: fazla alan", check({"x": 1}, {"type": "object", "additionalProperties": False}) != [])
    names = [n.split(".")[0] for n in os.listdir(SCHEMAS) if n.endswith(".schema.json")]
    t("her cikti icin sema var", set(names) >= {"rontgen", "yapi", "kapsam", "belge", "paket", "sonda"})
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "kapsam.json")
        with io.open(p, "w", encoding="utf-8") as f:
            json.dump({"share": "yuzde"}, f)
        _, e = validate_file(p)
        t("gercek sema bozuk kapsam.json'u reddeder", e != [])
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


def main() -> int:
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("files", nargs="*")
    ap.add_argument("--schema")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    rc = 0
    for f in a.files:
        schema, errs = validate_file(f, a.schema)
        if schema is None:
            print(f"OLCULMEDI {f}: {errs[0]}"); rc = max(rc, 2)
        elif errs:
            print(f"GECERSIZ  {f}: {len(errs)} hata"); print("\n".join("  " + e for e in errs[:20])); rc = max(rc, 1)
        else:
            print(f"gecerli   {f}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
