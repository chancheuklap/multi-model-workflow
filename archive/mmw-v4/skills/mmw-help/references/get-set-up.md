# Get set up

1. Install from the toolbox checkout: `bash mmw-v4/install.sh`. It links every skill for each host, registers the hooks, links the user-level prompt, writes `~/.mmw/models.json` when absent, and records the checkout in `~/.mmw/installed-root`. Installing changes what every session on the machine reads, so it is the owner's decision; `bash mmw-v4/install.sh --check` only reports, and `bash mmw-v4/install.sh --back` returns the machine to v3. The script's header comment lists every item.
2. Pick the host, model and reasoning effort of each dispatched role: `python3 mmw-v4/skills/dispatch/scripts/models.py config show`, then `config set`. The **dispatch** skill's `references/editing-models.md` has the usage. A change takes effect at the next start.
3. In each repository MMW is to work in, run the **setup-mmw** skill once: it creates the pipeline's labels, ignores its directories and gives it its `scripts/check`.
4. Start a real task in a session, with a goal and a check that can pass or fail.

Guide page 1 (`mmw-v4/docs/guide/01-setup.md`) has the details. Offer to word their first prompt with them, per [`references/prompting.md`](prompting.md).

If cost is the worry, say where the tokens go: dispatched workers and reviewers, the four review subagents each reviewer sends, and the candidates of `arena`. The four review axes use the `review-axis` subagent row, so you can change their model separately from the reviewer session. A cheaper model or a lower effort on a role's row of `~/.mmw/models.json` spends fewer.
