# Debt and refactor-or-rewrite — a table, not a verdict

Asked "how much debt?" or "refactor or rewrite?", fill one row per module
from the reports. Rontgen weighs; the owner decides, and the choice goes to
iskele as a task. Every cell names its report; the disposition is `[H]`.

| Module | Hotspot rank | `[K]` fan-in | In a cycle | Tests | People | Read share | Disposition |
|---|---|---|---|---|---|---|---|
| | `rontgen.json` | `yapi.json` | `yapi.json` | `rontgen.json` | `rontgen.json` | `kapsam.json` | keep / refactor / strangle / rewrite / retire |

Dispositions:

- **keep** — cold, or read and understood: cost without payoff.
- **refactor** — same behaviour, better shape, in place. Needs tests first.
- **strangle** — build the new path beside the old behind a switch, move
  callers one by one, delete the old last. The default for a large module
  that many parts lean on: never replace all of it at once.
- **rewrite** — behaviour itself is changing, and few parts lean on it.
- **retire** — nothing imports it, nothing names it (`belge.json`).

Two readings that recur:

- **No tests, high fan-in.** The first task is characterisation tests that
  pin today's behaviour, not the refactor.
- **One person, in a cycle.** That cost is knowledge before it is code: a
  module note comes before any change.

Not measured: whether a disposition from this table beats one from memory.
Do not size debt in days; name the counts that would move.
