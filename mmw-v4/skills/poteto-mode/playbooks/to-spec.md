### To spec

**You own the spec, not the decisions in it.** Do NOT interview the user; just synthesize what you already know.

Takes the current conversation context and codebase understanding and produces a spec, published as a GitHub issue. The template is `../references/spec.md`; the `gh` commands are in `../references/github-issues.md`.

1. Explore the repo to understand the current state of the codebase, if you haven't already. Use the project's domain glossary vocabulary throughout the spec, and respect any ADRs in the area you're touching.
2. Sketch out the seams at which you're going to test the feature. Existing seams should be preferred to new ones. Use the highest seam possible. If new seams are needed, propose them at the highest point you can. The fewer seams across the codebase, the better. The ideal number is one.

   Check with the user that these seams match their expectations.
3. Write the spec using `../references/spec.md`, then publish it as a GitHub issue. Apply the `ready-for-agent` triage label. No need for additional triage.

**Reply:** the spec by name with its link, and the seams the user agreed.
