# Vocabulary recheck (2026-09-29): brief for each verifier

Twelve slice reviewers examined every glossary entry (492, in `docs/contexts/*/CONTEXT.md`) to the standard in `BRIEF.md` beside this file, and wrote `candidates/<slice>.md`. Each proposed RENAME, FIX-NAME or UNSURE verdict is a claim until someone who did not make it checks it. You are that someone: your job is to find what is wrong with each proposal you are given, and to keep only what survives.

Read first: `BRIEF.md` (the standard and its sources), then `docs/reviews/2026-09-28-lightweight/vocabulary.md` (what was decided yesterday), then the candidate rows you are assigned, in their files.

## For each proposal

Check, and write down what you found, not what the reviewer said:

1. **The facts the proposal rests on.** Re-run the greps yourself across `mmw-v2/`, `docs/`, `AGENTS.md`, `CONTEXT-MAP.md`: "appears nowhere else", "the text already uses X", "no program reads this value", occurrence counts, line numbers. A proposal whose premise is false is rejected on that ground.
2. **The source and the meaning.** Is the proposed term really the established term of its field, in the sense claimed? Open the source (WebFetch or WebSearch) when it is an outside term, and cite the URL. Does the term bring in behaviour the concept does not have (a false friend)? Is the match exact, or only close?
3. **Collisions.** Grep the new name across all seven contexts, `mmw-v2/upstream/CONTEXT.md` and the skill text. A new name that collides with an existing one only moves the problem.
4. **Scope.** Machine identifiers (CLI verbs and flags, event names, JSON fields, output tokens and columns, labels, file names, headings a program or a reader finds by position) are not renamed in this round. Text the owner reads on a product surface (the task board page, a host's skill listing) is the owner's decision.
5. **Cost against gain.** How many places change (count them), and does the reader of the skill text actually gain a sharper concept?

Give each proposal one outcome:

- **ADOPT**: survives every check, as proposed.
- **ADOPT-CHANGED**: the problem is real but the proposed name or scope is wrong; give the corrected name or scope and why.
- **DEFINITION-ONLY**: the name stays; the entry's definition, `_Avoid_` line or a leading word needs changing; say exactly what.
- **REJECT**: say which check it fails.
- **OWNER**: only the owner can decide (an identifier or a product surface would have to change); state the decision in one sentence and what each answer costs.

A rejection is as valuable as an adoption. Do not adopt a proposal because a reviewer argued it well; do not reject one to look strict.

## Output

Write only `verify/<group>.md` (your group name is in your task). Do not edit any other file; do not commit. The file holds one table, one row per proposal: `| # | entry (context) | proposal | outcome | final name or change | evidence (what you checked, with paths or URLs) | places that change (count and list) |`. Then a short `## Notes` section for anything the proposals missed.

Your final message: the count per outcome, and every row in full.
