# Vocabulary recheck (2026-09-29): brief for each slice reviewer

The 2026-09-28 round (`docs/reviews/2026-09-28-lightweight/vocabulary.md`) renamed about twenty of MMW's concept names (rows R1-R12, S1-S8) and kept the rest. The owner doubts that the other ~460 glossary entries were each actually examined. This recheck examines every entry of the glossary, one by one, to the same standard, and records a verdict for each. It proposes; it renames nothing.

## The standard

Read these before starting, in full:

- `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL-SET-RULES.md` `### Vocabulary`: the naming order (the established term of its field whose meaning matches exactly; failing that, ordinary dictionary words; failing that, a coined term defined in one sentence), false friends, identifiers, metaphors, colloquial phrases, completeness.
- `mmw-v2/upstream/skills/productivity/writing-for-agents/SKILL.md` `## Leading words`: why an established term is worth more than a coinage.
- `docs/reviews/2026-09-28-lightweight/vocabulary.md`: `## Scope` (machine identifiers and upstream's own vocabulary do not change), the rename tables (the grain of a good rename: concept, old name, new name, source, why exactly), `## Kept, with the reason`, and `## Second pass`'s "Not adopted" paragraph.
- `CONTEXT-MAP.md`, for how an entry is read and the seven contexts.

## What to do for each entry in your slice

An entry is a bold line (`**name**:`) under `## Language`. For each one:

1. Read the definition, and open its `_Home_` far enough to know what the concept is and how the skill text actually uses the word (grep `mmw-v2/` for the name to see its uses).
2. Ask, in the naming order: is there an established term of some field (software engineering, testing, release engineering, distributed systems, messaging, version control, SRE and operations, project management, UI and design, agent engineering) whose meaning matches this concept exactly? Where to look: the books `SKILL-SET-RULES.md` names; ISO/IEC/IEEE 24765 (SEVOCAB) and IEEE 610.12; Hohpe and Woolf, *Enterprise Integration Patterns* (events, queues, channels, acks); Kleppmann, *Designing Data-Intensive Applications*; Humble and Farley, *Continuous Delivery*; Google's *Site Reliability Engineering*; `gitglossary(7)` and GitHub's own documentation terms; Anthropic's "Building effective agents"; Matt Pocock's *Dictionary of AI Coding*. Use WebSearch or WebFetch to confirm what a candidate term means in its field when you are not certain, and cite the URL.
3. Check a candidate against the concept before proposing it: does it bring in behaviour the concept does not have (a false friend, worse than a plain coinage)? Does it collide with a name already used in any of the seven contexts (grep `docs/contexts/`) or in upstream's vocabulary (`mmw-v2/upstream/CONTEXT.md`)? Is the current name in fact a machine identifier (then it stays, per `## Scope`)?
4. Also judge the current name on its own: a metaphor that is not a leading word, a colloquial phrase, a coinage with no definition, one word for two concepts, two words for one concept, an `_Avoid_` line that bans the established term. Each is a finding even when you have no replacement to offer.

Record one verdict per entry:

- **KEEP-ESTABLISHED**: the name is already the established term, used in its field's sense. Name the field or source.
- **KEEP-PLAIN**: the name is ordinary descriptive words and no established term matches exactly. Name the established terms you checked and say in a few words why each does not fit. A KEEP-PLAIN with no terms checked is not a verdict.
- **IDENTIFIER**: the name is a string a program, the tracker or a consuming repository reads; it stays. Say whether the prose also uses a second name for it (that second name is then a finding).
- **UPSTREAM**: upstream's own term used in upstream's sense.
- **RENAME**: propose the new name, its source, why the meaning matches exactly, which identifiers stay, and what else in the glossary or skills would change with it.
- **FIX-NAME**: the current name has a defect from step 4 and you found no replacement; state the defect.
- **UNSURE**: you could not settle it; state what would settle it.

A KEEP with a stated reason is a complete result. The owner's question is whether every entry was examined, not how many renames come out; a rename proposed to look thorough, or a borrowed term that fits only loosely, costs more than it gains, because every rename is applied across every skill. Rows R1-R12 and S1-S8 are decided: reopen one only if its new name is itself a false friend or a clearly better established term exists. The "Kept" and "Not adopted" reasons are claims: recheck them if they fall in your slice.

Beyond the entries: while reading the `_Home_` files and the entries' own text, list any concept the text uses with no entry in any context (grep all seven), and any word that names two different concepts across contexts.

## Output

Write only your output file, `docs/reviews/2026-09-29-vocabulary-recheck/candidates/<slice>.md`. Do not edit any other file, do not commit.

The file holds:

1. A header line: the slice (file and line range), and the number of entries in it.
2. A table with exactly one row per entry, in file order: `| entry | verdict | proposed name | source | reason | identifiers that stay | collisions |`. Leave cells that do not apply empty. The row count must equal the entry count in the header.
3. `## Concepts with no entry`, and `## One word, several concepts`, each a short table or "none found".

Write in English. Keep each reason to what a reader needs to accept or reject the verdict.

Your final message: the entry count, the count per verdict, and every RENAME and FIX-NAME row in full.
