---
name: maintain-verification-skill
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Maintain a feature map

Lint and the commit that changes a feature keep a feature map in shape. They miss a wrong step, an entry that does not open, a screen that was never registered, and a behaviour whose line is `check: none:`. The owner asks for this pass so the next agent can follow the map. A clean result that skipped the live drive is read as a finished review, and that next agent then drives a path that does not work.

The unit is the feature file. Cover every feature file from source, and drive every feature from every entry. Do not turn every bullet into its own procedure.

Drift is a mismatch between the feature map and the product.

## Outcomes

Pick one, and say which.

- **clean.** Every feature got source coverage and a live drive, and the feature map needs no commit. Product defects, with the map left as it is, are clean. List each issue URL beside the outcome.
- **changed.** The map, a drive script, `doctor`, or a journey changed. The change ships through the `mmw-mode` skill's `playbooks/make-a-small-change.md`, including **Get a second reading**.
- **blocked.** Coverage did not finish, or a proven fix could not ship. Say what blocked it.

## Edit scope

Edit only these.

- `docs/features/<product>/`
- `.mmw/<product>/drive/`
- the `doctor` of `.mmw/<product>/`
- a journey this pass writes under `.mmw/<product>/journeys/`

Leave product code and the product's own tests unchanged. A behaviour the map describes and the product does not do is either a wrong description, fixed in the map, or a broken product, reported as an issue.

## Pass

Open a todolist with one item per step below.

0. **Locate the product.** A product here is a name that has both `docs/features/<product>/` and `.mmw/<product>/`. No such name means the repository has nothing to review. Stop, and name the `create-verification-skill` skill. Do not invent a target. More than one such name means ask the owner which product to review.
   Done when one product is named and both directories are present, or the run has stopped and named the `create-verification-skill` skill.

1. **Fix the index.** Run `feature_map.py lint` from the repository root. The program is the `verify-ticket` skill's `scripts/feature_map.py`. Fix every problem it prints for this product before the source wave. A `NOTE` on a `check: none:` line does not fail the lint. Leave those lines for step 5. A problem it prints for another product is outside this pass. The outcome is **blocked**, and the run record names that product.
   Done when a fresh run exits 0, or the pass is **blocked** on another product.

2. **Read the source.** One read-only subagent per feature file, in one batch. Follow the `mmw-mode` skill's `## Subagents`. A subagent does not drive the product and does not edit files. The brief states the return and a limit of 200 words. The return has four parts.
   - What the user can finish.
   - The source entry points, each a file and a line.
   - Likely drift, or none. Each drift names a file and a line.
   - One way to drive the feature.
   Done when every feature file has that return.

3. **Register what is missing.** Read the commits since the newest commit that touched `docs/features/<product>/`. A user-facing screen those commits added, which no feature file names, is missing. Register one only with a concrete path in the product code. Write the file as the `mmw-mode` skill's `references/feature-map.md` says, and add it to the index in `README.md`. `source` follows that reference. When no decision record names the behaviour, `source` is `existing <YYYY-MM-DD>` and the date is the day it is written into the map.
   Done when each added file has a path in the product code and a `source`, and the index lists it.

4. **Drive every entry.** Do this even when step 2 found no drift. One session. Before the first command, the `ui-acceptance` skill's **Five rules while the product is running** bind the drive. Bring the product up with `start` and take it down with `stop`, through that skill's `scripts/lease.py`, passing `--product <product>`. Run `doctor` the same way. The three commands are the ones `.mmw/<product>/target.json` names. A web page or an Electron application is driven as that skill's `references/control-ui.md` says. A command-line product is driven as that skill's `references/control-cli.md` says. Drive each feature from each entry in `## How to get to it (user POV)`, following `## Driving it`.

   Three invariants hold for the whole pass.

   1. Run `doctor` before the first drive, again on each fresh session where a session is the unit, and again after any failed drive. When `doctor` exits 0 and the UI is wedged, reset to a known state or start again.
   2. Evidence captured so far is still at the path `## Proof and skip reporting` names, checked there after each cleanup.
   3. Nothing a drive started outlives that drive. Clean the residue. On a shared instance, clean the residue and leave the instance. After the last drive, including a re-drive of a fix, run `stop`.

   A `doctor` failure caused by `doctor` or a drive script is drift. Fix it inside the edit scope and retry once. Restart only what the fix invalidated. A second failure is **blocked**.

   A feature is unreachable only when the run record names the precondition and the route that was tried. A map that omits that precondition is a wrong description.
   Done when every feature is driven from every entry, or recorded unreachable with its precondition and route, and `stop` has run.

5. **Sort the drift.** Give each mismatch one of these.

   - A wrong or missing description is fixed in the feature map.
   - The product does the behaviour and the drive cannot reach it. Fix the script under `.mmw/<product>/drive/`, and drive that feature again before it ships.
   - The product is broken. Search open issues with `gh issue list --state open --limit 500 --label needs-triage`. Add nothing when one already states this defect. Otherwise `gh issue create --label needs-triage`. The title and body stand on their own for someone who did not watch the review. The issue is not part of the commit.
   - A `check: none:` line whose behaviour is one end-to-end path gets a journey under `.mmw/<product>/journeys/<flow>/`, written as the `ui-acceptance` skill's `references/journey.md` says. Its `check` is a command run from the repository root. The program is that skill's `scripts/journey.py`, and the arguments are `run <product>/<flow>`. Lint resolves that name to the journey directory, which has to exist. A line that only a test of the product can hold becomes an issue, by the same search. This pass writes no product test.
   Done when every mismatch has one of those outcomes, and every drive-script fix has been driven again.

6. **Commit or stop.** Re-read every changed file. Then run `feature_map.py lint` again, from the repository root, as step 1 does.

   For **changed**, follow the `mmw-mode` skill's `playbooks/make-a-small-change.md` in full, including **Get a second reading**. The request file is this pass's run record, at the path **Write down the change and judge its size** writes. It holds the owner's request word for word, the features covered, each unreachable precondition, each confirmed drift, and the outcome. Map corrections that do not fit one commit stay this pass. Commit once per feature, then one second reading covers those commits. They do not become a spec.

   For **clean** or **blocked**, commit nothing. The same run record goes under `.scratch/` and is not committed. **clean** lists each issue URL beside the outcome. **blocked** names what stopped the pass.
   Done when the outcome is one of the three, the run record is under `.scratch/`, and a **changed** result has been through **Get a second reading**.
