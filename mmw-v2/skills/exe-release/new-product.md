# Bring a product into the release system

Two ways in, and they meet at the same place — a key, written once the repo can support it:

- The product has never been packaged. Work through everything below.
- The product ships today through its own packaging scripts. Read "Coming from existing packaging scripts" at the end; most of what follows already exists in that repo.

Then write the key: [key.md](key.md).

## The product shape this skill packages

An Electron shell plus a Python backend compiled to a Windows executable, installed by an NSIS installer, built on a Windows machine over SSH. That is the shape. A product outside it — a different OS, no compiled backend, a different frontend runtime — is not something to bend a key into; it is a capability the skill does not have yet.

## What the repo must already have

Each item is work in the product repo, and the agent adding the product writes it. **A key written before these exist fails at minute forty of a compile, not at minute zero.**

| The repo must have | Missing shows up as |
| --- | --- |
| A backend entry module per compiled executable | nothing to compile |
| Runtime dependencies resolvable by one command | the compile packages the dev environment, not the shipped one |
| A self-check module the **compiled exe** can run | a green build that crashes on the customer's machine |
| An `electron-builder.yml` that carries the backend | a package that installs and then does nothing |
| A committed frontend lockfile | this package's dependencies are not the ones the repo records |
| An `.ico` per window the product shows | a default icon on a paid product |

Two facts about the build machine — which machine, and which folder on it — go in `remote-build.json` next to the key. [driving.md](driving.md) covers it.

### The self-check module

The one that gets skipped, and the only thing standing between a missing dynamic dependency and a customer finding it. It is a module that imports everything the app needs before it can serve its first request, and returns:

```python
SMOKE_IMPORTS = (
    "fastapi", "uvicorn",
    "<pkg>.app",
    # 函数体里 lazy import 的原生依赖：编译器静态追踪追不到，
    # 不在这里点名，客户跑到那个功能才崩。
    "PIL.Image",
)
```

The compiled exe must accept an argument that runs it — the existing products use `<exe> --run-module <pkg>._build_smoke`, handled in the backend's `__main__`. Whatever the product's argument is, the key declares it, and the build runs it right after the compile.

List the same modules in the key's `python_backend.smoke.modules`.

### The chain that carries the backend into the package

This is the one that produces a package that installs cleanly and then does nothing. Three files have to agree, and nothing checks them for you until the app fails to start:

| Where | What it says | Existing convention |
| --- | --- | --- |
| the key | where the compiler writes the exe | `python_backend.output_dir: ${DESKTOP_DIR}/python-runtime/backend` |
| `electron-builder.yml` | copy that tree into the installed app | `extraResources: [{from: "python-runtime/", to: "python-runtime/"}]` |
| the Electron main process | where to spawn it at run time | `{process.resourcesPath}/python-runtime/backend/<exe>` |

Give `extraResources` a filter that drops the business packages, `__pycache__`, and tests. The compiled exe already contains that code, and a stray copy of the sources beside it is the leak the whole compile exists to prevent.

### The installer name has to match the key

`win.artifactName` in `electron-builder.yml` decides the installer's filename; the key's `installer_glob` is where the build looks for it afterwards and where the engine collects it from. Disagree, and the build reports success while nothing is delivered.

A product whose installer needs semantics electron-builder's generic NSIS cannot express — carrying the VC++ runtime, stamping an app id, keeping user data on uninstall — writes its own `nsis.include` script, or takes over the whole step with `"installer": "repo_hook"`.

## Coming from existing packaging scripts

A product that ships today through its own Python is the same job read backwards. Open each script and sort it with the one question from [key.md](key.md):

- **Constants — lists of packages, paths, flags, versions, names.** These are the key. Copy the values across verbatim. Do not re-decide any of them: a value in there is usually a fix for something that once broke, and the commit that explains it is long gone.
- **Functions that build a command or copy a tree.** These are the skill. If the skill already does it, delete the copy. If it does not, add the capability there — not a second copy here.
- **What is left.** Usually one or two things: fetching a runtime, assembling a delivery format the app invented. That stays, and it becomes a `build_hooks` entry.

Prove the move before deleting anything: generate the command the key produces, generate the command the old script produces, and compare them. Flag order carries no meaning to the compiler — compare the set of flags and check the entrypoint is last. That comparison costs seconds and covers the part where a silent difference is most expensive.

Keep the old path working until a package built the new way installs. Then delete the old one: two ways to build the same product is the state where the next person edits the one that no longer runs.
