# Connect, verify, fail

## 0. What the cross-language edges connect

Native extract scans each language on its own. A request from the frontend and the backend function that handles it have no edge. The two parsers cannot see each other. The same break kills symbol query: a handler registered by a decorator has no static caller, and a symbol destructured from a dynamic import will not bind to its definition.

Build time adds these four edge classes:

| Edge | Connects |
| --- | --- |
| Request to handler | A call from the frontend or another service, to the backend function that handles it |
| IPC call to handler | A call from the renderer, to the handler registered in the main process |
| Producer to consumer | A write to a topic, to a read of that topic |
| Function to the route it registered | An ordinary function, to the interface a decorator hung on it |

**These four classes are the line between retrieval that works and retrieval that does not.** Without them, "who calls this interface" and "which page does this function change" look the same as "nobody calls it".

## 1. Connect a repo

Config lives under `retrieval.graph` in the repo-root `.mmw.json`. Each class is independent: omit one and that class is not counted. That is not a failure. A backend-only repo can still build request-to-handler edges.

| Key | Write | If omitted |
| --- | --- | --- |
| `services` | Backend service names, one per line. Route and HTTP edges use this to know whose interface | Required when `routes` or `http` is set |
| `routes` | How to enumerate backend routes. See the next section | No request-to-handler edges |
| `ipc` | Desktop-shell directory list, relative path of the channel-constant table in the shell, constant object name | No IPC edges |
| `topics` | Which file and constant holds producers, drainers, and consumers for message topics | No topic edges |
| `http` | Clients between services: Python is file plus class name, TypeScript is file plus name, each naming the target service | No service-to-service call edges |
| `assertions` | Topology facts for this repo. See section 3 | Silent extractor drift has nowhere to fail |
| `exclude_roots` | Root directories that must not enter the graph. Checked per node before publish | Markdown only |
| `tolerated_warnings` | Known accepted capability gaps for this repo. See section 5 | Any capability-missing warning rejects the whole graph |

Path exclusion is primarily `.graphifyignore` at the repo root, the retrieval tool's own mechanism. `exclude_roots` is a second check before publish. `mmw init` already writes two lines into that file: `*.md`, and the task-worktree directory.

**Markdown must be excluded.** The freshness fingerprint never looks at `.md`. Docs in the graph stay stale when docs change, while status still says fresh. `exclude_roots` catches Markdown, but only in repos that set `retrieval.graph`. A repo without that config runs bare `graphify update` with no intercept. So this rule lives in `.graphifyignore`.

**The task-worktree directory must be excluded.** Each worktree is a full code copy. Leave it in and the graph multiplies, all duplicate nodes. Other full copies in this repo — upstream mirrors, rebuild candidates, vendor — add those yourself.

## 2. How to enumerate routes

`routes.provider` points at a function in this repo, written `relative/path.py:function_name`. It returns `{service_name: app_object}`. The plugin runs it in an isolated subprocess and reads the full route table.

Do not scan decorators in source. When routers mount in layers, the prefix is joined at the mount, and the decorator only has the last segment. That segment will not match a frontend call to `/api/v1/hold`, and the edge breaks there.

The provider wires. It does not start user state: no boot, no directories, no migrations, no locks, no credentials. `routes.env` points the app's on-disk locations at a temp directory. `{tmp}` is the only placeholder.

`routes.user_data_guard` points at another function that returns the list of real user-data directories. The probe fingerprints before and after. A change fails immediately. That function runs in the plugin process and may use only the standard library — it computes paths.

## 3. Topology assertions

Coverage is a number. A dropped number is invisible. An assertion pins a concrete fact. Silent extractor drift fails there.

| Assertion | Pins |
| --- | --- |
| `route_handler` | This route must resolve to exactly this function in this file |
| `route_per_service` | Every service has this route, for example `GET /health` |
| `http_methods` | Calls between services must cover these methods. Breaks when the extractor degrades non-GET to GET |
| `topic_relations` | This topic's relation set must be exactly these |

When an assertion fails, decide: extractor bug, or legal topology change. The latter: edit the assertion in `.mmw.json`.

## 4. Verify the wiring

```bash
mmw graph verify
```

It reports how many edges each class produced. **The test is not the count. Every class the config says to count must be non-zero.** A zero class means the config does not match the current code structure, not that this repo has no such relations.

Then spot-check one: pick a decorator-registered interface, ask the structure query for its callers, and you should reach the frontend call site. If not, the route bridge is not wired.

## 5. It will not build

| Report | Action |
| --- | --- |
| A language parser is missing | Install it, then build. The graph at this point is partial. No graph is better than a wrong one. An accepted gap goes in `tolerated_warnings`, using the warning's identifying text |
| A class was configured and zero edges were built | The matching row in section 0 no longer matches the current code structure |
| An assertion failed | See section 3 |
| Route bridge has multiple candidates | Same-named handlers in the code. Real ambiguity. Do not guess. Read those source sites |
| Another process is building | Wait for it, or search and read source |
| The worktree changed mid-build | Build again. A mid-build edit leaves the graph off the code |

**None of these block the task.** Record why, continue with text search, and say this run did not use the graph.

## 6. Task worktree

A new task worktree whose graph input matches an existing graph reuses that graph. After the input differs, rebuild for the current worktree.

A worktree graph does not enter the repo and does not sync to other machines. It is derived data on this machine, tens of megabytes.

Symbol query has one extra constraint on a task worktree. Serena pins the project root to the current directory of the process that started it, and does not follow later directory switches. Start the session in the main checkout, then enter a task worktree, and the project root is still the main checkout.

Two consequences:

- Pass a task-worktree relative path from `.mmw.json` `paths.worktrees`, or an absolute path inside the worktree, and Serena refuses. The main checkout `.gitignore` excludes the task-worktree directory, and Serena treats every `.gitignore` line as its own exclude list. The error text is `while the path is ignored` or `Cannot extract symbols from file`.
- Pass a repo-relative path, and Serena answers — from the main checkout copy, not the current worktree copy.

So on a task worktree, query symbols with repo-relative paths, and first confirm that file is the same in the main checkout and the current worktree. If the current worktree edited it, Serena answers the old content. Then read source.
