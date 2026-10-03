# Several specs from one reference

For a run whose reference turned out to be several specs, by the rule in step 1 of `SKILL.md`.

When what you have read is several specs, the division is a judgement you hand to the user: list each spec's name, the decisions it covers by ticket name, the order they go in, and why the line falls there. Once the user confirms, write the division back to the map as a `## Specs` section, one line per spec: name, the decision tickets it covers, its position in the order, and its spec link once published. Then write the first spec only; publish it, fill its link into that line, and stop; tell the user that the next spec is written by running this skill again against the map. When the map already carries a `## Specs` section, skip the judgement and write the first spec on it that has no link yet.

When the reference is not a map (an issue, a URL, a file, or the conversation itself), there is no map to write the division back to. Write it into the first spec's `## Further Notes` instead, as the template there says. Publish that first spec and stop; tell the user that the next spec is written by running this skill again with this spec's issue number. When the reference is a spec whose `## Further Notes` carries a division, write the first spec on it that has no link yet, and fill the link into its line through `references/revising-a-spec.md`, since that spec is already published. When every line has a link, tell the user the division is fully written and stop.

Stopping ends the specs this run writes; the spec it wrote is still published as step 4 of `SKILL.md` says.
