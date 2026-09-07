# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Lint a screen contract against the handoff skeleton and, when given, openapi.json.

Usage: uv run python lint_contract.py --tools <drive-target scripts> <screen-contract.yaml> <skeleton.json> [<openapi.json>]
Exit 0 with no errors; 1 with errors listed one per line; warnings never fail.

A `uv run python` invocation (the form a ticket CHECK writes) does not read the
metadata block above; `main` then re-execs through `uv run --script` so PyYAML
comes from that block. `uv run --script lint_contract.py` skips the re-exec.

`--tools` is the `scripts/` directory of the drive-target skill. Two things
come from that driver, and this file holds no copy of either: the `.mmw/target.json`
check (the function `target --validate` runs), and matching (`volatile_triggers` /
`count_volatile_hits`). Target kinds come from the same driver (`KINDS`).
All are loaded in-process through `extract_skeleton.py`'s `load_driver()`.
Rules are the tables in ../references/contract-format.md.

Printed on every run, before the findings: each `retired_ids` entry with its note,
and each `volatile_values` entry with its reason — the two kinds of exclusion the
judges honour, kept in sight so they are never a silent allowance.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

_BOOTSTRAP = "MMW_LINT_CONTRACT_BOOTSTRAPPED"
try:
    import yaml
except ImportError:
    yaml = None


def _ensure_yaml() -> None:
    """Re-exec through `uv run --script` when this process has no PyYAML.

    Called from `main` only, so importing the module in a test without the
    dependency fails the import of `yaml` and does not replace the test process.
    """
    if yaml is not None:
        return
    if os.environ.get(_BOOTSTRAP) == "1":
        raise SystemExit(
            "lint_contract.py is missing pyyaml after uv run --script; "
            "install it with the script's metadata"
        )
    env = dict(os.environ)
    env[_BOOTSTRAP] = "1"
    os.execvpe("uv", ["uv", "run", "--script", str(Path(__file__).resolve()),
                      *sys.argv[1:]], env)

GAPS = {"aligned", "design-only", "backend-only"}
ID = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")
MOUNT = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VIEWPORT = re.compile(r"^(\d+)x(\d+)$")
IMPL_PNG = re.compile(r"^(.+)-(\d+x\d+)-impl\.png$")
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
BREAKPOINT = re.compile(r"@media[^{]*\((?:max|min)-width:\s*(\d+)px\)")

ROW_KEYS = {
    "id", "component", "trigger", "precondition", "scenes", "calls",
    "shows", "next", "on_failure", "source", "gap",
}
SCENE_KEYS = {"page"}
PAGE_KEYS = {"mount", "component", "route"}
TOP_KEYS = {
    "effort", "baselines", "target", "viewports", "pages", "scenes", "rows",
    "retired_ids", "volatile_values", "readme_dispositions",
    "backend_without_ui", "proposed_operations",
}

# The directories `--tools` named. The driver of the drive-target skill is found
# there and nowhere else; `target_kinds()`, `target_file_problem()`, and matching
# all ask it, through `extract_skeleton.py`'s `load_driver()`.
TOOLS: list[Path] = []

_SD = None


def extract_skeleton_mod():
    """`extract_skeleton.py` from `--tools`; Python's import cache holds it."""
    for directory in TOOLS:
        if (directory / "extract_skeleton.py").is_file():
            if str(directory) not in sys.path:
                sys.path.insert(0, str(directory))
            import extract_skeleton
            return extract_skeleton
    raise SystemExit("no extract_skeleton.py in any --tools directory; pass --tools <the "
                     "drive-target skill's scripts directory>")


def screen_driver_mod():
    """The drive-target driver from `--tools`, loaded the same way
    `extract_skeleton.py` loads it. Cached after the first load.
    Matching (`volatile_triggers` / `count_volatile_hits`) and the
    target kinds / `.mmw/target.json` check all come from this module."""
    global _SD
    if _SD is not None:
        return _SD
    _SD = extract_skeleton_mod().load_driver()
    return _SD


def page_stem(page: str) -> str:
    """The design page without its `.dc.html` suffix, as `extract_skeleton.py`
    strips it: the two must agree or the lint looks for target files under a name
    nothing writes."""
    return extract_skeleton_mod().page_stem(page)


def target_hashes(path: Path) -> dict[str, str]:
    """`{"scenes.json": sha, "page": sha}` from a target file's header, read by the
    same writer that put them there."""
    return extract_skeleton_mod().read_target_hashes(path)


def target_kinds() -> set[str]:
    return set(screen_driver_mod().KINDS)


def target_file_problem(repo: Path, kind: str) -> tuple[str, str] | None:
    """`("error", line)` or `("warning", line)` about the repository's `.mmw/target.json`,
    from the driver's own validation; `None` when the file is complete.

    The file is missing until the contract ticket lands it, so that case is a warning
    and names `screen_driver.py target --check`. A file that is there and fails
    `--validate` is an error.
    """
    if not (repo / ".mmw" / "target.json").exists():
        return ("warning", "no .mmw/target.json yet; the contract ticket lands it — run "
                           "`screen_driver.py target --check` (the drive-target skill) there")
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        code = screen_driver_mod().target_main(
            ["--validate", "--repo", str(repo), "--kind", kind])
    if code == 0:
        return None
    text = (buf_out.getvalue() or buf_err.getvalue()).strip()
    return ("error", text or f"target --validate exited {code}")


# The shapes a `source` may take. A story is legal for the audit trail and warned on:
# no worker ever reads a story, so a behaviour decided only there reaches nobody.
SOURCE_SHAPES = (
    ("story", re.compile(r"^#\d+ story \d+")),
    ("spec-section", re.compile(r"^#\d+ (Implementation Decisions|Testing Decisions)\b")),
    ("ticket", re.compile(r"^#\d+(\s|$)")),
    ("adr", re.compile(r"^ADR-\d{4}\b")),
    ("doc", re.compile(r"^docs/")),
    ("readme", re.compile(r"^README\b")),
    ("code", re.compile(r"^code:")),
)


def source_shape(src: str) -> str:
    for shape, rx in SOURCE_SHAPES:
        if rx.match(src):
            return shape
    return "unknown"


def is_http_call(call) -> bool:
    """A call whose first token is an HTTP method. `ipc …`,
    `chrome.runtime.sendMessage …`, and `none` are not."""
    return str(call).partition(" ")[0].upper() in HTTP_METHODS


def repo_root(contract: Path) -> Path:
    for parent in [contract.resolve()] + list(contract.resolve().parents):
        if (parent / ".git").exists():
            return parent
    return Path.cwd()


def stylesheet_breakpoints(baseline: Path) -> set[int]:
    widths: set[int] = set()
    for css in sorted((baseline / "styles").glob("*.css")) if (baseline / "styles").exists() else []:
        widths.update(int(w) for w in BREAKPOINT.findall(css.read_text(encoding="utf-8")))
    return widths


def unknown_keys(value: dict, allowed: set[str]) -> list[str]:
    return sorted(k for k in value if k not in allowed)


def latest_story_out(contract_dir: Path) -> Path | None:
    """The newest `media/` directory under the contract dir that holds
    story-parity `--out` files (`<scene>-<WxH>-impl.png`), or None."""
    found: list[tuple[float, Path]] = []
    for media in contract_dir.rglob("media"):
        if not media.is_dir():
            continue
        if "targets" in media.relative_to(contract_dir).parts:
            continue
        pngs = [p for p in media.iterdir() if p.is_file() and IMPL_PNG.match(p.name)]
        if not pngs:
            continue
        found.append((max(p.stat().st_mtime for p in pngs), media))
    if not found:
        return None
    found.sort()
    return found[-1][1]


def lint_declarations(doc: dict, skeleton: dict, baseline: Path | None,
                      contract_dir: Path | None) -> tuple[list[str], list[str]]:
    """Target, viewports, pages, scenes, target trees, volatile_values, and
    story coverage. Every finding names the key it is about."""
    errors: list[str] = []
    warnings: list[str] = []
    rows = {str(r.get("id")): r for r in doc.get("rows") or [] if isinstance(r, dict)}
    for key in unknown_keys(doc, TOP_KEYS):
        errors.append(f"{key} is not a contract field")
    # -- target
    target = doc.get("target") or {}
    kind = str(target.get("kind") or "")
    kinds = target_kinds()
    if kind not in kinds:
        errors.append(f"target.kind {kind!r} is not one of {sorted(kinds)}")
    if "adapter" in target:
        errors.append("target.adapter is not read by anything; the drive-target skill picks "
                      "the adapter by target.kind — drop the key")
    if kind in kinds and contract_dir is not None:
        problem = target_file_problem(repo_root(Path(contract_dir)), kind)
        if problem is not None:
            (errors if problem[0] == "error" else warnings).append(problem[1])
    # -- viewports
    raw_vps = doc.get("viewports")
    widths: list[int] = []
    if not raw_vps:
        errors.append("viewports missing (copy them from the handoff package README)")
    else:
        for vp in (raw_vps if isinstance(raw_vps, list) else [raw_vps]):
            m = VIEWPORT.match(str(vp).strip())
            if not m:
                errors.append(f"viewports entry {vp!r} is not WIDTHxHEIGHT")
            else:
                widths.append(int(m.group(1)))
    if baseline is not None and widths:
        for w in widths:
            if w in stylesheet_breakpoints(baseline):
                errors.append(f"viewports: width {w} is a breakpoint of the handoff "
                              f"stylesheets; a render there compares two reflows")
    # -- pages
    pages = doc.get("pages") or {}
    scene_pages: dict[str, str] = skeleton.get("scene_pages") or {}
    if not scene_pages:
        scene_pages = {sc: r["page"] for r in skeleton.get("table") or [] for sc in r["scenes"]}
    handoff_pages = set(scene_pages.values())
    component_values = {str(r.get("component")) for r in rows.values() if r.get("component")}
    declared_mounts: dict[str, str] = {}
    component_pages: dict[str, str] = {}
    for page in sorted(handoff_pages):
        if page not in pages:
            errors.append(f"pages: no declaration for {page!r} (mount)")
    for page, decl in pages.items():
        decl = decl or {}
        if not isinstance(decl, dict):
            errors.append(f"pages: {page!r} must be a mapping")
            continue
        for key in unknown_keys(decl, PAGE_KEYS):
            errors.append(f"pages: {page!r} {key} is not a contract field")
        if page not in handoff_pages:
            errors.append(f"pages: {page!r} is not a page of scenes.json")
        mount = str(decl.get("mount") or "")
        if not MOUNT.match(mount):
            errors.append(f"pages: {page!r} mount {mount!r} must be a short lowercase id")
        elif mount in declared_mounts:
            errors.append(f"pages: mount {mount!r} declared by both {declared_mounts[mount]!r} "
                          f"and {page!r}")
        else:
            declared_mounts[mount] = page
        if decl.get("route") and not page.startswith("App · "):
            errors.append(f"pages: {page!r} is not an App page and must not have route")
        if page.startswith("Component · "):
            comp = str(decl.get("component") or "")
            if not comp:
                errors.append(f"pages: {page!r} names no `component` (a value of the rows' "
                              f"component column)")
            elif comp not in component_values:
                errors.append(f"pages: {page!r} component {comp!r} is no row's component")
            elif comp in component_pages:
                errors.append(f"pages: component {comp!r} claimed by both "
                              f"{component_pages[comp]!r} and {page!r}")
            else:
                component_pages[comp] = page
    for comp in sorted(component_values - set(component_pages)):
        errors.append(f"pages: rows' component {comp!r} belongs to no Component page")
    # -- scenes
    scenes = doc.get("scenes") or {}
    for name in sorted(scene_pages):
        if name not in scenes:
            errors.append(f"scenes: no declaration for {name!r}")
    for name, decl in scenes.items():
        decl = decl or {}
        if not isinstance(decl, dict):
            errors.append(f"scenes: {name!r} must be a mapping")
            continue
        for key in unknown_keys(decl, SCENE_KEYS):
            errors.append(f"scenes: {name!r} {key} is not a contract field")
        if name not in scene_pages:
            errors.append(f"scenes: {name!r} is not in scenes.json")
            continue
        page = str(decl.get("page") or "")
        if page != scene_pages[name]:
            errors.append(f"scenes: {name!r} page {page!r} but scenes.json has "
                          f"{scene_pages[name]!r}")
    # -- target trees
    aria_of: dict[str, Path] = {}
    if contract_dir is not None and baseline is not None and handoff_pages:
        targets = contract_dir / "targets"
        scenes_hash = (hashlib.sha256((baseline / "scenes.json").read_bytes()).hexdigest()
                       if (baseline / "scenes.json").exists() else "")
        for page in sorted(handoff_pages):
            stem = page_stem(page)
            aria_of[page] = targets / f"{stem}.aria"
            for suffix in (".aria", ".classes"):
                f = targets / f"{stem}{suffix}"
                if not f.exists():
                    errors.append(f"targets: {f.name} missing; run extract_skeleton.py "
                                  f"--targets {targets}")
                    continue
                hashes = target_hashes(f)
                page_file = baseline / page
                page_hash = (hashlib.sha256(page_file.read_bytes()).hexdigest()
                             if page_file.exists() else "")
                if hashes.get("scenes.json") != scenes_hash or hashes.get("page") != page_hash:
                    errors.append(f"targets: {f.name} is stale — its hashes no longer match "
                                  f"scenes.json or {page}; regenerate with extract_skeleton.py")
    # -- volatile_values
    def tree_of(page: str) -> list[str]:
        """The page's target tree, as lines. `aria_of` holds the pages the target
        directory declared; a page it does not name is looked for where
        `extract_skeleton.py --targets` would have written it."""
        aria = aria_of.get(page)
        if aria is None:
            aria = contract_dir / "targets" / f"{page_stem(page)}.aria"
        return aria.read_text(encoding="utf-8").splitlines() if aria.exists() else []

    for entry in doc.get("volatile_values") or []:
        if not isinstance(entry, dict):
            continue
        trigger = entry.get("trigger") or {}
        page = str(entry.get("page") or "")
        role, name = str(trigger.get("role") or ""), str(trigger.get("name") or "")
        if not page or not role or not name:
            warnings.append("volatile_values: an entry is missing page or trigger "
                            "(role and name); the judges cannot replace it")
            continue
        if contract_dir is None:
            continue
        hits = screen_driver_mod().count_volatile_hits(
            tree_of(page),
            screen_driver_mod().volatile_triggers({"volatile_values": [entry]}))
        if hits == 0:
            warnings.append(f"volatile_values: {role} {name!r} on {page} is not in the "
                            f"target tree")
        elif hits > 1:
            errors.append(f"volatile_values: {role} {name!r} on {page} matches {hits} "
                          f"nodes")
    # -- story coverage: the newest story-parity --out under the contract dir.
    # App pages are outside this warning: story-parity.py --pages takes only
    # non-App mounts, so an App-page miss can never be repaired.
    if contract_dir is not None:
        media = latest_story_out(contract_dir)
        if media is not None:
            seen = {m.group(1) for p in media.iterdir()
                    if p.is_file() and (m := IMPL_PNG.match(p.name))}
            by_page: dict[str, list[str]] = {}
            for sname, page in scene_pages.items():
                if page.startswith("App · "):
                    continue
                by_page.setdefault(page, []).append(sname)
            for page, names in sorted(by_page.items()):
                missing = [n for n in names if n not in seen]
                if missing:
                    warnings.append(
                        f"story coverage: {page} scenes {', '.join(missing)} are not "
                        f"in the latest story-parity --out inventory")
    return errors, warnings


def lint(doc: dict, skeleton: dict, openapi: dict | None) -> tuple[list[str], list[str]]:
    """The control axis: one row per behaviour, as ../references/contract-format.md says."""
    errors: list[str] = []
    warnings: list[str] = []
    rows = doc.get("rows") or []
    retired_entries = [e if isinstance(e, dict) else {"id": e} for e in doc.get("retired_ids") or []]
    retired = {str(e.get("id")) for e in retired_entries}
    retired_triggers = {(e["trigger"].get("role"), e["trigger"].get("name"))
                        for e in retired_entries if isinstance(e.get("trigger"), dict)}
    for e in retired_entries:
        t = e.get("trigger")
        if isinstance(t, dict) and not e.get("page"):
            pages_with = {r["page"] for r in skeleton["table"]
                          if (r["role"], r["name"]) == (t.get("role"), t.get("name"))}
            if len(pages_with) > 1:
                warnings.append(f"retired {e.get('id')}: trigger {t.get('role')} {t.get('name')!r} "
                                f"exists on {len(pages_with)} pages and the entry names no `page`; "
                                f"the judges would hide it everywhere")
    triggers: dict[tuple[str, str], set[str]] = {}
    for r in skeleton["table"]:
        triggers.setdefault((r["role"], r["name"]), set()).update(r["scenes"])
    ops = ({(m.upper(), p) for p, methods in openapi["paths"].items() for m in methods}
           if openapi else None)
    proposed = {tuple(str(o).split(" ", 1)) for o in doc.get("proposed_operations") or []}
    proposed = {(m.upper(), p) for m, p in proposed}

    def op_known(method: str, path: str) -> str:
        if ops is not None and (method.upper(), path) in ops:
            return "yes"
        if (method.upper(), path) in proposed:
            return "proposed"
        return "no"

    seen_ids: set[str] = set()
    seen_triggers: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        if not isinstance(row, dict):
            errors.append(f"{row!r}: row must be a mapping")
            continue
        rid = str(row.get("id", "<no id>"))
        for key in unknown_keys(row, ROW_KEYS):
            errors.append(f"{rid}: {key} is not a contract field")
        if not ID.match(rid):
            errors.append(f"{rid}: id must look like <component>.<behaviour>")
        if rid in seen_ids:
            errors.append(f"{rid}: duplicate id")
        seen_ids.add(rid)
        if rid in retired:
            errors.append(f"{rid}: id is in retired_ids and still has a row")
        t = row.get("trigger") or {}
        key = (t.get("role"), t.get("name"))
        if key not in triggers:
            errors.append(f"{rid}: trigger {key[0]} {key[1]!r} not in handoff skeleton")
        else:
            if not (row.get("scenes") or []):
                warnings.append(f"{rid}: scenes is [] — the handoff shows no scene for this precondition")
            for sc in row.get("scenes") or []:
                if sc not in triggers[key]:
                    errors.append(f"{rid}: scene {sc!r} does not show this trigger in the skeleton")
        seen_triggers.setdefault(key, []).append(row.get("precondition") or {})
        calls = row.get("calls") or []
        if not calls:
            errors.append(f"{rid}: calls is empty (use [none])")
        for call in calls:
            if not is_http_call(call):
                continue
            method, _, path = str(call).partition(" ")
            known = op_known(method, path)
            if known == "proposed":
                warnings.append(f"{rid}: call is a proposed operation, not in openapi yet: {call}")
            elif ops is None:
                warnings.append(f"{rid}: call unverified (no openapi.json): {call}")
            elif known == "no":
                errors.append(f"{rid}: call not in openapi: {call}")
        if calls != ["none"] and not (row.get("on_failure") or {}):
            errors.append(f"{rid}: on_failure missing for a row with calls")
        for shown, expr in (row.get("shows") or {}).items():
            if "@" not in str(expr):
                errors.append(f"{rid}: shows.{shown} names no field@operation: {expr!r}")
            if re.search(r"(?<![\w{])\d+(?![\w}])", str(expr)):
                errors.append(f"{rid}: shows.{shown} carries a literal number: {expr!r}")
        sources = row.get("source") or []
        if not sources:
            errors.append(f"{rid}: source is empty")
        elif row.get("gap") == "aligned" and all(
                "README" in str(s) or str(s).startswith("code:") for s in sources):
            errors.append(f"{rid}: aligned but every source is the README or code:")
        for s in sources:
            shape = source_shape(str(s))
            if shape == "story":
                warnings.append(f"{rid}: source {s!r} is a story; no worker reads a story — "
                                f"fold its conclusion into an Implementation Decisions "
                                f"subsection and cite that")
            elif shape == "unknown":
                warnings.append(f"{rid}: source {s!r} has no recognised shape (#n, "
                                f"#n Implementation Decisions k, ADR-nnnn, docs/…, README §, "
                                f"code:…)")
        gap = row.get("gap")
        if gap not in GAPS:
            errors.append(f"{rid}: gap {gap!r} not one of {sorted(GAPS)}")
        elif gap != "aligned":
            errors.append(f"{rid}: gap {gap} unresolved")

    for key, pres in seen_triggers.items():
        if len(pres) > 1 and len({json.dumps(p, sort_keys=True, ensure_ascii=False) for p in pres}) < len(pres):
            errors.append(f"trigger {key[0]} {key[1]!r}: rows share a precondition")
    controls = {(r["page"], r["role"], r["name"]) for r in skeleton["table"]}
    covered_pages = {page for page, role, name in controls if (role, name) in seen_triggers}
    untouched = sorted({r["page"] for r in skeleton["table"]} - covered_pages)
    for page, role, name in sorted(controls):
        if (role, name) in retired_triggers:
            continue
        if page in covered_pages and (role, name) not in seen_triggers:
            errors.append(f"skeleton control without a row: {page} / {role} {name!r}")
    for page in untouched:
        warnings.append(f"page has no rows yet: {page}")
    return errors, warnings


def retired_lines(doc: dict) -> list[str]:
    out = []
    for e in doc.get("retired_ids") or []:
        if isinstance(e, dict):
            out.append(f"RETIRED {e.get('id')}: {e.get('note') or '(no note)'}")
        else:
            out.append(f"RETIRED {e}: (no note)")
    return out


def volatile_lines(doc: dict) -> list[str]:
    out = []
    for e in doc.get("volatile_values") or []:
        if not isinstance(e, dict):
            out.append(f"VOLATILE {e}: (no reason)")
            continue
        trigger = e.get("trigger") or {}
        page = e.get("page") or "(no page)"
        role = trigger.get("role") or "?"
        name = trigger.get("name") or ""
        reason = e.get("reason") or "(no reason)"
        out.append(f'VOLATILE {page} {role} "{name}": {reason}')
    return out


def main(argv: list[str]) -> int:
    _ensure_yaml()
    rest: list[str] = []
    TOOLS[:] = []
    i = 1
    while i < len(argv):
        if argv[i] == "--tools" and i + 1 < len(argv):
            TOOLS.append(Path(argv[i + 1]).resolve())
            i += 2
        elif argv[i].startswith("--tools="):
            TOOLS.append(Path(argv[i][len("--tools="):]).resolve())
            i += 1
        else:
            rest.append(argv[i])
            i += 1
    argv = [argv[0], *rest]
    if len(argv) not in (3, 4) or not TOOLS:
        print(__doc__)
        return 2
    contract = Path(argv[1])
    doc = yaml.safe_load(contract.read_text(encoding="utf-8"))
    skeleton = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    openapi = json.loads(Path(argv[3]).read_text(encoding="utf-8")) if len(argv) == 4 else None
    look = (doc.get("baselines") or {}).get("look")
    baseline = (repo_root(contract) / look) if look else None
    if baseline is not None and not baseline.exists():
        baseline = None
    for line in retired_lines(doc):
        print(line)
    for line in volatile_lines(doc):
        print(line)
    errors, warnings = lint(doc, skeleton, openapi)
    e2, w2 = lint_declarations(doc, skeleton, baseline, contract.resolve().parent)
    errors += e2
    warnings += w2
    for w in warnings:
        print("WARN ", w)
    for e in errors:
        print("ERROR", e)
    print(f"{len(errors)} errors, {len(warnings)} warnings over {len(doc.get('rows') or [])} rows")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
