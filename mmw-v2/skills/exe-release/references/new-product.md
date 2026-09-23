# Bring a product into the release system

Two ways in, and they meet at the same place — a release manifest, written once the repository can support it:

- The product has never been packaged. Work through everything below.
- The product ships today through its own packaging scripts. Read "Coming from existing packaging scripts" at the end; most of what follows already exists in that repository.

Then write the release manifest: [key.md](key.md).

## The product shape this skill packages

An Electron shell plus a Python backend compiled to a Windows executable, installed by an NSIS installer, built on a Windows machine over SSH. That is the shape. A product outside it — a different OS, no compiled backend, a different frontend runtime — is not something to bend a release manifest into; it is a capability the skill does not have yet.

## What the repository must already have

Each item is work in the product repository, and the agent adding the product writes it. **A release manifest written before these exist fails at minute forty of a compile, not at minute zero.**

| The repository must have | Missing shows up as |
| --- | --- |
| A backend entry module per compiled executable | nothing to compile |
| Runtime dependencies resolvable by one command | the compile packages the dev environment, not the shipped one |
| A self-check module the **compiled exe** can run | a green build that crashes on the customer's machine |
| An `electron-builder.yml` that carries the backend | a package that installs and then does nothing |
| A committed frontend lockfile | this package's dependencies are not the ones the repository records |
| An `.ico` per window the product shows | a default icon on a paid product |

### The self-check module

The only thing standing between a missing dynamic dependency and a customer finding it. It is a module that imports everything the app needs before it can serve its first request, and returns:

```python
SMOKE_IMPORTS = (
    "fastapi", "uvicorn",
    "<pkg>.app",
    # 函数体里 lazy import 的原生依赖：编译器静态追踪追不到，
    # 不在这里点名，客户跑到那个功能才崩。
    "PIL.Image",
)
```

The compiled exe must accept an argument that runs it — the existing products use `<exe> --run-module <pkg>._build_smoke`, handled in the backend's `__main__`. Whatever the product's argument is, the release manifest declares it, and the build runs it right after the compile.

List the same modules in the release manifest's `python_backend.smoke.modules`.

### The chain that carries the backend into the package

This is the one that produces a package that installs cleanly and then does nothing. Three files have to agree, and nothing checks them for you until the app fails to start:

| Where | What it says | Existing convention |
| --- | --- | --- |
| the release manifest | where the compiler writes the exe | `python_backend.output_dir: ${DESKTOP_DIR}/python-runtime/backend` |
| `electron-builder.yml` | copy that tree into the installed app | `extraResources: [{from: "python-runtime/", to: "python-runtime/"}]` |
| the Electron main process | where to spawn it at run time | `{process.resourcesPath}/python-runtime/backend/<exe>` |

Give `extraResources` a filter that drops the business packages, `__pycache__`, and tests. The compiled exe already contains that code, and a stray copy of the sources beside it is the leak the whole compile exists to prevent.

### The installer name has to match the release manifest

`win.artifactName` in `electron-builder.yml` decides the installer's filename; the release manifest's `installer_glob` is where the build looks for it afterwards and where the release engine collects it from. Disagree, and the build reports success while nothing is delivered.

A product whose installer needs semantics electron-builder's generic NSIS cannot express — carrying the VC++ runtime, stamping an app id, keeping user data on uninstall — writes its own `nsis.include` script, or takes over the whole step with `"installer": "repo_hook"`.

## Remote build machine

A product that builds on another machine needs two facts: which machine, and which folder on it. The release engine takes them from `RELEASE_REMOTE_HOST` and `RELEASE_REMOTE_ROOT`, and when either is empty it falls back to `remote-build.json` sitting next to that product's `.release-adapter.json`:

```json
{
  "host": "<build machine>",
  "root": "D:/<a folder on it>",
  "delivery_root": "D:/<where packages are kept>",
  "cache_root": "D:/<where toolchain caches live>",
  "build_env": {"UV_INDEX_URL": "<a mirror that is reachable from there>"}
}
```

Everything after `root` is optional, and each says something only that machine knows.

`delivery_root` is where finished installers are gathered; without it the release engine uses `<root>-delivered`. Set it when that machine already keeps packages somewhere, so they do not land in a second place.

`cache_root` is where uv, Nuitka, zig, ccache, pnpm and Electron keep their caches; without it the release engine uses `<root>-cache`. Left to themselves those six write under `%LOCALAPPDATA%` on the system drive, which fills until a disk check stops the release. Point several products at one folder and they share the downloads; the caches are content-addressed, so a second copy buys nothing. It has to be a folder the build survives, not one inside the build directory: a successful build deletes that directory, and a cache that dies each round is not a cache.

`build_env` is applied before anything else runs — mirrors that are reachable from that machine, where ccache is installed. Anything named here wins over what the release engine would have chosen, including the cache directories.

Missing in both places is a `PAUSED:needs-context` you can often close yourself: the release engine's log names the variable. Write the file so the next run does not stop here again. The environment variables win over the file — that is how a one-off switch to another machine is done.

## Coming from existing packaging scripts

A product that ships today through its own Python is the same job read backwards. Open each script and sort it with the one question from [key.md](key.md):

- **Constants — lists of packages, paths, flags, versions, names.** These are the release manifest. Copy the values across verbatim. Do not re-decide any of them: a value in there is usually a fix for something that once broke, and the commit that explains it is long gone.
- **Functions that build a command or copy a tree.** These are the skill. If the skill already does it, delete the copy. If it does not, add the capability there — not a second copy here.
- **What is left.** Usually one or two things: fetching a runtime, assembling a delivery format the app invented. That stays, and it becomes a `build_hooks` entry.

Prove the move before deleting anything: generate the command the release manifest produces, generate the command the old script produces, and compare them. Flag order carries no meaning to the compiler — compare the set of flags and check the entrypoint is last. That comparison costs seconds and covers the part where a silent difference is most expensive.

Keep the old path working until a package built the new way installs. Then delete the old one: two ways to build the same product is the state where the next person edits the one that no longer runs.
