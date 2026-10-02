---
name: memory-records
description: >-
  Opens, searches, saves, corrects and closes Memory records, the facts an agent verified and saved in Nowledge Mem for the agents after it.
  Use when a Memory index lists records that may bear on the work, when a command or tool behaves in a way nothing at hand explains, when a verified fact is worth keeping, or when a spec's records have to be judged once its batch has landed.
---

# Memory records

This skill opens, searches, saves, corrects and closes Memory records in Nowledge Mem. Memory records are what a spec's workers left for the workers after them: each carries the `mmw-experience` label, so later workers in this repository see it in their Memory index and act on it before reading any code. A record saved without evidence, or left standing after what it describes has changed, sends each of those workers the wrong way.

Current artifacts, verified evidence, the user's instructions, repository instructions, the ticket, and its parent spec override Memory. Verify every Memory against current repository evidence before acting on it (**principle-clues-are-not-evidence**).

## Open a record

A Memory index lists one record per line: its `id`, its `title`, its first line as `applies`, and its `space`. A `truncated:` line means more task records exist than are listed: search them with the task-scope command below.

Open a record with the `id` and the `space` its index line gives:

```sh
nmem --json memories show "<id>" --space "<space from the index line>"
```

## Search by the error

Search with the commands below when a command or tool behaves in a way that the records you opened do not explain: the current task first, then repository and approved toolbox experience. Keep the query to the exact error, command and component, and keep `--` before it: Nowledge returns nothing for a query that names something no record holds, which long prose always does, and reads a query that starts with `-` as an option.

```sh
nmem --json memories search --space "$NMEM_SPACE" --label "$MMW_TASK_SCOPE" \
  --limit 10 -- "<exact error + command + component>"
nmem --json memories search --space "$NMEM_SPACE" --label mmw-experience \
  --limit 10 -- "<exact error + command + component>"
```

## Save or correct a record

Save a Memory as soon as all three conditions hold: another ticket or later agent may reuse the fact, a current command result or authority verifies it, and the ticket and code do not already make it obvious. To save or correct one, follow `references/saving-memory.md`.

## Close a spec's records

A record that was true mid-night can be wrong once the batch has landed. Judge each against what landed: keep what still holds, deprecate or supersede what the batch made untrue, and propose to the retro what should change how the pipeline works.

For each record in the `--memory-decisions` file decide exactly one of `retain`, `propose`, `deprecate` or `supersede`: `retain` remains useful as it is; `propose` is a candidate for the later retro and does not change the Memory here; `deprecate` is no longer valid; `supersede` names the existing `replacement_id` that replaces it. A `propose` decision's `evidence` is exactly one event comment URL (`https://github.com/<owner>/<name>/issues/<n>#issuecomment-<id>`) or commit URL (`https://github.com/<owner>/<name>/commit/<40-hex sha>`): the retro counts the proposal only when that string is one of its problem's sources, and the file is refused with any other value.

Each entry carries non-empty `memory_id`, `decision`, `reason` and `evidence` strings, and a `supersede` entry also carries `replacement_id`; an entry with any other field is refused. Leave `status`, `total` and `returned` as the file came, and keep one entry per record: a file that leaves a record out is refused. A file that holds the `unchecked` object has no entries to decide: the record list could not be read whole, and the file goes on as it was written.

## Output

- **An opened record.** The record as `nmem --json memories show` prints it.
- **A search.** Up to ten records per command, each with its `id` and `space_id`.
- **A save or a correction.** What the `nmem --json memories` command from `references/saving-memory.md` prints, or the one line `not saved: …` when the task is neither a map nor a spec task.
- **A spec's closing decisions.** The `--memory-decisions` file with one decision per record, or the `unchecked` object as it was written.
