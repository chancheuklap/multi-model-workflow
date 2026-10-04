# Memory while working a ticket

How a worker reads and saves the shared experience a ticket can use. Work a ticket's **Read yourself in and write the code** opens this file; the two indexes it reads are in the worker's start prompt, which the `dispatch` skill's `dispatch.sh start` builds.

## Read

Your first prompt carries two Memory indexes, one line per record (`id`, `title`, its
first line as `applies`, `space`). Before working, open every record whose title or
`applies` line bears on this ticket; skip the rest. A `truncated:` line means more
task records exist than are listed: search them with the task-scope command below.

```sh
nmem --json memories show "<id>" --space "<space from the index line>"
```

Current artifacts, verified evidence, the owner's instructions, repository
instructions, the ticket, and its parent spec override Memory. Verify every Memory
against current repository evidence before acting on it.

When a command or tool behaves in a way that the ticket, repository authority, and
the records you opened do not explain, search the current task with the exact error,
command, and component before trying a workaround; if that has no answer, search
repository and approved toolbox experience. Keep the query to that error, command and
component, and keep `--` before it: Nowledge returns nothing for a query that names
something no record holds, which long prose always does, and reads a query that starts
with `-` as an option.

```sh
nmem --json memories search --space "$NMEM_SPACE" --label "$MMW_TASK_SCOPE" \
  --limit 10 -- "<exact error + command + component>"
nmem --json memories search --space "$NMEM_SPACE" --label mmw-experience \
  --limit 10 -- "<exact error + command + component>"
```

## Save

Save a Memory as soon as all three conditions hold: another ticket or later agent may
reuse the fact, a current command result or authority verifies it, and the ticket and
code do not already make it obvious.

Store only reusable engineering context that is safe for repository collaborators.
Exclude secrets, customer data, raw chat transcripts, private host paths and unverified
claims. Use unit type `learning`, or `procedure` for fixed steps. Take the labels from
the environment rather than reconstructing the numbers from prose: a map task adds its
map label, and a standalone spec's task label already is `mmw-spec-<spec>`. Give it a
title that names the component and the behaviour, and name in `证据` every repository
path the fact concerns: a later worker's Related experience ranks a record first when
it names a path that worker owns. Write this exact body:

```sh
[[ "$MMW_TASK_SCOPE" == mmw-map-* || "$MMW_TASK_SCOPE" == mmw-spec-* ]] || {
  echo "not saved: MMW_TASK_SCOPE is '$MMW_TASK_SCOPE', not a map or spec task"; exit 0; }

label_args=(
  --label mmw-experience
  --label "mmw-spec-$MMW_SPEC"
  --label "mmw-ticket-$MMW_TICKET"
)
if [[ "$MMW_TASK_SCOPE" == mmw-map-* ]]; then
  label_args+=(--label "$MMW_TASK_SCOPE")
fi

nmem --json memories add --stdin \
  --space "$NMEM_SPACE" \
  --agent-id "$NMEM_AGENT_ID" \
  --unit-type learning \
  "${label_args[@]}" \
  --title "<searchable title>" <<'MEMORY'
适用条件：<环境、版本或前提>
问题：<已证实的非显然行为>
有效做法：<下一名 worker 可以直接执行的操作>
证据：<命令与输出首行，或 path:line>
发生位置：<repository、spec #n、ticket #n、日期>
MEMORY
```

A failed Memory write does not block the ticket: continue the ticket work.

## Correct

Correct only a record whose `space` (in an index line) or `space_id` (in a search or
show result) equals `NMEM_SPACE`; a toolbox record is context, not a record for this
worker to change. When current evidence verifies a replacement, save
the replacement first and supersede the old record with its id; when a record simply
no longer applies, deprecate it. Use one lifecycle command per old record, and do not
leave two active records that conflict:

```sh
nmem --json memories supersede "$OLD_ID" "$NEW_ID" \
  --space "$NMEM_SPACE" --reason "<current evidence for the replacement>"
nmem --json memories deprecate "$OLD_ID" \
  --space "$NMEM_SPACE" --reason "<current evidence that it no longer applies>"
```
