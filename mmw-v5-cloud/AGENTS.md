# MMW v5 cloud edition

This directory is a complete cloud edition: all skills, tools, board assets and project configuration are present here. It packages and runs without reading `mmw-v5/` or importing the MMW development checkout.

Preserve the professional methods and standards shared with the local edition. Adapt dispatch-related roles, inputs, communication and reporting where this edition's workflow requires it.

The Coordinator on this Mac manages GitHub Issues, Blocked by links, and merges. A cloud Worker pushes `ticket/issue-N`, opens the draft PR, and writes the ticket's result there. The Coordinator reads that PR and lands it. A question returns to the sender. Local runners, relay and event/report protocols belong to the local edition.

Skills remain model-invocable. Put role documents in `references/` with lowercase, hyphen-separated filenames.
