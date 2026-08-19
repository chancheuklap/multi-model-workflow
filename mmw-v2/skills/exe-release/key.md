# Write a key

A product ships by declaring one key: `<product>.release-adapter.json`, one file, JSON only.

**Adding a product means writing a key. It does not mean writing Python.** When something cannot
be said in the key, the answer is a new key field or a new capability in the skill — never a
script in the product repo. A script there is a copy of packaging knowledge that the next product
will have to write again.

The engine validates every key against `scripts/release_contracts.py`. That file is the authority
on field names and shapes; this file is why each part exists.

## What belongs where

Ask one question about any piece of the build:

> **Move to a different app — does this have to be rewritten?**

| Answer | Goes | Shape |
| --- | --- | --- |
| No, only the values differ | **the key** | JSON |
| No, it is the same action | **the skill** | code, written once |
| Yes, it is this app's own business | **the product repo** | code, and keep it thin |

Two things are genuinely the product's own and stay in its repo: fetching an embedded runtime,
and a delivery format the app invented (a self-update feed, a hand-written NSIS installer with
its own install semantics). Everything else about producing a Windows package is the skill's.

## Shape

```jsonc
{
  "schema_version": "2",
  "product": "duck",

  "toolchain": ["python", "pnpm", "node", "uv"],

  "build_target": {
    "desktop_dir": "desktop",          // the Electron app directory
    "entry_module": "local_agent",
    "installer_brand": "…",
    "installer_glob": "…/*-setup.exe", // where the finished installer lands
    "asset_roots": ["src/…/assets/**"] // which paths mean "this product changed"
  },

  "python_backend": { /* see below */ },
  "electron": { /* see below */ },

  "build_machine": {"setup": [...], "teardown": [...]},
  "stages": [ /* verify_key → assemble → build */ ],
  "build_hooks": { /* see below */ },
  "diagnose": ["…", "${RELEASE_PLUGIN_DIR}/diagnose_core.py", "--adapter", "…"],
  "diagnose_branches": [ /* this repo's own checks */ ],
  "diagnose_rules": [ /* log patterns only this product produces */ ],
  "fix_executor": ["…", "${RELEASE_PLUGIN_DIR}/fix_dispatch.py"],
  "protection_source": "…/release_protection.json",
  "editable_paths": [ /* what a self-heal may touch */ ]
}
```

`${RELEASE_PLUGIN_DIR}` expands to the skill's own `scripts/` directory. Use it for anything the
skill provides — where the skill is installed is the host's business, not the key's.

Paths in the key are repository-relative POSIX paths. Two templates are available:
`${DESKTOP_DIR}` and `${BUILD_ROOT}`. Absolute paths are refused: the key is written on one
machine and executed on another.

## `python_backend` — compiling the backend

One Nuitka invocation per entry in `targets`. The skill renders the command; the key supplies
every value in it.

```jsonc
"python_backend": {
  "runner": ["uv", "run", "--extra", "build", "python"],  // up to `python`
  "output_dir": "${DESKTOP_DIR}/python-runtime/backend",
  "output_mode": "onefile",
  "jobs": {"default": 10, "env": "AGENTFLOW_NUITKA_JOBS"},
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
  "smoke": {"exe": "….exe", "run_module": "…._build_smoke", "modules": [...]}
}
```

Each of these fields exists because a build failed without it:

- **`include_package_data` is separate from `include_packages`.** The first brings code, the
  second brings the data files inside it. Miss it and the app raises FileNotFound on a customer
  machine, not on the build machine.
- **`include_modules` for anything imported inside a function body.** Nuitka traces imports
  statically; a C extension imported lazily is invisible to it and simply will not be in the
  package. The customer finds out when they reach that feature.
- **`smoke.modules` is also the guard on `nofollow_imports`.** A nofollow pattern can block a
  module the built exe needs. The skill checks this at assemble time, because finding out after
  the compile costs tens of minutes.
- **`console: false` for a GUI app**, or every customer gets a black console window.
- **`env` values may use `${REPO_ROOT}`.** The build machine's repository path changes every
  round (the directory is named after the commit), so a value like `CCACHE_BASEDIR` can only be
  computed there. Without it ccache never hits and every build compiles from scratch.
- **`isolate_dirs` moves directories out of the way during the compile.** When the Electron app's
  `node_modules` sits inside the Python package scan path, Nuitka scans it: the compile time
  explodes and front-end files can end up in the package. They are moved back afterwards, and a
  failed restore stops the build — an Electron build against a missing `node_modules` fails in a
  way nobody can trace back to here.

Native extensions that need a DLL Nuitka does not carry go in `build_target.native_ext_dll`:

```jsonc
{"reason": "…", "dll_names": ["python3.dll"], "dll_source": "compile_interpreter",
 "dest": "pyd_package_dir", "pyd_package": "uharfbuzz"}
```

`dest` matters more than it looks. Windows loads a `.pyd` looking for its dependencies **only in
the `.pyd`'s own directory**, so a DLL dropped at the dist root is not found. `dll_source`
decides where the build machine looks: `compile_interpreter` (an abi3 forwarder like
`python3.dll`, which must match the interpreter Nuitka ran under), `system32` (the MSVC C++
runtime), or `repo`.

## `electron` — the shell and the installer

```jsonc
"electron": {
  "dist_dir": "dist",
  "unpacked_dir": "dist/win-unpacked",
  "compression": "maximum",
  "compression_env": "MMW_ELECTRON_BUILDER_COMPRESSION",
  "installer": "electron_builder"      // or "repo_hook"
}
```

NSIS comes with electron-builder, so the build machine does not need a standalone `makensis`.
Requiring one more tool would turn a working build machine away at step 1.

`"installer": "repo_hook"` is for a product whose delivery format is its own — a self-update feed,
or a hand-written NSIS whose install semantics (carrying the VC++ runtime, stamping an AUMID,
keeping user data on uninstall) electron-builder's generic installer cannot reproduce. That key
must also declare `build_hooks.installer`. Leave a product on `electron_builder` unless it truly
has its own format.

Omit `electron` entirely for a product with no Electron shell.

## `build_hooks` — where the product gets called back

Hooks hang on phases, not on step numbers: which steps exist depends on what the key declares,
so the numbers move; the phases do not.

| Phase | Hook | What the product does here |
| --- | --- | --- |
| `runtime_ready` | `runtime_prepare` | fetch the embedded runtime, ffmpeg, media assets |
| `runtime_ready` | `asset_parity`, `credential_proof` | check assets, emit proofs |
| `backend_ready` | `backend_verify` | the compiled exe just landed — prove it starts |
| `artifact_ready` | `artifact_scan` | scan the packed output |
| `installer_ready` | `installer` | only with `"installer": "repo_hook"` |
| `release_ready` | `package_integrity` | the installer exists — verify it |

Every hook is optional except `artifact_scan` and `package_integrity`. Declaring one with an
empty argv is refused: that reads as configured but does nothing.

## `diagnose_*` — turning a failure into something actionable

The skill owns the general translation table (`scripts/diagnose_core.py`), because most of its
patterns match text the engine and the templates print themselves.

The key adds the two parts that are the product's:

- **`diagnose_branches`** — this repo's own checks, each printing a findings envelope on stdout.
  `${CORE_EXE}` in a branch's argv is filled from `diagnose_core_exe_glob`; a branch that needs
  an artifact that does not exist yet is skipped rather than run against nothing.
- **`diagnose_rules`** — log patterns only this product produces. They are matched **before** the
  general table.

A rule's `fingerprint` prefix decides what the engine does with it. `transient:` means there is no
code to fix and the stage is simply re-run. Get that prefix wrong and a network blip is dispatched
to a code fix, or a real defect is retried until the budget runs out.

## Before you claim a key works

```bash
uv run --with 'pydantic>=2' python scripts/release_script_assembler.py assemble \
  --adapter <key> --repo-root <repo> --output /tmp/release.ps1 --context-output /tmp/ctx.json
uv run --with 'pydantic>=2' python scripts/release_script_assembler.py check \
  --script /tmp/release.ps1 --context /tmp/ctx.json
```

Read the generated script. The compile step should carry every flag you declared and nothing else.

With a build machine reachable, also check that the generated PowerShell parses on it —
`tests/check-generated-powershell.sh <host> /tmp/release.ps1`. A syntax error caught here costs
seconds; caught on the build machine it costs the whole compile before it.
