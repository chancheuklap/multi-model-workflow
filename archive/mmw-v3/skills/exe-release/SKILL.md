---
name: exe-release
description: "Run only when the user, mmw-mode or another skill names it; do not invoke it on your own."
---

# Release

This skill packages one shape of product: an Electron shell plus a Python backend compiled to a Windows executable, installed by an NSIS installer, built on a Windows machine over SSH. The Ship a release playbook drives it; this skill keeps what it drives: the release manifest, the release engine, and the scripts behind both.

A **release manifest** is the JSON file that declares how one product is packaged: one product per file, its filename ending in `.release-adapter.json`. Adding a product means writing a release manifest, not writing Python. `references/key.md` says why each of its parts exists and what it costs to get wrong, and how to prove one without building; `references/new-product.md` is where a product that has never shipped through this skill starts, before it hands off to `references/key.md`.

The **release engine** is `scripts/release-flow.sh`. It owns each product's release loop: its state, the next stage, the repair count, and whether it succeeded. The build machine receives `git archive HEAD` and nothing else, so only committed work ships.

```bash
bash scripts/release-flow.sh init --manifest <path> [--max-rounds N]   # start one product's loop; refuses a dirty tree
bash scripts/release-flow.sh where                                      # the state, and the next thing to do
bash scripts/release-flow.sh stage run --stage <name>                   # run one stage; on failure it triages, dispatches the fix and counts the round
bash scripts/release-flow.sh receipt                                    # what the loop has tried, with the logs it names
bash scripts/release-flow.sh resume|close|abort                          # continue after a pause; finish a shipped loop; drop one
bash scripts/release-flow.sh same-commit <product>...                   # whether each product's delivery record is at HEAD
```

What happened is on stdout; the exit code says only which of three things happened, the same for every subcommand. The header of `scripts/release-flow.sh` has the full table.

| Script | What it does |
| --- | --- |
| `scripts/release-flow.sh` | The release engine: the loop's state machine, triage, dispatch of fixes by tier (P2 derive committed automatically, P1 a fix brief for the agent driving the release, P0 stop), the delivery record |
| `scripts/release_contracts.py` | The authority on the release manifest's field names and shapes, and on findings and loop events: `validate-manifest`, `classify-findings` |
| `scripts/verify_key.py` | Checks a release manifest against the repository before a build: the files it names exist, its declarations agree with each other |
| `scripts/release_script_assembler.py` | Assembles a release manifest into the script the build machine runs, from `scripts/release_templates/nuitka_electron.ps1.tmpl` |
| `scripts/builders/nuitka.py` | Generates the Nuitka compile command from the release manifest's `python_backend` section |
| `scripts/diagnose_core.py` | Translates a failed build's logs into findings with a tier and a root-cause fingerprint |
| `scripts/fix_dispatch.py` | On a P1 failure, writes the findings as a fix brief for the agent driving the release |
