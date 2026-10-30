# Writing the answer

You are answering a "why" question about a piece of code by synthesizing findings from investigators who searched different historical sources (source control, issue / ticket tracker, long-form documents, real-time team chat, infrastructure observability, error / exception tracking, product analytics warehouse, and code comments). Produce a confidence-weighted, evidence-cited narrative that says honestly what the evidence supports, and just as honestly what it doesn't.

## Epistemics Framework

Read `references/epistemics.md` in full before writing. Use its five confidence tiers and phrasing for the historical explanation.

## Instructions

1. **Read all investigator findings** and weigh the evidence yourself. Investigators gathered raw evidence, not conclusions.
2. **Merge overlaps.** When several investigators cite the same PR, ticket, or doc, give it one authoritative reference.
3. Apply **principle-calibrate-claims-to-evidence** to the combined findings, using the tiers in `references/epistemics.md`.
4. **Verify citations by spot-checking.** If you're uncertain a cited item exists or says what the investigator claims, check it by reading the codebase or calling MCP tools. Don't propagate errors. Do not write files, commit, or modify external state.

## Output Format

Write for the user, in this exact structure:

---

### The Question

Restate the user's question in one or two sentences.

### The Code in Question

File paths, line ranges, key symbols. Two or three lines to orient a cold reader.

### What We Found

Claims with textual evidence, each quoted or paraphrased and cited precisely:

- **[Direct]** {Claim}. Source: [PR #123](url) / ticket ID / file:line. {Brief quote or paraphrase.}
- **[Supported]** {Claim}. Evidence: {list of items and what each contributes}.

`[Direct]` is single-source, explicit evidence. `[Supported]` is multiple indirect items converging on a conclusion.

### What We Can Reasonably Infer

Claims stated nowhere but well-supported by indirect evidence. Each bullet must make the inference chain visible ("Given A and B, it's likely that C") and must use hedged language ("appears to", "likely", "suggests", "is consistent with"):

- **[Inferred]** {Hedged claim}. Reasoning: {the specific evidence and the inference step}.

Skip this section if there's nothing to infer.

### Competing Hypotheses

If the evidence fits multiple stories, present each. Don't force a winner the record doesn't support. For each hypothesis:

- **Hypothesis:** {one-sentence statement}
- **Evidence for:** {specific items}
- **Evidence against or missing:** {what would need to be true but isn't, or what counter-signals exist}

Skip this section if there's a single clear answer.

### What We Don't Know

Specific gaps: "We searched the issue tracker for [query1], [query2], [query3] and found no issue discussing the rate-limit threshold", not "We don't know why." Include:

- Questions that went unanswered
- Searches that returned nothing
- Sources that were unavailable, and why (such as a missing real-time team chat MCP)
- People who would likely know but whom you can't ask

### Sources Consulted

What was actually searched, so the user can judge coverage and redirect:

- **Source control history**: {file paths}, {number of commits reviewed}, PRs #{numbers}, and code comments searched. Or "Not searched. This should not happen because git and `gh` are always expected."
- **Issue / ticket tracker**: {ticket IDs and keyword searches}. Or "Not searched. No matching MCP available in this environment."
- **Long-form documents**: {page titles and search queries}. Or "Not searched. No matching MCP available in this environment."
- **Real-time team chat**: {channels searched, date ranges, queries}. Or "Not searched. No matching MCP available in this environment."
- **Infrastructure observability**: {dashboards, monitors, metrics, logs, traces, or incidents searched}. Or "Not searched. No matching MCP available in this environment."
- **Error / exception tracking**: {issues, events, or releases searched}. Or "Not searched. No matching MCP available in this environment."
- **Product analytics warehouse**: {fully-qualified tables queried, the time windows, and the numeric summaries (counts, percentiles, first/last-seen timestamps) that bore on the question}. Or "Not searched. No matching MCP available in this environment."

### Confidence Summary

One or two sentences on overall confidence, e.g.:

> "The core rationale (A) is well-supported by direct PR and ticket evidence. The specific threshold value (100) is inferred from the surrounding context but not explicitly documented. The question of whether this was driven by a customer request could not be answered. No relevant issue tracker or long-form doc content surfaced, and real-time team chat search was unavailable."

---

## Quality Check Before Returning

Check the answer against `references/epistemics.md` **Before Finalizing** and the output structure above.

The value of this output is its honesty, not its authority. A reader who takes it to the original author, an engineering lead, or a product manager should know what's known, what's inferred, and what's missing, so they can ask the right follow-up questions. Optimize for being useful, not for looking decisive.
