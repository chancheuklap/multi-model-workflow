# Benny automation

Benny is an optional pack for two Cursor automations. One classifies a report from a configured Slack channel. The other can reproduce the reported defect, verify a fix someone already made, or prepare a draft pull request for a fix of its own.

## Language

### Pack, configuration, and live automations

**Benny pack**:
The setup instructions, operational files, references, and templates shipped with pstack. The target repository holds its committed copy under `.cursor/automations/benny/`. The pack is dormant until the operator configures the live automations.

**Source-managed file**:
A file delivered and refreshed with the pack. Setup merges the source pack into the target repository, preserves destination-only files, and reconciles local edits before replacing a file.

**Benny configuration**:
The operator's settings for channels, triage identity, repository, tracker, routing, app control, status messages, and time budgets. The configuration selects models for triage, reproduction, code work, and media review. The configuration and maps live outside the source-managed pack. Secrets belong in the deployment environment.

**Operational file**:
The committed instructions a live automation reads directly from the target repository for each run. Triage and reproduction each have an operational file named `SKILL.md`. The plugin lists its invocable skills separately from these files.

**Project-scoped dependency**:
A shared pstack skill that a fresh automation agent can load through the target repository's committed `.cursor/settings.json`. Benny uses these dependencies for work such as tracing a cause, writing a failing test, and editing a verdict.

**Live automation prompt**:
The deployed request that points to the committed operational file. It links configuration committed on the automation's branch or states the required values itself. The pack's intent file supplies the operator's requirements. Each prompt template supplies secondary material for the corresponding draft.

**Automation draft**:
The proposed name, description, trigger, prompt, tools, repository, and model for one live automation. Creation or update requires the operator's request. For first installation, the operator approves the triage draft and confirms readiness for the editor handoff before setup begins the reproduction draft. The operator updates existing automations in their own editors.

**Thread-safety test**:
A harmless report used after the editor save and before enabling normal traffic. It checks the location and authorship of the verdict, the reproduction automation's use of the original thread, worker write restrictions, and the absence of posts or tracker issues when the source cannot be verified.

**Fail closed**:
Benny's rule to withhold an action when it cannot establish the conditions for taking it. An uncertain source parent prevents a post or tracker write. An unavailable control capability blocks a reproduction claim.

[Benny pack](../../../automations/benny/README.md) · [Automation intent](../../../automations/benny/FOR_AGENTS.md) · [setup-benny](../../../automations/benny/skills/setup-benny/SKILL.md) · [Configuration example](../../../automations/benny/templates/configuration.example.yaml)

### Source report and handoff

**Source report**:
The new top-level message in the configured source channel, together with its replies and attachments. The two automations normally start from the same message. A supported alternative trigger for reproduction still has to identify the original thread.

**Source coordinates**:
The source channel ID and the root message's timestamp. They identify the same source thread throughout the run, including after the automation opens a separate operations thread.

**Source permalink**:
The stable link back to the reporter's original thread. Triage checks the permalink against tracker issues and prior triage replies so a repeated trigger produces no duplicate issue or verdict.

**Source-parent preflight**:
A fresh check that the root exists, is readable, and matches the stored coordinates. Triage checks before a tracker write and immediately before posting its verdict. Reproduction checks before every source reply. Both verify that a sent reply landed under the intended root.

**Triage automation**:
The live automation named `benny-triage`. It examines the report, checks the likely owning layer and possible duplicates, and posts one substantive verdict in the source thread. A follow-up answer can correct a fact but carries no second marker.

**Triage verdict**:
The source-thread reply that gives the classification, any relevant tracker link or routing advice, and exactly one final marker. Triage can issue a bug verdict without creating a tracker issue, for example when a possible duplicate needs human judgment.

**Triage identity**:
The Slack identity configured as the trusted author of triage verdicts. A reporter or utility bot quoting a valid marker cannot qualify the report for reproduction.

**Trusted triage marker**:
Exactly one configured marker in a reply from the triage identity in the original thread. `[benny:bug]` and `[benny:performance]` make the report eligible for reproduction and may carry a tracker URL. The run stops silently on `[benny:other]`, conflicting markers, an untrusted author, or an expired verdict wait.

**Reproduction automation**:
The live automation named `benny-reproduce`. It waits silently for a trusted verdict and checks whether someone owns the fix or has produced a fix artifact. For an eligible report it exercises the reported path through the real app.

**Operations thread**:
An optional thread in a separate operations channel for reproduction status, detailed evidence, follow-ups, and a draft PR link. Its status message is the one root message the reproduction automation may create there. Without this channel, detailed status goes in the automation run output.

**Benny coordinator**:
The only agent allowed to post to Slack. In the fix phase it also owns the final diff review, commits, and draft PR. Analysis and media workers return findings. A code worker may make a scoped edit only in an environment that excludes Slack credentials and write actions.

**Follow-up window**:
The configured time after the initial result when Benny can respond to a direct question or concrete correction. Triage watches the source thread. Reproduction watches its operations thread when one exists. The separate verdict-wait budget limits how long reproduction can await the first marker.

**Polling and effort budgets**:
The time limits for triage, reproduction, and a new fix, together with the time allowed for a verdict, follow-up, or rejection. The polling interval sets how often the automation checks a thread while waiting.

[Triage prompt template](../../../automations/benny/templates/triage-automation-prompt.md) · [Reproduction prompt template](../../../automations/benny/templates/reproduce-automation-prompt.md) · [triage-issue-reports](../../../automations/benny/skills/triage-issue-reports/SKILL.md) · [reproduce-and-fix-issues](../../../automations/benny/skills/reproduce-and-fix-issues/SKILL.md)

### Classification, routing, and tracker intake

**Report category**:
One of five triage classifications. A **bug** violates intended behavior. **Performance** is a defect expressed as measurable delay, resource use, or loss of responsiveness. A **feature request** asks to change intentional behavior. **Question or feedback** covers questions and preferences without a concrete defect. A **reroute** belongs to another configured destination. Feature requests, questions or feedback, and reroutes carry the `other` marker. An unclear bug report can receive that marker and one focused question.

**Cause tracing**:
A bounded review of code and recent history that connects the reported action to the symptom and identifies the likely owning layer. A lower-level dependency can own a failure visible in another feature. Triage keeps a possible cause separate from a confirmed finding.

**Routing map**:
The optional, operator-owned mapping from confirmed product areas, code paths, or error signatures to destinations and owners. A reroute names the destination in the source thread. Without a matching route, the owner can remain unknown.

**Owner ping**:
A mention of a named person in the source verdict. The routing map and configuration must allow it. The eligible cases are a feature owner whose input a request needs, or a likely regression author identified by strong evidence. The default is no ping.

**Issue-tracker adapter**:
The configured connection for searching and reading tracker issues, creating one with a source link, updating a recurrence, and reversing a failed handoff. Benny can use GitHub Issues or another tracker. Its intake status and labels come from the configured tracker.

**Duplicate match**:
The result of comparing a report with a tracker issue. A **confident duplicate** shares an error signature, the affected area, trigger and symptom together, or a confirmed cause. **Possibly related** means a shared cause remains plausible. **Weak resemblance** means the similarity is superficial. **No match** means the search found no corresponding issue.

**Recurrence note**:
A short update to an existing issue that links a confident duplicate's source thread. Reopening, relabeling, or reassigning the issue requires a separate instruction in the configuration. A possibly related issue can appear in the verdict as uncertain. A long-closed issue can supply a lead when investigating a regression.

**Tracker intake issue**:
A record for a clear new bug or performance defect that is still live or has no known fix. Creation requires a verified source link, resolved tracker fields, no confident or plausible live match, and a way to reverse a failed handoff. The issue records the reporter's expected and observed behavior. A pstack execution ticket separately defines an assignment and its acceptance criteria. [Planning and tickets](../planning-and-tickets/GLOSSARY.md)

**Compensation action**:
The tracker operation that cancels, closes, or deletes an issue this run created if its verdict fails to land in the source thread. Triage checks that the reversal took effect.

[triage-issue-reports](../../../automations/benny/skills/triage-issue-reports/SKILL.md) · [Routing map example](../../../automations/benny/skills/triage-issue-reports/references/routing.example.md) · [Configuration example](../../../automations/benny/templates/configuration.example.yaml)

### Ownership and reproduction

**Fix ownership**:
A person's explicit claim to fix the defect, concrete implementation plan, or instruction to another agent to implement a fix. Log lookups, bot diagnoses, and requests to reproduce supply evidence. A person who has claimed the work keeps it. A concrete fix artifact can be verified.

**Fix artifact**:
An open PR with relevant code changes, a merged PR, or a merged commit that could resolve this report. Benny can find one in the source thread, tracker, repository history, or PR search. The artifact sends the run to verification of that revision.

**Control adapter**:
The configured skill for starting the target app at a specified revision, driving mapped features through the real UI, inspecting state read-only, taking screenshots, recording a run, and cleaning up. It also resets the feature for an independent attempt and identifies the app and test environment.

**Benny feature map**:
The operator-owned description of each user-facing feature Benny may reproduce. A section gives the user's path, adapter actions and reset, stable selectors, relevant states, preconditions, expected captures, and a read-only cross-check. A report outside the map leaves reproduction blocked. [Product verification](../product-verification/GLOSSARY.md)

**Environment translation**:
A safe substitution that exercises the same behavior in an available test environment. The result counts as *translated evidence*. If the missing environment is part of the defect, the substitution cannot establish an exact reproduction.

**Discriminating state**:
The point at which the reported path yields an observably different result from the correct path. The broken final state is the **discriminating symptom**. A recording that ends at a loading screen cannot establish a defect that appears only after loading finishes.

**Read-only state cross-check**:
An underlying value that independently confirms what the UI shows, such as the saved item ID after a selection. The cross-check observes the state without forcing the symptom. Patched-build evidence uses the same value when available.

**Media reviewer**:
A read-only worker who inspects a recording and screenshot to decide whether the discriminating broken state is visible. An uncertain review leaves the reproduction unconfirmed.

**Confirmed repro**:
A finding that the exact broken state appears on two independent attempts through the same real UI path. The run includes a reset, screenshots and a recording of the path, and a media review that confirms the visible symptom. The coordinator may send one unprompted source update.

**Could not reproduce**:
The required environment was available but the run did not establish the symptom within its reproduction budget. Ambiguous captures can lead to this outcome. The result goes to the operations thread or run output.

**Blocked**:
The run lacked a prerequisite for testing the report, such as the required app environment, an adapter capability, or a mapped feature. The missing prerequisite is recorded in the operations thread or run output.

[reproduce-and-fix-issues](../../../automations/benny/skills/reproduce-and-fix-issues/SKILL.md) · [Control-adapter contract](../../../automations/benny/skills/reproduce-and-fix-issues/references/control-adapter.md) · [Feature-map example](../../../automations/benny/skills/reproduce-and-fix-issues/references/feature-map.example.md)

### Existing fixes and new draft fixes

**Verify mode**:
The run that checks someone else's fix artifact. For an open PR the baseline is its base branch. For a merged fix the baseline is the preceding revision if it builds and represents the old behavior. Benny compares that version with the patched build using the same environment, data, and user actions. The existing author retains the patch.

**Confirmed**:
The existing-fix verdict when the baseline reproduces the symptom twice and the patched build shows the correct state twice. The coordinator can reply in the source thread with the before-and-after result and the original fix link.

**Insufficient fix**:
The existing-fix verdict when the baseline and patched build both exhibit the reported defect. The run keeps the original artifact and can report the confirmed reproduction in the source thread.

**Inconclusive**:
The existing-fix verdict when either side of the comparison lacks usable evidence. For example, the baseline does not reproduce twice or the patched build cannot run. The result identifies the missing observation in the operations thread or run output.

**Rejection window**:
The time after a confirmed reproduction when a person can challenge the setup or interpretation. A valid correction allows one corrected attempt. A claim of fix ownership prevents Benny from starting a competing change.

**Bounded fix**:
One optional attempt to correct a root cause established by runtime evidence. It follows a confirmed reproduction and an expired rejection window, with no outstanding rejection, fix owner, or existing artifact. The change must fit the repository scope and fix budget, and the adapter must be able to run both revisions. A cheap local test calls for a failing test before the fix.

**Before-and-after proof**:
Matched evidence of the broken state on the baseline and the expected state on the patched build. Benny repeats the real UI path twice on each, retains recordings and screenshots, and compares the same underlying value when available. A new fix also has to pass focused tests and checks of nearby behavior its changes could disturb.

**Draft pull request**:
The delivery of a new bounded fix after before-and-after proof, blast-radius checks, final review, and the repository's required checks. The coordinator links the tracker issue when one exists. The repository's own process decides merge and deployment.

**Operations status**:
The coordinator's account of a reproduction run in the operations thread or run output. Its status labels are *Reproducing*, *Could not reproduce*, *Blocked*, *Reproduced*, *Verifying existing fix*, *Attempting bounded fix*, *Draft pull request opened*, and *Fix did not land*. For an existing artifact, verification can also report *verified* or *reproduced but not fixed*. Configured status emoji display progress.

[reproduce-and-fix-issues](../../../automations/benny/skills/reproduce-and-fix-issues/SKILL.md) · [Verify an existing fix](../../../automations/benny/skills/reproduce-and-fix-issues/references/verify-existing-fix.md) · [Control-adapter contract](../../../automations/benny/skills/reproduce-and-fix-issues/references/control-adapter.md)
