# One analyzed retro record

The main agent writes one UTF-8 JSON file after Gather, Analyze and Decide. `retro.py finalize` reads it once; the file is neither a database nor a source of running facts. Copy `task_root`, the entire `evidence_checked` array and `observed.base_commit` from `retro.py gather`, and retain every missing or unreadable item. `observed.at` is the actual retro time. Every category gets a nonempty result: `none` only when checked evidence supports no candidate. A problem in a category requires a candidate result there. Done when the complete inventory and all seven category results occur in the file.

```json
{
  "spec": 424,
  "task_root": {"kind": "map|standalone-spec", "number": 0},
  "evidence_checked": [
    {"source": "URL|path|commit range", "status": "present|missing|unreadable", "detail": "..."}
  ],
  "previous_proposals": [
    {"url": "...", "status": "landed|no-evidence-found", "evidence": "commit|Rule id|Memory id|file|none"}
  ],
  "categories": {
    "Navigation": "none|candidate summary",
    "Automated checks": "none|candidate summary",
    "Coding standards": "none|candidate summary",
    "Global AGENTS.md": "none|candidate summary",
    "Tool economy": "none|candidate summary",
    "No-ops": "none|candidate summary",
    "Information access": "none|candidate summary"
  },
  "problems": [
    {
      "category": "...",
      "cause": "...",
      "evidence": ["event URL|commit URL|repository-relative file|check:read-only command"],
      "handled_here": "...",
      "prevention": {"destination": "<a value from SKILL.md ## Owner-approved destinations>", "text": "..."},
      "earlier_occurrences": [{"memory_id": "...", "evidence": "original event|commit URL"}],
      "proposal": null
    }
  ],
  "intent_reconciliation": {"expected": "...", "observed": "...", "gap": "aligned|diverged|unverified"},
  "review_learning": "...|none",
  "observed": {"at": "ISO-8601", "base_commit": "40-hex"}
}
```

## Primary sources and independent occurrences

A current problem needs a primary source whose opened text or output states the cause. Use a script-written event comment URL or Git commit URL for running facts and repeated occurrences. A current repository file is its path relative to the checkout root; `finalize` opens that file. A standalone observed check is `check:<command>`: supply a rerunnable, read-only `rg` command or read-only `git diff|show|log|status|grep|rev-parse|cat-file` command whose actual output states the cause. `finalize` runs its arguments without a shell and records its exit and output; a check already recorded by the pipeline uses the `ticket.checked` event URL instead. File and standalone-check sources support a problem, not the two-event-or-commit proposal threshold. Earlier occurrences name an `mmw-retro` Memory id discovered by category-plus-cause search, and the original event/commit URL in that Memory; reopen both. Two event comments on one ticket/spec are one occurrence, not two. `spec.closed.payload.memory_closing.decisions` entries with `decision=propose` supply candidate Memory record ids only; the `NIGHT SUMMARY` prose and a second proposed-id field supply none. A proposed candidate with one actual blocking event (one of the four `SKILL.md` step 12 names) may qualify if that decision's evidence URL is the problem's current source. A source that is missing or unreadable cannot support a proposal. Done when every retained problem has a primary source, independent Handled here and Prevention, and no proposal is based only on a label, title, issue closure or Memory assertion.

## Proposal and prompt replacement

When the independently verified threshold is met, `proposal` is an object with `repository` (`owner/name` responsible for the change), `title`, `body`, and optional `prompt_change`. A prompt change additionally has `target_file`, `heading`, `source` (one of the problem's primary evidence URLs), `current_passage`, `proposed_passage`, `changes_made` and `expected_behavior`. Both passages are complete; sentences unaffected by the change stay identical. `changes_made` has four nonempty answers under `context_or_constraints`, `ambiguity`, `success_criteria_or_requirement` and `timing`, each explaining whether that class changed or explicitly saying it did not. A previous proposal is `landed` only with a checked commit SHA, `Rule: <active-id>`, `nowledgemem://memory/<id>` or current repository file path; otherwise `no-evidence-found`. Done when the proposal contains the source spec, original evidence, how this instance was handled, prevention, responsible repository, destination and fixed Retro Memory id, leaving behaviour change to owner-approved tickets.
