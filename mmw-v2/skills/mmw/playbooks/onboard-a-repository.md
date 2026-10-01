### Onboard a repository

This playbook takes a repository to the state the landing pipeline can run a night in. What you write here is read at the moment of acting by every skill that publishes or triages an issue, and by every agent that explores this codebase; a wrong command or label is repeated by each spec, ticket and night after it, without an error. So make each file this playbook writes true of this repository rather than filling in a template: check a command against the repository before you write it down.

**Entry.**
- **Routed from mode `## Playbooks`.** Start at **Set up the tracker**.
- **Unattended.** This playbook runs with the user present. An unattended session that reaches it records the question where its role records a decision (mode `## Autonomy`) and stops.

1. **Set up the tracker.** Run the `setup-matt-pocock-skills` skill. Two of its answers decide whether the pipeline can run on this repository. The tracker you choose is also the landing pipeline's store: the skills that publish specs and tickets, the night's scripts and the task board talk to GitHub Issues through `gh` and to nothing else. Any other choice means no night can run on this repository; say that when you propose it. The night's scripts and the skills that publish specs and tickets write the default label strings verbatim; an override changes what `triage` applies and nothing else. In a repository the pipeline runs on, keep the defaults. When the tracker is GitHub Issues, add to `docs/agents/issue-tracker.md` what `references/issue-tracker-pipeline-sections.md` holds, as that reference's first lines say.
   Done when `docs/agents/issue-tracker.md` records the tracker the user chose and, for GitHub Issues, carries `## Three label sets` and the **Map** and **Frontier query** lines of `references/issue-tracker-pipeline-sections.md`.
2. **Write the agent files.** Run the `manage-agents-md` skill on this repository's `AGENTS.md` and `CLAUDE.md`. Write no line that points at the `mmw` skill: its description loads it in a repository that has a `docs/agents/issue-tracker.md` or a `.mmw/` directory, and the user can start it with `/mmw`.
   Done when the `manage-agents-md` skill's `bash scripts/check.sh .` prints `ok` and no line of `AGENTS.md` names the `mmw` skill.
3. **Install the checkers.** Run the `code-checkers` skill, which writes one checker command that runs every checker. Add the command to `checks` in `.mmw/target.json`, creating the file when the repository has none, in the form the `ui-acceptance` skill's `references/product-answers.md` gives for `checks`. The pipeline runs `checks` before a ticket closes and again at merge, and it is the only gate a commit made with `--no-verify` still passes through.
   Done when `checks` in `.mmw/target.json` runs the checker command, and that command exits 0 on the base branch as it stands.
4. **Answer the product questions.** A repository with a UI fills `.mmw/target.json` with the `ui-acceptance` skill and runs its `python3 scripts/target_config.py --check` until it exits 0.
   Done when `target_config.py --check` has exited 0, or the repository has no UI.
5. **Say how it takes changes.** Ask the user how this repository takes a finished change, and write the answer into `.mmw/target.json` as `delivery`, with a value the `ui-acceptance` skill's `references/product-answers.md` lists.
   Done when `.mmw/target.json` holds the `delivery` the user chose.
6. **Check the machine.** Run `bash "$(cat ~/.mmw/installed-root)/install.sh" --check`, which reads this machine's MMW install and changes nothing. A line saying it could not check (`没查`) is reported as not checked, never as fine (**principle-silence-is-never-a-pass**). Running `install.sh` itself is the user's call (mode `## Autonomy`).
   Done when `--check` has exited 0, or the user has every line it printed that was not ok.

**Reply:** each file this playbook wrote or changed; the tracker and the labels the user chose; the checker command in `checks`; the `delivery` value; the last result of `target_config.py --check`, or that the repository has no UI; every line of `install.sh --check` that was not ok.
