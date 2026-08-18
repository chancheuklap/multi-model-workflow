---
name: mmw-research
description: Investigate a question against high-trust primary sources and capture the findings as a Markdown file in the repo. Use when the user wants a topic researched, docs or API facts gathered, reading legwork delegated to a background agent, a `wayfinder:research` ticket arrives, or a question needs several independent primary sources.
---

Each Explore writes one findings file. You write `README.md`. `README.md` is the index of this research directory: the question, and the files in it. It is not the findings. Downstream names `README.md` and reads the files it lists.

1. If answering needs real credentials, production access, spend, or writing data outside this repo, ask the user first. Do not continue until they agree.

2. Decide whether files are written. A `wayfinder:research` ticket is yes. Otherwise ask. If they say no, do not create files.

3. If files will be written:

Confirm where this repo is first. Judge top to bottom; stop at the first row that hits.

| Case | How to tell | What you do |
| --- | --- | --- |
| Not in a git repo | `git rev-parse --is-inside-work-tree` fails | Ask the user for the target repo path. Enter that repo, then judge again |
| In the main checkout | `git rev-parse --path-format=absolute --git-dir` equals `--git-common-dir` | Stop. Ask the user to open a worktree with this host, then start a session there |
| No branch | `git symbolic-ref --quiet --short HEAD` is empty | Run `git switch -c <full task-branch name>`. Use the name this skill or the caller already gave; with none in hand, name it after the work in this repo's own branch-naming shape, and say which name you took |
| Task branch already there | None of the above holds | Use the current branch |

`<topic>` is a short kebab of the overall question. `mmw artifact path research --sub <topic>/README.md` prints the index path. For each Explore, `mmw artifact path research --sub <topic>/<slug>.md` prints that agent's findings path. `<slug>` is a short kebab of that agent's question. Add `--name` and `--issue` when the caller passed them.

4. Spin up a **group of Explore** agents to do the research, so you keep working while they read. Independent questions: one Explore each, one group, same turn. Pass each its question and its findings path. Do not pass a file list; the question is the boundary. Do not pass the README path.

Each Explore's job:

1. Investigate the question against **primary sources** — official docs, source code, specs, first-party APIs — not a secondary write-up of them. Follow every claim back to the source that owns it. Source code includes this repo.
2. Write the findings to a single Markdown file, citing each claim's source.
3. Save it where the repo already keeps such notes; match the existing convention, and if there is none, put it somewhere sensible and say where.

The findings path you passed is that convention. Explore writes that file. You do not rewrite it.

5. Write `README.md` at the index path from step 3. List the overall question and each findings file. Do not copy the findings into it.

6. Return the README path. If no file was written, report that.
