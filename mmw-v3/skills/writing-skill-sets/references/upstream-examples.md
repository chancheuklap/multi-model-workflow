# Upstream examples

mattpocock's own skills show several checks done well. The in-repository copies under `mmw-v2/upstream/skills/` carry this repository's edits; read the original from the latest squash commit (found as `mmw-v2/merge-notes/README.md` says), with `git show <commit>:skills/<bucket>/<skill>/<file>`. The in-progress `retro` below is upstream's, not MMW's own `retro` skill.

| Check | Upstream file | What to look at |
| --- | --- | --- |
| What skill text is for | `engineering/wayfinder/SKILL.md` opening, `## Plan, don't do`, `## Fog of war`; `productivity/grilling/SKILL.md` last two paragraphs | purpose and stance in a few sentences, which the agent carries into cases no step names |
| Descriptions | `engineering/wizard/SKILL.md`, `engineering/prototype/SKILL.md` | the trigger branches; one explicit non-trigger |
| Load and disclosure | `engineering/prototype/SKILL.md` with `LOGIC.md` and `UI.md` | each branch file whole, each naming the other branch for a reader who took the wrong one |
| Load and disclosure | `engineering/codebase-design/SKILL.md` `## Going deeper` | each pointer carries its condition |
| Load and disclosure | `productivity/to-questionnaire/SKILL.md`, `engineering/to-spec/SKILL.md` | the template stays inline because every run writes one |
| Redundancy and bloat | `engineering/code-review/SKILL.md` `## Why two axes` | the one reason kept, because without it the agent would merge the axes |
| Scripts and judgement | `engineering/wizard/SKILL.md` | "The delightful UX is already solved by template.sh ... Your job is only to scope the procedure and author its stages" |
| Scripts and judgement | `engineering/code-review/SKILL.md` `### 3. Identify the standards sources` | the smell baseline: each item is what it is and how to fix it, marked "always a judgement call" |
| Scripts and judgement | `engineering/code-review/SKILL.md` `### 1. Pin the fixed point` | "A bad ref or empty diff should fail here, not inside two parallel sub-agents": one early check, placed where it saves the most |
| Scripts and judgement | `in-progress/retro/SKILL.md` | a mechanical violation gets a deterministic check; the standards document keeps only judgement calls |
| Vocabulary | `engineering/codebase-design/SKILL.md` `## Glossary`; `engineering/improve-codebase-architecture/HTML-REPORT.md` `## Tone` | "Use these terms exactly"; "Use exactly" / "Never substitute"; each term with its `_Avoid_` line, and its source where it has one (**Seam** _(Michael Feathers)_) |
| Vocabulary | `engineering/to-tickets/SKILL.md` `### 3. Draft vertical slices` | **tracer bullet**, a term from *The Pragmatic Programmer*, carrying a whole way of cutting work in two words |
| What skill text is for (fact 7) | `productivity/grill-me/SKILL.md`, `engineering/grill-with-docs/SKILL.md` | the whole skill is one line naming the skill that owns the method |
| Hand-offs | `productivity/grilling/SKILL.md` | facts (look them up) kept apart from decisions (put them to the user); the end stated as "the frontier is empty" |
| Hand-offs | `engineering/to-spec`, `to-tickets`, `triage` against `tdd`, `diagnosing-bugs` | a hard dependency names `setup-matt-pocock-skills` in one line; a soft one only says to read the domain glossary if it exists |
| Prompts | `engineering/code-review/SKILL.md` `### 4. Spawn both sub-agents in parallel` | the Standards subagent gets the smell baseline "pasted in full (the sub-agent has no other access to it)", and a length limit |
| Examples | `engineering/triage/AGENT-BRIEF.md` | good and bad briefs side by side, with why the bad one fails |
