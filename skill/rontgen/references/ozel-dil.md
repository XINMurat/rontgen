# A language of the project's own — step 1

When the logic lives in a language the repository defines for itself — a DSL,
an experimental systems language with its compiler alongside — the
unclassified-extensions list is the first sign: many files of one extension
the scripts do not know. Do not read those files first. Read the project's
own specification of the language (grammar, spec, taxonomy documents;
`belge.md` ranks them by how many existing paths they name), and describe the
language in the config:

```json
{"extra_sources": {".path": {"name": "Path",
  "import": "^\\s*use\\s+([\\w.:/]+)",
  "decl": "^\\s*(?:fn|type|cage)\\s+(\\w+)",
  "comment": "//"}}}
```

`import` (one capture group: the target, `a.b`, `a::b` or `a/b`) gives `[K]`
edges to files of the same language; `decl` gives the outline and name edges;
`comment` keeps comment text out. Quote the spec lines you took each pattern
from in the session log: the patterns are the spec's claim about the language,
and a wrong one shows as unresolved imports in `yapi.md`. The glossary then
carries the language's own terms, cited to the spec.
