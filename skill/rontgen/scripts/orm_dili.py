#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- tables declared through an ORM rather than in SQL.

WHY THIS EXISTS
---------------
On a C# repository whose whole schema lives in an EF Core context, the
stores section said "0 tables": it read only SQL files. The tables were one
file away, as `DbSet<Entity> Name` properties. This module reads the common
declarations and reports each table with the file that declares it:

  EF Core       public DbSet<Entity> Name           -> table Name
  SQLAlchemy    __tablename__ = "name"              -> table name
  Django        class Name(models.Model)            -> table Name
  TypeORM       @Entity("name") / @Entity() class N -> table name / N
  Prisma        model Name {   (in .prisma files)   -> table Name

Use is counted as `[H]`: a file that touches `.Name` (EF), `Name.objects`
(Django) or the model class is listed as a reader; an ORM call cannot be told
apart from a read without running it, so nothing is called a write.
"""
from __future__ import annotations

import re
import sys

EF = re.compile(r"\bDbSet<\s*(\w+)\s*>\s+(\w+)")
SQLA = re.compile(r"__tablename__\s*=\s*[\"'](\w+)[\"']")
DJANGO = re.compile(r"^class\s+(\w+)\((?:[\w.]*\.)?Model\)", re.M)
TYPEORM = re.compile(r"@Entity\(\s*(?:[\"'](\w+)[\"'])?[^)]*\)\s*(?:export\s+)?class\s+(\w+)")
PRISMA = re.compile(r"^model\s+(\w+)\s*\{", re.M)


def tables(files: dict) -> dict:
    """files = {path: (family, text)} -> {table: (path, model or None)}"""
    out = {}
    for p, (fam, text) in files.items():
        found = []
        if fam == "cs":
            found = [(prop, ent) for ent, prop in EF.findall(text)]
        elif fam == "py":
            found = [(n, None) for n in SQLA.findall(text)] + [(n, n) for n in DJANGO.findall(text)]
        elif fam == "web":
            found = [(n or c, c) for n, c in TYPEORM.findall(text)]
        elif p.endswith(".prisma"):
            found = [(n, n) for n in PRISMA.findall(text)]
        for name, model in found:
            out.setdefault(name, (p, model))
    return out


def uses(files: dict, orm: dict) -> dict:
    """-> {table: set(files that touch it)} for the ORM tables, [H]."""
    out = {t: set() for t in orm}
    pats = {t: re.compile(r"\." + re.escape(t) + r"\b" + (r"|\b" + re.escape(m) + r"\b" if m else "")) for t, (_, m) in orm.items()}
    for p, (_, text) in files.items():
        for t, rx in pats.items():
            if p != orm[t][0] and rx.search(text):
                out[t].add(p)
    return out


def self_test() -> int:
    ok = []

    def check(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    files = {"Data/Ctx.cs": ("cs", "class Ctx : DbContext { public DbSet<AppUser> Users => Set<AppUser>(); "
                                    "public DbSet<Order> Orders { get; set; } }"),
             "Api/U.cs": ("cs", "var u = db.Users.Find(id);"),
             "Api/X.cs": ("cs", "var users = 3; // Users"),
             "m.py": ("py", "class Kayit(models.Model):\n  pass\nclass T(Base):\n  __tablename__ = 'olay'\n"),
             "e.ts": ("web", "@Entity('musteri')\nexport class Customer {}\n@Entity()\nclass Fatura {}"),
             "schema.prisma": ("", "model Post {\n id Int @id\n}\n")}
    t = tables(files)
    check("EF: ozellik adi tablo, varlik model", t["Users"] == ("Data/Ctx.cs", "AppUser") and "Orders" in t)
    check("SQLAlchemy, Django, TypeORM (adli/adsiz), Prisma",
          {"olay", "Kayit", "musteri", "Fatura", "Post"} <= set(t) and t["musteri"][1] == "Customer")
    u = uses(files, t)
    check("kullanim: .Users dokunan dosya okur sayilir; ayni ad yerel degisken degil", u["Users"] == {"Api/U.cs"})
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else 0)
