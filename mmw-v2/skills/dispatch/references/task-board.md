# Opening the task board

Resolve `<dispatch>` in the `## Resolve `<dispatch>` once` section of [../SKILL.md](../SKILL.md).

Run `<dispatch> board` from any checkout or worktree of the consuming repository. It registers the main checkout in `MMW_HOME/boards.json`, reuses that repository's fixed local port, and starts the task board if it is not already answering. Opening a night, and `open-ticket` for one ticket outside a night, do the registering and starting by themselves and print the URL; this command is what opens the board in front of somebody, and what starts it when no night is open. The selected runner's adapter opens the URL in the current worktree when it implements `open-url`; otherwise the command prints the exact local URL for you to open. Exit 0 means the tab was opened or the URL was printed. Exit 2 means setup or startup was refused, with the reason on stderr.
