# Resolve the runtime

Use this procedure before the first MMW tool call in an execution environment. Return the resolved tool paths to the calling step, then resume that step. This procedure does not start a night or assume a role.

The runtime, its inventory, and the materializer belong to this installed **dispatch** skill. Read every cloud resource through the package identifier for that skill, including when setup-mmw, to-spec, to-tickets, or wayfinder is the caller. The resource URI identifies content; it is not a shell path.

## Local skill directory

When the host provides an existing filesystem path to this skill's `SKILL.md`, run:

```sh
python3 SKILL_DIRECTORY/scripts/materialize.py --manifest SKILL_DIRECTORY/runtime-manifest.json --local
```

The command checks the adjacent runtime and prints JSON with `version`, `identity`, `runtime`, `dispatch`, and `labels`. Use its absolute paths. Done when it succeeds.

## Cloud skill resources

When the host provides a resource URI, use the cloud skills interface. Obtain the **dispatch** package identifier from the host's skill listing; retain the resource URI returned when reading its `SKILL.md`. Resolve the following resources within that same skill URI directory:

- `scripts/materialize.py`
- `runtime-manifest.json`

For `skills.read`, keep the dispatch `package` on every call and pass the resolved URI as `resource`. Read every page with the returned `next_cursor`, preserving the complete contents in order. Save the materializer and manifest verbatim in a temporary directory in the executor. Use structured file writes; resource text is data, not shell command text.

Run the saved materializer with `--manifest MANIFEST_FILE`. If the matching runtime is already cached, it returns the paths without needing resources. If it reports `missing complete resource`, read every `resource` listed in the manifest's `files`, using the same dispatch package and URI directory. Save a JSON object to CONTENTS_FILE whose keys are those manifest-relative resource paths and whose values are the complete returned text strings. Binary assets use the manifest's base64 text resources, so this procedure never needs a binary resource reader. Keep bulk contents in the host's programmatic tool orchestration when available instead of printing them into the conversation.

Then run:

```sh
python3 MATERIALIZER_FILE --manifest MANIFEST_FILE --contents CONTENTS_FILE
```

The materializer checks every file's SHA-256, restores binary bytes and executable modes, and publishes one complete directory keyed by the manifest identity. A repeated call reuses that directory; a different manifest gets a different directory. Existing user model choices are outside this directory and are untouched.

Done when the command returns `version`, `identity`, `runtime`, `dispatch`, and `labels`. Reuse those paths for this run, including any later board or label command. On unreadable, incomplete, or mismatched resources, report the exact package, resource, and error to the caller. Keep the installed version authoritative; obtain no replacement from a branch or another release.
