# Probes — step 3

The blind-spot table counts mechanisms the fixed scripts cannot follow:
dependency injection, reflection, an ORM, SQL built from parts, events,
interfaces. Where a count is large the diagram is missing real edges.

You may write a small project-specific script — a **probe** — that resolves
one of those mechanisms for this project and turns `[H]` into `[K]`. The
rules exist because a free-form tool breaks three things at once (read the
head of `scripts/sonda.py`):

- **Gap first.** A probe is written for a row of the blind-spot table, or
  for an unclassified extension that carries behaviour (step 1), produced
  before any code was read — never for a pattern you noticed while
  reading. A tool written after reading measures what you already saw.
- **Tested, with a control.** A probe has a `--self-test`, and may claim `[K]`
  only if it names a known positive it found and a known negative it did
  not. A result that does not say its self-test passed in full is refused.
- **Any existing file may end an edge.** A probe edge may point at a table,
  a DSL file or a build script, not only at measured source; such ends are
  drawn and counted as "kaynak disi". An end the measurement excluded is
  refused and counted, and a path that does not exist is "unknown".
- **Kept, with its commit.** The probe and its result live in `sondalar/`
  (in the repository, or in the output folder when the repository is not
  yours to write) and are listed under `probe_results`. Its numbers are their
  own series; they are never folded into the core's scorecard, so the core
  stays comparable across projects and across time.

Prefer a real tool over a written one: a compiler's own analysis (Roslyn,
`tsc`, `go list`), the ORM's schema dump, the framework's route listing. A
probe that wraps one of those is a few lines and is `[K]` by construction.
Do not write a parser for a language.
