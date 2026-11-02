# MMW v5 cloud edition

This directory contains cloud-specific deliverables. Shared skills and reusable code come from `mmw-v5/` at packaging time; do not copy and maintain a second source of them here. The installed package is self-contained and never imports this development checkout.

Keep cloud dispatch native: only the local Coordinator reads or writes GitHub Issues, dependencies, comments and PRs. Cloud agents return through their native parent-child channel. No local runners, relay, event/report protocol or new session registry belongs in this edition.

Skills remain model-invocable. Put role documents in `references/` with lowercase, hyphen-separated filenames.
