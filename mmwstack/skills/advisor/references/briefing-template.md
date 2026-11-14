# Advisor brief

Fill every section. Quote evidence verbatim and summarize only narrative. Redact secrets. A stranger with only this brief and the repository must be able to reconstruct the decision. For a problem that resisted repeated attempts, each attempt and what it produced is the core of the evidence.

Your framing is what the advisor checks, so leave the advisor's work to the advisor. Write no list of what to check, no file it should skip and no conclusion for it to confirm. Keep a "which option" question about the options, not one option's details.

```markdown
## Checkpoint

<major decision | stuck | operator's question> — <one line on why now>

## Operator's request

<the original request, verbatim>

<later constraints or corrections from the operator, verbatim, in order>

## What has happened so far

<chronological and compact: what you investigated, decided, changed, tried, and ruled out, with the reason for each>

## Evidence

<verbatim tool output relevant to this checkpoint: errors, stack traces, test output, command output, the relevant diff hunks. Trim unrelated noise and mark trims with [...]>

## Current state

<repository, branch and commit; `git status --short` and `git diff --stat` output; approved baselines; anything half-done>

## Constraints you believe bind

<constraints from the request, the spec, the ticket or the codebase>

## Options and your leaning

<For a decision: the options with the tradeoffs as you see them, and your current leaning with reasons.
For stuck: what you expected vs. what you observed, and the hypotheses you have ruled out.>

## Questions for the advisor

1. <specific question>
2. ...

## Relevant paths

<files and directories you believe matter>
```
