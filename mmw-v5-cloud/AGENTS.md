# MMW v5 cloud edition

This directory is a complete cloud edition: all skills, tools, board assets and project configuration are present here. It packages and runs without reading `mmw-v5/` or importing the MMW development checkout.

Preserve the professional methods and standards shared with the local edition. Adapt dispatch-related roles, inputs, communication and reporting where this edition's workflow requires it.

The local Coordinator manages GitHub Issues, dependencies, final PR bodies and merges. Cloud Workers push their assigned branches and create their draft PRs. Cloud agents return questions and work reports through the host's native tools; the caller resumes the same agent with its answer. Local runners, relay and event/report protocols belong to the local edition.

Skills remain model-invocable. Put role documents in `references/` with lowercase, hyphen-separated filenames.
