# Upstream comparison, 2026-10-30

This comparison refreshes MMW's upstream snapshots and identifies changes worth adopting. It does not implement those adoption proposals. The owner's added sources are OpenClaw's maintainer skills, OpenCode's own skills, and unlazy.

MMW baseline: `e33217652cda679de034552269829c0464b583cd`. Working branch: `codex/upstream-review-20261030`. Versions below are the branch heads observed during this fetch, not a promise that the remote heads remain unchanged.

## Sources and versions

The catalog has seven repositories and eight snapshot directories. Changed-file counts compare each existing snapshot with the MMW baseline. Counts for new snapshots are imported files, not upstream changes since MMW's original adoption.

| Snapshot | Source commit | Selected scope | Result |
| --- | --- | --- | --- |
| `upstream/mattpocock/` | `mattpocock/skills@a496f5513d4a4cf889bc48e189e579f4b0bdf6aa` | Whole `main` repository | Updated; 37 changed files |
| `upstream/pstack/` | `cursor/plugins@4dd1d05818d19792e7cd6e818f1667f95f7e1dbe` | `main:pstack/` | Updated; 462 changed files; version 0.15.36 |
| `upstream/cursor-team-kit/` | `cursor/plugins@4dd1d05818d19792e7cd6e818f1667f95f7e1dbe` | `main:cursor-team-kit/` | No changes in the selected directory |
| `upstream/diagram-design/` | `cathrynlavery/diagram-design@0cf73c3fcc56667ad91a9a04c439ac6ccfabc9d1` | Whole `main` repository | Updated; 73 changed files; version 2.6.136 |
| `upstream/e2e/` | `tester-army/e2e@5b6fd01042c96e5d79e662325cfaae2157d6eac9` | `main:skills/` | Updated; 10 changed files |
| `upstream/openclaw/` | `openclaw/openclaw@6ac91adabcc273e76a2d652a5aefc9955b0600f8` | `main:.agents/skills/` | Added; 300 files, 54 SKILL.md files |
| `upstream/opencode/` | `anomalyco/opencode@95fc3c87ca438527388b773e4c788cb7f5eb0e5b` | `dev:.opencode/skills/` | Added; 8 files, 8 SKILL.md files |
| `upstream/unlazy/` | `Leonxlnx/unlazy@16671491f6679ad9378f52604d3bc2415b4120c7` | Whole `main` repository | Added; 37 files; source version unchanged since original adoption |

The partial snapshots flatten the selected directory into their snapshot root. OpenClaw's separate product `skills/` directory is excluded. OpenCode's application, server and other repository code are excluded. Git object fetches used to obtain the selected trees do not expand these tracked snapshot scopes.

Split commits used for partial imports:

| Snapshot | Split commit |
| --- | --- |
| pstack | `424f2f6b0e1c805d1d227dbc7a59dcb290c89f8a` |
| cursor-team-kit | `8f96a272f10521413bcf022b978f01aefea42ff5` |
| e2e | `44b573ba1c9340fd5cf29702d5b5f6d891027e91` |
| openclaw | `23ce9061768aba123670d904f585a7411182482e` |
| opencode | `cce896b26c42472aee64f269067bbe1d24f9bc12` |

## What changed and what MMW should do

### Adopt the worktree-audit portability fix

pstack's `skills/poteto-mode/scripts/worktree-audit.sh` now selects GNU or BSD forms of `stat` and `date`. MMW's `mmw-v4/skills/mmw-mode/scripts/worktree-audit.sh` still uses `stat -f %m` for transcript modification times and `date -r` for dates. Those are BSD forms and do not provide the intended result with GNU tools.

Carry the portability fix into MMW's existing scanner while retaining its multi-host transcript lookup, base selection and cleanup decisions. This is a concrete compatibility fix, not a new cleanup gate. Validation belongs on the GNU and BSD branches of the time-reading operation; the audit must remain read-only.

Source: [pstack worktree-audit.sh](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/scripts/worktree-audit.sh).

### Update diagram-design as one coherent skill

Upstream 2.6.136 adds box-plot support and fixes existing behavior: Mermaid parsing, draw.io labels containing angle brackets, Excalidraw grouping, SVG export with stylesheet media conditions, SVG geometry parsing, and rejection of truncated HTML documents. It also corrects onboarding links and several type-specific checks.

MMW keeps local copies of `mermaid_extract.py`, `drawio_extract.py`, `excalidraw_extract.py`, `export_svg.py`, `verify-geometry.py` and `self_check.py`. Those local copies take precedence over `repo-root/scripts/`. Updating only the upstream snapshot therefore leaves these fixes out of the owned scripts. Conversely, resources reached through the existing `repo-root` symlink already follow the refreshed snapshot in this branch.

Update the owned scripts, affected references and assets together. Preserve MMW's `page-for-a-person.md`, profile behavior, source-content treatment and owner-facing drawing rules. Check a representative repaired import and export rather than adding another general review stage. Do not import upstream's release automation, host packaging or review-bot policy.

Source: [diagram-design comparison](https://github.com/cathrynlavery/diagram-design/compare/b46c9701f035844a20b13ab0551315977188933b...0cf73c3fcc56667ad91a9a04c439ac6ccfabc9d1).

### State the measurement decision before measuring

pstack's `principle-explain-the-number` now asks for the result that would change a decision and the noise floor before a run. MMW's principle already requires scope, alternative explanations, run count and spread, but its entry starts before trusting, reporting or acting on a number. The advance decision criterion is not explicit there.

Add that judgment to MMW's existing principle and change its mode trigger to include preparing a measurement. Keep benchmark procedure in benchmark-checklist. Keep the existing distinction between performance measurements and agent evals: an eval does not require a CPU or I/O limiter by default. A difference within run variation does not justify a claimed improvement. No new skill, form or gate is needed.

Source: [pstack principle-explain-the-number](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/principle-explain-the-number/SKILL.md).

### Make independent subagent context explicit

Matt's update explicitly requests a fresh context window for independent subagent jobs, including review and research. Its contributor guidance explains the failure: some hosts fork the parent's conversation by default, defeating the context separation the task needs.

MMW's dispatched worker, reviewer and researcher sessions already have separate startup prompts. The remaining ambiguity is the host's general-purpose subagent call: mmw-mode requires a complete brief but does not explicitly select a clean context when the host offers that choice.

Clarify that choice once in mmw-mode's `## Subagents`. An independent job receives its complete brief in a clean context. Follow-on work on the same job reuses the suitable existing subagent, as the owner's shared prompt requires. This does not authorize replacing, interrupting or rushing a running subagent. Do not scatter the same instruction through every calling skill.

Source: [Matt's comparison](https://github.com/mattpocock/skills/compare/49dd158d1076134a641b33efb035946536778336...a496f5513d4a4cf889bc48e189e579f4b0bdf6aa).

### Complete the comparison map alongside future adoption

`writing-for-agents/scripts/upstream-map.tsv` is incomplete. It maps one diagram-design file, not the owned import/export scripts, and does not cover all adopted Matt skills or TypeScript guidance. OpenClaw, OpenCode and unlazy had no catalog snapshots before this refresh.

The existing upstream-hunks classifier therefore cannot establish that the whole skill set is current. In this review it inspected 38 pstack mappings, 14 Matt mappings, one diagram-design mapping and one e2e mapping. The changed source files were also compared outside that table.

Keep the existing comparison mechanism. Add missing direct-copy mappings when carrying their changes. Record folded or substantially rewritten methods by their owning skill and adaptation intent rather than pretending they are byte-for-byte copies. The source catalog is now expanded; this task does not claim that the classifier map is complete.

## Updates already covered or not worth another rule

### Matt's tracker and setup changes

The upstream GitHub guide adds newer gh shorthand for native dependencies and sub-issues, distinguishes open blockers from closed blockers in `blockedBy`, and clarifies PR-body reads. MMW's wayfinder already uses the native REST dependency endpoint and open-blocker summary. setup-mmw already checks repository reachability through `gh repo view` and probes sub-issue and dependency support.

These changes do not establish a missing MMW capability. Keep MMW's current commands unless a consuming task demonstrates a defect. Keep the owner's `CONTEXT.md` and `CONTEXT-MAP.md` names; do not take Matt's glossary rename.

Matt's fresh implementer per independent ticket is also already represented by MMW's dispatched ticket sessions. It does not override reuse within a continuing task.

### e2e's runner and diagnosis guidance

The changed e2e guides improve failure evidence, precise `file:line` reruns, starting near the behavior under test, saved session setup and locator APIs. The `create-verification-skill` source itself is unchanged in this interval.

MMW already tells agents to read `npx e2e guide <topic>` from the product's installed runner, not blindly use the snapshot's API version. test-audit already preserves the original failure, reproduces predecessor order when relevant and removes duplicated setup without dropping contracts. Let those existing entry points supply the updated runner details. Shortening a test must preserve the journey when that journey is the acceptance contract.

Do not add e2e's model-based test filters or exploratory agent flow to MMW's fixed-step acceptance path. Do not replace scripts/check's deterministic test selection with an AI exclusion decision. Screenshot and secret-handling changes require the product's actual runner version and evidence policy, not a blanket relaxation in MMW.

Source: [e2e skill tree](https://github.com/tester-army/e2e/tree/5b6fd01042c96e5d79e662325cfaae2157d6eac9/skills).

### TypeScript branded types

pstack now shows a validating type guard that narrows a branded value without a subsequent `as` cast. MMW still permits casts after validation and demonstrates that pattern in `typescript-best-practices/references/patterns.md`.

This is a possible style refinement, not a reproduced runtime bug. If adopted, change the rule and example together, retaining the requirement that a guard verifies its claim. It is lower priority than the portability and diagram defects.

## New capabilities to keep as references

### pstack formal verification and orchestration

`create-formal-verification-skill`, `maintain-formal-verification-skill` and `statechart` provide model checking, counterexample traces, explicit scope limits, negative controls and model/code synchronization. Keep them available for a concrete concurrency or protocol question that current tests cannot settle. Their presence upstream alone does not justify a mandatory formal-verification layer or importing the whole toolchain.

pstack's Orchestrate now uses the host's own agent and PR tools, removes its former script engine, and describes cloud workers and owner-per-PR supervision. Autopilot-full and Autopilot-stack retain their own CI, swarm and PR-head verification contracts. They are alternatives to parts of MMW's runtime, not missing steps to insert into Run a night. Preserve MMW's dispatch, events, relay, watch and frozen installed version. Do not import automatic replacement of stalled agents; the owner forbids interrupting or rushing running subagents without an explicit request.

The rewritten interrogate emphasizes executed adversarial evidence. MMW already requires real evidence through principle-prove-it-works. Preserve legitimate Standards and Spec review findings instead of restricting all review to executed failures. Keep the settled MMW departures for arena's judge topology, model configuration, sharpen, PR delivery and the retired swarm.

`ketchup-video` is a new presentation option, not a reason to add video to the owner's existing Artifact and wait-what flow. Matt's chief-of-staff wiki likewise does not justify a parallel MMW knowledge store.

Sources: [pstack skills](https://github.com/cursor/plugins/tree/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills), [Orchestrate](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/playbooks/orchestrate.md).

### OpenClaw, OpenCode and unlazy

The adopted OpenClaw `test-audit` tree and the separately cited `docs/help/testing/writing-tests.md` are unchanged between the adoption commit `5310270e46cf020ab1e37204075970f3b2679812` and the fetched source commit. OpenCode's previously cited root `AGENTS.md` is unchanged between `92b2ca0dd727942e00aba3523ed141d53e78ea28` and the fetched commit. unlazy is still at the source commit MMW originally adopted. No refresh of those adopted passages is justified by this fetch.

OpenClaw's newly cataloged skills include `pr-simplify`, testing, performance, documentation and maintainer workflows. The inspected `pr-simplify` offers useful concrete simplification questions, but MMW's root instructions, principle-subtract-before-you-add, unslop and test-audit already own that work. It does not warrant a second mandatory PR pass or OpenClaw's fixed diff-size budgets.

OpenCode's eight skills are `app-e2e-tests`, `component-tests`, `effect`, `opencode-dev`, `rtl-aware-development`, `sample-skill`, `tui-tests` and `unit-tests`. `rtl-aware-development` is a useful future source for a product with RTL requirements. Its test skills contain product-specific Bun, Effect, Playwright and CI facts; they are not generic MMW runtime requirements.

The expanded catalogs make future research possible. This comparison inventories the full selected trees, verifies the adopted-source baselines, and reads selected new candidates. It does not claim a full semantic review of every OpenClaw skill and reference.

Sources: [OpenClaw maintainer skills](https://github.com/openclaw/openclaw/tree/6ac91adabcc273e76a2d652a5aefc9955b0600f8/.agents/skills), [OpenCode skills](https://github.com/anomalyco/opencode/tree/95fc3c87ca438527388b773e4c788cb7f5eb0e5b/.opencode/skills), [unlazy](https://github.com/Leonxlnx/unlazy/tree/16671491f6679ad9378f52604d3bc2415b4120c7).

## Delivery boundary

This branch contains refreshed and new upstream snapshots, the expanded source catalog and this comparison. The owned live skill instructions and runtime scripts are unchanged. The repository checker now excludes upstream test trees from its own-suite discovery, matching the existing read-only boundary. The host-neutrality exceptions follow the changed source-catalog lines. diagram-design's linked upstream resources do change in this branch, as described above. No upstream scripts were executed, no host installation was changed, and no branch was pushed or released by this task.

Validation: all eight snapshot trees match their recorded source or split trees. The adopted OpenClaw and OpenCode source comparisons are unchanged as reported. `python3 scripts/check` passed its five selected steps: self-check, syntax, shared-checks, lib and check-interfaces. The Artifact's geometry check passed. Its installed HTML self-check rejects external citation links, and the browser's URL policy blocked opening the local file, so no successful full-page render inspection is claimed.

The next adoption should start with worktree-audit and diagram-design, then the two small method clarifications. Keep the comparison map aligned with those adopted files. Defer optional capabilities until a named task needs them.
