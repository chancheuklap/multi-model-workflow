# Probe every checker

The failure that costs the most is a checker that silently does nothing: a type-aware linter that never found its engine, a checker baseline that swallows everything, a rule set that excluded the directory it was aimed at. All three report success.

So write a file that must fail, run the checker on it, confirm it fails, delete it. One probe per checker, each aimed at the mechanism you would otherwise be trusting:

| Checker | Probe |
| --- | --- |
| Type checker with a baseline | A new type error in a new file — the baseline must not cover it |
| Type-aware linter | A floating promise, or anything else undecidable without type information |
| Template linter | An unclosed tag and an image without alt text |
| Formatter | A badly formatted file — `--check` must reject it |

Report each checker's count **and** its probe result. A count alone does not distinguish a clean repository from a checker that never ran.
