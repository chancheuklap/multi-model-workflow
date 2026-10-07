# Forensics tools

Which tool captures and which loads each kind of diagnostic artifact. Runtime forensics step 1 picks the capture here, Trace forensics steps 1 and 2 and the artifact reducer pick the loader. A repository whose instructions name its own capture command for a process (a script that wraps one of these) is followed first.

Every capture runs on the machine the process runs on, and none needs the process restarted unless its row says so. On another machine, run it the way the repository's instructions run commands there, write the artifact outside the repository's working copy on that machine, and bring it back the way those instructions move files from it.

## Which process

A product is often several processes (a desktop shell's main and renderer processes, a backend). Before capturing, find the one that shows the symptom: sample each candidate's CPU and resident memory a few times over the period the symptom builds (`ps -o pid,rss,%cpu,command` on macOS and Linux, `Get-Process` on Windows), and capture from the one that climbs.

## Capture

| Process | Symptom | Capture | Artifact |
| --- | --- | --- | --- |
| Python | hang, deadlock | `py-spy dump --pid <pid>`; add `--native` when the top frame is in C | thread stacks, printed |
| Python | CPU spin, slowness | `py-spy record --pid <pid> --format raw -o <file>`; `--nonblocking` when pausing the process for each sample is not acceptable | collapsed stacks |
| Python | memory that grows | needs an instance started with the environment variable `PYTHONTRACEMALLOC=25`; a probe (Runtime forensics step 3) calls `tracemalloc.take_snapshot()` twice while the same workload runs, and `Snapshot.compare_to` lists the lines whose allocations grew | allocation sites with their growth |
| Chrome, Electron, Node (JavaScript) | CPU spin, slowness | through the process's debugging port, Chrome DevTools Protocol `Profiler.enable`, `Profiler.start`, then `Profiler.stop`, which returns the profile; a Node process started by you can instead run with `node --cpu-prof` | `.cpuprofile` (JSON: `nodes`, `startTime`, `endTime`, `samples`, `timeDeltas`) |
| Chrome, Electron, Node (JavaScript) | memory that grows, a leak | Chrome DevTools Protocol `HeapProfiler.collectGarbage`, then `HeapProfiler.takeHeapSnapshot`, which streams the snapshot in `HeapProfiler.addHeapSnapshotChunk` events. For one action that leaks, take three: before it, after it, and after undoing it. For growth over hours of use, take a snapshot at intervals while the same workload runs, at least three | `.heapsnapshot` |
| Chrome, Electron | a visual glitch, a slow frame | Chrome DevTools Protocol `Tracing.start`, then `Tracing.end`; the trace arrives in `Tracing.dataCollected` events until `Tracing.tracingComplete` | Chrome JSON trace |
| any, on macOS | hang, CPU spin | `sample <pid> <seconds> -file <file>` | call-tree text |
| any, on Linux | CPU spin, slowness | `perf record -g -p <pid>`, then `perf script > <file>` | perf text |

A process opens a debugging port only when it was started with one; which port, and which builds open it, is in the repository's own instructions. An installed release usually opens none: its JavaScript is reached only by reproducing on a build that opens one, while its Python processes and the operating-system rows still apply. Playwright connects to a debugging port with `chromium.connectOverCDP(<address>)` (`connect_over_cdp` in Python) and opens a Chrome DevTools Protocol session with `newCDPSession` on a page or `newBrowserCDPSession` on the browser; it runs on the machine whose port it reaches. A capture slows the process while it runs: profile in a run whose numbers you do not report.

## Load and query

| Artifact | Load with | What it gives |
| --- | --- | --- |
| Chrome JSON trace, collapsed stacks, perf text, pprof | the Perfetto trace processor, the `perfetto` package on PyPI: `TraceProcessor(trace=<file>)` from `perfetto.trace_processor`, then `query("<SQL>")` | SQL over slices, samples and stack frames |
| `.cpuprofile` | a short script that writes `nodes` (one row per call-tree node, with its `callFrame`'s function, URL and line, and the ids of its `children`) and `samples` with `timeDeltas` (one row per sample) into SQLite | time per function and per call path, by SQL |
| `.heapsnapshot` | memlab; each command below takes files and prints its result, with no interactive prompt. `memlab analyze unbound-shape --snapshot-dir <dir>` and `memlab analyze unbound-object --snapshot-dir <dir>` for growth across several snapshots; `memlab find-leaks --baseline <before> --target <after> --final <undone>` for one action; `memlab analyze object-size --snapshot <file>` for the largest objects in one snapshot; `memlab trace --snapshot <file> --node-id <id>` for one object's retainer chain | the classes and objects that keep growing, the retainer chain from a GC root |
| thread stacks, `sample` call trees, a macOS spindump | read as text | the thread stuck on-CPU or blocked, and its wait reason |

One heap snapshot alone shows what is large, not what leaks: what grows needs at least two, so a finding from one is reported as a hypothesis. `memlab anonymize --snapshot <file> --output <file>` removes user data from a heap snapshot; run it before a snapshot leaves this machine.

A minified JavaScript frame maps back to source through the source map of the exact build the artifact came from. When the artifact does not say which build that is, ask the owner. Without that build's source map, the frame is reported as unmapped.
