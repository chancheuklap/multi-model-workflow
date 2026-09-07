"""Lint a screen contract against the handoff skeleton and, when given, openapi.json.

Usage: uv run python lint_contract.py --tools <drive-target scripts> <screen-contract.yaml> <skeleton.json> [<openapi.json>]
       uv run python lint_contract.py --tools <drive-target scripts> --pin [--base <ref>] <screen-contract.yaml>
Exit 0 with no errors; 1 with errors listed one per line; warnings never fail.

`--pin` repairs the locators a contract defect leaves undrivable, and proves each write
before it keeps it: the repaired row must resolve to one node, and every other row must
resolve to the node it resolved to in the committed contract at `--base` (the ticket
branch's recorded base by default). It writes `after` only when one candidate is free and
`occurrence: 1` otherwise, never reading the product — so it cannot search for the value
that turns a criterion green. Anything else it refuses to a person by name. It needs the
contract and the target trees beside it, nothing more; the skeleton is not read.
`--tools` is the `scripts/` directory of the drive-target skill. Three things
come from that driver, and this file holds no copy of any: the target kinds
(its `ADAPTERS`), the `.mmw/target.json` check (the function `target
--validate` runs), and matching (`volatile_triggers` / `row_trigger` /
`count_volatile_hits` / `count_trigger_hits`).
All three are loaded in-process through `extract_skeleton.py`'s `load_driver()`.
Rules are the tables in ../references/contract-format.md: the control axis (rows), the
screen axis (`target`, `viewports`, `pages`, `scenes`), the mechanism table, and the
target trees under `<contract dir>/targets/`.

Printed on every run, before the findings: each `retired_ids` entry with its note,
and each `volatile_values` entry with its reason — the two kinds of exclusion the
judges honour, kept in sight so they are never a silent allowance.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import yaml

GAPS = {"aligned", "design-only", "backend-only"}
REACH = re.compile(r"^(seed|stub|dev):[a-z0-9][a-z0-9-]*$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")
MOUNT = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VIEWPORT = re.compile(r"^(\d+)x(\d+)$")
TICKET = re.compile(r"^#\d+$")
PROVEN = re.compile(r"^#\d+ AC\d+$")
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
    Matching (`volatile_triggers` / `row_trigger` / `count_volatile_hits` /
    `count_trigger_hits`) and the target kinds / `.mmw/target.json` check all
    come from this module."""
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
    return set(screen_driver_mod().ADAPTERS)


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


VIA = {"api", "storage"}
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
INPUT_ROLES = {"textbox", "combobox", "spinbutton", "searchbox"}
BREAKPOINT = re.compile(r"@media[^{]*\((?:max|min)-width:\s*(\d+)px\)")
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


def mechanisms_of(doc: dict) -> tuple[dict[str, dict], bool]:
    raw = doc.get("mechanisms") or {}
    if isinstance(raw, list):
        return {str(m): {} for m in raw}, True
    return {str(k): (v or {}) for k, v in raw.items()}, False


def scene_name_of(value) -> str:
    """The scene a `next` or `on_failure` value names: its first token, before any
    explanation in parentheses or a `|` alternative."""
    return re.split(r"[\s(|]", str(value or "").strip(), maxsplit=1)[0]


def open_lands(row: dict, scene: str, page: str, scene_pages: dict[str, str], decl: dict) -> bool:
    """Whether performing `row` last lands `scene`. Four ways it can: the row's `next`
    is the scene; its `next` is a scene on the same design page (the action lands the
    page, the `reach` decides which state); one of its `on_failure` values is the scene
    (a failure the scene's stub scripts); or the scene is an `App · ` whole-surface page
    that contains the block the action lands. A scene that lists the row among its
    visible controls and stays on screen after the action (a queue row selected while
    the task opens beside it) counts too."""
    nxt = scene_name_of(row.get("next"))
    if nxt == scene:
        return True
    if nxt in scene_pages and scene_pages[nxt] == page:
        return True
    for value in (row.get("on_failure") or {}).values():
        if scene_name_of(value) == scene:
            return True
    if page.startswith("App · "):
        return True
    if scene in (row.get("scenes") or []):
        return True
    return False


def after_advice(lines: list[str], trigger, scenes: set[str] | None,
                 row_id: str = "", page: str = "") -> str:
    """What to do about a trigger that reaches more than one node, opening with the
    class the driver's own reader assigned it.

    The class is never derived here. `TriggerConflict.kind` is the one place that turns a
    tree into a class, so the contract lint, the ticket lint and the merge rule all say
    the same word about the same row; what differs between them is only the sentence each
    writes for its own reader."""
    sd = screen_driver_mod()
    candidates = sd.trigger_after_candidates(lines, trigger, scenes)
    conflict = sd.TriggerConflict(row_id, page, 0, candidates)
    named = [c for c in candidates if c[1]]
    if conflict.kind == sd.PIN_AFTER:
        shown = " | ".join(f"{role} {name!r}" for role, name in named[:4])
        more = "" if len(named) <= 4 else f" (+{len(named) - 4} more)"
        return f"[{conflict.kind}] name the previous named node as after — candidates: {shown}{more}"
    if named:
        role, name = named[0]
        return (f"[{conflict.kind}] every match follows the same node ({role} {name!r}): they "
                f"sit in blocks the design repeats, no named node tells the blocks apart, "
                f"and after cannot reach further back than the previous named node")
    return (f"[{conflict.kind}] no named node precedes the matches, so after has nothing "
            f"to pin to")


def lint_screen_axis(doc: dict, skeleton: dict, baseline: Path | None,
                     contract_dir: Path | None) -> tuple[list[str], list[str]]:
    """The screen axis: target, viewports, pages, scenes, the mechanism table, the
    target trees, volatile_values, and a row trigger that is not unique on its
    scene. Every finding names the key it is about."""
    errors: list[str] = []
    warnings: list[str] = []
    rows = {str(r.get("id")): r for r in doc.get("rows") or []}
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
            errors.append(f"pages: no declaration for {page!r} (mount and route)")
    for page, decl in pages.items():
        decl = decl or {}
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
        if not decl.get("route"):
            errors.append(f"pages: {page!r} has no route")
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
    mechanisms, as_list = mechanisms_of(doc)
    for name, decl in scenes.items():
        decl = decl or {}
        if name not in scene_pages:
            errors.append(f"scenes: {name!r} is not in scenes.json")
            continue
        page = str(decl.get("page") or "")
        if page != scene_pages[name]:
            errors.append(f"scenes: {name!r} page {page!r} but scenes.json has "
                          f"{scene_pages[name]!r}")
        page_decl = pages.get(page) or {}
        mount = str(decl.get("mount") or page_decl.get("mount") or "")
        if not mount:
            errors.append(f"scenes: {name!r} has no mount, on the scene or its page")
        elif mount not in declared_mounts:
            errors.append(f"scenes: {name!r} mount {mount!r} is declared by no page")
        if not (decl.get("route") or page_decl.get("route")):
            errors.append(f"scenes: {name!r} has no route, on the scene or its page")
        for r in decl.get("reach") or []:
            if not REACH.match(str(r)):
                errors.append(f"scenes: {name!r} reach {r!r} is not seed:/stub:/dev: plus a name")
            elif str(r) not in mechanisms:
                errors.append(f"scenes: {name!r} reach {r!r} not in mechanisms")
        steps = decl.get("open") or []
        for i, step in enumerate(steps):
            rid = step if isinstance(step, str) else str((step or {}).get("row"))
            value = None if isinstance(step, str) else (step or {}).get("value")
            row = rows.get(rid)
            if row is None:
                errors.append(f"scenes: {name!r} open step {i + 1} names no row: {rid!r}")
                continue
            role = str((row.get("trigger") or {}).get("role"))
            if role in INPUT_ROLES and value in (None, ""):
                errors.append(f"scenes: {name!r} open step {i + 1} ({rid}) is a {role} and "
                              f"carries no value")
            if i == len(steps) - 1 and not open_lands(row, name, page, scene_pages, decl):
                errors.append(f"scenes: {name!r} open ends on {rid}, whose next is "
                              f"{row.get('next')!r} and whose on_failure names no "
                              f"{name!r}; the action does not land this scene")
        clock = decl.get("clock")
        if clock is not None and (not isinstance(clock, int) or clock < 0):
            errors.append(f"scenes: {name!r} clock {clock!r} is not a whole number of milliseconds")
    # -- mechanisms
    if as_list and mechanisms:
        errors.append("mechanisms is a list; each entry needs `via` and `built_by` "
                      "(mechanisms: {seed:x: {via: api, built_by: '#n'}})")
    for mname, m in mechanisms.items():
        if not REACH.match(mname):
            errors.append(f"mechanisms: {mname!r} is not seed:/stub:/dev: plus a name")
        if as_list:
            continue
        via = str(m.get("via") or "api")
        if via not in VIA:
            errors.append(f"mechanisms: {mname} via {via!r} is not api or storage")
        built_by = str(m.get("built_by") or "")
        if not TICKET.match(built_by):
            errors.append(f"mechanisms: {mname} built_by {built_by!r} is not a ticket number")
        if via == "storage" and not PROVEN.match(str(m.get("proven_by") or "")):
            errors.append(f"mechanisms: {mname} via storage needs proven_by '#<n> AC<k>'")
    # -- drivability: the wiring check acts on the trigger of every observed row on one
    # scene; the design's tree of that scene has to show the trigger, and enabled,
    # unless the row brings its own `drive.open` (a form the design never shows complete)
    trees = skeleton.get("trees") or {}
    scene_decls = doc.get("scenes") or {}
    for rid, row in rows.items():
        if not row.get("observe"):
            continue
        drive = row.get("drive") or {}
        if not isinstance(drive, dict):
            errors.append(f"{rid}: drive must be a mapping (scene, reach, open)")
            continue
        chosen = drive.get("scene")
        row_scenes = [scene_name_of(x) for x in row.get("scenes") or []]
        if chosen and chosen not in scene_decls:
            errors.append(f"{rid}: drive.scene {chosen!r} is not a declared scene")
            continue
        if chosen and chosen not in row_scenes and not drive.get("open"):
            errors.append(f"{rid}: drive.scene {chosen!r} is not one of the row's scenes, and "
                          f"no drive.open brings the control on screen there")
        driving = chosen or (row_scenes[0] if row_scenes else None)
        if driving is None:
            if not drive.get("scene"):
                errors.append(f"{rid}: has observe lines but no scene to drive on; give it "
                              f"`drive: {{scene, open}}`")
            continue
        if driving not in scene_decls:
            continue  # reported by the scene rules
        trig = row.get("trigger") or {}
        head = f'- {trig.get("role")} "{trig.get("name")}"'
        lines = [ln for ln in trees.get(driving, []) if ln.startswith(head)]
        if not lines:
            if not drive.get("open"):
                errors.append(f"{rid}: trigger {trig.get('role')} {trig.get('name')!r} is not in the "
                              f"design's tree of its driving scene {driving}; name a scene that "
                              f"shows it in drive.scene or add drive.open")
            continue
        if all("[disabled]" in ln for ln in lines) and not drive.get("open"):
            errors.append(f"{rid}: trigger is [disabled] on its driving scene {driving}; the "
                          f"wiring check cannot act on it — add drive.open with the steps "
                          f"that make it actionable, or pick another drive.scene")
    # -- typed values: a textbox the design shows with a value was typed by someone
    for sname, decl in scene_decls.items():
        decl = decl or {}
        typed = any(isinstance(st, dict) and st.get("value") is not None
                    for st in decl.get("open") or [])
        for ln in trees.get(sname, []):
            m = re.match(r'^- (textbox|searchbox|combobox|spinbutton)(?: "[^"]*")?: (.+?)(?: <|$)', ln)
            if m and not typed:
                warnings.append(f"scene {sname}: the design shows {m.group(1)} with value "
                                f"{m.group(2)!r} but no open step types anything; the product "
                                f"will show an empty field")
                break
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
                          f"nodes; {after_advice(tree_of(page), screen_driver_mod().VolatileTrigger(role, name), None, page=page)}")
    # -- row trigger pins: which pin a row may use is decided by the design tree
    sd = screen_driver_mod()
    for rid, row in rows.items():
        wanted = sd.row_trigger(row)
        if not wanted.role or not wanted.name:
            continue
        if wanted.after is not None and wanted.occurrence is not None:
            errors.append(f"{rid}: trigger carries both after and occurrence; a row has one "
                          f"pin, and which one is the tree's answer, not a preference")
        row_scenes = [scene_name_of(s) for s in (row.get("scenes") or [])]
        if not row_scenes or contract_dir is None:
            continue
        pages_for: dict[str, set[str]] = {}
        for sc in row_scenes:
            page = scene_pages.get(sc)
            if page:
                pages_for.setdefault(page, set()).add(sc)
        for page, scs in pages_for.items():
            tree = tree_of(page)
            bare = sd.VolatileTrigger(wanted.role, wanted.name)
            drawn = sd.count_trigger_hits(tree, bare, scs)
            label = f"{rid}: trigger {wanted.role} {wanted.name!r} on {page}"
            if drawn <= 1:
                if wanted.occurrence is not None:
                    errors.append(f"{label} matches {drawn} node; a positional pin claims "
                                  f"an ambiguity the design does not have — drop it")
                continue
            kind = sd.TriggerConflict(
                rid, page, drawn, sd.trigger_after_candidates(tree, bare, scs)).kind
            # Which pin is legal is the tree's answer. Leaving the choice to whoever writes
            # the row is how one thing gets two ways of being said: `after` survives the
            # design putting another control before it and `occurrence` does not, so a row
            # that *can* use `after` must, and a row in a repeated block cannot.
            if kind == sd.PIN_AFTER and wanted.occurrence is not None:
                errors.append(f"{label} matches {drawn} nodes, and their previous named "
                              f"nodes differ, so this row is pinned with after, not by "
                              f"position; {after_advice(tree, bare, scs, rid, page)}")
            elif kind == sd.PIN_OCCURRENCE and wanted.after is not None:
                errors.append(f"{label} matches {drawn} nodes; "
                              f"{after_advice(tree, bare, scs, rid, page)}")
            if wanted.occurrence is not None:
                if wanted.of != drawn:
                    errors.append(f"{label} matches {drawn} nodes, and the row says of "
                                  f"{wanted.of}; a positional pin means nothing against a "
                                  f"number that has moved")
                elif not 1 <= wanted.occurrence <= drawn:
                    errors.append(f"{label}: occurrence {wanted.occurrence} is outside the "
                                  f"{drawn} nodes the design draws")
                if wanted.occurrence != 1 and not (row.get("source") or []):
                    errors.append(f"{label}: occurrence {wanted.occurrence} is not the "
                                  f"first match, so it is a judgement about which block "
                                  f"this row means; say where it came from in source")
            resolved = sd.count_trigger_hits(tree, wanted, scs)
            if resolved > 1:
                errors.append(f"{label} matches {resolved} nodes; "
                              f"{after_advice(tree, bare, scs, rid, page)}")
    return errors, warnings


def lint(doc: dict, skeleton: dict, openapi: dict | None) -> tuple[list[str], list[str]]:
    """The control axis: one row per behaviour, as ../references/contract-format.md says."""
    errors: list[str] = []
    warnings: list[str] = []
    rows = doc.get("rows") or []
    mechanisms, _ = mechanisms_of(doc)
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
        rid = str(row.get("id", "<no id>"))
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
        if calls != ["none"]:
            if not row.get("route"):
                errors.append(f"{rid}: route missing for a row with calls")
            observe = row.get("observe") or []
            if not observe and not any(is_http_call(c) for c in calls):
                warnings.append(f"{rid}: observe is empty on a non-HTTP row; the wiring check reads nothing")
            elif not observe:
                errors.append(f"{rid}: observe missing for a row with calls; a wiring check has nothing to read")
            for line in observe:
                op, arrow, _ = str(line).partition("->")
                method, _, path = op.strip().partition(" ")
                if not arrow:
                    errors.append(f"{rid}: observe line has no '->' expression: {line}")
                else:
                    known = op_known(method, path)
                    if known == "proposed":
                        warnings.append(f"{rid}: observe reads a proposed operation: {op.strip()}")
                    elif ops is not None and known == "no":
                        errors.append(f"{rid}: observe operation not in openapi: {op.strip()}")
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
        reach = str(row.get("reach", ""))
        if not REACH.match(reach):
            errors.append(f"{rid}: reach {reach!r} is not seed:/stub:/dev: plus a name")
        elif reach not in mechanisms:
            errors.append(f"{rid}: reach {reach!r} not in mechanisms")
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


# ---------------------------------------------------------------- the repair command
ROW_HEAD = re.compile(r"^- id: (\S+)\s*$", re.M)


def row_blocks(text: str) -> dict[str, tuple[int, int]]:
    """Every row's span in the contract's own bytes, by id.

    The repair edits the file as text, never as a parsed document: a 200 KB contract is
    written by hand, and round-tripping it through a YAML dumper would rewrite every line
    a person laid out to say something."""
    heads = [(m.group(1), m.start()) for m in ROW_HEAD.finditer(text)]
    out = {}
    for i, (rid, start) in enumerate(heads):
        end = heads[i + 1][1] if i + 1 < len(heads) else len(text)
        out[rid] = (start, end)
    return out


def after_trigger(block: str) -> int:
    """Where a sibling of `trigger` goes: the offset just past the trigger construct."""
    m = re.search(r"^  trigger:(.*)$", block, re.M)
    if not m:
        return -1
    end = m.end() + 1
    if m.group(1).strip():
        return end                      # inline `trigger: { … }`
    for line in block[end:].splitlines(keepends=True):
        if line.strip() and not line.startswith("    "):
            break
        end += len(line)
    return end


def write_pin(text: str, rid: str, lines: list[str]) -> str:
    """`lines` as siblings of the row's `trigger`, where `after` already lives."""
    start, end = row_blocks(text)[rid]
    block = text[start:end]
    at = after_trigger(block)
    if at < 0:
        raise SystemExit(f"{rid}: no trigger to pin")
    body = "".join(f"  {line}\n" for line in lines)
    return text[:start] + block[:at] + body + block[at:] + text[end:]


def taken_after(doc: dict, wanted) -> set[tuple[str, str]]:
    """The `after` values other rows sharing this exact trigger already use. A candidate
    one of them has taken is not this row's to take."""
    sd = screen_driver_mod()
    out = set()
    for row in doc.get("rows") or []:
        other = sd.row_trigger(row)
        if (other.role, other.name) == (wanted.role, wanted.name) and other.after:
            out.add(other.after)
    return out


def settles(doc: dict, contract_dir: Path, row: dict, pin: dict) -> bool:
    """Whether this pin leaves at most one node on every scene the row is drawn on.

    Tried before anything is written. A candidate that merely differs from the others can
    still cover two matches — three matches where two share a previous node have two
    candidates and only one of them selects a single node."""
    trial = dict(row, **pin)
    probe = {"rows": [trial], "scenes": doc.get("scenes") or {}}
    got = screen_driver_mod().trigger_resolution(probe, contract_dir).get(str(row.get("id")))
    return bool(got) and all(len(v) <= 1 for v in got.values())


def taken_within(doc: dict, trigger) -> set[tuple[str, str]]:
    """The containers other rows sharing this trigger already claim. A pin another row
    holds is not free: writing it here would give two rows one node."""
    sd = screen_driver_mod()
    out = set()
    for row in doc.get("rows") or []:
        w = sd.row_trigger(row)
        if (w.role, w.name) == (trigger.role, trigger.name) and w.within is not None:
            out.add(w.within)
    return out


def pin_plan(doc: dict, contract_dir: Path) -> tuple[dict[str, list[str]], list[str]]:
    """What the repair may write, and what it refuses to a person.

    Two rules make this safe to run without reading the product. `after` is written only
    when the candidates left after removing the ones sibling rows already took come to
    exactly one — choosing among several is choosing what the row *means*, and no proof
    catches a wrong meaning. `occurrence` is only ever 1: the first match in reading
    order, decided before the product is ever asked, so the command cannot search for the
    value that turns a criterion green.
    """
    sd = screen_driver_mod()
    writes: dict[str, list[str]] = {}
    refusals: dict[str, str] = {}
    rows = {str(r.get("id")): r for r in doc.get("rows") or []}
    # A row conflicts once per page it is drawn on; it is repaired or refused once.
    for c in sd.contract_trigger_conflicts(doc, contract_dir):
        if c.row_id in writes or c.row_id in refusals:
            continue
        wanted = sd.row_trigger(rows[c.row_id])
        if wanted.after is not None or wanted.occurrence is not None:
            refusals[c.row_id] = (f"{c.row_id}: already pinned, and the pin does not "
                                  f"resolve it; that is a contract question, not a repair")
            continue
        # A scene with no match at all is fine — the control is simply not drawn there.
        # Scenes that do draw it must all draw the same number, or no single pin serves
        # them: the driver asserts one count, on whichever scene it is driving.
        seen = {k: v for k, v in (sd.trigger_resolution(doc, contract_dir, [c.row_id])
                                  .get(c.row_id) or {}).items() if v}
        counts = {len(v) for v in seen.values()}
        if c.kind == sd.PIN_WITHIN:
            # Both halves are tried, `within: {role: ""}` included: the button that opens
            # a dialog is told from the one that confirms inside it by being under no
            # container at all, and without the negative half only one of the pair could
            # be said.
            free = [a for a in c.ancestors if a not in taken_within(doc, wanted)]
            works = [a for a in free if settles(doc, contract_dir, rows[c.row_id],
                                                {"within": {"role": a[0], "name": a[1]}})]
            if len(works) != 1:
                refusals[c.row_id] = (
                    f"{c.row_id}: [{sd.NEEDS_DECISION}] {len(works)} of the {len(free)} free "
                    f"containers leave one node on every scene, so which one this row means "
                    f"is a decision, not a repair")
                continue
            writes[c.row_id] = [
                f'within: {{ role: "{works[0][0]}", name: "{works[0][1]}" }}']
        elif c.kind == sd.PIN_AFTER:
            free = [p for p in c.candidates if p[1] and p not in taken_after(doc, wanted)]
            works = [p for p in free if settles(doc, contract_dir, rows[c.row_id],
                                                {"after": {"role": p[0], "name": p[1]}})]
            if len(works) != 1:
                refusals[c.row_id] = (
                    f"{c.row_id}: [{sd.NEEDS_DECISION}] {len(works)} of the {len(free)} free "
                    f"candidates leave one node on every scene, so which one this row means "
                    f"is a decision, not a repair")
                continue
            writes[c.row_id] = [f"after: {{ role: {works[0][0]}, name: \"{works[0][1]}\" }}"]
        else:
            # `of` is the number on the scene that actually has the ambiguity; a scene
            # that draws one needs no pin and the driver says so. Whether the pair settles
            # every scene is proved below, not assumed from the counts.
            trial = {"occurrence": 1, "of": max(counts)}
            if not settles(doc, contract_dir, rows[c.row_id], trial):
                refusals[c.row_id] = (
                    f"{c.row_id}: [{sd.NEEDS_DECISION}] the first of {max(counts)} does not "
                    f"leave one node on every scene this row is driven on")
                continue
            writes[c.row_id] = ["occurrence: 1", f"of: {max(counts)}"]
    return writes, sorted(refusals.values())


def pin(contract: Path, base_ref: str | None) -> int:
    """Repair every mechanically repairable locator, and prove it before it is kept."""
    sd = screen_driver_mod()
    text = contract.read_text(encoding="utf-8")
    doc = yaml.safe_load(text)
    contract_dir = contract.resolve().parent
    root = repo_root(contract)

    base = base_ref or recorded_base(root) or "HEAD"
    rel = contract.resolve().relative_to(root.resolve())
    shown = subprocess.run(["git", "-C", str(root), "show", f"{base}:{rel}"],
                           capture_output=True, text=True)
    if shown.returncode != 0:
        print(f"ERROR cannot read {rel} at {base}: {shown.stderr.strip()}")
        return 2
    # Against the committed contract, never the working copy. Otherwise a caller could
    # delete a hand-written pin, then have this command "repair" it, and each write would
    # pass its own proof while the pair changed what the contract means.
    before = sd.trigger_resolution(yaml.safe_load(shown.stdout), contract_dir)
    print(f"proving against {base}:{rel}")

    writes, refused = pin_plan(doc, contract_dir)
    # A row the committed contract already resolved is not broken; something in the working
    # copy broke it. Repairing it would let a caller delete a hand-written pin, have this
    # command write a different one, and pass — each write proving itself while the pair
    # moved the row to another node. This is the one way a repair could change meaning.
    for rid in sorted(writes):
        was = before.get(rid) or {}
        if was and all(len(v) <= 1 for v in was.values()):
            del writes[rid]
            refused.append(f"{rid}: resolved at {base} and does not here, so the working "
                           f"copy broke it; this command repairs contracts, not edits")
    for line in refused:
        print("REFUSED", line)
    if not writes:
        print(f"pinned 0 rows, {len(refused)} left to a person")
        return 1 if refused else 0

    edited = text
    for rid, lines in writes.items():
        edited = write_pin(edited, rid, lines)
    after = sd.trigger_resolution(yaml.safe_load(edited), contract_dir)

    kept, broke = [], []
    for rid in writes:
        got = after.get(rid) or {}
        if not got or any(len(v) > 1 for v in got.values()):
            broke.append(f"{rid}: the pin still leaves more than one node on some scene")
    for rid, pages in before.items():
        if rid not in writes and (after.get(rid) or {}) != pages:
            broke.append(f"{rid}: a repair of another row moved this one; nothing written")
    if broke:
        for line in broke:
            print("ERROR", line)
        print(f"pinned 0 rows: the proof failed, the contract is untouched")
        return 2

    contract.write_text(edited, encoding="utf-8")
    for rid, lines in writes.items():
        kept.append(f"{rid}: {' '.join(lines)}")
    for line in sorted(kept):
        print("PINNED ", line)
    print(f"pinned {len(writes)} rows, {len(refused)} left to a person; "
          f"every other row resolves to the same node it did at {base}")
    return 1 if refused else 0


def recorded_base(root: Path) -> str | None:
    """The base commit `dispatch.sh` recorded for this ticket's branch, when there is one."""
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "--abbrev-ref", "HEAD"],
                          capture_output=True, text=True)
    if head.returncode != 0:
        return None
    got = subprocess.run(["git", "-C", str(root), "config",
                          f"branch.{head.stdout.strip()}.mmw-base"],
                         capture_output=True, text=True)
    return got.stdout.strip() or None


def main(argv: list[str]) -> int:
    rest: list[str] = []
    TOOLS[:] = []
    pin_mode = False
    base_ref: str | None = None
    i = 1
    while i < len(argv):
        if argv[i] == "--pin":
            pin_mode = True
            i += 1
        elif argv[i] == "--base" and i + 1 < len(argv):
            base_ref = argv[i + 1]
            i += 2
        elif argv[i] == "--tools" and i + 1 < len(argv):
            TOOLS.append(Path(argv[i + 1]).resolve())
            i += 2
        elif argv[i].startswith("--tools="):
            TOOLS.append(Path(argv[i][len("--tools="):]).resolve())
            i += 1
        else:
            rest.append(argv[i])
            i += 1
    argv = [argv[0], *rest]
    if pin_mode:
        if len(argv) != 2 or not TOOLS:
            print(__doc__)
            return 2
        return pin(Path(argv[1]), base_ref)
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
    e2, w2 = lint_screen_axis(doc, skeleton, baseline, contract.resolve().parent)
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
