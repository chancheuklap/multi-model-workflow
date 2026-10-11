# GitHub fixtures

`responses.json` maps one compact JSON array of `gh` arguments to an object with
`stdout`, optional `stderr`, and optional `exit`. The harness records every argument
array in `$MMW_DATA_DIR/gh-calls` and fails loudly when the exact array has no response.

The catalog contains one map, one spec and one open ticket. Its first comments read
returns an ETag; later reads return `304 Not Modified`, so automated board pages never
contact GitHub and still exercise the production cache path.
