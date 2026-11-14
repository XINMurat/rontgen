<!-- GENERATED PAGE - do not edit here.
     Source of truth: skill/rontgen/references/okuma.md
     Regenerate:      python tools/sync_en_docs.py
     CI (`--check`) fails if this page drifts from its source. -->

# Step 4 — reading

> **Mirrored from the skill package.** This is the canonical English text that
> Claude actually loads, published here so it can be read next to its Turkish
> mirror instead of only on GitHub. Edit the source above, not this
> page; the Turkish mirror is `docs/tr/okuma.md`.

## Reading — step 4 in full

For each of the top hotspots (five is usually enough), open the file and
answer: what is it responsible for, what does it know about that it should
not, what can a change here break elsewhere. Check the coupling table against
the code: a pair that changes together with no visible dependency is a hidden
contract — find it and name it. Without git there are no hotspots and no
coupling table: rank modules by `[K]` fan-in (`yapi.md` gives it per
module), then within the module files by size and by no test naming them,
and write that this was the order.

Before the first hotspot, open the project's **own navigation documents**: a
docs index, a contributor's code map, an "adding a command" checklist. They
are claims, checked against the code like any other, but they are where the
axis is written down. One run read 900 lines of code and missed the
principle that a module map in the docs states in its first sentence.
`belge.md` ranks the documents by how many existing code paths they name;
on that repository the module map came first. A module no document names
is where the docs cannot help; a named path that does not exist is `[H]`
until opened — most were run outputs and placeholders, not stale code.
Then follow the map: open the documents it lists as design (layout,
memory, durability) before the code they describe. A second run opened the
map, did not follow its links, and missed the storage layout, the runtime
and replication — each one document away. A broken link in `belge.md` is a
document the set has lost; say so where the map would have pointed.
A checklist of the places one change touches ("adding a command": twelve
files, each with what catches a missed step) is the project's own
change-together table; without git it stands in for the coupling table.
A step it marks as caught by nothing is a hidden contract: check it in code.

Look for the project's **own design vocabulary** while you read: numbered
decisions (`ADR-030`), layer names (`L0`–`L4`), principle codes (`P3`) that
recur in comments, and named invariants in those documents. They are the axis the authors think in; a map drawn only
along directories can be right and still miss it. Name each one in the
glossary with where it is defined. If the repository has its own
architecture documents, set their stated date against the last commit: a
document that calls itself current but is older than much of the history is
a finding. Without git its age is unmeasured; file times of a copy are not.

**Record every range you open** in `okunan.tsv` and every line you will cite
in `atiflar.tsv`, as you go. Ranges in files that are not measured source
(a build script, a table) belong there too: they are counted apart and never
raise the share. Both are one line each; neither can be rebuilt
honestly afterwards. An anchor proves the text on a line, not which function
holds it: if the same text occurs twice in the file, the sentence names the
enclosing function. `atif.py` warns about such anchors (`COKLU`); choose a
longer piece of the line.
