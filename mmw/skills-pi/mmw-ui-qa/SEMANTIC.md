# Semantic layer: B2, B3, B4

The three checks are listed in [SKILL.md](SKILL.md) under "Checks: two classes, nine kinds". This file is how to run them: method, where paths come from, dispatch contract.

The semantic layer judges whether the function, flow, and purpose the interface means to express are realized. **It does not judge whether a component exists.**

## Two fixed practices

**Keep the full session history.** Carry screens already visited, actions already taken, and reasons already given into every later step. Without history, repeat runs disagree.

**The agent completing the path is not the user completing the path.** Task completion is **not** a pass criterion.

## Cognitive walkthrough · four questions · B2

At each step ask:

1. Will the user want the correct outcome
2. Will the user notice that the correct action is available
3. Will the user connect the correct action with the outcome they want
4. After the action, will the user see feedback that things are moving

**Only question 2 needs visual information.** It uses both: structured visual-salience numbers (in first screen, size, contrast, occluded, stacking — how each is computed is [SKILL.md](SKILL.md) step 8) and one screenshot cropped to the relevant region. Questions 1, 3, and 4 use structured data only.

Ask the four questions per step. As many rounds as the path has steps.

## Trunk Test · six questions · B4

**One round per step.** Assume the user is placed on this step's screen with no prior context. Can they answer:

1. What product is this
2. Which screen am I on
3. What are the main regions of this screen
4. What actions can I take at this layer
5. Where am I in the whole flow
6. How do I go up a layer, or find what I need

Question 6 is adjusted for desktop apps: the original asks "how do I search", which assumes a search box. A desktop workbench may not have one. The other five stay in the original wording.

**Ask the six questions in the wording above. Do not rewrite them per product.** Results stay comparable. Any unanswered question is one B4.

## Confusion scale · B3

**Score each step alone**, three bands:

| Band | Means |
| --- | --- |
| Not confused | What to do now is obvious |
| Somewhat confused | Need to stop, read, or think before knowing what to do |
| Very confused | Still unsure after reading, or two or more options both look right |

**"High" means:** any step scored "very confused" is one B3; two consecutive steps on the same path scored "somewhat confused" is also one B3, pointing at that path segment, not a single step. **One isolated "somewhat confused" is not recorded.**

Consecutive steps across two paths do not merge — each path is scored on its own.

## Where walkthrough tasks come from

Walkthrough tasks cover **screens in this run's scope** (scope is [SKILL.md](SKILL.md) step 7). Two sources, different bars:

- **Paths from MMW artifacts.** Run `mmw artifact path prototype --sub README.md` and `mmw artifact index spec`, read the files about this product, and take operation paths written in user walkthrough conclusions and acceptance sections. The path must be a full path the user walked for a real goal, across several screens, and must include at least one failure path or edge. A single action merges up into its full path. Do not split to pad the count.
- **No artifact path in scope: build from jumps in the screen map** ([SKILL.md](SKILL.md) step 6). From the main window, one shortest path to each in-scope screen. Failure paths are not required. **The report must mark these as constructed** — they guarantee reach, not that a user would walk them.

The second source means B2, B3, and B4 always have a path. **Do not skip these three checks when artifacts yield nothing.**

## Handoff: main agent walks, `designer` judges

**The main agent owns the browser. The `designer` does not get it.** A second instance would reset app state, and a screen that appears at step five would be unreachable.

**One `designer` per full path, not one per step.** Per-step dispatch gives each `designer` an empty context, and question 4 cannot judge — it needs the state before the action.

**The main agent walks the whole path first, then delivers once.** Operate the app step by step, collect the data below, and after the path is done hand the whole **path pack** over once.

### Path pack

Path level:

| Field | Type | Content |
| --- | --- | --- |
| `product` | string | Product this run checks |
| `path-name` | string | What this path does, one sentence |
| `user-goal` | string | What the user wants from this path. Question 1 judges this |
| `source` | enum | `artifact` or `constructed` |
| `steps` | array | Below, in order |

Each step:

| Field | Type | Content |
| --- | --- | --- |
| `index` | integer | From 1 |
| `screen-id` | string | Node id in the screen map |
| `screen-title` | string | The title the user sees |
| `action` | string | What this step did. Step 1 writes "arrived at this screen" |
| `interactive-elements` | array | Each item: `name`, `role`, `in-first-screen`, `size`, `contrast`, `occluded`, `stacking`. Question 2 uses this |
| `a11y-snapshot` | text | Snapshot after this step |
| `change-after-action` | string | Diff the main agent wrote by comparing snapshots before and after. Step 1 has no before: write `initial state on arrival`. Question 4 uses this |
| `crop-screenshot` | string | Path of the cropped region. Question 2 uses it. The other three questions do not |
| `runtime-errors` | array | Errors this step produced. Empty array if none |

**Screenshots go in a temp directory and are deleted when the run ends.** A subagent cannot read bytes in the main agent's process, so screenshots go through files. Create the directory with `mktemp -d`, pass the path in the pack, delete the directory at the end of this run. After the run they have no consumer. **They are not artifacts. Do not resolve them with `mmw artifact path`.**

If `mktemp -d` fails, continue. Question 2 judges from structured visual-salience numbers only, and that finding notes there was no screenshot.

**Session history is not a file.** The path pack is the full history, loaded once into the `designer` context. Inside one task it can see every earlier step, so question 4 can judge.

### Dispatch

Four fields:

| Field | Write |
| --- | --- |
| Goal | First sentence: "Semantic layer: <this path's name>". Then: for every step in the pack, run the four cognitive-walkthrough questions and the six Trunk Test questions, and give this step's confusion band |
| Read | The full path pack, the screenshot directory path, and **the original wording of these three blocks**: the four cognitive-walkthrough questions, the six Trunk Test questions, the three confusion bands |
| Constraints | Read-only; do not touch the browser; do not edit any file; do not start the app; ask the four and the six in the wording given, verbatim, no rewrite, no add, no drop |
| Acceptance | The structured list below, plus a confusion band per step |

**Copy the four questions, the six questions, and the three bands into the task in full.** The `designer` is independent context and cannot read this file. "Evaluate with the cognitive walkthrough" makes it invent four questions, different per path, and results are not comparable. Criteria travel with the task.

Dispatch one independent-context `designer`. Read-only. No working directory.
Launch: call the native `subagent` tool with agent `mmw-designer` and the four-field task table in full as task.

Independent paths start in the same message. Summarize after all have returned.

### What the `designer` returns

A structured list. Each item: `check` (`B2`, `B3`, or `B4`), `step-index`, `screen-id`, `element` (filled when a specific element was judged, else empty), `failed-question` (number of the four or the six), `one-line-problem`, `reason`.

Also a confusion band per step, one of the three bands above. **The main agent computes B3 from those bands with the rule above. The `designer` does not report B3 directly.**

Empty return, bad shape, or a mid-run failure: skip B2, B3, B4. The report header "Skipped this run" names why. **Do not substitute the main agent's own judgment for the independent-context evaluation.**

### After return

Everything B2, B3, and B4 produce is a finding candidate. Go to disposition. Report items with no location as `needs-evidence`.
