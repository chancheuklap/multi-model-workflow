# Write a key

A product ships by declaring one key: `<product>.release-adapter.json`, one file, JSON only.

**Adding a product means writing a key. It does not mean writing Python.** When something cannot
be said in the key, the answer is a new key field or a new capability in the skill — never a
script in the product repo. A script there is a copy of packaging knowledge that the next product
will have to write again.

**A product that does not ship through this skill yet starts in
[new-product.md](new-product.md)** — whether it has never been packaged, or ships today through
its own packaging scripts. That file covers what the repo must contain before a key is worth
writing, and it sends you back here for the fields.

`scripts/release_contracts.py` is the authority on field names and shapes. This file is why each
part exists and what it costs to get wrong.

## What belongs where

Ask one question about any piece of the build:

> **Move to a different app — does this have to be rewritten?**

| Answer | Goes | Shape |
| --- | --- | --- |
| No, only the values differ | **the key** | JSON |
| No, it is the same action | **the skill** | code, written once |
| Yes, it is this app's own business | **the product repo** | code, and keep it thin |

Two things are genuinely the product's own and stay in its repo: fetching an embedded runtime,
and a delivery format the app invented (a self-update feed, a hand-written installer with its own
install semantics). Everything else about producing a Windows package is the skill's.

Applied to checks, the same question reads: **a check every product needs is the skill's job and
is never optional; a check that exists only because of how one repo is built is the product's, and
is.** When you are about to require a new field, ask which side it falls on. If every product would
have to write the same thing, the skill should be writing it instead.

## The shape

```jsonc
{
  "schema_version": "2",
  "product": "<name>",                 // one word, used in fingerprints and delivery paths

  "toolchain": [],                     // extra tools only — see below

  "build_target": {
    "desktop_dir": "<electron app dir>",
    "installer_brand": "…",
    "installer_glob": "…/*-setup.exe",     // where the finished installer lands
    "asset_roots": ["src/…/assets/**"]     // which paths mean "this product changed"
  },

  "python_backend": { /* below */ },
  "electron": { /* below */ }
}
```

That is a complete key. The engine supplies the pipeline — `verify_key`, `assemble`, `build` —
and the skill supplies the diagnoser. A key adds `stages` only for what it needs to run *before*
that, on its own repository: the version is not one that already shipped, the repository still
matches what the key claims. The engine appends its three afterwards.

Those three names are reserved; a key that uses one is refused. The rule used to be that a key
naming one of them took over the whole list — and a key that had copied `assemble` from another
key silently turned the engine's `verify_key` off, with every step still reporting green. If a
product needs a different assemble or a different build, the skill is missing a capability: add
it there, not by shadowing a stage here.

Paths in the key are repository-relative POSIX paths, and two templates are available:
`${DESKTOP_DIR}` and `${BUILD_ROOT}`. Absolute paths are refused: the key is written on one
machine and executed on another. `${RELEASE_PLUGIN_DIR}` expands to the skill's own `scripts/`
directory — use it for anything the skill provides, since where the skill is installed is the
host's business.

**`toolchain` is extras only.** Step 1 of the build checks every command the generated script
actually invokes — the compile runner, the package manager, the build-machine setup script — all
derived from what this key already says. List a tool here only when the product needs one beyond
those. Restating the derived ones is how a key ends up demanding a tool the build does not use,
and turning a working build machine away at step 1.

### `vendor_artifacts` — a binary the package ships but git cannot hold

ffmpeg, an embedded interpreter, anything too large to commit. Put the files on the build machine
under `<cache_root>/vendor/<name>/`, and the key says which ones to copy in and where:

```jsonc
"vendor_artifacts": [{
  "name": "ffmpeg",
  "lock": "resources/ffmpeg/.ffmpeg-version-lock-win64.json",
  "members": [
    {"file": "ffmpeg.exe",  "dest": "resources/ffmpeg/bin/ffmpeg.exe",  "sha256_key": "ffmpeg_exe_sha256"},
    {"file": "ffprobe.exe", "dest": "resources/ffmpeg/bin/ffprobe.exe", "sha256_key": "ffprobe_exe_sha256"}
  ]
}]
```

**Nothing is downloaded.** Upstream retention is not yours to control: one product locked an address
that has since gone dead -- the release branch it named was dropped from the upstream tag, so those
exact bytes can no longer be obtained by anyone. A file on a machine you own does not rot.

**The hashes are the point.** `lock` is a JSON file in the repository recording each file's sha256,
and a copy that does not match stops the release. The same tool built from a different source is
not the same file, and the difference does not announce itself: the build succeeds, the app runs,
and on a customer machine it quietly does the slow thing. The one this rule caught: the locked
ffmpeg needs an NVIDIA driver from 2021, the current upstream build needs one from 2025, and
customers in between lose GPU encoding and never see an error.

Keep the hashes in the lock file rather than in the key when the repo already reads them -- one
place, or they drift.

### `python_backend` — compiling the backend

One Nuitka invocation per entry in `targets`. The skill renders the command; the key supplies
every value in it.

```jsonc
"python_backend": {
  "runner": ["uv", "run", "--extra", "<runtime extra>", "python"],  // up to `python`
  "output_dir": "${DESKTOP_DIR}/python-runtime/backend",
  "jobs": {"default": 10, "env": "…_NUITKA_JOBS"},
  "console": false,                    // false ⇒ --windows-console-mode=disable
  "icon": "src/…/tray.ico",
  "include_packages": [],              // code
  "include_package_data": [],          // data files inside those packages
  "include_distribution_metadata": [], // packages that read their own version at runtime
  "include_modules": [],
  "nofollow_imports": [],
  "include_data_dirs": [{"source": "src/…/assets", "dest": "…/assets"}],
  "extra_flags": [],                   // escape hatch, not the front door
  "env": {"CCACHE_BASEDIR": "${REPO_ROOT}"},
  "isolate_dirs": ["${DESKTOP_DIR}/node_modules"],
  "targets": [{"name": "…", "exe": "….exe", "entrypoint": "src/…/__main__.py"}],
  "smoke": {"exe": "….exe", "args": ["--run-module", "…._build_smoke"], "modules": [...]}
}
```

Each of these fields exists because a build failed without it:

- **`include_packages` brings the code; the data files inside it do not come with it.** Miss the
  data and the app raises FileNotFound on a customer machine, not on the build machine. Name the
  directories you need in `include_data_dirs`. Reach for `include_package_data` only when you
  cannot name them, because it sweeps the *whole* package: every non-code file that happens to sit
  there, including the `CLAUDE.md` and `AGENTS.override.md` written for people inside your company.
  One product shipped 36 of those inside the customer's exe, and nothing said a word. When both
  fields cover the same file, Nuitka prints `Duplicate data file ... ignored` -- that line is
  telling you `include_package_data` is doing nothing you asked for and something you did not.
- **`include_modules` for anything imported inside a function body.** The compiler traces imports
  statically; a C extension imported lazily is invisible to it and simply will not be in the
  package. The customer finds out when they reach that feature.
- **`smoke.modules` is also the guard on `nofollow_imports`.** A nofollow pattern can block a
  module the built exe needs. The skill checks this at assemble time, because finding out after
  the compile costs tens of minutes.
- **`console: false` for a GUI app**, or every customer gets a black console window.
- **`env` values may use `${REPO_ROOT}`.** The build machine's repository path changes every round
  (the directory is named after the commit), so anything that has to name that path -- a compile
  cache's base directory, for one -- can only be computed there.
- **`isolate_dirs` moves directories out of the way during the compile.** When the Electron app's
  `node_modules` sits inside the Python package scan path, the compiler scans it: compile time
  explodes and front-end files can end up in the package. They are moved back afterwards, and a
  failed restore stops the build — an Electron build against a missing `node_modules` fails in a
  way nobody can trace back to here.

Native extensions that need a DLL the compiler does not carry go in `build_target.native_ext_dll`:

```jsonc
{"reason": "…", "dll_names": ["python3.dll"], "dll_source": "compile_interpreter",
 "dest": "pyd_package_dir", "pyd_package": "<the package holding the .pyd>"}
```

`dest` matters more than it looks. Windows loads a `.pyd` looking for its dependencies **only in
the `.pyd`'s own directory**, so a DLL dropped at the dist root is not found. `dll_source`
decides where the build machine looks: `compile_interpreter` (an abi3 forwarder like
`python3.dll`, which must match the interpreter the compiler ran under) or `system32` (the MSVC
C++ runtime).

### `electron` — the shell and the installer

```jsonc
"electron": {
  "dist_dir": "dist",
  "unpacked_dir": "dist/win-unpacked",
  "compression": "maximum",
  "compression_env": "MMW_ELECTRON_BUILDER_COMPRESSION",
  "installer": "electron_builder"      // or "repo_hook"
}
```

Every field has a default that fits the common case; `"electron": {}` is a complete declaration.
The front end is installed and built with pnpm and a `build` script — one set of commands in the
skill, not a field each key restates. NSIS comes with electron-builder, so the build machine does
not need a standalone `makensis`: requiring one more tool would turn a working build machine away
at step 1.

`"installer": "repo_hook"` is for a product whose delivery format is its own — a self-update feed,
or a hand-written installer whose semantics (carrying the VC++ runtime, stamping an app id,
keeping user data on uninstall) the generic installer cannot reproduce. That key must also declare
`build_hooks.installer`. Leave a product on `electron_builder` unless it truly has its own format.

### `build_hooks` — where the product gets called back

Hooks hang on phases, not on step numbers: which steps exist depends on what the key declares,
so the numbers move; the phases do not.

| Phase | Hook | What the product does here |
| --- | --- | --- |
| `runtime_ready` | `runtime_prepare` | fetch the embedded runtime, media assets |
| `runtime_ready` | `asset_parity`, `credential_proof` | check assets, emit proofs |
| `backend_ready` | `backend_verify` | the compiled exe just landed — prove it starts |
| `artifact_ready` | `artifact_scan` | scan the packed output |
| `installer_ready` | `installer` | only with `"installer": "repo_hook"` |
| `release_ready` | `package_integrity` | the installer exists — verify it |

**`build_hooks` is optional as a whole, and a first key omits it.** Add one when the product has a
check of its own to run at that moment. Declaring a hook with an empty argv is refused: that reads
as configured but does nothing.

**A hook's own logging has to survive the build machine's codepage.** A Windows build machine
outside an English locale runs Python with a legacy codepage on both ends, and a hook that moves
subprocess output around crashes on it while the check it ran was passing. Both directions need
saying, once, in the hook: read with `subprocess.run(..., encoding="utf-8", errors="replace")`,
and at start-up `sys.stdout.reconfigure(errors="replace")` for what the hook prints itself.
Without the first, the reader thread dies and `result.stdout` is `None`; without the second, one
Chinese character or one replacement character raises on the way out.

A hook is an **addition**, never a substitute. Two checks the skill runs on every build, with no
hook and no key field:

- **No business source in the shipped tree.** Compiling exists to not ship source. A package that
  ships it still installs and still runs, so nothing reveals the leak — the product's commercial
  premise is simply gone. The packages to look for are `python_backend.include_packages`, which
  the key already declares.
- **An installer really landed at `installer_glob`.** "The installer step exited 0" and "there is
  an installer" are different facts: a packer can fail its own cleanup, a repo hook can run half
  way. Which is why a key with an installer step must declare where the installer lands.

### What is genuinely optional

`fix_executor`, `editable_paths`, `protection_source`, `post_fix_gate`, `derive`, `event_sink` are
the self-heal and observability equipment. These are optional because each one only exists once
the product has grown the thing it guards — a derived artifact to regenerate, a test suite to
re-run after an automated fix, a log system to feed. A product with none of them still ships a
correct package; the engine skips what the key does not declare, and says so rather than
pretending it ran.

### `diagnose_rules` — this product's own log patterns

Patterns only this product's build produces, matched **before** the skill's general table. A rule's `fingerprint` prefix decides what the engine does with it: `transient:`
means there is no code to fix and the stage is simply re-run. Get that prefix wrong and a network
blip is dispatched to a code fix, or a real defect is retried until the budget runs out.

## Prove it without building

Check the key against the repo first. It is seconds, and it catches the class of mistake whose
alternative is finding out forty minutes into a compile:

```bash
uv run --with 'pydantic>=2' python scripts/verify_key.py --adapter <key> --repo-root <repo>
```

It checks only what a machine can decide: every path the key names exists, the self-check runs an
executable the key actually builds, no two compile targets write the same filename, no
`nofollow_imports` pattern blocks a module the self-check needs, and — the expensive one — the
key's `--adapter` arguments point at *this* key. Give a key a stage that reads a different key and
the build runs from that one while every step reports green.

Then assemble and read the script:

```bash
uv run --with 'pydantic>=2' python scripts/release_script_assembler.py assemble \
  --adapter <key> --repo-root <repo> --output /tmp/release.ps1 --context-output /tmp/ctx.json
uv run --with 'pydantic>=2' python scripts/release_script_assembler.py check \
  --script /tmp/release.ps1 --context /tmp/ctx.json
```

Read the generated script. Every step it prints is a step the key asked for, the compile carries
every flag you declared and nothing else, and no step refers to a path the repo does not have.

With a build machine reachable, also check that the generated PowerShell parses on it —
`tests/check-generated-powershell.sh <host> /tmp/release.ps1`. A syntax error caught here costs
seconds; caught on the build machine it costs the whole compile before it.

Then ship it once, and read what the build machine says. A key is proven by a package that
installs, not by a script that assembles.
