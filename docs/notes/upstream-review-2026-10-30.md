# Upstream comparison, 2026-10-30

This record covers the upstream snapshot refresh and the unambiguous maintenance updates adopted afterward. Optional new capabilities remain unadopted. The owner's added sources are OpenClaw's maintainer skills, OpenCode's own skills, and unlazy.

MMW baseline: `e33217652cda679de034552269829c0464b583cd`. Working branch: `codex/upstream-review-20261030`. Versions below are the branch heads observed during this fetch, not a promise that the remote heads remain unchanged.

## Adoption status

Completed on `codex/upstream-review-20261030`:

- worktree-audit uses GNU or BSD time commands while retaining MMW's four-host transcript lookup.
- diagram-design carries the current draw.io, Mermaid, Excalidraw and SVG-export helpers from `cathrynlavery/diagram-design@0cf73c3fcc56667ad91a9a04c439ac6ccfabc9d1`. Its locally adapted geometry checker retains multi-SVG and CJK handling while taking upstream's quoting, translation and definition-custody fixes. self_check takes the document-completeness fix while retaining inline interaction and allowing ordinary HTTP source links as navigation. Related references, onboarding anchors and affected existing templates are corrected. The export reference delegates the parser to the packaged helper instead of maintaining a second prose algorithm; the offline-font caveat and PNG dependency policy remain.
- principle-explain-the-number and its mode trigger establish the decision before measuring. Existing performance and eval distinctions remain.
- mmw-mode chooses fresh context for independent subagent jobs when supported, and reuses the suitable subagent and context for continuing work.
- wait-what/KETCHUP.md retains every pending decision and its context while keeping progress short, grouping shared decisions and asking only the next decision. This is committed as `98c9696c`.
- setup-mmw, its label setup and migration, dispatch and register-problem resolve the consuming repository through an explicit origin lookup. Their subsequent tracker operations use that target, preserving register-problem's explicit `--repo` and separately resolved toolbox destination.
- typescript-best-practices takes pstack's verifying type guard rule and branded-type example together. This is an engineering writing choice, not an owner-only product decision.

The comparison map adds 289 source-to-owned-copy relationships, including diagram-design, related Matt skills, TypeScript and OpenClaw test-audit. A mapping records provenance and enables comparison; it does not approve every upstream method. The earlier classifier counts below describe the initial comparison, before this map expansion.

Box plot, formal-verification skills, statechart, ketchup-video and chief-of-staff's wiki remain candidates. Orchestrate, Autopilot and other settled workflow departures retain MMW's existing decisions. The host installation remains unchanged.

The findings below describe the original baseline comparison and the adopted response.

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

pstack's `skills/poteto-mode/scripts/worktree-audit.sh` now selects GNU or BSD forms of `stat` and `date`. Before adoption, MMW's `mmw-v4/skills/mmw-mode/scripts/worktree-audit.sh` used `stat -f %m` for transcript modification times and `date -r` for dates. Those are BSD forms and do not provide the intended result with GNU tools.

The portability fix is carried into MMW's existing scanner, retaining its multi-host transcript lookup, base selection and cleanup decisions. This is a concrete compatibility fix, not a new cleanup gate. Validation belongs on the GNU and BSD branches of the time-reading operation; the audit must remain read-only.

Source: [pstack worktree-audit.sh](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/scripts/worktree-audit.sh).

### Update diagram-design as one coherent skill

Upstream 2.6.136 adds box-plot support and fixes existing behavior: Mermaid parsing, draw.io labels containing angle brackets, Excalidraw grouping, SVG export with stylesheet media conditions, SVG geometry parsing, and rejection of truncated HTML documents. It also corrects onboarding links and several type-specific checks.

MMW keeps local copies of `mermaid_extract.py`, `drawio_extract.py`, `excalidraw_extract.py`, `export_svg.py`, `verify-geometry.py` and `self_check.py`. Those local copies take precedence over `repo-root/scripts/`. Updating only the upstream snapshot therefore leaves these fixes out of the owned scripts. Conversely, resources reached through the existing `repo-root` symlink already follow the refreshed snapshot in this branch.

The owned import/export scripts, affected references and existing templates are updated together. Box-plot additions remain outside this adoption. Preserve MMW's `page-for-a-person.md`, profile behavior, source-content treatment and owner-facing drawing rules. Check a representative repaired import and export rather than adding another general review stage. Do not import upstream's release automation, host packaging or review-bot policy.

Source: [diagram-design comparison](https://github.com/cathrynlavery/diagram-design/compare/b46c9701f035844a20b13ab0551315977188933b...0cf73c3fcc56667ad91a9a04c439ac6ccfabc9d1).

### State the measurement decision before measuring

pstack's `principle-explain-the-number` now asks for the result that would change a decision and the noise floor before a run. MMW's principle already requires scope, alternative explanations, run count and spread, but its entry starts before trusting, reporting or acting on a number. The advance decision criterion was not explicit in the baseline.

That judgment is added to MMW's existing principle, and its mode trigger includes preparing a measurement. Keep benchmark procedure in benchmark-checklist. Keep the existing distinction between performance measurements and agent evals: an eval does not require a CPU or I/O limiter by default. A difference within run variation does not justify a claimed improvement. No new skill, form or gate is needed.

Source: [pstack principle-explain-the-number](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/principle-explain-the-number/SKILL.md).

### Make independent subagent context explicit

Matt's update explicitly requests a fresh context window for independent subagent jobs, including review and research. Its contributor guidance explains the failure: some hosts fork the parent's conversation by default, defeating the context separation the task needs.

MMW's dispatched worker, reviewer and researcher sessions already have separate startup prompts. The baseline left an ambiguity in the host's general-purpose subagent call: mmw-mode required a complete brief but did not explicitly select a clean context when the host offers that choice.

That choice is now explicit once in mmw-mode's `## Subagents`. An independent job receives its complete brief in a clean context. Follow-on work on the same job reuses the suitable existing subagent, as the owner's shared prompt requires. This does not authorize replacing, interrupting or rushing a running subagent. Do not scatter the same instruction through every calling skill.

Source: [Matt's comparison](https://github.com/mattpocock/skills/compare/49dd158d1076134a641b33efb035946536778336...a496f5513d4a4cf889bc48e189e579f4b0bdf6aa).

### Complete the comparison map alongside future adoption

At the initial comparison, `writing-for-agents/scripts/upstream-map.tsv` mapped one diagram-design file and omitted owned import/export scripts and adopted Matt and TypeScript guidance. The adopted scope is now mapped as described under Adoption status. OpenClaw, OpenCode and unlazy had no catalog snapshots before this refresh.

The existing upstream-hunks classifier therefore cannot establish that the whole skill set is current. In this review it inspected 38 pstack mappings, 14 Matt mappings, one diagram-design mapping and one e2e mapping. The changed source files were also compared outside that table.

The existing comparison mechanism is retained, with missing direct-copy mappings added alongside the carried changes. Record folded or substantially rewritten methods by their owning skill and adaptation intent rather than pretending they are byte-for-byte copies. The source catalog is now expanded; this task does not claim that the classifier map is complete.

## Updates already covered or not worth another rule

### Matt's tracker and setup changes

The upstream GitHub guide adds newer gh shorthand for native dependencies and sub-issues, distinguishes open blockers from closed blockers in `blockedBy`, and clarifies PR-body reads. MMW's wayfinder already uses the native REST dependency endpoint and open-blocker summary. setup-mmw already checks repository reachability through `gh repo view` and probes sub-issue and dependency support.

These changes do not establish a missing MMW capability. Keep MMW's current commands unless a consuming task demonstrates a defect. Keep the owner's `CONTEXT.md` and `CONTEXT-MAP.md` names; do not take Matt's glossary rename.

The focused Matt review found an exception to that initial assessment: repository reachability does not establish that the selected tracker is the consuming repository's intended tracker. `setup-mmw/scripts/check.py` calls `gh repo view` without an explicit repository and accepts its `nameWithOwner`. In an isolated probe, the project's origin was `owner/product`, the simulated gh default response named `upstream/skills`, and the real `check_tracker` returned `upstream/skills` with status `ok`. The probe used a temporary Git repository and a fake gh response, with no network or tracker writes. It proves the setup consumer accepts a mismatched default, not that a real issue was posted to the wrong repository.

The baseline `dispatch/scripts/dispatch.sh` `repo_slug` and `register-problem/scripts/register.py` `current_repo` used the same unspecified repository lookup. GitHub CLI's [default-repository documentation](https://cli.github.com/manual/gh_repo_set-default) confirms that the selected default is used for issues, PRs, releases and Actions.

The repair uses `dispatch/scripts/tracker.py` to read origin and ask `gh repo view <origin>` for its canonical owner/name. It ignores an inherited `GH_REPO` during that lookup. setup-mmw and its label commands pass the resolved target in each gh environment. dispatch exports it at command entry so its gh calls and child scripts share the target and relay identity. Started sessions receive the same `GH_REPO` through the runner environment. The shared task-board supervisor does not inherit that per-command target across repositories. register-problem uses it for the default target and occurrence context; explicit `--repo` and the toolbox destination retain their existing routing. A missing or unreadable origin refuses tracker operations instead of falling back to gh's default. No configuration file or owner-confirmation step is added.

Regression tests supply a conflicting gh default and inherited `GH_REPO`. They exercise setup reporting, registration issue creation and dispatch PR creation and checks against fake GitHub boundaries. Registration and dispatch also refuse writes when origin is absent. Existing explicit-destination tests remain in the registration suite. A read-only call to the installed gh confirms that `gh repo view` accepts the SSH remote syntax used by the resolver. This is not a live issue or PR write test.

Matt's fresh implementer per independent ticket is also already represented by MMW's dispatched ticket sessions. It does not override reuse within a continuing task.

### e2e's runner and diagnosis guidance

The changed e2e guides improve failure evidence, precise `file:line` reruns, starting near the behavior under test, saved session setup and locator APIs. The `create-verification-skill` source itself is unchanged in this interval.

MMW already tells agents to read `npx e2e guide <topic>` from the product's installed runner, not blindly use the snapshot's API version. test-audit already preserves the original failure, reproduces predecessor order when relevant and removes duplicated setup without dropping contracts. Let those existing entry points supply the updated runner details. Shortening a test must preserve the journey when that journey is the acceptance contract.

Do not add e2e's model-based test filters or exploratory agent flow to MMW's fixed-step acceptance path. Do not replace scripts/check's deterministic test selection with an AI exclusion decision. Screenshot and secret-handling changes require the product's actual runner version and evidence policy, not a blanket relaxation in MMW.

Source: [e2e skill tree](https://github.com/tester-army/e2e/tree/5b6fd01042c96e5d79e662325cfaae2157d6eac9/skills).

### TypeScript branded types

pstack now shows a validating type guard that narrows a branded value without a subsequent `as` cast. The MMW baseline permitted casts after validation and demonstrated that pattern in `typescript-best-practices/references/patterns.md`.

The rule and example are adopted together, retaining the requirement that a guard verifies its claim. This is a style refinement, not a reproduced runtime bug, and needs no owner product decision.

## New capabilities to keep as references

### pstack formal verification and orchestration

`create-formal-verification-skill`, `maintain-formal-verification-skill` and `statechart` provide model checking, counterexample traces, explicit scope limits, negative controls and model/code synchronization. Keep them available for a concrete concurrency or protocol question that current tests cannot settle. Their presence upstream alone does not justify a mandatory formal-verification layer or importing the whole toolchain.

pstack's Orchestrate now uses the host's own agent and PR tools, removes its former script engine, and describes cloud workers and owner-per-PR supervision. Autopilot-full and Autopilot-stack retain their own CI, swarm and PR-head verification contracts. They are alternatives to parts of MMW's runtime, not missing steps to insert into Run a night. Preserve MMW's dispatch, events, relay, watch and frozen installed version. Do not import automatic replacement of stalled agents; the owner forbids interrupting or rushing running subagents without an explicit request.

The rewritten interrogate emphasizes executed adversarial evidence. MMW already requires real evidence through principle-prove-it-works. Preserve legitimate Standards and Spec review findings instead of restricting all review to executed failures. Keep the settled MMW departures for arena's judge topology, model configuration, sharpen, PR delivery and the retired swarm.

`ketchup-video` is a new presentation option, not a reason to add video to the owner's existing Artifact and wait-what flow. Matt's chief-of-staff wiki likewise does not justify a parallel MMW knowledge store.

The focused Matt review refines the wiki assessment: chief-of-staff's wiki records historical experience, including dated claims and the commits those claims concern. CONTEXT.md defines terms and ADRs record qualifying decisions; neither substitutes for the history of attempted approaches and their outcomes. The capability deserves discussion on that distinct purpose. It does not justify importing chief-of-staff's whole orchestration model, a new schedule or a second store before establishing the missing use case.

Sources: [pstack skills](https://github.com/cursor/plugins/tree/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills), [Orchestrate](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/playbooks/orchestrate.md).

### Focused pstack adoption judgment

The focused review uses the same fetched pstack 0.15.36 at `4dd1d05818d19792e7cd6e818f1667f95f7e1dbe`; it is not another remote refresh. The measurement, TypeScript and worktree-audit changes are already adopted.

One additional synchronization gap is `wait-what/KETCHUP.md`. Its whole-reply limit remains well under 150 words. Upstream ketchup instead keeps the progress account short while preserving every waiting decision and enough context to decide it. The MMW text already prioritizes action items over narrative, but its global cap can conflict with that completeness when many decisions are waiting. Adopt the completeness and grouping judgment while retaining the owner's one-decision-at-a-time discussion. Do not copy fixed per-item word counts or mandatory risk boilerplate. This adaptation is now committed as `98c9696c`, changing KETCHUP.md and upstream intent P42. The assigned subagent made the edit and commit; the parent read the diff. Four selected checker steps and the bounded zero-item, one-item, many-item and shared-decision paper cases passed. No fresh-agent behavior proof or release is claimed.

The strongest optional new capability is the combination of create-formal-verification-skill, maintain-formal-verification-skill and statechart. The first generates a project-local check of a chosen property with a suitable tool; the second keeps that verification aligned with covered code; statechart explains TLA+ state exploration and failure paths. MMW's existing create-verification-skill generates fixed-step product-surface evidence, rather than this code-property verification. If adopted, keep the new capability optional, begin with one concrete property and coverage gap, preserve negative controls and code correspondence, and replay model counterexamples against the real code. Do not claim that a bounded model pass proves the whole product. Do not add a routine setup-mmw prompt or replace diagram-design with pstack's renderer. The statechart implementation and its toolchain have not been executed or audited in this review.

The interrogate rewrite makes executed adversarial evidence central. MMW already requires claim verification through principle-prove-it-works and code-review's finding judgment. Preserve Standards, Spec, Tests and Correctness; a documented decision or ineffective test can be a valid finding without a failing product run. The update does not justify a second generic review pass. Orchestrate's deletion of its former ledger machinery is a useful example of subtracting duplicate work, not evidence that MMW can remove the runtime supplying its cross-host event and watch behavior. Preserve the settled model, arena, sharpen, frozen-runtime and delivery decisions. ketchup-video remains an optional presentation candidate without a demonstrated need in the owner's Artifact workflow.

Sources: [ketchup](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/ketchup/SKILL.md), [create-formal-verification-skill](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/create-formal-verification-skill/SKILL.md), [maintain-formal-verification-skill](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/maintain-formal-verification-skill/SKILL.md), [statechart](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/statechart/SKILL.md), [interrogate](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/interrogate/SKILL.md), [Orchestrate](https://github.com/cursor/plugins/blob/4dd1d05818d19792e7cd6e818f1667f95f7e1dbe/pstack/skills/poteto-mode/playbooks/orchestrate.md).

### OpenClaw, OpenCode and unlazy

The adopted OpenClaw `test-audit` tree and the separately cited `docs/help/testing/writing-tests.md` are unchanged between the adoption commit `5310270e46cf020ab1e37204075970f3b2679812` and the fetched source commit. OpenCode's previously cited root `AGENTS.md` is unchanged between `92b2ca0dd727942e00aba3523ed141d53e78ea28` and the fetched commit. unlazy is still at the source commit MMW originally adopted. No refresh of those adopted passages is justified by this fetch.

OpenClaw's newly cataloged skills include `pr-simplify`, testing, performance, documentation and maintainer workflows. The inspected `pr-simplify` offers useful concrete simplification questions, but MMW's root instructions, principle-subtract-before-you-add, unslop and test-audit already own that work. It does not warrant a second mandatory PR pass or OpenClaw's fixed diff-size budgets.

OpenCode's eight skills are `app-e2e-tests`, `component-tests`, `effect`, `opencode-dev`, `rtl-aware-development`, `sample-skill`, `tui-tests` and `unit-tests`. `rtl-aware-development` is a useful future source for a product with RTL requirements. Its test skills contain product-specific Bun, Effect, Playwright and CI facts; they are not generic MMW runtime requirements.

The expanded catalogs make future research possible. This comparison inventories the full selected trees, verifies the adopted-source baselines, and reads selected new candidates. It does not claim a full semantic review of every OpenClaw skill and reference.

Sources: [OpenClaw maintainer skills](https://github.com/openclaw/openclaw/tree/6ac91adabcc273e76a2d652a5aefc9955b0600f8/.agents/skills), [OpenCode skills](https://github.com/anomalyco/opencode/tree/95fc3c87ca438527388b773e4c788cb7f5eb0e5b/.opencode/skills), [unlazy](https://github.com/Leonxlnx/unlazy/tree/16671491f6679ad9378f52604d3bc2415b4120c7).

## Delivery boundary

This branch contains refreshed and new upstream snapshots, the expanded source catalog, the maintenance changes under Adoption status, and this comparison. The repository checker excludes upstream test trees from its own-suite discovery, matching the existing read-only boundary. No upstream scripts were executed, no host installation was changed, and no branch was pushed or released by this task.

Validation:

- All eight snapshot trees match their recorded source or split trees. The adopted OpenClaw and OpenCode source comparisons are unchanged as reported.
- The worktree-audit regression exercises recent transcript detection for four hosts under strict emulations of GNU and BSD command formats. It fails before the repair and passes afterward. This is not a native Linux run.
- Five import/export CLI regressions fail against the previous owned scripts, with four assertion failures and one rejected-flag error. They pass against the adopted copies. Geometry and HTML checks also pass, retaining the existing multi-SVG, CJK and inline-interaction cases.
- `python3 scripts/check` passes the eight selected steps: self-check, syntax, shared-checks, lib, check-interfaces, diagram-design, writing-for-agents and worktree-audit.
- The repository-target repair passes shared checks, check-interfaces, setup-mmw and register-problem, plus the full dispatch suite. The initial retro run exposed fixtures without origin and without jq output support. Those fixtures now represent the consuming repository explicitly, and all 50 retro tests pass. Final dispatch coverage also checks runner target propagation and board startup after isolating their environments.
- The Artifact passes the owned HTML self-check and geometry check. The browser's URL policy blocked opening the local file, so no successful full-page render inspection is claimed.

The measurement and subagent prose was checked against the independent-job, continuing-job, benchmark and eval cases. No model behavior eval is claimed. Optional capabilities need a concrete use case before adoption; retain the current workflow until that discussion changes it.

## Verification integration follow-up

The owner requested a systemic investigation of create-verification-skill and maintain-verification-skill before deciding how to adopt the two formal verification methods. The existing UI path is substantially connected: prototype and bug preparation generate assets, preparation reads affected features, ticket writing prepares e2e acceptance, verify-ticket runs CHECK lines, the Spec axis compares prototype screenshots when named, and single-ticket/night closeout uses scripts/check --all. Full-product maintenance is deliberately owner-requested under ADRs 0048, 0055 and 0065.

The investigation identifies a missing common generation step for supported products without a verify skill, an unavailable-input cycle when a blank project's prototype preparation calls full generation before a runnable prototype exists, and an unresolved scope question when the shared UI protocol requires a prototype for known-behavior repairs. The last point intersects ADR 0055 and is a design clarification to accept before editing, rather than permission to weaken the UI baseline. API-only and unsupported surfaces need explicit handling through the already selected engine or control/testing method. These are textual route findings and paper traces, not observed product failures.

The proposed formal integration reuses Testing Decisions or independent Seam, Read first, Owns, CHECK/EXPECT/EVIDENCE, the existing review axes, reverify and scripts/check. A project-local formal verify skill records code coverage, properties, assumptions, bounds, commands and its code-sync commit; ordinary related changes update it, while maintain-formal handles missed updates and broader requested maintenance. UI acceptance remains frozen as agreed; formal model/harness changes are scoped separately under Owns without allowing properties to be weakened for a pass. No new Playbook, event, watch, model role, registry or verification orchestrator is proposed.

The upstream TLA+ path depends on statechart. Importing only the two method entries would leave that reference unresolved. The proposed minimal first adoption explicitly adapts the reporting step to the selected verifier's native counterexamples and existing diagram-design. This omits statechart's automated multi-rule shortest-path reporting; full statechart adoption remains a separate toolchain choice. No upstream scripts or formal tools were executed.

The new Artifact is `mmw-verification-integration.html` beside the existing upstream review. It records the current flow, proposed connections, exact call locations, three findings, scope/authority boundaries, source excerpts and a scenario matrix. The source inventory and content fingerprints are in `.scratch/verification-integration/`. The task-board verify skill, configuration and feature/test headers were inspected as one existing example; no app, device or e2e run was performed. Verification skills and runtime remain unmodified by this investigation.

### Approved frontend and verification integration

Following the focused pstack review, the owner approved a complete frontend workflow restructuring after advisor review. Design a UI now owns the design interaction, prototype retains its construction methods, prepare-ui-acceptance owns per-change UI proof, and shared ticket preparation calls all four create/maintain methods at their respective conditions. The two formal skills use the pinned pstack methods with native checker output and real-code replay, without adopting statechart's runtime or automated reporting. ADR [0066](../adr/0066-ui-design-and-verification-have-distinct-owners.md) and the [implementation record](frontend-workflow-implementation-2026-10-30.md) record the architecture, content migration, bounded agent walks and validation limits. The eighteen branch documents moved to references/ with actual consumers; historical source citations stay unchanged. This supersedes the earlier optional-adoption status for the two formal skills, not the separate unresolved statechart or wiki questions.
