<!-- GENERATED PAGE - do not edit here.
     Source of truth: skill/rontgen/references/olcum.md
     Regenerate:      python tools/sync_en_docs.py
     CI (`--check`) fails if this page drifts from its source. -->

# Steps 1–2 — measuring

> **Mirrored from the skill package.** This is the canonical English text that
> Claude actually loads, published here so it can be read next to its Turkish
> mirror instead of only on GitHub. Edit the source above, not this
> page; the Turkish mirror is `docs/tr/olcum.md`.

## Measuring — details for steps 1 and 2

SKILL.md keeps the loop; this file keeps the details the core's
runs taught.

### Running and configuring

Run them as plain `python scripts/<name>.py` from anywhere; they import each
other, so `python -I` fails. If you may not write to the repository, keep
`rontgen.config.json` and any probes in the output folder and pass
`--config` to `rontgen.py`, `yapi.py` and `belge.py`; `probe_results` are looked up next
to the config file first, then from the repository root. `atif.py` and
`kapsam.py` take no config: they read the output folder, which carries it.

Run them first, read code second: reading first anchors you on whichever
file you opened. With no git history, churn, coupling and knowledge are
**unmeasured**, not zero. Without git the files are read from the directory;
build and hidden directories are not entered, and each one is listed.

Then read the **"Olcume girmeyenler"** list. The scripts exclude what looks
generated (bundles, migrations, `*.Designer.cs`, files marked generated). If
something hand-written is on it, or something generated is not, put the
correction in `exclude_globs` and re-run — do not carry the error forward.
Hand-written code that is dead on purpose (an `_archive/`, a parked copy) is
excluded the same way, by your decision: it distorts the hotspots and the
coverage, and the documents name it as out of scope rather than mapping it.
Borrowed code that is live (a trimmed upstream library the project calls)
stays measured; it may be left unread, but the documents say what the
project uses it for — one run called such a copy "out of scope" and the
architecture rested on it.
Read the **unclassified extensions** the same way: if behaviour lives in
files the scripts do not know as source (a DSL, a table format), name them
in `extra_sources`. They are then counted, measured and may end a probe
edge; they are never parsed. If the program starts somewhere other than a
`main` (a kernel entry, a plugin hook), name that function in
`entry_points`; the entry surface shows it with its line, and a name that is
not found is reported as such. Entry names are never guessed. A `main` is
found by pattern (C anywhere, Rust only in a binary target); a name that
also occurs in libraries is given with its path, `src/plugins/*:start`.

### Edge tiers

Solid arrows are `[K]`: a declared dependency that resolves in the
repository. Dashed arrows are `[H]`: a name declared in one file and used in
another. A C / C++ `#include` is `[K]` only when it resolves to exactly one
file in the repository; the include roots it was resolved against are
printed with their source, and ambiguous or unresolved includes are counted
as blind spots, not drawn. A Rust `mod x;` or `use crate::…` / `use
<crate>::…` is `[K]` when it reaches a file of a crate in the repository;
Rust gets no `[H]` name edges at all — on a real repository they were wrong
in every case checked. Only `[K]` edges make a cycle; an `[H]` cycle is a **candidate** and
is called one until a reader confirms it.
