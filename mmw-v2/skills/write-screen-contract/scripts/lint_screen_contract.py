# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6"]
# ///
"""Lint a screen contract against the handoff skeleton and, when given, openapi.json.

Usage: uv run python lint_screen_contract.py [--tools <ui-acceptance scripts>] <screen-contract.yaml> <skeleton.json> [<openapi.json>]
Exit 0 with no errors; 1 with errors listed one per line; warnings never fail.

A `uv run python` invocation (the form a ticket CHECK writes) does not read the
metadata block above; `main` then re-execs through `uv run --script` so PyYAML
comes from that block. `uv run --script lint_screen_contract.py` skips the re-exec.

`--tools` is the `scripts/` directory of the ui-acceptance skill, an override.
Without it this file finds that directory beside this skill under `skills/`. The
`.mmw/target.json` check comes from those scripts (`target_config.py --validate`).
Rules are the tables in ../references/screen-contract-format.md.

Printed on every run, before the findings: each `retired_ids` entry with its note,
kept in sight so a retired identity is never a silent allowance.
"""
from __future__ import annotations

import io
import json
import os
import re
import sys
from contextlib import redirect_stderr, redirect_stdout
from html.parser import HTMLParser
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
            "lint_screen_contract.py is missing pyyaml after uv run --script; "
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
LOCALE = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")
IMPL_PNG = re.compile(r"^(.+)-(\d+x\d+)-impl\.png$")
HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
BREAKPOINT = re.compile(r"@media[^{]*\((?:max|min)-width:\s*(\d+)px\)")
INTERACTIVE_TAGS = {"button", "input", "select", "textarea"}
INTERACTIVE_ROLES = {
    "button", "textbox", "checkbox", "combobox", "link", "tab", "radio", "switch",
    "slider", "menuitem", "searchbox", "spinbutton",
}

ROW_KEYS = {
    "id", "component", "trigger", "precondition", "scenes", "calls", "app",
    "shows", "next", "on_failure", "source", "gap",
}
SCENE_KEYS = {"page", "input"}
PAGE_KEYS = {"mount", "component", "viewports"}
TOAST = re.compile(r"toast:[A-Z][A-Z0-9_]*")
TOP_KEYS = {
    "effort", "baselines", "locale", "viewports", "pages", "scenes", "states", "rows",
    "retired_ids",
    "backend_without_ui", "proposed_operations",
}
REMOVED_TOP_KEYS = {"target", "volatile_values", "readme_dispositions"}
REMOVED_PAGE_KEYS = {"route"}

HERE = Path(__file__).resolve().parent
# The ui-acceptance skill sits beside this one under `skills/`; `--tools` overrides that.
SIBLING_UA = HERE.parents[1] / "ui-acceptance" / "scripts"

# The directories `--tools` named, else the sibling ui-acceptance scripts.
# `target_file_problem()` asks `target_config.py`.
TOOLS: list[Path] = []


def tools_dirs() -> list[Path]:
    return TOOLS or [SIBLING_UA]


def target_config_mod():
    """`target_config.py` from `--tools` or the sibling ui-acceptance skill;
    Python's import cache holds it. The `.mmw/target.json` check (`target_main`) comes
    from this module."""
    looked = tools_dirs()
    for directory in looked:
        if (directory / "target_config.py").is_file():
            if str(directory) not in sys.path:
                sys.path.insert(0, str(directory))
            import target_config
            return target_config
    paths = ", ".join(str(d) for d in looked)
    if TOOLS:
        raise SystemExit(
            f"no target_config.py in any --tools directory ({paths}). "
            "Pass --tools <the ui-acceptance skill's scripts directory>."
        )
    raise SystemExit(
        f"no target_config.py in the sibling ui-acceptance skill ({paths}). "
        "Pass --tools <the ui-acceptance skill's scripts directory>."
    )


def target_file_problem(repo: Path) -> tuple[str, str] | None:
    """`("warning", line)` about the repository's `.mmw/target.json`, from
    `target_config.py`'s own validation; `None` when the file is complete.

    Both a missing file and one that fails `--validate` are warnings naming
    `target_config.py --check`: the contract ticket, cut after the spec that needs this
    lint clean, is the ticket that lands `.mmw/` or brings a file written for an earlier
    MMW version to the current shape.
    """
    if not (repo / ".mmw" / "target.json").exists():
        return ("warning", "no .mmw/target.json yet; the contract ticket lands it — run "
                           "`target_config.py --check` (the ui-acceptance skill) there")
    buf_out, buf_err = io.StringIO(), io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        code = target_config_mod().target_main(["--validate", "--repo", str(repo)])
    if code == 0:
        return None
    text = (buf_out.getvalue() or buf_err.getvalue()).strip()
    text = " ".join(text.split()) or f"exited {code}"
    return ("warning", f".mmw/target.json fails `target_config.py --validate`: {text}; "
                       "the contract ticket brings .mmw/ to the current shape — run "
                       "`target_config.py --check` (the ui-acceptance skill) there")


# The shapes a `source` may take. A story is legal for the audit trail and warned on:
# no worker ever reads a story, so a behaviour decided only there reaches nobody.
SOURCE_SHAPES = (
    ("conversation", re.compile(r"^conversation \d{4}-\d{2}-\d{2}\b")),
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


def operation(entry) -> tuple[str, str] | None:
    """Return the HTTP method/path prefix; non-HTTP calls and `none` return None."""
    parts = str(entry).split()
    if len(parts) < 2 or parts[0].upper() not in HTTP_METHODS:
        return None
    return parts[0].upper(), parts[1]


def repo_root(contract: Path) -> Path:
    """The repository `baselines.look` and `.mmw/target.json` are relative to.

    A contract still in a run's scratch directory (step 6 keeps it there until every
    gap is aligned) sits in no repository; the repository is then the one the lint
    is run from, found from the current directory rather than taken as it."""
    for start in (contract.resolve(), Path.cwd().resolve()):
        for parent in [start] + list(start.parents):
            if (parent / ".git").exists():
                return parent
    return Path.cwd()


def stylesheet_breakpoints(baseline: Path) -> set[int]:
    """Every width a media query names anywhere the pages take CSS from: each `.css`
    under the package (`styles/`, the design system's `_ds/<folder>/`) and each page's
    `<style>` blocks."""
    widths: set[int] = set()
    sources = sorted(baseline.rglob("*.css")) + sorted(baseline.glob("*.dc.html"))
    for path in sources:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            continue
        widths.update(int(w) for w in BREAKPOINT.findall(text))
    return widths


SCENE_INPUT_KEYS = {"file", "value", "with"}


def scene_input_errors(name: str, spec: object, baseline: Path | None) -> list[str]:
    """`scenes.<name>.input`: {file, value, with?}; the file lies inside the package."""
    if not isinstance(spec, dict):
        return [f"scenes: {name!r} input must be a mapping with file and value"]
    errors = [f"scenes: {name!r} input.{key} is not a contract field"
              for key in unknown_keys(spec, SCENE_INPUT_KEYS)]
    file, value = spec.get("file"), spec.get("value")
    if not isinstance(file, str) or not file or not isinstance(value, str) or not value:
        errors.append(f"scenes: {name!r} input needs file and value")
        return errors
    if "with" in spec and not isinstance(spec["with"], dict):
        errors.append(f"scenes: {name!r} input.with must be a mapping")
    if baseline is not None and baseline.is_dir():
        target = (baseline / file).resolve()
        if baseline.resolve() not in target.parents or not target.is_file():
            errors.append(f"scenes: {name!r} input file {file!r} is not in the handoff package")
    return errors


def unknown_keys(value: dict, allowed: set[str]) -> list[str]:
    return sorted(k for k in value if k not in allowed)


def removed_field(location: str, key: str) -> str:
    return (f"{location}{key} was removed; see migration note "
            "mmw-v2/downstream-notes/494-screen-contract-format.md for the replacement")


def skeleton_scene_pages(skeleton: dict) -> dict[str, str]:
    declared = skeleton.get("scene_pages") or {}
    if declared:
        return {str(scene): str(page) for scene, page in declared.items()}
    return {str(scene): str(row["page"])
            for row in skeleton.get("table") or []
            for scene in row.get("scenes") or []}


class HandoffPageParser(HTMLParser):
    """Source checks complementing the renderer's inventory."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.controls_without_id: list[tuple[int, int, str]] = []
        self.props: dict | None = None
        # The page's root: the first element inside `<x-dc>` outside its `<helmet>`.
        # The product story's root pairs with it by `data-ui` id.
        self.in_xdc = False
        self.in_helmet = False
        self.root: tuple[int, str, str] | None = None

    def handle_endtag(self, tag: str) -> None:
        if tag == "helmet":
            self.in_helmet = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attr = dict(attrs)
        if tag == "x-dc":
            self.in_xdc = True
        elif tag == "helmet":
            self.in_helmet = True
        elif self.in_xdc and not self.in_helmet and self.root is None:
            self.root = (self.getpos()[0], tag, str(attr.get("data-ui") or "").strip())
        role = str(attr.get("role") or "").lower()
        style = re.sub(r"\s+", "", str(attr.get("style") or "").lower())
        hidden = (
            "hidden" in attr
            or str(attr.get("aria-hidden") or "").lower() == "true"
            or (tag == "input" and str(attr.get("type") or "").lower() == "hidden")
            or "display:none" in style
            or "visibility:hidden" in style
            or "opacity:0" in style
        )
        interactive = (
            tag in INTERACTIVE_TAGS
            or (tag == "a" and "href" in attr)
            or role in INTERACTIVE_ROLES
            or str(attr.get("contenteditable") or "").lower() == "true"
        )
        if interactive and not hidden and not str(attr.get("data-ui") or "").strip():
            line, column = self.getpos()
            self.controls_without_id.append((line, column + 1, tag))
        if tag == "script" and "data-dc-script" in attr:
            raw = attr.get("data-props")
            if raw:
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError:
                    value = None
                self.props = value if isinstance(value, dict) else None


def handoff_page_errors(baseline: Path, pages: set[str]) -> list[str]:
    errors: list[str] = []
    # A Component page with no scene prop never reaches scenes.json, so read every
    # Component page on disk, not only the ones scenes.json names.
    on_disk = {p.name for p in baseline.glob("Component · *.dc.html")}
    for page_name in sorted(pages | on_disk):
        page = baseline / page_name
        if not page.is_file():
            errors.append(f"handoff page missing: {page_name} (named by scenes.json)")
            continue
        parser = HandoffPageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        for line, column, tag in parser.controls_without_id:
            errors.append(
                f"{page.name}:{line}:{column}: clickable or editable {tag} has no data-ui id")
        if page.name.startswith("Component · ") and not (
                isinstance(parser.props, dict) and "scene" in parser.props):
            errors.append(f"{page.name}: Component page has no scene prop in data-props")
        if parser.root is not None and not parser.root[2] \
                and page.name.startswith(("Component · ", "App · ")):
            line, tag, _ = parser.root
            errors.append(f"{page.name}:{line}: the page's root <{tag}> has no data-ui id; "
                          "the product story's root carries the same id and pairs with it")
    return errors


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
    """Validate removed/unknown fields, baseline pages, locale, target config,
    viewports, page/component mappings, scenes, and story coverage.

    Every finding names the key or artifact it is about.
    """
    errors: list[str] = []
    warnings: list[str] = []
    rows = {str(r.get("id")): r for r in doc.get("rows") or [] if isinstance(r, dict)}
    for key in sorted(REMOVED_TOP_KEYS & set(doc)):
        errors.append(removed_field("", key))
    for key in unknown_keys(doc, TOP_KEYS | REMOVED_TOP_KEYS):
        errors.append(f"{key} is not a contract field")
    if baseline is None:
        errors.append("baselines.look is missing")
    elif not baseline.is_dir():
        errors.append(f"baselines.look path does not exist: {baseline}")
    locale = doc.get("locale")
    if not locale:
        errors.append("locale missing (use the product's BCP 47 language tag)")
    elif not LOCALE.match(str(locale)):
        errors.append(f"locale {locale!r} is not a BCP 47 language tag")
    # -- target runtime
    if contract_dir is not None:
        problem = target_file_problem(repo_root(Path(contract_dir)))
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
    if baseline is not None and baseline.is_dir() and widths:
        for w in widths:
            if w in stylesheet_breakpoints(baseline):
                errors.append(f"viewports: width {w} is a breakpoint of the handoff "
                              f"stylesheets; a render there compares two reflows")
    # -- pages
    pages = doc.get("pages") or {}
    scene_pages = skeleton_scene_pages(skeleton)
    handoff_pages = set(scene_pages.values())
    if baseline is not None and baseline.is_dir():
        errors.extend(handoff_page_errors(baseline, handoff_pages))
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
        for key in sorted(REMOVED_PAGE_KEYS & set(decl)):
            errors.append(removed_field(f"pages: {page!r} ", key))
        for key in unknown_keys(decl, PAGE_KEYS | REMOVED_PAGE_KEYS):
            errors.append(f"pages: {page!r} {key} is not a contract field")
        if page not in handoff_pages:
            errors.append(f"pages: {page!r} is not a page of scenes.json")
        if "viewports" in decl:
            own = decl.get("viewports")
            entries = own if isinstance(own, list) else [own]
            if not own:
                errors.append(f"pages: {page!r} viewports is empty; omit it to use the top-level list")
            for vp in entries if own else []:
                m = VIEWPORT.match(str(vp).strip())
                if not m:
                    errors.append(f"pages: {page!r} viewports entry {vp!r} is not WIDTHxHEIGHT")
                elif baseline is not None and baseline.is_dir() and \
                        int(m.group(1)) in stylesheet_breakpoints(baseline):
                    errors.append(f"pages: {page!r} viewports width {m.group(1)} is a breakpoint "
                                  "of the handoff stylesheets; a render there compares two reflows")
        mount = str(decl.get("mount") or "")
        if not MOUNT.match(mount):
            errors.append(f"pages: {page!r} mount {mount!r} must be a short lowercase id")
        elif mount in declared_mounts:
            errors.append(f"pages: mount {mount!r} declared by both {declared_mounts[mount]!r} "
                          f"and {page!r}")
        else:
            declared_mounts[mount] = page
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
        if "input" in decl:
            errors += scene_input_errors(name, decl.get("input"), baseline)
    # -- story coverage: the newest element-parity --out under the contract dir.
    if contract_dir is not None:
        media = latest_story_out(contract_dir)
        if media is not None:
            seen = {m.group(1) for p in media.iterdir()
                    if p.is_file() and (m := IMPL_PNG.match(p.name))}
            by_page: dict[str, list[str]] = {}
            for sname, page in scene_pages.items():
                by_page.setdefault(page, []).append(sname)
            for page, names in sorted(by_page.items()):
                missing = [n for n in names if n not in seen]
                if missing:
                    warnings.append(
                        f"story coverage: {page} scenes {', '.join(missing)} are not "
                        f"in the latest element parity --out inventory")
    return errors, warnings


def lint(doc: dict, skeleton: dict, openapi: dict | None) -> tuple[list[str], list[str]]:
    """The control axis: one row per behaviour, as ../references/screen-contract-format.md says."""
    errors: list[str] = []
    warnings: list[str] = []
    rows = doc.get("rows") or []
    retired_entries = [e if isinstance(e, dict) else {"id": e} for e in doc.get("retired_ids") or []]
    retired = {str(e.get("id")) for e in retired_entries}
    for entry in retired_entries:
        for key in ("page", "trigger"):
            if key in entry:
                errors.append(removed_field(f"retired_ids {entry.get('id')}: ", key))
    triggers: dict[str, set[str]] = {}
    for r in skeleton["table"]:
        triggers.setdefault(str(r["id"]), set()).update(r["scenes"])
    ops = ({(m.upper(), p) for p, methods in openapi.get("paths", {}).items()
            for m in methods if m.upper() in HTTP_METHODS}
           if openapi is not None else None)
    proposed = {parsed for raw in doc.get("proposed_operations") or []
                if (parsed := operation(raw)) is not None}
    accounted = set(proposed)
    accounted.update(parsed for raw in doc.get("backend_without_ui") or []
                     if (parsed := operation(raw)) is not None)
    region_pages: dict[str, set[str]] = {}
    for entry in skeleton["table"]:
        region = str(entry.get("id") or "").partition(".")[0]
        if region:
            region_pages.setdefault(region, set()).add(str(entry.get("page") or ""))

    def op_known(method: str, path: str) -> str:
        if ops is not None and (method.upper(), path) in ops:
            return "yes"
        if (method.upper(), path) in proposed:
            return "proposed"
        return "no"

    seen_ids: set[str] = set()
    seen_triggers: dict[str, list[dict]] = {}
    next_values = {
        "stay",
        *(str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id")),
        *(str(name) for name in (doc.get("scenes") or {})),
        *(str(name) for name in (doc.get("states") or [])),
    }
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
        trigger = str(row.get("trigger") or "")
        if trigger not in triggers:
            errors.append(f"{rid}: trigger {trigger!r} not in handoff skeleton")
        else:
            if not (row.get("scenes") or []):
                warnings.append(f"{rid}: scenes is [] — the handoff shows no scene for this precondition")
            for sc in row.get("scenes") or []:
                if sc not in triggers[trigger]:
                    errors.append(f"{rid}: scene {sc!r} does not show this trigger in the skeleton")
        seen_triggers.setdefault(trigger, []).append(row.get("precondition") or {})
        calls = row.get("calls") or []
        if not calls:
            errors.append(f"{rid}: calls is empty (use [none])")
        for call in calls:
            parsed = operation(call)
            if parsed is None:
                if str(call) != "none":
                    warnings.append(
                        f"UNVERIFIED {rid}: no machine-readable source for {call}")
                continue
            method, path = parsed
            accounted.add(parsed)
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
            # `<field@operation …> → <what is drawn from it>`: the binding is before the
            # arrow; the description after it is prose and may name a ticket.
            binding = str(expr).split(" → ", 1)[0]
            if "@" not in binding:
                errors.append(f"{rid}: shows.{shown} names no field@operation: {expr!r}")
            if re.search(r"(?<![\w{])\d+(?![\w}])", binding):
                errors.append(f"{rid}: shows.{shown} carries a literal number: {expr!r}")
        failures = row.get("on_failure")
        if failures not in (None, {}) and not isinstance(failures, dict):
            errors.append(f"{rid}: on_failure must map each failure kind to an outcome")
        for kind, outcome in (failures.items() if isinstance(failures, dict) else ()):
            where = str(outcome).split(" — ", 1)[0].strip()
            if where not in next_values and not TOAST.fullmatch(where):
                errors.append(f"{rid}: on_failure.{kind} starts with {where!r}, not a row id, "
                              "scene, state, stay or toast:<KEY> (then ' — ' and what the "
                              "user sees)")
        next_value = str(row.get("next") or "")
        if not next_value:
            errors.append(f"{rid}: next missing (use a row id, scene, state, or stay)")
        elif next_value not in next_values:
            errors.append(f"{rid}: next {next_value!r} is not a row id, scene, state, or stay")
        app = row.get("app")
        if app:
            if app not in (doc.get("pages") or {}) or not str(app).startswith("App · "):
                errors.append(f"{rid}: app {app!r} is not a declared App page")
            next_decl = (doc.get("scenes") or {}).get(next_value)
            if not isinstance(next_decl, dict):
                errors.append(f"{rid}: cross-component next {next_value!r} must name a scene")
            else:
                region = trigger.partition(".")[0]
                owners = region_pages.get(region, set()) - {str(app)}
                next_page = str(next_decl.get("page") or "")
                if not owners:
                    errors.append(f"{rid}: trigger region {region!r} belongs to no skeleton page")
                elif len(owners) > 1:
                    errors.append(f"{rid}: trigger region {region!r} appears on multiple skeleton pages")
                elif next_page in owners:
                    errors.append(f"{rid}: cross-component next {next_value!r} points to its own "
                                  f"region page {next_page}")
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
                                f"code:…, conversation YYYY-MM-DD)")
        gap = row.get("gap")
        if gap not in GAPS:
            errors.append(f"{rid}: gap {gap!r} not one of {sorted(GAPS)}")
        elif gap != "aligned":
            errors.append(f"{rid}: gap {gap} unresolved")

    if ops is None:
        warnings.append(
            "UNVERIFIED no machine-readable interface inventory; reverse sweep was not run")
    else:
        for method, path in sorted(ops - accounted):
            errors.append(f"reverse sweep: {method} {path} has no row, backend_without_ui, "
                          "or proposed_operations entry")

    for trigger, pres in seen_triggers.items():
        if len(pres) > 1 and len({json.dumps(p, sort_keys=True, ensure_ascii=False) for p in pres}) < len(pres):
            errors.append(f"trigger {trigger!r}: rows share a precondition")
    controls = {(str(r["page"]), str(r["id"])) for r in skeleton["table"]
                if r.get("interactive")}
    covered_pages = {str(r["page"]) for r in skeleton["table"]
                     if str(r["id"]) in seen_triggers
                     and not str(r["page"]).startswith("App · ")}
    covered_pages.update(str(row.get("app")) for row in rows
                         if isinstance(row, dict) and row.get("app"))
    all_pages = set(skeleton_scene_pages(skeleton).values())
    untouched = sorted(all_pages - covered_pages)
    for page, trigger in sorted(controls):
        if trigger not in seen_triggers:
            errors.append(f"skeleton control without a row: {page} / {trigger}")
    for page in untouched:
        errors.append(f"page has no rows: {page}")
    # A disabled state is a row: every scene a control is disabled in is listed by a
    # row for that trigger that calls nothing and stays.
    inert_scenes: dict[str, set[str]] = {}
    for row in rows:
        if isinstance(row, dict) and row.get("calls") in (["none"], "none") \
                and row.get("next") == "stay":
            inert_scenes.setdefault(str(row.get("trigger") or ""), set()).update(
                str(sc) for sc in row.get("scenes") or [])
    for entry in skeleton["table"]:
        trigger = str(entry.get("id") or "")
        for scene in entry.get("disabled_in") or []:
            if trigger in seen_triggers and scene not in inert_scenes.get(trigger, set()):
                errors.append(f"disabled state without a row: {trigger} is disabled in "
                              f"{scene!r}; add a row with calls [none] and next stay "
                              "that lists that scene")
    return errors, warnings


def retired_lines(doc: dict) -> list[str]:
    out = []
    for e in doc.get("retired_ids") or []:
        if isinstance(e, dict):
            out.append(f"RETIRED {e.get('id')}: {e.get('note') or '(no note)'}")
        else:
            out.append(f"RETIRED {e}: (no note)")
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
    if len(argv) not in (3, 4):
        print(__doc__)
        return 2
    contract = Path(argv[1])
    doc = yaml.safe_load(contract.read_text(encoding="utf-8"))
    skeleton = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    openapi = json.loads(Path(argv[3]).read_text(encoding="utf-8")) if len(argv) == 4 else None
    look = (doc.get("baselines") or {}).get("look")
    baseline = (repo_root(contract) / look) if look else None
    for line in retired_lines(doc):
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
