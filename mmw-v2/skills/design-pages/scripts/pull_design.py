#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58", "pyyaml>=6"]
# ///
"""Pull one Claude Design project into a complete handoff package.

Usage: pull_design.py <manifest.json> <handoff-dir> [--reread <dir>] [--tools <dir>]
                      [--state-list <README.md>] [--contract <screen-contract.yaml>]

The manifest is the unchanged JSON result of `mcp__claude-design__list_files` with
`depth: -1`. The short-lived preview address is read only from
`MMW_DESIGN_PREVIEW_URL`; it is never printed or persisted.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

import yaml


READ_FILE_LIMIT = 256 * 1024
MEDIA_SUFFIXES = {
    ".apng", ".avif", ".gif", ".ico", ".jpeg", ".jpg", ".m4v", ".mov",
    ".mp4", ".mpeg", ".mpg", ".png", ".svg", ".webm", ".webp",
}
TEXT_SUFFIXES = {
    ".css", ".csv", ".html", ".js", ".json", ".md", ".mjs",
    ".txt", ".xml", ".yaml", ".yml",
}
VENDOR_CONSTANTS = ("REACT_URL", "REACT_DOM_URL", "BABEL_URL")


@dataclass(frozen=True)
class ManifestFile:
    path: str
    size: int
    etag: str | None


@dataclass
class HandoffPackage:
    root: Path
    scenes: list[dict]
    sizes: dict[str, tuple[int, int]]
    state_list: str = ""


@dataclass
class RenderAudit:
    rendered: int
    empty_scenes: list[str]
    console_errors: list[tuple[str, str]]
    data_ui_ids: set[str]
    text_by_id: dict[str, list[str]]
    text_without_id: list[tuple[str, str]]
    controls_without_id: list[tuple[str, str]]


class PullRefused(Exception):
    def __init__(self, what: str, why: str, next_step: str, code: int = 2):
        super().__init__(what)
        self.what = what
        self.why = why
        self.next_step = next_step
        self.code = code


class DownloadFailed(Exception):
    def __init__(self, status: str):
        super().__init__(status)
        self.status = status


class _PropsParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.props: dict = {}

    def handle_starttag(self, tag, attrs):
        if tag != "script":
            return
        attr = dict(attrs)
        if "data-dc-script" not in attr:
            return
        raw = attr.get("data-props")
        if raw:
            self.props = json.loads(raw)


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def tool_scripts(tools: Path | None) -> Path:
    return tools or (
        Path(__file__).resolve().parents[2] / "ui-acceptance" / "scripts"
    )


def refusal_text(
    what: str, why: str, next_step: str, tools: Path | None = None,
) -> str:
    try:
        refusal = _load_module(
            "_pull_design_refusal", tool_scripts(tools) / "refusal.py",
        )
        return refusal.refusal(what, why, next_step)
    except (OSError, ImportError):
        return " ".join(part.strip() for part in (what, why, next_step) if part.strip())


def safe_path(raw: object) -> str:
    path = str(raw or "").replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    pure = PurePosixPath(path)
    if not path or pure.is_absolute() or ".." in pure.parts:
        raise PullRefused(
            f"manifest path is unsafe: {raw!r}.",
            "A project file must be a non-empty project-relative path.",
            "Fix the manifest path and rerun.",
        )
    return pure.as_posix()


def load_manifest(path: Path) -> list[ManifestFile]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PullRefused(
            f"manifest cannot be read: {path} ({type(exc).__name__}).",
            "The pull has no trustworthy file inventory.",
            "Save a readable list_files JSON result at that path and rerun.",
        ) from exc
    if not isinstance(raw, list):
        raise PullRefused(
            f"manifest {path} is not a list_files array.",
            "The pull needs the unchanged JSON array returned by list_files.",
            "Run list_files with depth -1, save its JSON result, and rerun.",
        )
    files = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        if str(row.get("type") or "").lower() == "directory":
            continue
        if "size" not in row:
            continue
        try:
            size = int(row["size"])
        except (TypeError, ValueError) as exc:
            raise PullRefused(
                f"manifest size is invalid for {row.get('path')!r}.",
                "Every file needs the byte size reported by list_files.",
                "Run list_files with depth -1, save its JSON result, and rerun.",
            ) from exc
        files.append(ManifestFile(
            safe_path(row.get("path")),
            size,
            str(row["etag"]) if row.get("etag") is not None else None,
        ))
    if not files:
        raise PullRefused(
            f"manifest {path} contains 0 files.",
            "A silent empty pull cannot produce a handoff package.",
            "Run list_files with depth -1 for the intended project and rerun.",
        )
    return files


def handoff_path(path: str) -> bool:
    return any(part.startswith("design_handoff_") for part in PurePosixPath(path).parts)


def preview_file_url(preview: str, path: str) -> str:
    parsed = urllib.parse.urlsplit(preview)
    marker = "/serve/"
    if marker not in parsed.path:
        raise PullRefused(
            "MMW_DESIGN_PREVIEW_URL has no /serve/ file path.",
            "render_preview serve_url identifies one project file under /serve/.",
            "Set MMW_DESIGN_PREVIEW_URL to the current render_preview serve_url and rerun.",
        )
    base = parsed.path.partition(marker)[0] + marker
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, base + quoted, parsed.query, "")
    )


def project_id_from_preview(preview: str) -> str:
    host = urllib.parse.urlsplit(preview).hostname or ""
    marker = ".claudeusercontent."
    if marker not in host:
        raise PullRefused(
            "MMW_DESIGN_PREVIEW_URL has no Claude Design project host.",
            "README.md must identify the project from <project id>.claudeusercontent.com.",
            "Set MMW_DESIGN_PREVIEW_URL to the current render_preview serve_url and rerun.",
        )
    project = host.partition(marker)[0]
    if not project:
        raise PullRefused(
            "MMW_DESIGN_PREVIEW_URL has an empty project id.",
            "README.md must identify the Claude Design project that was pulled.",
            "Set MMW_DESIGN_PREVIEW_URL to the current render_preview serve_url and rerun.",
        )
    return project


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "mmw-pull-design/1"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise DownloadFailed(f"HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise DownloadFailed(type(exc).__name__) from exc


HEAD = re.compile(br"<head\b[^>]*>", re.IGNORECASE)
INJECTED_TAG = re.compile(
    br"<(style|script)\b(?=[^>]*\bdata-omelette-injected\b)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)


def strip_injected_head(raw: bytes) -> bytes:
    head = HEAD.search(raw)
    if head is None:
        return raw
    cursor = head.end()
    removed_to = cursor
    while True:
        start = cursor
        while start < len(raw) and raw[start:start + 1].isspace():
            start += 1
        tag = INJECTED_TAG.match(raw, start)
        if tag is None:
            break
        removed_to = tag.end()
        cursor = tag.end()
    if removed_to == head.end():
        return raw
    return raw[:head.end()] + raw[removed_to:]


def previous_etags(target: Path) -> dict[str, str | None]:
    path = target / "design-manifest.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    rows = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return {}
    return {
        str(row.get("path")): row.get("etag")
        for row in rows
        if isinstance(row, dict) and row.get("path")
    }


def is_media(path: str) -> bool:
    return PurePosixPath(path).suffix.lower() in MEDIA_SUFFIXES


def is_text(path: str, body: bytes | None = None) -> bool:
    if PurePosixPath(path).suffix.lower() in TEXT_SUFFIXES:
        return True
    if body is None:
        return False
    try:
        body.decode("utf-8")
        return True
    except UnicodeDecodeError:
        return False


def reread_body(reread: Path | None, path: str) -> bytes | None:
    if reread is None:
        return None
    candidate = reread.joinpath(*PurePosixPath(path).parts)
    try:
        return candidate.read_bytes()
    except OSError:
        return None


def write_project_files(
    files: list[ManifestFile], preview: str, reread: Path | None,
    target: Path, staged: Path,
) -> None:
    old_etags = previous_etags(target)
    needs_reread: list[str] = []
    for entry in files:
        if handoff_path(entry.path):
            continue
        dest = staged.joinpath(*PurePosixPath(entry.path).parts)
        dest.parent.mkdir(parents=True, exist_ok=True)
        if (
            is_media(entry.path)
            and entry.etag is not None
            and old_etags.get(entry.path) == entry.etag
            and (target / entry.path).is_file()
        ):
            shutil.copy2(target / entry.path, dest)
            continue
        body = reread_body(reread, entry.path)
        if body is None:
            try:
                body = fetch(preview_file_url(preview, entry.path))
            except DownloadFailed as exc:
                if entry.size <= READ_FILE_LIMIT and is_text(entry.path):
                    needs_reread.append(entry.path)
                    continue
                raise PullRefused(
                    f"download failed for {entry.path} ({exc.status}).",
                    f"The {entry.size}-byte file has no faithful read_file fallback.",
                    "Restore the preview download, then rerun; the target was not changed.",
                ) from exc
        if entry.path.lower().endswith(".html"):
            body = strip_injected_head(body)
        if not is_media(entry.path) and len(body) != entry.size:
            if is_text(entry.path, body) and entry.size <= READ_FILE_LIMIT:
                needs_reread.append(entry.path)
                continue
            raise PullRefused(
                f"downloaded size differs for {entry.path}: {len(body)} != {entry.size}.",
                "The bytes cannot be trusted and the file has no text reread route.",
                "Restore the preview download, then rerun; the target was not changed.",
            )
        dest.write_bytes(body)
    if needs_reread:
        names = ", ".join(needs_reread)
        raise PullRefused(
            f"text files need rereading: {names}.",
            "Their downloaded bytes do not match the list_files sizes.",
            "Read those paths with mcp__claude-design__read_file into one directory, "
            "then rerun with --reread <dir>.",
            code=1,
        )


def vendor_urls(support: Path) -> dict[str, str]:
    try:
        text = support.read_text(encoding="utf-8")
    except OSError as exc:
        raise PullRefused(
            f"support.js cannot be read: {type(exc).__name__}.",
            "The vendor script addresses are unknown.",
            "Restore support.js in the project and rerun.",
        ) from exc
    out = {}
    for name in VENDOR_CONSTANTS:
        match = re.search(
            rf"\b(?:const|let|var)\s+{name}\s*=\s*(['\"])(.*?)\1", text
        )
        if match is None:
            raise PullRefused(
                f"support.js has no {name} string constant.",
                "The offline renderer cannot identify all three runtime scripts.",
                f"Restore {name} in support.js and rerun.",
            )
        out[name] = match.group(2)
    return out


def pull_vendor(staged: Path) -> dict[str, Path]:
    urls = vendor_urls(staged / "support.js")
    vendor = staged / "vendor"
    vendor.mkdir(parents=True, exist_ok=True)
    by_url = {}
    names = set()
    for url in urls.values():
        name = Path(urllib.parse.urlsplit(url).path).name
        if not name or name in names:
            raise PullRefused(
                f"vendor URL has a missing or duplicate filename: {name or '(none)'}.",
                "Each support.js runtime script needs its own package filename.",
                "Fix the three support.js URL constants and rerun.",
            )
        names.add(name)
        try:
            body = fetch(url)
        except DownloadFailed as exc:
            raise PullRefused(
                f"vendor download failed for {name} ({exc.status}).",
                "The handoff package would not render with the network off.",
                "Restore that vendor address and rerun; the target was not changed.",
            ) from exc
        path = vendor / name
        path.write_bytes(body)
        by_url[url] = path
    return by_url


def page_props(path: Path) -> dict:
    parser = _PropsParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PullRefused(
            f"page props cannot be read from {path.name} ({type(exc).__name__}).",
            "Scenes must come from the page's data-props declaration.",
            "Fix that design page and rerun.",
        ) from exc
    return parser.props


def scenes_from_pages(staged: Path, state_list: str = "") -> HandoffPackage:
    scenes = []
    sizes = {}
    for page in sorted(staged.rglob("*.dc.html")):
        rel = page.relative_to(staged).as_posix()
        name = PurePosixPath(rel).name.removesuffix(".dc.html")
        if PurePosixPath(rel).name.casefold() == "overview.dc.html":
            continue
        props = page_props(page)
        scene = props.get("scene")
        if not isinstance(scene, dict) or scene.get("editor") != "enum":
            continue
        options = scene.get("options")
        if not isinstance(options, list):
            continue
        excluded = set(scene.get("out_of_scope") or [])
        preview = props.get("$preview")
        if not isinstance(preview, dict):
            raise PullRefused(
                f"{rel} has scenes but no $preview size.",
                "The offline render needs the design page's declared viewport.",
                "Add $preview.width and $preview.height to data-props, then rerun.",
            )
        try:
            width, height = int(preview["width"]), int(preview["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PullRefused(
                f"{rel} has an invalid $preview size.",
                "The offline render needs positive integer width and height.",
                "Fix $preview.width and $preview.height, then rerun.",
            ) from exc
        if width < 1 or height < 1:
            raise PullRefused(
                f"{rel} has an invalid $preview size {width}x{height}.",
                "The offline render needs positive width and height.",
                "Fix the $preview size, then rerun.",
            )
        sizes[rel] = (width, height)
        for value in options:
            if value in excluded:
                continue
            value = str(value)
            scene_name = f"{name}.{value}"
            if "/" in scene_name:
                raise PullRefused(
                    f"scene name contains '/': {scene_name}.",
                    "Scene wrapper URLs require names without path separators.",
                    "Rename that page or scene option in Claude Design, then rerun.",
                )
            scenes.append({"name": scene_name, "page": rel, "props": {"scene": value}})
    return HandoffPackage(staged, scenes, sizes, state_list)


def load_design_render(tools: Path | None):
    scripts = tool_scripts(tools)
    path = scripts / "design_render.py"
    try:
        return _load_module("_pull_design_render", path)
    except (OSError, ImportError) as exc:
        raise PullRefused(
            f"design_render.py is unavailable in {scripts}.",
            "Scene data and the offline render check share that renderer.",
            "Pass --tools with the ui-acceptance scripts directory, then rerun.",
        ) from exc


def render_scenes(
    package: HandoffPackage, vendor: dict[str, Path], tools: Path | None,
) -> RenderAudit:
    dr = load_design_render(tools)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PullRefused(
            "playwright is not importable.",
            "The offline render check cannot start Chromium.",
            "Run the executable pull_design.py so its PEP 723 Playwright dependency is loaded.",
        ) from exc
    pages = {
        dr.wrapper_path(scene["name"]): dr.wrapper_page(
            dr.component_of(scene["page"]), scene["props"]
        )
        for scene in package.scenes
    }
    server, port = dr.serve_baseline(package.root, pages)
    origin = f"http://127.0.0.1:{port}"

    def route_offline(route, request):
        if request.url.startswith(origin):
            route.continue_()
        elif request.url in vendor:
            route.fulfill(path=str(vendor[request.url]), content_type="application/javascript")
        else:
            route.abort()

    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            context = browser.new_context(device_scale_factor=1, reduced_motion="reduce")
            context.route("**/*", route_offline)
            page = context.new_page()
            try:
                rendered = 0
                empty_scenes: list[str] = []
                console_errors: list[tuple[str, str]] = []
                data_ui_ids: set[str] = set()
                text_by_id: dict[str, list[str]] = {}
                text_without_id: list[tuple[str, str]] = []
                controls_without_id: list[tuple[str, str]] = []
                current_scene = [""]

                def console_message(message):
                    if message.type == "error":
                        console_errors.append((current_scene[0], message.text))

                def page_error(error):
                    console_errors.append((current_scene[0], str(error)))

                page.on("console", console_message)
                page.on("pageerror", page_error)
                for scene in package.scenes:
                    current_scene[0] = scene["name"]
                    dr.resize(page, package.sizes[scene["page"]])
                    dr.navigate(page, f"{origin}{dr.wrapper_path(scene['name'])}")
                    dr.wait_for_mount(page, "#dc-root")
                    root = page.locator("#dc-root").first
                    if not root.inner_html().strip():
                        empty_scenes.append(scene["name"])
                    scene["data"] = dr.nest_ui_values(dr.read_ui_values(page, "#dc-root"))
                    audit = root.evaluate("""
                        root => {
                          const visible = el => {
                            const style = getComputedStyle(el);
                            return style.display !== 'none' && style.visibility !== 'hidden'
                              && el.getClientRects().length > 0;
                          };
                          const clean = value => (value || '').replace(/\\s+/g, ' ').trim();
                          const label = el => {
                            const classes = Array.from(el.classList || []).slice(0, 2);
                            const stem = el.tagName.toLowerCase() + classes.map(c => '.' + c).join('');
                            return stem + (clean(el.innerText) ? ': ' + clean(el.innerText).slice(0, 120) : '');
                          };
                          const rows = Array.from(root.querySelectorAll('*')).filter(visible);
                          if (visible(root)) rows.unshift(root);
                          const ids = {};
                          const textMissing = [];
                          const controlsMissing = [];
                          for (const el of rows) {
                            const id = el.getAttribute('data-ui');
                            if (id) {
                              (ids[id] ||= []).push(clean(el.innerText));
                            }
                            const ownText = clean(Array.from(el.childNodes)
                              .filter(node => node.nodeType === Node.TEXT_NODE)
                              .map(node => node.textContent).join(' '));
                            if (!id && ownText && !['script', 'style'].includes(el.tagName.toLowerCase())) {
                              textMissing.push(label(el));
                            }
                            if (!id && el.matches('button,input,select,textarea,a[href],[role="button"],[role="textbox"],[contenteditable="true"]')) {
                              controlsMissing.push(label(el));
                            }
                          }
                          return {ids, textMissing, controlsMissing};
                        }
                    """)
                    for data_id, values in audit["ids"].items():
                        data_ui_ids.add(data_id)
                        text_by_id.setdefault(data_id, [])
                        for value in values:
                            if value not in text_by_id[data_id]:
                                text_by_id[data_id].append(value)
                    for label in audit["textMissing"]:
                        row = (scene["name"], label)
                        if row not in text_without_id:
                            text_without_id.append(row)
                    for label in audit["controlsMissing"]:
                        row = (scene["name"], label)
                        if row not in controls_without_id:
                            controls_without_id.append(row)
                    rendered += 1
            finally:
                browser.close()
    except PullRefused:
        raise
    except Exception as exc:
        raise PullRefused(
            f"offline rendering failed ({type(exc).__name__}).",
            "At least one scene could not be verified with external network requests blocked.",
            "Fix the named page or local Chromium runtime, then rerun; the target was not changed.",
        ) from exc
    finally:
        server.shutdown()
        server.server_close()
    return RenderAudit(
        rendered=rendered,
        empty_scenes=empty_scenes,
        console_errors=console_errors,
        data_ui_ids=data_ui_ids,
        text_by_id=text_by_id,
        text_without_id=text_without_id,
        controls_without_id=controls_without_id,
    )


def manifest_for_package(project: str, files: list[ManifestFile]) -> dict:
    return {
        "project_id": project,
        "files": [
            {"path": row.path, "size": row.size, "etag": row.etag}
            for row in files
        ],
    }


def write_readme(
    package: HandoffPackage, project: str, rendered: int,
) -> None:
    lines = [
        "# Claude Design handoff package",
        "",
        "## Viewport and size source",
        "",
    ]
    for page, (width, height) in sorted(package.sizes.items()):
        lines.append(f"- `{page}`: `{width}x{height}` from `$preview.width` and `$preview.height`.")
    if not package.sizes:
        lines.append("- No page declared a `scene` prop; no scene viewport was required.")
    lines.extend([
        "",
        "## Offline render check",
        "",
        f"- Passed: {rendered}/{len(package.scenes)} scenes rendered with external network requests blocked.",
        "",
        "## Pull provenance",
        "",
        f"- Pulled at: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`.",
        f"- Claude Design project id: `{project}`.",
        "",
    ])
    if package.state_list:
        lines.extend([package.state_list.rstrip(), ""])
    (package.root / "README.md").write_text("\n".join(lines), encoding="utf-8")


def state_list_section(readme: Path) -> str:
    try:
        text = readme.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return ""
    match = re.search(r"(?ms)^## State list\s*\n.*?(?=^## |\Z)", text)
    return match.group(0).rstrip() if match else ""


def state_list_regions(section: str) -> dict[str, list[str]]:
    regions: dict[str, list[str]] = {}
    current = None
    for line in section.splitlines():
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            current = heading.group(1).strip()
            regions.setdefault(current, [])
            continue
        item = re.match(r"^\s*[-*]\s+(.+?)\s*$", line)
        if item and current:
            raw = item.group(1).strip()
            if raw.startswith("`") and "`" in raw[1:]:
                value = raw[1:].split("`", 1)[0]
            else:
                value = re.split(r"\s+(?:—|–|-)\s+|:\s+|\s+", raw, maxsplit=1)[0]
            if value:
                regions[current].append(value)
    return regions


def page_inventory(root: Path) -> tuple[dict[str, set[str]], dict[str, set[str]], list[str]]:
    scene_values: dict[str, set[str]] = {}
    excluded_values: dict[str, set[str]] = {}
    no_scene: list[str] = []
    for page in sorted(root.rglob("*.dc.html")):
        rel = page.relative_to(root).as_posix()
        if page.name.casefold() == "overview.dc.html":
            continue
        props = page_props(page)
        scene = props.get("scene")
        if (
            not isinstance(scene, dict)
            or scene.get("editor") != "enum"
            or not isinstance(scene.get("options"), list)
        ):
            no_scene.append(rel)
            continue
        scene_values[rel] = {str(value) for value in scene["options"]}
        excluded_values[rel] = {str(value) for value in (scene.get("out_of_scope") or [])}
    return scene_values, excluded_values, no_scene


def selector_findings(root: Path) -> list[str]:
    css_files = sorted(root.rglob("*.css"))
    if not css_files:
        return []
    check = Path(__file__).with_name("check_editable_selectors.py")
    result = subprocess.run(
        [sys.executable, str(check), *(str(path) for path in css_files)],
        capture_output=True,
        text=True,
    )
    if result.returncode not in (0, 1):
        said = " ".join((result.stdout + result.stderr).split())
        return [f"选择器检查未完成：{said or f'exit {result.returncode}'}"]
    prefix = str(root) + os.sep
    return [
        line.replace(prefix, "", 1)
        for line in result.stdout.splitlines()
        if line.strip() and not line.startswith("every selector")
        and not re.match(r"^\d+ selectors the editor cannot reach$", line)
    ]


def git_context(target: Path) -> tuple[Path, str] | None:
    start = target if target.exists() else target.parent
    result = subprocess.run(
        ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    root = Path(result.stdout.strip()).resolve()
    try:
        relative = target.resolve().relative_to(root).as_posix()
    except ValueError:
        return None
    return root, relative


def committed_snapshot(target: Path, destination: Path) -> tuple[Path | None, bool]:
    context = git_context(target)
    if context is None:
        return None, False
    repo, relative = context
    exists = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"HEAD:{relative}"],
        capture_output=True,
    )
    if exists.returncode != 0:
        return None, False
    status = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain=v1", "--untracked-files=all", "--", relative],
        capture_output=True,
        text=True,
    )
    locally_edited = bool(status.stdout.strip())
    listed = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", "--name-only", "HEAD", "--", relative],
        capture_output=True,
        check=True,
    ).stdout.split(b"\0")
    destination.mkdir(parents=True)
    prefix = relative.rstrip("/") + "/"
    for raw in listed:
        if not raw:
            continue
        full = raw.decode("utf-8", "surrogateescape")
        if not full.startswith(prefix):
            continue
        rel = full.removeprefix(prefix)
        blob = subprocess.run(
            ["git", "-C", str(repo), "show", f"HEAD:{full}"],
            capture_output=True,
            check=True,
        ).stdout
        path = destination.joinpath(*PurePosixPath(rel).parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    return destination, locally_edited


def vendor_map(root: Path) -> dict[str, Path]:
    urls = vendor_urls(root / "support.js")
    return {
        url: root / "vendor" / Path(urllib.parse.urlsplit(url).path).name
        for url in urls.values()
    }


def changed_pages(previous: Path, current: Path) -> list[str]:
    old = {path.relative_to(previous).as_posix(): path for path in previous.rglob("*.dc.html")}
    new = {path.relative_to(current).as_posix(): path for path in current.rglob("*.dc.html")}
    changed = []
    for name in sorted(set(old) | set(new)):
        if name not in old or name not in new or old[name].read_bytes() != new[name].read_bytes():
            changed.append(name)
    return changed


def contract_row_ids(path: Path | None) -> set[str]:
    if path is None:
        return set()
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise PullRefused(
            f"screen contract cannot be read: {path} ({type(exc).__name__}).",
            "Contract-referenced copy cannot be classified without its row ids.",
            "Pass a readable screen-contract.yaml to --contract and rerun.",
        ) from exc
    rows = doc.get("rows") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return set()
    return {
        str(row["id"])
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }


def display_text(audit: RenderAudit, data_id: str) -> str | None:
    values = audit.text_by_id.get(data_id)
    if not values:
        return None
    return " | ".join(values)


def write_pull_report(
    package: HandoffPackage,
    audit: RenderAudit,
    previous: Path | None,
    previous_audit: RenderAudit | None,
    locally_edited: bool,
    state_list_given: bool,
    contract: Path | None,
) -> None:
    selectors = selector_findings(package.root)
    current_scenes, excluded, no_scene = page_inventory(package.root)
    lines = ["# Pull report", "", "## 设计检查", ""]
    for finding in selectors:
        lines.append(f"- 编辑器点不中的选择器：{finding}")
    for scene in audit.empty_scenes:
        lines.append(f"- 渲染为空：`{scene}`")
    for scene, message in audit.console_errors:
        lines.append(f"- 控制台报错：`{scene}` — {message}")
    if not selectors and not audit.empty_scenes and not audit.console_errors:
        lines.append("- 未发现设计检查问题。")

    lines.extend(["", "## 覆盖", ""])
    if not state_list_given:
        lines.append("- state list 未给出，未核对。")
    else:
        regions = state_list_regions(package.state_list)
        components = {
            PurePosixPath(page).name.removesuffix(".dc.html").removeprefix("Component · "): values
            for page, values in current_scenes.items()
            if PurePosixPath(page).name.startswith("Component · ")
        }
        for region, states in regions.items():
            if region not in components:
                lines.append(f"- state list 区域找不到同名页：`{region}`")
                continue
            for state in states:
                if state not in components[region]:
                    lines.append(f"- state list 状态缺失：`{region}` 的 `{state}` 不在该页 `scene` prop。")
        if not regions:
            lines.append("- state list 的 `## State list` 下没有可核对的区域。")
    for scene, label in audit.text_without_id:
        lines.append(f"- 带文字但没有 `data-ui` id：`{scene}` — {label}")
    for scene, label in audit.controls_without_id:
        lines.append(f"- 可点或可输入却没有 `data-ui` id：`{scene}` — {label}")
    for page in no_scene:
        lines.append(f"- 没有 `scene` prop 的页面：`{page}`")
    for page, values in sorted(excluded.items()):
        for value in sorted(values):
            lines.append(f"- `out_of_scope`：`{page}` 的 `{value}`")

    lines.extend(["", "## 改动分类", ""])
    if previous is None or previous_audit is None:
        lines.append("- 分类：首次")
        lines.append("- 没有上一次提交的 handoff package 可比较。")
    else:
        old_scenes, _old_excluded, _old_no_scene = page_inventory(previous)
        pages = changed_pages(previous, package.root)
        added_ids = sorted(audit.data_ui_ids - previous_audit.data_ui_ids)
        removed_ids = sorted(previous_audit.data_ui_ids - audit.data_ui_ids)
        scene_changes = []
        for page in sorted(set(old_scenes) | set(current_scenes)):
            added = sorted(current_scenes.get(page, set()) - old_scenes.get(page, set()))
            removed = sorted(old_scenes.get(page, set()) - current_scenes.get(page, set()))
            if added or removed:
                scene_changes.append((page, added, removed))
        copy_changes = []
        for data_id in sorted(contract_row_ids(contract)):
            old_text = display_text(previous_audit, data_id)
            new_text = display_text(audit, data_id)
            if old_text != new_text:
                copy_changes.append((data_id, old_text, new_text))
        controls_or_flow = bool(
            added_ids or removed_ids or scene_changes
            or set(path.relative_to(previous).as_posix() for path in previous.rglob("*.dc.html"))
            != set(path.relative_to(package.root).as_posix() for path in package.root.rglob("*.dc.html"))
            or copy_changes
        )
        category = "增删控件或改流转" if controls_or_flow else "只改外观或文案"
        lines.append(f"- 分类：{category}")
        lines.append("- design page：" + ("、".join(f"`{page}`" for page in pages) if pages else "无变化"))
        lines.append("- `data-ui` id 新增：" + ("、".join(f"`{item}`" for item in added_ids) if added_ids else "无"))
        lines.append("- `data-ui` id 删除：" + ("、".join(f"`{item}`" for item in removed_ids) if removed_ids else "无"))
        for page, added, removed in scene_changes:
            lines.append(
                f"- `scene` 取值变化：`{page}`；新增 {', '.join(added) or '无'}；删除 {', '.join(removed) or '无'}。"
            )
        for data_id, old, new in copy_changes:
            lines.append(f"- 合同行引用的文字变化：`{data_id}`：`{old or '(无)'}` → `{new or '(无)'}`")

    lines.extend(["", "## 本地改过的说明", ""])
    if previous is None:
        lines.append("- 没有上一次提交，未作本地改动比较。")
    elif locally_edited:
        lines.append("- pull 前 handoff package 有本地改动；pull 仍已完成。")
    else:
        lines.append("- pull 前 handoff package 与上次提交一致。")
    lines.append("")
    (package.root / "pull-report.md").write_text("\n".join(lines), encoding="utf-8")


def previous_paths(target: Path) -> set[str]:
    path = target / "design-manifest.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    rows = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return set()
    return {
        str(row["path"])
        for row in rows
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }


def prepare_staging(
    target: Path, staged: Path, files: list[ManifestFile],
) -> str:
    state_list = state_list_section(target / "README.md")
    old_paths = previous_paths(target)
    if target.exists():
        if not target.is_dir():
            raise PullRefused(
                f"handoff target is not a directory: {target}.",
                "The pull cannot preserve files beside the generated package.",
                "Move that file aside, create a directory target, and rerun.",
            )
        shutil.copytree(target, staged)
    else:
        staged.mkdir()

    current = {entry.path for entry in files if not handoff_path(entry.path)}
    for stale in old_paths - current:
        try:
            path = staged.joinpath(*PurePosixPath(safe_path(stale)).parts)
        except PullRefused:
            continue
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
    vendor = staged / "vendor"
    if vendor.is_dir():
        shutil.rmtree(vendor)
    elif vendor.exists():
        vendor.unlink()
    return state_list


def install(staged: Path, target: Path) -> None:
    backup = None
    if target.exists():
        backup = Path(tempfile.mkdtemp(prefix=f".{target.name}.before-pull-", dir=target.parent))
        backup.rmdir()
        os.replace(target, backup)
    try:
        os.replace(staged, target)
    except Exception:
        if backup is not None and backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    if backup is not None:
        try:
            if backup.is_dir():
                shutil.rmtree(backup)
            else:
                backup.unlink()
        except OSError as exc:
            print(
                f"WARNING: installed the handoff package but could not remove {backup} "
                f"({type(exc).__name__}).",
                file=sys.stderr,
            )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("target", nargs="?")
    parser.add_argument("--reread")
    parser.add_argument("--tools")
    parser.add_argument("--state-list")
    parser.add_argument("--contract")
    try:
        args, unknown = parser.parse_known_args(argv)
    except SystemExit as exc:
        raise PullRefused(
            "pull_design.py arguments could not be parsed.",
            "The command shape is fixed.",
            "Run: pull_design.py <manifest.json> <handoff dir> [--reread <dir>] "
            "[--tools <dir>] [--state-list <README.md>] [--contract <screen-contract.yaml>].",
        ) from exc
    if unknown or not args.manifest or not args.target:
        raise PullRefused(
            f"pull_design.py received {len(argv)} arguments.",
            "The command needs a manifest and a handoff directory.",
            "Run: pull_design.py <manifest.json> <handoff dir> [--reread <dir>] "
            "[--tools <dir>] [--state-list <README.md>] [--contract <screen-contract.yaml>].",
        )
    return args


def run(args: argparse.Namespace) -> None:
    preview = os.environ.get("MMW_DESIGN_PREVIEW_URL")
    if not preview:
        raise PullRefused(
            "MMW_DESIGN_PREVIEW_URL is not set.",
            "The pull has no short-lived Claude Design preview address.",
            "Set MMW_DESIGN_PREVIEW_URL from render_preview serve_url and rerun.",
        )
    manifest = Path(args.manifest)
    target = Path(args.target)
    reread = Path(args.reread) if args.reread else None
    tools = Path(args.tools) if args.tools else None
    project = project_id_from_preview(preview)
    files = load_manifest(manifest)
    requested_state_list = Path(args.state_list) if args.state_list else None
    requested_section = state_list_section(requested_state_list) if requested_state_list else ""
    contract = Path(args.contract) if args.contract else None
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{target.name}.pull-", dir=target.parent) as temp:
        temp_root = Path(temp)
        previous, locally_edited = committed_snapshot(target, temp_root / "previous")
        staged = temp_root / "package"
        preserved_state_list = prepare_staging(target, staged, files)
        state_list = requested_section if requested_state_list is not None else preserved_state_list
        write_project_files(files, preview, reread, target, staged)
        vendor = pull_vendor(staged)
        package = scenes_from_pages(staged, state_list)
        audit = render_scenes(package, vendor, tools)
        previous_audit = None
        if previous is not None:
            previous_package = scenes_from_pages(previous)
            previous_audit = render_scenes(previous_package, vendor_map(previous), tools)
        (staged / "scenes.json").write_text(
            json.dumps(package.scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (staged / "design-manifest.json").write_text(
            json.dumps(manifest_for_package(project, files), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_readme(package, project, audit.rendered)
        write_pull_report(
            package,
            audit,
            previous,
            previous_audit,
            locally_edited,
            requested_state_list is not None,
            contract,
        )
        install(staged, target)
    print(f"pulled {len(files)} files and rendered {audit.rendered} scenes")


def main() -> int:
    tools = None
    try:
        args = parse_args(sys.argv[1:])
        tools = Path(args.tools) if args.tools else None
        run(args)
        return 0
    except PullRefused as exc:
        print(refusal_text(exc.what, exc.why, exc.next_step, tools), file=sys.stderr)
        return exc.code
    except Exception as exc:
        print(refusal_text(
            f"pull_design.py failed ({type(exc).__name__}).",
            "The handoff package could not be completed atomically.",
            "Inspect the target, fix the reported local failure, and rerun.",
            tools,
        ), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
