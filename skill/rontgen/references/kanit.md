# Evidence behind the rules

Each rule in SKILL.md and these references comes from an observation below.

Draft 0.4. Not yet a member of the family: no git repository, no bilingual
docs, no package, no CI, no token budget, no schema, no eval.

Evidence so far, and its limits:

- The core has run on five repositories (C#/TypeScript, C#/SQL, Python).
  That run found generated migration files counted as source in one of them;
  the exclusion rule comes from it. On a C-heavy repository (522 C files)
  `#include` resolution raised `[K]` module edges from 1 to 123; ten edges
  checked by hand against their `#include` lines all held. Includes whose
  name exists under two roots (35 there) get no edge, although the build's
  root order would decide them. On a directory with no git at all (Rust and
  C#, 575 source files) both core scripts ran and the four history sections
  said "unmeasured"; that run also showed `src/bin` holding Rust source,
  which had been excluded as build output. On the C-heavy repository a fresh
  reader found behaviour living in 300 files of four in-house formats the
  scripts did not count; a probe lost 29 of its 40 edges to them. Naming them
  in `extra_sources` brought 290 into the measurement and cut the lost edges
  to 13; letting any existing file end a probe edge cut them to 0. The same
  run's saved checklist produced 13 false "unanchored" citations on the next
  check, and a root `CMakeLists.txt` was called ambiguous; both are fixed.
  Java and Go patterns are exercised only by self-tests. On a Rust repository
  without git (291 Rust files), the first outline missed half the
  definitions of generic code and 8 of 10 sampled name edges were wrong; after
  the Rust module (`mod` / `use` resolution, no name proxy) the outline found
  every definition in the four files checked, and 10 of 10 sampled edges held.
- The reading half has been done **five times**. The fifth repeated the
  Rust run with that rule: it opened the module map first, named 3 of the 8
  missed points (was 0) and held 16 of 20; the rest were one link further,
  which the follow-the-map rule comes from. A second fresh run on the
  C-heavy repository, after the rules above, held 12 of 20 in its blind
  check. A fresh run on the Rust repository (0.4% of lines read, no git)
  held 15 of 20 and contradicted its architecture document nowhere, but
  missed its principle, runtime, storage layout and replication: they were
  in the docs it did not open. The navigation-documents rule comes from it.
  Earlier, twice: Once on a repository its reader
  already knew (6% of the source lines read, checked by no one else). Once by
  a fresh session on the C-heavy repository it had never seen: 1.9% of the
  source lines read, 30 of 30 anchors in place, and a blind check of 20 cited
  sentences by another session (not a person) found 9 that held, 1 that did
  not and 10 that said more than their line shows — the "one claim, one
  anchor" rule comes from that. The session's map matched the repository's
  own architecture documents on mechanism and missed the authors' design
  vocabulary (layers, principles, numbered decisions); the vocabulary rule
  comes from that. Its blind reading was imperfect: the repository's
  `CLAUDE.md` was loaded into its context automatically at start.
- **With and without this skill**, once, on a small C# library no session
  had seen (1,944 lines), two fresh sessions got the same task. A blind
  reader, not told which wrote what, held 19 of 20 cited sentences from the
  skill's arm and 16 of 20 from the other; the skill's arm made no wrong
  claim, the other one. But the arm without the skill covered all 12 points
  of a reference list written from the code (the skill's arm 10) and found
  more risks. Here the skill made what was written more accurate, not what
  was understood wider; its own second reader, run before delivery, is where
  the accuracy came from (its first draft held 6 of 12). One repository, one
  sample: a hypothesis, not a measurement of the skill in general. A third
  arm, without the skill but told to have a second reader check twelve of
  its sentences before delivery, held 16 of 20 against the skill's 17 in a
  new blind sample, and covered all 12 points. On a repository small enough
  to read whole, the skill's measurable gain was that one step; its
  measuring half was not tested there. The same documents scored 19 and 17
  in two samples: differences of two or three are within the noise.
- **The same three arms on a large repository** (Rust, about 108k lines,
  its architecture document removed from the whole history). All three read
  under 2% of the source and walked the same path (key, command, edit).
  A blind reader held 18 of 20 from the skill's arm, 15 from the plain arm
  and 20 from the arm with a second reader; none made a wrong claim. Against
  a 14-point list written from the removed document they covered 5.5, 6 and
  4.5. None found the design ideas the document names (functional core,
  per-view selections, one view per split). So on a large repository too the
  measuring half did not widen the map, and the arm that ran a second reader
  was the most accurate. The skill's arm skipped its own second reader that
  time; the arm with the second reader read another arm's identical copy;
  an old version of the document survived in history under another path.
  None of these favours the skill. Taken together: the one step that has
  shown a gain twice is the second reader before delivery.
- One probe has been written (in-house artifact names → their users, 40
  edges, self-test 6/6). Whether probes pay for themselves is still a
  hypothesis.
- **A reader with the documents only** (no code) answered the same eight
  questions about that large repository: 4.5 of 8 from the skill's
  documents, 3 and 2 from the other two arms. Part of the gap came from the
  generated function outline, not the written pages; one detail misled the
  reader about a cause; and no arm said where per-view state lives. The
  architecture page and the "keep the reports" rule come from it. With code
  access all three readers answered all eight: that test was at its ceiling.
- **Version 0.5 on the same large repository** (fresh copy, one run): the
  session ran its own second reader (11 of 12 held, one shifted line fixed)
  and wrote the architecture page. Against the 14-point reference list it
  covered 10 (the earlier skill run 5.5): per-view selections, anchor and
  head, the rope and the global editor state were now found. A reader with
  the documents only answered 5.5 of 8 (was 4.5; other arms 3 and 2). A
  blind reader held 17 of 20 of its sentences and 20 of 20 of the arm with
  a second reader but no skill; the three misses were table cells whose
  cited line held only part of the cell. Wider and more useful to a reader
  without the code; not yet as accurate in its tables.
- **A second run of 0.5, with table rows weighted in the checklist**: the
  second reader caught three table cells and they were fixed, yet the
  blind reader again held 17 of 20 (the arm without the skill 20 again).
  Two of the three were "owned by" cells citing the owned type's own field:
  the architecture template's ownership column invited a claim its citation
  could not carry. The template now cites the owner's field for that cell.
- **A third run, with the ownership table citing each owner's field**: a
  blind reader held 19 of 20 from the skill's documents and 19 of 20 from
  the arm without the skill; no ownership cell was faulted. Coverage was
  8.5 of 14 and the documents-only reader 4.5 of 8 — across the three runs
  of 0.5 these drifted down (10, 9.5, 8.5; 5.5, 5, 4.5) as each run chose a
  different module to write up. Three samples cannot tell a trend from noise.
- **Five runs of 0.5 in all.** Blind accuracy 17, 17, 19, 19, 18 of 20 (the
  arm without the skill, same lists: 20, 20, 19, 18, 20); coverage 10, 9.5,
  8.5, 7.5, 10 of 14; documents-only reader 5.5, 5, 4.5, 4, 5 of 8. The dip
  after the third run was noise: the fifth went back to 10. One run is worth
  about plus or minus 1.5 on coverage; judge a change on several runs.
- **0.6 (manifests, how-a-value-is-made, module choice by fan-in × lines)**,
  three runs on the large repository: coverage 11.5, 12.5, 10.5 of 14 (0.5:
  9.1); the terminal tie, visible only in a manifest feature, found in two of
  three; the main edit interface named in all three. Blind accuracy 19, 19,
  18 of 20 (the arm without the skill 19, 19, 20).
- **A second language** (a Go bundler, ~139k lines): the core first drew 2
  resolved edges, because Go imports name a package by module path; resolving
  through go.mod gave 193. With module choice by fan-in alone the run wrote up
  a logging helper and covered 2 of 14 points (the arm without the skill 3);
  weighted by lines it chose the parser and covered 7.
