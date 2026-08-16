---
name: mmw-retrieval
description: Keep MMW's structure graph and retrieval tools connected. Use on a repo's first retrieval setup, a missing or stale graph, a failed build, a fresh graph that cannot answer a known relation, or MCP tools that will not connect or do not match the contract. Not for ordinary code text or symbol lookup.
---

# Retrieval

How to query — which questions go to the graph, which go to symbols, which two blind spots still need source, and why a candidate must be verified in current source — lives in the Serena and Graphify server instructions. That is the only source for that usage. This skill does not copy it.

The host hands those instructions over at MCP handshake. **If this host does not attach them, and the dispatch prompt did not include the retrieval discipline, the instruction face is down.** Follow section 3.

This skill covers two jobs the server instructions do not. Only the main agent does them: **keep the graph usable**, and **diagnose when the tools themselves will not connect**.

Pick which job: the graph is there but answers wrong → section 1. The tools will not run → section 3.

## 1. Three graph states

A structure query reconciles the graph before it runs. Read what it reports:

| State | Test | Action |
| --- | --- | --- |
| Missing | No graph file | Build once. If a wait is not worth it, search and read source, and say this run did not use the graph |
| Stale | Graph input fingerprint differs from the last build | Same as missing |
| Fresh | Fingerprint matches | Query |

The test is graph input content, not a commit. **Markdown edits and empty commits are not stale:** docs are not in the graph, and an empty commit changes no files. Judging by commit would make a new task worktree drop a graph that is still fresh.

## 2. Build once

```bash
mmw graph build
```

Five stages. Any failure leaves the old graph in place. It reports which stage broke:

| Stage | Means |
| --- | --- |
| Native extract | A language parser is missing. Refuse to publish. No graph is better than a partial one |
| Cross-language edges | That config item does not match the current code structure. See [building.md](building.md) |
| Merge | The two graphs will not combine. Plugin fault. Report it |
| Route bridge | Same-named handlers, no unique edge. Read those source sites |
| Validate and publish | A partial graph was blocked. The old graph remains. Report the listed violations |

## 3. Tools will not connect

A good graph with tools that will not run is a different job. Rebuilding the graph does not help.

```bash
mmw doctor
```

It actually starts the three servers — Serena, Graphify, and Context7 for `$mmw:mmw-research` official docs — handshakes each, and compares the exposed tools to the trim contract. Checking only that config exists misses a class of faults: the config is there, the tool names are in the list, and the model errors only when it calls, mid-review.

| doctor reports | Means |
| --- | --- |
| A server will not start | That Python package is not installed. The plugin does not install it. The command is in the output |
| Tool set does not match the contract | Upstream changed the default surface. An extra tool is a broken guard. A missing tool is a missing capability. Handle both now |
| User-level config is missing or disagrees with the plugin | Run the install script it prints. This face only shows up when switching hosts |
| None of the above | Keep the raw doctor output. Degrade as the end of section 4: continue with text search, and say so in the report |

## 4. Three rules

| Rule | Action |
| --- | --- |
| Only `mmw graph build` updates the graph | The retrieval tool's own update command does native extract only. Cross-language edges and the route bridge are dropped. Filename and size look the same |
| Want a new graph, run that command now | Watcher updates and commit hooks leave graphs with no provenance |
| The graph stays on this machine | It is tens of megabytes of derived data, tied to the checkout. `mmw init` already keeps it out of the repo |

If the graph will not build or the tools will not connect, record why, continue with text search and file reads, and say this run did not use retrieval tools.

| Case | Action |
| --- | --- |
| Graph built, one class of cross-language edge is zero | Report incomplete retrieval for this repo and which class is missing. Let the user choose: fix the config, or use it as-is |
| A relation you know exists is unanswered, and the graph is fresh | Report the relation and what you queried. Let the user judge: extractor gap, or a bad question |
| Graph is usable | Return to the work that called you |

## 5. First connect, verify, fail

On a repo's first connect, or when query results look wrong, read [building.md](building.md): cross-language edges, config, verify, failure handling, and graph reuse on a task worktree.
