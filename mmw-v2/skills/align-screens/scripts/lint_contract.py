"""Lint a screen contract against the handoff skeleton and, when given, openapi.json.

Usage: uv run python lint_contract.py --tools <drive-target scripts> <screen-contract.yaml> <skeleton.json> [<openapi.json>]
Exit 0 with no errors; 1 with errors listed one per line; warnings never fail.
`--tools` is the `scripts/` directory of the drive-target skill: the target kinds and
the check of `.mmw/target.json` are that driver's, asked through `screen_driver.py
target`, so this file holds no copy of either.
Rules are the tables in ../references/contract-format.md: the control axis (rows), the
screen axis (`target`, `viewports`, `pages`, `scenes`), the mechanism table, and the
target trees under `<contract dir>/targets/`.

Printed on every run, before the findings: each `retired_ids` entry with its note,
and each `volatile_values` entry with its reason — the two kinds of exclusion the
judges honour, kept in sight so they are never a silent allowance.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

GAPS = {"aligned", "design-only", "backend-only"}
REACH = re.compile(r"^(seed|stub|dev):[a-z0-9][a-z0-9-]*$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]*(\.[a-z0-9][a-z0-9-]*)+$")
MOUNT = re.compile(r"^[a-z0-9][a-z0-9-]*$")
VIEWPORT = re.compile(r"^(\d+)x(\d+)$")
TICKET = re.compile(r"^#\d+$")
PROVEN = re.compile(r"^#\d+ AC\d+$")
# The directories `--tools` named. The driver of the drive-target skill is found there
# and nowhere else; `target_kinds()` and `target_file_problem()` ask it.
TOOLS: list[Path] = []


def driver() -> Path:
    for directory in TOOLS:
        candidate = directory / "screen_driver.py"
        if candidate.is_file():
            return candidate
    raise SystemExit("no screen_driver.py in any --tools directory; pass --tools <the "
                     "drive-target skill's scripts directory>")


def target_kinds() -> set[str]:
    out = subprocess.run([sys.executable, str(driver()), "target", "--kinds"],
                         capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"screen_driver.py target --kinds failed: {out.stderr.strip()}")
    return set(out.stdout.split())


def target_file_problem(repo: Path, kind: str) -> tuple[str, str] | None:
    """`("error", line)` or `("warning", line)` about the repository's `.mmw/target.json`,
    from the driver's own validation; `None` when the file is complete."""
    if not (repo / ".mmw" / "target.json").exists():
        return ("warning", "no .mmw/target.json yet; the contract ticket lands it — run "
                           "`screen_driver.py target --check` (the drive-target skill) there")
    out = subprocess.run([sys.executable, str(driver()), "target", "--validate",
                          "--repo", str(repo), "--kind", kind],
                         capture_output=True, text=True)
    if out.returncode == 0:
        return None
    return ("error", (out.stdout or out.stderr).strip())
VIA = {"api", "storage"}
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


def target_hashes(path: Path) -> dict[str, str]:
    out = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8").splitlines()[:6]:
        m = re.match(r"^# (scenes\.json|page) sha256=([0-9a-f]{64})$", line)
        if m:
            out[m.group(1)] = m.group(2)
    return out


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


def lint_screen_axis(doc: dict, skeleton: dict, baseline: Path | None,
                     contract_dir: Path | None) -> tuple[list[str], list[str]]:
    """The screen axis: target, viewports, pages, scenes, the mechanism table, the
    target trees. Every finding names the key it is about."""
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
        warnings.append("target.adapter is not read by anything; the drive-target skill picks "
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
    if contract_dir is not None and baseline is not None and handoff_pages:
        targets = contract_dir / "targets"
        scenes_hash = (hashlib.sha256((baseline / "scenes.json").read_bytes()).hexdigest()
                       if (baseline / "scenes.json").exists() else "")
        for page in sorted(handoff_pages):
            stem = re.sub(r"\.dc\.html$", "", page)
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
        stem = re.sub(r"\.dc\.html$", "", page)
        aria = contract_dir / "targets" / f"{stem}.aria"
        tree = aria.read_text(encoding="utf-8") if aria.exists() else ""
        if not volatile_in_tree(tree, role, name):
            warnings.append(f"volatile_values: {role} {name!r} on {page} is not in the "
                            f"target tree")
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
            if call == "none" or str(call).startswith("ipc "):
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
            ipc_only = all(str(c).startswith("ipc ") for c in calls)
            if not observe and ipc_only:
                warnings.append(f"{rid}: observe is empty on an ipc-only row; the wiring check reads nothing")
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


def volatile_in_tree(text: str, role: str, name: str) -> bool:
    """Whether the handoff target tree names this trigger — quoted accessible name
    or the `: value` form of a static text node."""
    return f'- {role} "{name}"' in text or f'- {role}: {name}' in text


def main(argv: list[str]) -> int:
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
