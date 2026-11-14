# Pull request delivery

The assignee receives a ticket describing the result to deliver. Its PR gives reviewers the code change and its proof. The selected forge records where the change actually lands.

## Language

### The PR and its owner

**Pull request (PR)**:
The request to merge the code change for one [execution ticket](../planning-and-tickets/GLOSSARY.md). Its `Why` section links the ticket. The main chat records the returned PR URL on the ticket so an owner or verifier can find the same change from either record.

**PR owner**:
The agent role responsible for a code ticket's PR and the sole writer of its branch in Autopilot and Orchestrate. It receives the ticket URL and any existing PR URL. A replacement agent can take over the role. The execution playbook determines whether the owner merges the verified change or hands it to the operator.
_Avoid_: owner alone when the operator or the author of an individual finding could be meant.

**Forge**:
The code host the run uses for PRs, checks, review threads, and merge state. pstack supports Origin and GitHub. A run-provided PR tool can track changes on the selected forge. Origin here is the forge, distinct from the Git remote named `origin`.

**Ready for review**:
An open, non-draft PR. Opening it in this state lets CI and automated reviews start while the owner continues work.

**Code-ready head**:
The exact commit an Autopilot owner reports after finishing the change, cleaning the diff and comments, checking the affected paths, and updating the branch to its intended base. The independent verification swarm can start at this revision.

**Self-proof**:
The PR owner's evidence that the implemented change works on the real artifact. The owner includes it in the merge-ready report. An independent PR verifier checks the change separately.

**Merge-ready**:
The state Babysit reports when the frontier clears the selected forge's checks, review threads, and merge gates within its remit. Under Autopilot, the owner's merge-ready report also carries its self-proof. Independent verification and the operator's grant govern landing.
_Avoid_: ready without a qualifier when it could mean ready for review or ready for merge.

**Landed**:
A PR the forge reports as merged with trunk as its base. For work on a project branch, that branch is trunk. Enabling auto-merge or getting a successful queue submission records a request. The resulting merge is confirmed separately.

### Stacks and the portion that can land

**Project branch**:
A branch the operator names to collect the PRs of one spec before they reach trunk. While it is named, trunk means that branch for this work. PRs open against it, and a PR is landed when it merges into it. Merging the project branch into the repository's trunk is a separate step the operator authorizes.

**PR stack**:
A chain of base branches. The root PR targets trunk. Each child PR targets the branch of the parent PR it builds on. *Upstack* means closer to the tip. A group of sibling tickets or a list of PRs in time order can have no such branch relationship.

**PR queue**:
The PRs covered by an Autopilot assignment. Autopilot-full runs independent PRs from trunk. Autopilot-stack can include dependent PRs in a base-branch chain and leaves the verified changes to the operator.

**Merge queue**:
The forge's queue for changes submitted to land. Admission can precede the actual merge. The GitHub watcher's `WAITING` reason `merge-queue` describes a blocker-free frontier still waiting to merge. The watcher derives that reason from the PR state, without checking queue enrollment.

**Merge frontier**:
The lowest unmerged PR in a stack. It is the first candidate for landing and the focus of a babysit pass. A lower PR moving to trunk can change the base and head of every PR above it.
_Avoid_: frontier alone when a [ticket frontier](../planning-and-tickets/GLOSSARY.md) could also be meant.

**Owning PR**:
The lowest PR in the stack that owns the code requiring a fix. A fix discovered on an upper PR can belong to a lower one. Once the owning PR has merged, Babysit can open a **follow-up PR** for a new ticket on top of the remaining stack.

**Verified run**:
The contiguous group starting at the lowest unmerged PR for which every PR has a current passing Shipping verdict. The first gap ends the run, even if a higher PR has passed.

**Ceiling**:
The highest PR in the verified run. It sets the limit of one shipping pass.

**Merge prep**:
The check that the verified patch still works on the trunk onto which it would land. A change in a caller, a shared file, or the checks that apply can require testing the merge result or rebasing. CI belongs to the head on which it ran.

**Patch-id rule**:
Shipping's rule for carrying verification across a rebase or restack. The verdict SHA identifies the commit that was checked. The patch ID identifies the change introduced relative to its base. An unchanged patch can retain its verdict across a new SHA. For a test, documentation, or lint-only difference, a lane's previous result can stand when its build output matches apart from demonstrated build noise. The changed material still receives fresh checks and review.

**Build noise**:
A difference that also appears across two builds of the verdict commit, or an embedded commit SHA. Shipping can exclude such differences when comparing the output a lane exercised. A lane with no comparable build output needs another run.

### Independent judgments on a PR

**PR verifier**:
An agent independent of the PR author, assigned to exercise the change at a named head. Shipping's verifier compares that PR's base and head on a real product interface and posts the judgment on the PR. [Product verification](../product-verification/GLOSSARY.md) defines the underlying evidence.

**Shipping verdict**:
An independent verifier's judgment on a particular PR patch. `PASS` and `PASS+NOTES` admit the PR to a verified run. `FAIL` stops the run at that PR. A green CI report and an approving bot comment answer different questions.

**PR verification swarm**:
Autopilot's independent verification of the code-ready head. The gates lane reruns repository checks, live lanes exercise the product, and audit lanes inspect the diff and the evidence. The regression lane compares the same scenario on trunk and head. The performance check compares like measurements or uses an absolute budget where trunk lacks the behavior.

**Clean verdict**:
The root's Autopilot judgment after the required live verification and audit of the owner's evidence. A demonstrated user-facing bug, failed gate, or shipped documentation made wrong by the PR can block. A base defect blocks when the PR copies it or newly reaches it. Each new head still needs green CI.

### Babysitting and review

**Babysit mode**:
The scope of a status request. `drive` continues to merge-ready. `background` triages alongside ongoing work. `threads-only` addresses review comments. `check` makes one status pass. Authorization to merge comes from the operator.

**Push wave**:
A batch of verified fixes published together so one round of checks covers them. Babysit gives conflicts priority over review threads and CI. A rebase belongs to the branch owner. A **drift sweep** checks for callers added on trunk that the stack's change now affects.

**Unresolved review thread**:
A forge discussion that still awaits disposition. The comment is a claim to check against the code. A CI pass does not resolve the thread.

**Bugbot pass**:
One review run by Bugbot, which can produce several threads. The GitHub watcher combines the review history into a pass count. Origin uses its own review history and thread list. From the third pass, a documented low-risk pattern can justify dismissal when the current evidence confirms it.

**Bugbot triage**:
The decision on an individual finding. `fix` identifies a real defect in the owning PR. `dismiss` records concrete disproof on the thread. `ask` refers a novel, ambiguous, or high-risk concern to the operator.

**Dismissal pattern**:
A documented low-risk case with conditions, exceptions, an example, and a source. Its confidence is `candidate` after one or two examples, `recurring` after multiple actual dismissals, and `strong` for a narrow, low-risk pattern repeatedly verified.

### Forge status and watcher results

**GitHub watcher mode**:
The scope inspected by the PR watcher. `single` observes one PR. `stack` can report readiness across the connected PRs. `queued-stack` follows a frozen bottom-to-top list and tracks the lowest unmerged PR as the merge frontier. The sanctioned follow-up for an already merged owning PR is the exception that can change this frozen list.

**GitHub watcher verdict**:
A report about the PR state observed on GitHub. The same word *verdict* in Shipping names a verifier's judgment on the code.

| Watcher report | Meaning |
| --- | --- |
| `QUEUE` | The watcher captured the queued stack in bottom-to-top order. |
| `STATUS` | A snapshot of the PRs, checks, reviews, and merge state. A status-only request ends with this report. |
| `READY` | Single or stack mode has cleared its readiness checks. The scope can include PRs already merged. |
| `WAITING` | `pending-checks` identifies the PR actually waiting. Stack mode can name an upper PR. Queued mode reports the lowest unmerged PR. Its `merge-queue` reason signals a blocker-free frontier, which Babysit can report merge-ready. |
| `ADVANCE` | The previous queued frontier merged and a new PR is now lowest. |
| `COMPLETE` | Every PR in the captured queue has merged. |
| `BLOCKER` | The watch ended on a conflict, unresolved thread, failing checks, merge gate, or persistent inability to read status. The reason determines who can act. |
| `RETRY` / `TIMEOUT` | A status read will be retried, or the watch reached its deadline. Neither report proves a defect in the patch. |

**Origin merge-ready state**:
The frontier's checks are green, Origin reports it mergeable with no blockers, and its thread list has no unresolved blockers. The Origin playbook reads its own forge state after a check watch. On Origin, merging an upper PR can include PRs below it, which is why Shipping addresses the lowest unmerged PR.

**CI state**:
The checks observed on a specific PR head. GitHub's watcher distinguishes checks that failed, checks still pending, a clean set, and an explicit GitHub refusal despite a clean visible list. For example, a `BLOCKED` merge state with a `FAILURE` or `ERROR` rollup for that head counts as failing checks. An earlier head's passing checks are history.

**Code Review Gate**:
The GitHub check with this exact name when it is pending or awaiting an owner's action. The watcher recognizes the human approval condition separately from failing or pending builds. A forge-enforced approval still requires its authorized reviewer.

**Merge gate**:
In GitHub watcher output, a closed-without-merge PR, a draft when drafts are disallowed, or a changes-requested review. A plan's **Review gate** is the operator's decision about the delivered behavior.

**CI failure classification**:
The explanation for a failed check during Babysit. A suspected flake or infrastructure failure permits one fresh build. The same failure again needs a diagnosis. A stale base calls for the owner to rebase. A failure caused by the change calls for a fix to the patch.

### Worktree cleanup

**Worktree audit bucket**:
The cleanup audit's recommendation. `hold-wip` identifies tracked changes, `hold-open-pr` an open or draft PR, `verify-recent-chat` recent transcript activity, `safe` a possible cleanup candidate, and `review` a worktree requiring investigation. A pinned or active chat and its in-use subagent worktrees take precedence over the recommendation.

**Worktree WIP**:
Tracked, uncommitted edits, reported as `wip:N`. Removing the worktree would lose them. `scratch:N` counts untracked files when there are no tracked edits. On a squash-merged PR, the recorded PR state can establish landing even when the branch tip is absent from trunk's ancestry.

## Sources

PR ownership, reporting, and the two authorization models come from [Opening a PR](../../../skills/poteto-mode/playbooks/opening-a-pr.md), [Autopilot-full](../../../skills/poteto-mode/playbooks/autopilot-full.md), [Autopilot-stack](../../../skills/poteto-mode/playbooks/autopilot-stack.md), and [Orchestrate](../../../skills/poteto-mode/playbooks/orchestrate.md).

Stack and review semantics come from [Babysit](../../../skills/poteto-mode/playbooks/babysit.md), [Bugbot triage](../../../skills/poteto-mode/references/bugbot-triage.md), and [Shipping](../../../skills/poteto-mode/playbooks/shipping.md). GitHub's [watcher policy](../../../skills/poteto-mode/scripts/watch-pr/policy.ts), [verdict types](../../../skills/poteto-mode/scripts/watch-pr/types.ts), and [readiness cases](../../../skills/poteto-mode/scripts/watch-pr/policy.test.ts) define the status meanings. Cleanup recommendations follow the [worktree audit](../../../skills/poteto-mode/scripts/worktree-audit.sh) and [cleanup playbook](../../../skills/poteto-mode/playbooks/worktree-cleanup.md).
