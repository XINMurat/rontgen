# Citations and delivery — step 6 details

**One claim, one anchor.** A cited line supports only what is on it: a
declaration supports "declared here", a header comment supports only
itself. A sentence or table cell that says more — a list, a count, a
"never", a "therefore" — cites the lines that show each part, or a range
that contains them, or carries `[H]`. `atif.py` checks that the anchor is
still on its line; it cannot check that the sentence follows from it.
Two forms fail a second reader most often: a citation "near" a line
(`file.c:490 civari`) — cite the line itself or a range, never an
approximate one — and a generalisation from one place ("all `*.ctab`",
"always") — say how many places you looked at, or tag it `[H]`. A third
form: the right line with an intent, a scope or a process note laid on it
("on purpose", "the only entry", "recorded in the log"). None of these is
on a line; write them apart from the citation, or tag them `[H]`.

`kapsam.md` also lists **cited but unread** lines: an anchor that no range in
`okunan.tsv` contains. Each one was cited without its context being read, or
its range was never written down; open it, or record the range you read.

Without git the same four commands run: anchors are tied to the files as
they are and labelled commit-less, and whether a file changed after it was
read (`DEGISTI`, `BAYAT`) is unmeasured; only a moved anchor is caught.

The checklist may be saved next to the documents: `atif.py` does not read
it, nor a `doc.md:12` that points at another document, as a citation.
Nor the core's own reports in the output folder, nor a quoted line: quote a
script's message in a `>` line, or it is counted as your citation.

**A table cell is a claim.** In one run every sentence a blind reader
faulted was a table cell — a role, a list of variants, an abbreviation —
whose cited line held only part of it. Cite the field or the range that
shows the whole cell, or leave the extra words out. `--ornek` now gives
table rows at least a third of the checklist when the documents have them.

**A signature supports a name, not a behaviour.** Across four blind checks
on two repositories, the skill's most frequent miss was a function's or a
type's declaration line cited for what it does ("`Run` turns arguments into
options", "`rebuildImpl`: scan, compile, write"). The declaration shows the
name and the parameters; what the function does is in its body. Cite the
range of the lines that do it, or say only that it is declared there.

**A measured number names its report.** The second most frequent miss was a
count (lines, commits, file pairs, "the largest hotspot") written next to a
code citation, as if the line showed it. Write the number with its source
(`rontgen.md`, `yapi.md`) and keep the code citation for what the code says.
