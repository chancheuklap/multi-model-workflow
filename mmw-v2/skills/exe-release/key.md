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

## The product shape this skill packages

An Electron shell plus a Python backend compiled to a Windows executable, installed by an NSIS
installer, built on a Windows machine over SSH. That is the shape. A product outside it — a
different OS, no compiled backend, a different frontend runtime — is not something to bend a key
into; it is a capability the skill does not have yet.

## Step 1 — what the repo must already have

Each item below is work in the product repo, and the agent adding the product writes it. A key
written before these exist fails at minute forty of a compile, not at minute zero.

| The repo must have | Missing shows up as |
| --- | --- |
| A backend entry module per compiled executable | nothing to compile |
| Runtime dependencies resolvable by one command | the compile packages the dev environment, not the shipped one |
| A self-check module the **compiled exe** can run | a green build that crashes on the customer's machine |
| An `electron-builder.yml` that carries the backend | a package that installs and then does nothing |
| A committed frontend lockfile | this package's dependencies are not the ones the repo records |
| An `.ico` per window the product shows | a default icon on a paid product |

Two facts about the build machine — which machine, and which folder on it — go in
`remote-build.json` next to the key. [driving.md](driving.md) covers it.

### The self-check module

The one that gets skipped, and the only thing standing between a missing dynamic dependency and
a customer finding it. It is a module that imports everything the app needs before it can serve
its first request, and returns:

```python
SMOKE_IMPORTS = (
    "fastapi", "uvicorn",
    "<pkg>.app",
    # 函数体里 lazy import 的原生依赖：编译器静态追踪追不到，
    # 不在这里点名，客户跑到那个功能才崩。
    "PIL.Image",
)
```

The compiled exe must accept an argument that runs it — the existing products use
`<exe> --run-module <pkg>._build_smoke`, handled in the backend's `__main__`. Whatever the
product's argument is, the key declares it, and the build runs it right after the compile.

List the same modules in `python_backend.smoke.modules`. That list is checked against
`nofollow_imports` **before** the compile starts, because finding out afterwards costs tens of
minutes.

### The chain that carries the backend into the package

This is the one that produces a package that installs cleanly and then does nothing. Three files
have to agree, and nothing checks them for you until the app fails to start:

| Where | What it says | Existing convention |
| --- | --- | --- |
| the key | where the compiler writes the exe | `python_backend.output_dir: ${DESKTOP_DIR}/python-runtime/backend` |
| `electron-builder.yml` | copy that tree into the installed app | `extraResources: [{from: "python-runtime/", to: "python-runtime/"}]` |
| the Electron main process | where to spawn it at run time | `{process.resourcesPath}/python-runtime/backend/<exe>` |

Give `extraResources` a filter that drops the business packages, `__pycache__`, and tests — the
compiled exe already contains that code, and a stray copy of the sources beside it is the leak
the whole compile exists to prevent. The skill scans the built tree for exactly this and stops
the build, but the filter is where it should never have happened.

### The installer name has to match the key

`win.artifactName` in `electron-builder.yml` decides the installer's filename; the key's
`installer_glob` is where the build looks for it afterwards and where the engine collects it
from. Disagree, and the build reports success while nothing is delivered.

A product whose installer needs semantics electron-builder's generic NSIS cannot express —
carrying the VC++ runtime, stamping an app id, keeping user data on uninstall — writes its own
`nsis.include` script, or takes over the whole step with `"installer": "repo_hook"`.

## Step 2 — write the key

```jsonc
{
  "schema_version": "2",
  "product": "<name>",                 // one word, used in fingerprints and delivery paths

  "toolchain": [],                     // extra tools only — see below

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

**`toolchain` is extras only.** Step 1 of the build checks every command the generated script
actually invokes — the compile runner, the package manager, the build-machine setup script — all
derived from what this key already says. List a tool here only when the product needs one beyond
those. Restating the derived ones is how a key ends up demanding a tool the build does not use,
and turning a working build machine away at step 1.

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

That is the line: **a check that every product needs is the skill's job and is never optional. A
check that only exists because of how one repo is built is the product's, and is.** When you find
yourself about to require a new field, ask which side of that line it falls on. If every product
would have to write the same thing, the skill should be writing it instead.

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

Core the key against the repo first. It is seconds, and it catches the class of mistake whose
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
