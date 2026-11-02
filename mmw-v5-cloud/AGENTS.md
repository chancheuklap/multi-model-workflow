# MMW v5 cloud edition

This directory is a complete cloud edition: all skills, tools, board assets and project configuration are present here. It packages and runs without reading `mmw-v5/` or importing the MMW development checkout.

Except for dispatch, skill files must match the local edition byte-for-byte. Apply ordinary skill changes to both complete editions. Keep role orchestration and cloud-specific commands in dispatch and its tools.

Only the local Coordinator reads or writes GitHub Issues, dependencies, comments and PRs. Cloud agents use their native parent-child channel. Local runners, relay and event/report protocols belong to the local edition.

Skills remain model-invocable. Put role documents in `references/` with lowercase, hyphen-separated filenames.
