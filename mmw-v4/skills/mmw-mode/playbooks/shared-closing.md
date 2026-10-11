### Shared closing

**Prove the change, have it read by eyes that did not write it, and deliver it as one pull request.**

Invoked at the end of a playbook whose session wrote a change itself, in a session the owner opened. A ticket's closing is in Work a ticket; this one has no ticket. Use GitHub CLI (`gh`) for every PR operation.

1. **Prove it on the product.** Run the changed behaviour the way its user meets it (**principle-prove-it-works**), then the tests that prove this change and no more (**principle-run-the-smallest-test-set**). A test that will not pass is answered as **principle-fix-root-causes** says. Done when the product shows the change and those tests pass.
2. **Clean the comments.** Run the **no-comments** skill on the diff. Done when it has run.
3. **Have it read.** Write the owner's request, word for word, to a file `mktemp` makes. Start four of your host's general-purpose subagents in one message, one per axis of the **code-review** skill, naming no model, each with one sentence: `Read the mmw-mode skill in full, then read the code-review skill's references/<axis file> and review the request in <file> from base commit <base-commit>.`, the axis files being `standards-reviewer.md`, `spec-reviewer.md`, `tests-reviewer.md` and `correctness-reviewer.md`. Hold this turn until all four have reported; a host that cannot run subagents runs the four files one after another itself. Verify every finding as the code-review skill's `references/session.md` step 3 says, then fix each that holds in the commit of its cause, or note what refutes it. Done when every finding is fixed, refuted, or named in the reply as one you could not tell.
4. **Commit.** One commit per cause; a commit touches only what its cause requires and the tests that prove it, and its message quotes the line the test run printed (`ran 188 skipped 0`, not "the tests pass"). The message says what changed and why; the files say only what is true now (**principle-files-describe-the-present**). Rebase into small, ordered commits that tell the story. Done when the branch is those commits.
5. **Merge the latest project branch.** Fetch, and merge `origin/<project branch>` into the branch. A conflict, or a clean merge that turns the checks red, goes through the **resolving-merge-conflicts** skill. Run the repository's checks (`checks` in `.mmw/target.json`); a red check is answered as **principle-fix-root-causes** says. Done when the merge is committed and the checks pass.
6. **Open one pull request.** Push the change's own branch, cut from the project branch (`git switch -c <branch>` first when the session wrote on the project branch itself), and open one pull request to the project branch, written as **The pull request** below says. One change, one pull request: never a stack. Done when it is open.
7. **Hand it over.** Give the owner the link. When the owner says yes, `gh pr merge <pr> --merge --delete-branch`. Done when it is merged, or the owner has the link and has not said yes.

**Reply:** each review finding, with the commit that fixed it, what refuted it, or that you could not tell; whether step 5 ran the repository's checks or `.mmw/target.json` names none; that the merge waits for the owner's yes. It goes into the reply of the playbook that invoked this one.

#### The pull request

The same rules write every pull request MMW opens: this one, a night's (the Run a night playbook) and one ticket's.

Write every PR title, PR description, and commit body with `/technical-writing`, then apply `/unslop`. Apply every technical-writing layer except Diátaxis. Use one word for each action, keep articles, and avoid `-ing` when a plain verb works. Name every file, section and ticket the description mentions by its anchor (**principle-anchor-every-reference**).

**Titles.** Use Conventional Commits in the form `type(scope): subject`. Use `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf` as the type. Use the changed area, such as `pstack` or `mmw-mode`, as the scope. Keep the subject short and imperative. Name a real symbol when one carries the change. For example, `fix(dispatch): refuse a finish whose pull request has an open thread`. Do not add a trailing period. A night's pull request is titled as Run a night step 6 says.

**Two readers.** The owner reads the top and does not read code; a collaborator reads the rest with the diff. The top says, in plain words: what changes for the people who use the product; what the owner must decide, each with a recommendation; what was not done and why; what changes once it is merged.

**For code readers.** This half of the body is a briefing, not the lab notebook. A reviewer who has the diff should learn why the change exists, what it leaves out, what it could break, and how you proved it works, in under a minute. Write short, simple sentences with few identifiers. Do not write walls of text. Keep this half under about 40 lines.

Put each section under a `##` heading, not a bold lead-in, so the sections stand apart. Use these sections in order. Drop a section when it has nothing to say.

- `## Why` gives the problem and the approach in one to three short sentences. Do not list SHAs or rebase genealogy. Do not add a "based on main" preamble.
- `## What changed` has one to three short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget.
- `## Scope` always names what the PR covers and what it deliberately leaves out, for example a related follow-up or a known gap. Use one to three short items. Do not list symbols or paths, and do not write a file-by-file essay.
- `## Tradeoffs` names only rejected alternatives that a reviewer would otherwise ask about. Skip this section when there was no real choice.
- `## Blast Radius` gives one or two sentences on who or what the change touches and why that is safe or risky. If main is red, state the cost of leaving it red.
- `## Verification` has one to three bullets. Each bullet names a real run path and its outcome. For a performance change, report one primary number with its unit in `before → after` form. Do not include sample-size methodology or metric tables.

After these sections, attach videos or screenshots when they prove a claim. Do not paste full SHAs, arena lane recitals, lever-correction essays, file-by-file checklists, or "CLEAN" verdicts. Put these details in a linked artifact. A commit body does not restate its subject.

**Readiness.** Open every PR ready, never as a draft: with `gh`, omit `--draft`. Run `gh pr view <number>` before you refer to PR status.
