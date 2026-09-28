# Vocabulary candidates — release

| concept | current name | proposed name | source | why the meaning matches exactly | identifiers it has (which stay) |
| --- | --- | --- | --- | --- | --- |
| The product-side module that imports everything the app needs before serving its first request, run once right after the compile to catch a missing dependency before a customer does | self-check module | smoke module | software testing: a smoke test, a quick, shallow check run before deeper testing to catch a defect severe enough to reject the build | It is exactly that: a fast check ("does it even import") gating the release before any deeper acceptance runs, and the release manifest's own sibling field for invoking it is already named `smoke` (`python_backend.smoke`); one leading word would then name both halves of the same idea instead of two different words for them | `SMOKE_IMPORTS`, `--run-module <pkg>._build_smoke`, `python_backend.smoke` (all stay) |
