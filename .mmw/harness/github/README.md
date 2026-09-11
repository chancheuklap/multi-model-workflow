# GitHub fixtures

`responses.json` maps one compact JSON array of `gh` arguments to an object with
`stdout`, optional `stderr`, and optional `exit`. The harness records every argument
array in `$MMW_DATA_DIR/gh-calls` and fails loudly when the exact array has no response.
