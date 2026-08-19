# Add a product

A product ships by declaring one key: `<product>.release-adapter.json`, one file, JSON only.

**Adding a product means writing a key. It does not mean writing Python.** When something cannot
be said in the key, the answer is a new key field or a new capability in the skill — never a
script in the product repo. A script there is a copy of packaging knowledge that the next product
will have to write again.

You are here for a product that has no key, or one whose key predates a capability it now needs.
Work the three steps in order: a key written before the repo can support it fails at minute forty
of a compile, not at minute zero.

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

## Step 1 — what the repo must already have

Check each one. A missing item is work in the product repo before the key is worth writing.

| The repo must have | Why the skill needs it | Missing shows up as |
| --- | --- | --- |
| A backend entry module the compiler can start from | one Nuitka run per `targets[]` entry | nothing to compile |
| Runtime dependencies resolvable by one command | that command becomes `python_backend.runner` | the compile imports the dev environment, not the shipped one |
| A self-check the **compiled exe** can run and exit 0 from | the only way a missing dynamic dependency is caught before a customer finds it | a green build that crashes on the customer's machine |
| An electron-builder config — app id, product name, icon | what the installer is called and looks like is the product's identity, not packaging knowledge | electron-builder refuses, or ships a nameless app |
| A committed lockfile for the frontend | dependencies install frozen: the lockfile is the only authority on what shipped | this package's dependencies do not match what the repo records |
| An `.ico` for the backend exe, if it shows a window | Windows needs that format | a default icon on a paid product |

Two facts about the build machine — which machine, and which folder on it — come from
`remote-build.json` next to the key, or from the environment. [driving.md](driving.md) covers it.

**The self-check is the one that gets skipped.** It is a module that imports what the app needs at
startup and returns. The compiled exe must accept an argument that runs it — the key declares
that argument, so the shape is the product's choice, but something must be there. A build without
it proves only that the compiler exited 0.

## Step 2 — write the key

```jsonc
{
  "schema_version": "2",
  "product": "<name>",                 // one word, used in fingerprints and delivery paths

  "toolchain": ["python", "pnpm", "node", "uv"],   // checked before anything expensive runs

  "build_target": {
    "desktop_dir": "<electron app dir>",   // omit for a product with no Electron shell
    "installer_brand": "…",
    "installer_glob": "…/*-setup.exe",     // where the finished installer lands
    "asset_roots": ["src/…/assets/**"]     // which paths mean "this product changed"
  },

  "python_backend": { /* below */ },
  "electron": { /* below */ },

  "stages": [ /* what the engine runs, in order, ending in the remote build */ ],
  "diagnose": ["…", "${RELEASE_PLUGIN_DIR}/diagnose_core.py", "--adapter", "<this file>"],
  "build_hooks": {}                        // add one only when the product has something to do
}
```

`${RELEASE_PLUGIN_DIR}` expands to the skill's own `scripts/` directory. Use it for anything the
skill provides — where the skill is installed is the host's business, not the key's.

Paths in the key are repository-relative POSIX paths, and two templates are available:
`${DESKTOP_DIR}` and `${BUILD_ROOT}`. Absolute paths are refused: the key is written on one
machine and executed on another.

**`stages` reads this key.** `assemble` points its `--adapter` at the key's own filename. Point it
at another key and the build runs from that one instead, while every step reports green.

### `python_backend` — compiling the backend

One Nuitka invocation per entry in `targets`. The skill renders the command; the key supplies
every value in it.

```jsonc
"python_backend": {
  "runner": ["uv", "run", "--extra", "<runtime extra>", "python"],  // up to `python`
  "output_dir": "${DESKTOP_DIR}/python-runtime/backend",
  "output_mode": "onefile",
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
  "smoke": {"exe": "….exe", "run_module": "…._build_smoke", "modules": [...]}
}
```

Each of these fields exists because a build failed without it:

- **`include_package_data` is separate from `include_packages`.** The first brings code, the
  second brings the data files inside it. Miss it and the app raises FileNotFound on a customer
  machine, not on the build machine.
- **`include_modules` for anything imported inside a function body.** The compiler traces imports
  statically; a C extension imported lazily is invisible to it and simply will not be in the
  package. The customer finds out when they reach that feature.
- **`smoke.modules` is also the guard on `nofollow_imports`.** A nofollow pattern can block a
  module the built exe needs. The skill checks this at assemble time, because finding out after
  the compile costs tens of minutes.
- **`console: false` for a GUI app**, or every customer gets a black console window.
- **`env` values may use `${REPO_ROOT}`.** The build machine's repository path changes every
  round (the directory is named after the commit), so a value like `CCACHE_BASEDIR` can only be
  computed there. Without it the compile cache never hits and every build starts from scratch.
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
`python3.dll`, which must match the interpreter the compiler ran under), `system32` (the MSVC C++
runtime), or `repo`.

### `electron` — the shell and the installer

```jsonc
"electron": {
  "package_manager": "pnpm",           // and its two commands, if yours differ
  "install_args": ["install", "--frozen-lockfile", "--prefer-offline"],
  "build_script": "build",             // the package.json script that builds the front end
  "dist_dir": "dist",
  "unpacked_dir": "dist/win-unpacked",
  "compression": "maximum",
  "compression_env": "MMW_ELECTRON_BUILDER_COMPRESSION",
  "installer": "electron_builder"      // or "repo_hook"
}
```

Every field has a default that fits the common case; `"electron": {}` is a complete declaration.
NSIS comes with electron-builder, so the build machine does not need a standalone `makensis` —
requiring one more tool would turn a working build machine away at step 1.

`"installer": "repo_hook"` is for a product whose delivery format is its own — a self-update feed,
or a hand-written installer whose semantics (carrying the VC++ runtime, stamping an app id,
keeping user data on uninstall) the generic installer cannot reproduce. That key must also declare
`build_hooks.installer`. Leave a product on `electron_builder` unless it truly has its own format.

Omit `electron` entirely for a product with no Electron shell.

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

**Every hook is optional, and a first key usually declares none.** Add one when the product has a
check of its own to run at that moment. Declaring a hook with an empty argv is refused: that reads
as configured but does nothing.

### The rest is optional too

`fix_executor`, `editable_paths`, `protection_source`, `post_fix_gate`, `derive`, `event_sink`
are the self-heal and observability equipment. A product that has none of it still ships; the
engine skips what the key does not declare. Add each one when the product grows the thing it
guards.

`diagnose_rules` are log patterns only this product produces, matched **before** the skill's
general table. A rule's `fingerprint` prefix decides what the engine does with it: `transient:`
means there is no code to fix and the stage is simply re-run. Get that prefix wrong and a network
blip is dispatched to a code fix, or a real defect is retried until the budget runs out.

## An existing product that already has packaging scripts

A product that ships today through its own Python is the same job read backwards. Open each
script and sort it with the one question:

- **Constants — lists of packages, paths, flags, versions, names.** These are the key. Copy the values
  across verbatim. Do not re-decide any of them: a value in there is usually a fix for something
  that once broke, and the commit that explains it is long gone.
- **Functions that build a command or copy a tree.** These are the skill. If the skill already
  does it, delete the copy. If it does not, add the capability there — not a second copy here.
- **What is left.** Usually one or two things: fetching a runtime, assembling a delivery format
  the app invented. That stays, and it becomes a `build_hooks` entry.

Prove the move before deleting anything: generate the command the key produces, generate the
command the old script produces, and compare them. Flag order carries no meaning to the
compiler — compare the set of flags and check the entrypoint is last. That comparison costs
seconds and covers the part where a silent difference is most expensive.

Keep the old path working until a package built the new way installs. Then delete the old one:
two ways to build the same product is the state where the next person edits the one that no
longer runs.

## Step 3 — prove it without building

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
