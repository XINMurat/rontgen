# Röntgen

**Maps an existing codebase and writes the documents that make it understandable — every sentence tied to a source line.**
Part of a family of Claude skills: iskele builds, mizan weighs, kiyas generates, ux-mizan audits experience, **röntgen maps**.

[English](#english) · [Türkçe](#türkçe)

---

## English

Hand Röntgen a repository you did not write. It measures first — inventory, hotspots, dependencies resolved through
each language's own imports and package manifests, blind spots, entry points, data stores — and only then reads, in
the order the measurement points to. It writes a reading order, an architecture page (what the system is made of
and who owns which state), module notes, flows, a glossary and a risk list. Every factual sentence cites
`path/file.ext:line`; a second reader who did not write the documents checks a sample before delivery.

**What it is good at, measured** (details in `skill/rontgen/references/kanit.md`): on a 108k-line Rust repository
with its architecture document removed, three runs covered 11.5 of 14 points of that document on average, against
4.5 to 6 for sessions without the skill, and held 18–19 of 20 sentences in a blind check. On a 139k-line Go
repository one run covered 7 of 14 against 3. **What it is not:** it reads 1–2% of a large codebase; its documents
say so, and name what they did not read.

**Supported:** dependency resolution for Python, TypeScript/JavaScript (relative imports), C#, C/C++, Rust, Go,
Java/Kotlin; manifests for Cargo, npm, .NET, Python, Go, Maven, Gradle; ORM tables for EF Core, SQLAlchemy,
Django, TypeORM, Prisma. Other languages are counted and labelled "unmeasured", never silently zero.
Output: Markdown always; SVG, PNG, Word, LaTeX and PDF when the machine can make them.

```bash
python skill/rontgen/scripts/rontgen.py --repo . --out rontgen-out
python skill/rontgen/scripts/yapi.py    --repo . --out rontgen-out
python skill/rontgen/scripts/paket.py   --repo . --out rontgen-out
```

A real line from `paket.md` on that Rust repository — the tie no import showed:

```text
| `helix-view` `helix-view/Cargo.toml` | rust | helix-core, helix-dap, … | 24 | helix-tui | crossterm (term), termina (term) |
```

Standard library only. Every script has `--self-test`. Documentation: [docs/](docs/index.md).

---

## Türkçe

Röntgen'e yazmadığınız bir depo verin. Önce ölçer — envanter, sıcak noktalar, her dilin kendi import'ları ve paket
bildirimleri üzerinden çözülen bağımlılıklar, kör noktalar, giriş yüzeyi, veri depoları — sonra ölçümün gösterdiği
sırayla okur. Bir okuma sırası, bir mimari sayfası (sistem neyden yapılmış, hangi durumu kim tutuyor), modül notları,
akışlar, bir sözlük ve bir risk listesi yazar. Her olgusal cümle `yol/dosya.uzanti:satir` gösterir; teslimden önce
belgeleri yazmamış bir ikinci okuyucu bir örneklemi denetler.

**Ölçülen başarısı** (ayrıntı `skill/rontgen/references/kanit.md`): mimari belgesi çıkarılmış 108 bin satırlık bir
Rust deposunda üç koşu, o belgenin 14 maddesinden ortalama 11,5'ini kapsadı; skill'siz oturumlar 4,5–6. Kör denetimde
20 cümleden 18–19'u tuttu. 139 bin satırlık bir Go deposunda tek koşu 14'te 7 kapsadı (skill'siz 3). **Ne olmadığı:**
büyük bir kod tabanının %1–2'sini okur; belgeleri bunu söyler ve okumadığını adıyla yazar.

**Desteklenen:** Python, TypeScript/JavaScript (göreli import), C#, C/C++, Rust, Go, Java/Kotlin bağımlılık çözümü;
Cargo, npm, .NET, Python, Go, Maven, Gradle paket bildirimleri; EF Core, SQLAlchemy, Django, TypeORM, Prisma tabloları.
Diğer diller sayılır ve "ölçülmedi" diye etiketlenir, sessizce sıfır yazılmaz. Çıktı: her zaman Markdown; makine
üretebiliyorsa SVG, PNG, Word, LaTeX ve PDF.

Yalnız standart kütüphane. Her betiğin `--self-test`'i var. Belgeler: [docs/](docs/index.md).

---

Code MIT · prose CC BY 4.0.
