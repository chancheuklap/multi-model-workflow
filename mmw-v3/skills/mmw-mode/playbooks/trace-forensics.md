### Trace forensics

**You own the diagnosis from the artifact. Load it, shape it, narrow to the cause, attribute to source.**

Distinct from **Runtime forensics**, which instruments the live process. Here the capture already exists: the owner handed it over, or it came from a machine you cannot reach. The artifact is a fixed dataset, read it, don't re-run it. The tool for each format is in the `mmw-mode` skill's `references/forensics-tools.md`. An artifact can carry customer data and credentials. Keep it outside the repository, and on the tracker and in a ticket quote from it only function names, the product's own file paths and numbers.

1. **Identify the format and load it** with the tool `references/forensics-tools.md` names for it. Ask the owner which build and which machine it came from when the artifact does not say. For an artifact too large to read whole, send out one subagent, the artifact reducer, with the prompt in the `mmw-mode` skill's `references/artifact-reducer.md`, and keep its reduced finding here.
   Done when the format and the build are named and the artifact loads.
2. **Transform the raw artifact into a form you can query.** Load a trace into the Perfetto trace processor, dump the artifact into SQLite (one row per sample, frame or node), or run the analysis commands of the tool built for its format (memlab for a heap snapshot). Reach the queryable shape before you read.
   Done when one query or analysis command over the artifact returns results.
3. **Narrow to the cause.** Query for the frames that hold the most time and walk the call tree to the hot path. For a leak, find what grows across snapshots and follow its retainer chain to a GC root; one snapshot shows only what is large. For a thread dump, find the thread stuck on-CPU or blocked and its wait reason.
   Done when one candidate cause is named with the query that singles it out.
4. **Attribute to source.** Map the hot frame to file, symbol, and line via the artifact's own symbols. A frame with no source mapping is not yet a diagnosis. Resolve the symbols (the source map of the build step 1 named, for minified JavaScript), or say plainly the artifact does not carry them.
   Done when the cause has a file, a symbol and a line, or the reply says the artifact does not carry them.
5. **Confirm against a paired capture** when you have one. Diff a before and after artifact. Without one, mark the finding as the strongest hypothesis the artifact supports, not a confirmed cause.
   Done when the finding is marked confirmed or hypothesis.
6. **Hand back a cited diagnosis,** no fix unless asked. Once the cause is known, a fix runs the Bug fix playbook from its step **Write the ticket**.
   Done when the diagnosis, each claim cited to the artifact, is in the reply, or Bug fix has been run from **Write the ticket**.

**Reply:** the artifact, its format and build, the reduced finding, the source location, the artifact paths, and whether a paired capture confirmed it.
