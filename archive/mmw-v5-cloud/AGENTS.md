# MMW v5 cloud edition

This directory is the cloud edition. Shared tools, board assets and default models are under `skills/dispatch/runtime/`, inside the dispatch skill's resource boundary. The edition packages and runs from this directory.

The Coordinator runs in a cloud agent. It renames that branch to `night/spec-N` or `night/ticket-N`, manages GitHub Issues, Blocked by links, and merges with gh. A Worker renames its branch to `ticket/issue-N`, opens the draft PR, and writes the ticket's result there. The Coordinator reads that PR and lands it. A question returns to the sender.

Skills remain model-invocable. Put role documents in `references/` with lowercase, hyphen-separated filenames.
