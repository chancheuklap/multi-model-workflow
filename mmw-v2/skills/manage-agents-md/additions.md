# Additions

Branch: **incremental**. You have `scope.md` and `survey-list.md` built from the change sets. For each `AGENTS.md` in scope you now decide what the code changes made false and what they added, and edit the file. Every edit has code evidence in the survey list; the user-owned lines named in [incremental.md](incremental.md) stay as they are, and a doubt about one of them goes to the report.

## Steps

For each file in `scope.md`:

1. Read the file. For each line, look for a survey entry that contradicts it. A contradicted line is fixed when the entry gives the new fact, removed when it gives none. Write the old line, the new line, and the evidence into `changes.md` in the scratch directory.
2. For each survey entry with no line covering it, decide whether it belongs in the file by the categories below, and add it where its type goes: command to `## Commands`, reference to `## External References`, convention to `## Key Conventions`, gotcha to `## Gotchas` — or, when the entry has a `when` line, to the domain section whose condition is that value (open the block if none exists). Write the addition one line per concept: a command as a table row, anything else as `<pattern>` - `<brief description>`.
3. When no entry contradicts or extends the file, record "no change needed" for it in `changes.md`.

## Where an addition goes

A fact whose place is a directory goes into that directory's `AGENTS.md`; when the directory has no pair yet, create both files on the nested template in [write.md](write.md), with the purpose line taken from the survey list's purpose entry and listed under **Pending user decisions** for confirmation. A fact whose place is `root` goes into the root file. A directory whose last rule just disappeared is an **empty pair**: it keeps both files on this branch; the report lists it under **Pending user decisions** and the user removes it.

When the root file passes 150 lines after additions, move the lines whose place is one directory into that directory's file, as [write.md](write.md) says.

Done when every file in `scope.md` has an entry in `changes.md` — edits with evidence, or "no change needed".

Next: [prune.md](prune.md).
