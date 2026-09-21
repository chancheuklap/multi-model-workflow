#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58"]
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
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


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
    pages: list[PageInfo]
    state_list: str = ""


@dataclass(frozen=True)
class PageInfo:
    path: str
    name: str
    scene_values: tuple[str, ...] | None
    out_of_scope: frozenset[str]
    preview: dict | None


@dataclass
class RenderAudit:
    rendered: int
    empty_scenes: list[str]
    console_errors: list[tuple[str, str]]
    data_ui_ids: set[str]
    text_by_id: dict[str, list[str]]
    scene_text_by_id: dict[str, dict[str, list[str]]]
    text_without_id: list[tuple[str, str]]
    controls_without_id: list[tuple[str, str]]


@dataclass(frozen=True)
class SelectorAudit:
    checked: bool
    findings: tuple[str, ...]
    issue: str | None = None


@dataclass(frozen=True)
class StateListInput:
    provided: bool
    section: str = ""
    issue: str | None = None


@dataclass(frozen=True)
class ContractReference:
    row_id: str
    data_id: str
    scenes: tuple[str, ...]


@dataclass(frozen=True)
class ContractInput:
    provided: bool
    references: tuple[ContractReference, ...] = ()
    issue: str | None = None


@dataclass
class PreviousPackage:
    root: Path
    locally_edited: bool
    pages: list[PageInfo] | None
    audit: RenderAudit | None
    issue: str | None = None


class PullRefused(Exception):
    def __init__(self, what: str, why: str, next_step: str, code: int = 2,
                 paths: list[str] | None = None):
        super().__init__(what)
        self.what = what
        self.why = why
        self.next_step = next_step
        self.code = code
        # Printed whole, one per line, above the refusal: the refusal line is trimmed
        # to a fixed length and a list inside it would lose its tail.
        self.paths = paths or []


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


# Files Claude Design writes for itself and rewrites on its own: `.thumbnail` is the
# project card image, regenerated after page edits (seen 2026-09-21: 5357 bytes in
# list_files, 11128 when downloaded minutes later). Nothing downstream reads them.
NOT_PULLED = {".thumbnail"}


def handoff_path(path: str) -> bool:
    return path in NOT_PULLED or any(
        part.startswith("design_handoff_") for part in PurePosixPath(path).parts
    )


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


# A connection error is retried; an HTTP status is an answer and is not. One pull
# downloads about two hundred files, and on 2026-09-21 one of them failed once with
# URLError and succeeded on the next run.
FETCH_ATTEMPTS = 3


def fetch(url: str, attempts: int = FETCH_ATTEMPTS, pause: float = 1.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "mmw-pull-design/1"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            raise DownloadFailed(f"HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            if attempt == attempts:
                raise DownloadFailed(type(exc).__name__) from exc
            time.sleep(pause * attempt)
    raise AssertionError("unreachable")


HEAD = re.compile(br"<head\b[^>]*>", re.IGNORECASE)
INJECTED_TAG = re.compile(
    br"<(style|script)\b(?=[^>]*\bdata-omelette-injected\b)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)


def strip_injected_head(raw: bytes, expected_size: int | None = None) -> bytes:
    """Remove the preview server's injected `<style>`/`<script>` right after `<head>`.

    Measured 2026-09-21 on a live project, the injection is `\n<style …></style><script
    …></script>\n`: its closing newline stays behind when the tags are removed, and
    beside a page's own newline after `<head>` the two cannot be told apart by bytes
    alone. When removing the tags leaves exactly one byte more than list_files
    reported and the byte after `<head>` is a newline, that newline is removed too.
    """
    stripped = _strip_injected_tags(raw)
    if (
        expected_size is not None
        and stripped is not raw
        and len(stripped) == expected_size + 1
    ):
        head = HEAD.search(stripped)
        if head is not None and stripped[head.end():head.end() + 1] == b"\n":
            return stripped[:head.end()] + stripped[head.end() + 1:]
    return stripped


def _strip_injected_tags(raw: bytes) -> bytes:
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
            body = strip_injected_head(body, entry.size)
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
        raise PullRefused(
            f"{len(needs_reread)} text files need rereading (listed above).",
            "Their downloaded bytes do not match the list_files sizes.",
            "Read those paths with mcp__claude-design__read_file into one directory, "
            "then rerun with --reread <dir>.",
            code=1,
            paths=needs_reread,
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


def design_pages(root: Path) -> list[PageInfo]:
    pages = []
    for page in sorted(root.rglob("*.dc.html")):
        rel = page.relative_to(root).as_posix()
        filename = PurePosixPath(rel).name
        if filename.casefold() == "overview.dc.html":
            continue
        props = page_props(page)
        scene = props.get("scene")
        options = scene.get("options") if isinstance(scene, dict) else None
        if (
            not isinstance(scene, dict)
            or scene.get("editor") != "enum"
            or not isinstance(options, list)
        ):
            values = None
            excluded = frozenset()
        else:
            values = tuple(str(value) for value in options)
            excluded = frozenset(str(value) for value in (scene.get("out_of_scope") or []))
        pages.append(PageInfo(
            path=rel,
            name=filename.removesuffix(".dc.html"),
            scene_values=values,
            out_of_scope=excluded,
            preview=props.get("$preview") if isinstance(props.get("$preview"), dict) else None,
        ))
    return pages


def scenes_from_pages(
    staged: Path, state_list: str = "", pages: list[PageInfo] | None = None,
) -> HandoffPackage:
    scenes = []
    sizes = {}
    pages = pages if pages is not None else design_pages(staged)
    for page in pages:
        if page.scene_values is None:
            continue
        preview = page.preview
        if not isinstance(preview, dict):
            raise PullRefused(
                f"{page.path} has scenes but no $preview size.",
                "The offline render needs the design page's declared viewport.",
                "Add $preview.width and $preview.height to data-props, then rerun.",
            )
        try:
            width, height = int(preview["width"]), int(preview["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise PullRefused(
                f"{page.path} has an invalid $preview size.",
                "The offline render needs positive integer width and height.",
                "Fix $preview.width and $preview.height, then rerun.",
            ) from exc
        if width < 1 or height < 1:
            raise PullRefused(
                f"{page.path} has an invalid $preview size {width}x{height}.",
                "The offline render needs positive width and height.",
                "Fix the $preview size, then rerun.",
            )
        sizes[page.path] = (width, height)
        for value in page.scene_values:
            if value in page.out_of_scope:
                continue
            scene_name = f"{page.name}.{value}"
            if "/" in scene_name:
                raise PullRefused(
                    f"scene name contains '/': {scene_name}.",
                    "Scene wrapper URLs require names without path separators.",
                    "Rename that page or scene option in Claude Design, then rerun.",
                )
            scenes.append({"name": scene_name, "page": page.path, "props": {"scene": value}})
    return HandoffPackage(staged, scenes, sizes, pages, state_list)


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


def _display_parts(value: object) -> list[str]:
    if isinstance(value, dict):
        parts = []
        if value.get("_text") not in (None, ""):
            parts.append(str(value["_text"]))
        for key, child in value.items():
            if key != "_text":
                parts.extend(_display_parts(child))
        return parts
    if isinstance(value, list):
        parts = []
        for child in value:
            parts.extend(_display_parts(child))
        return parts
    return [] if value in (None, "") else [str(value)]


def _scene_ui_values(data: dict) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for data_id, child in node.items():
                if data_id == "_text":
                    continue
                rendered = " ".join(_display_parts(child)).strip()
                values.setdefault(str(data_id), [])
                if rendered and rendered not in values[str(data_id)]:
                    values[str(data_id)].append(rendered)
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(data)
    return values


def scene_data_audit(scenes: list[dict]) -> tuple[set[str], dict[str, list[str]], dict[str, dict[str, list[str]]]]:
    data_ui_ids: set[str] = set()
    text_by_id: dict[str, list[str]] = {}
    by_scene: dict[str, dict[str, list[str]]] = {}
    for scene in scenes:
        data = scene.get("data")
        if not isinstance(data, dict):
            continue
        values = _scene_ui_values(data)
        name = str(scene.get("name") or "")
        by_scene[name] = values
        for data_id, texts in values.items():
            data_ui_ids.add(data_id)
            text_by_id.setdefault(data_id, [])
            for text in texts:
                if text not in text_by_id[data_id]:
                    text_by_id[data_id].append(text)
    return data_ui_ids, text_by_id, by_scene


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
                empty_scenes: list[str] = []
                console_errors: list[tuple[str, str]] = []
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
                    ui_values = dr.read_ui_values(page, "#dc-root")
                    scene["data"] = dr.nest_ui_values(ui_values)
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
                          const textMissing = [];
                          const controlsMissing = [];
                          for (const el of rows) {
                            const id = el.getAttribute('data-ui');
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
                          return {textMissing, controlsMissing};
                        }
                    """)
                    for label in audit["textMissing"]:
                        row = (scene["name"], label)
                        if row not in text_without_id:
                            text_without_id.append(row)
                    for label in audit["controlsMissing"]:
                        row = (scene["name"], label)
                        if row not in controls_without_id:
                            controls_without_id.append(row)
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
    data_ui_ids, text_by_id, scene_text_by_id = scene_data_audit(package.scenes)
    failed_scenes = set(empty_scenes) | {scene for scene, _message in console_errors if scene}
    return RenderAudit(
        rendered=len(package.scenes) - len(failed_scenes),
        empty_scenes=empty_scenes,
        console_errors=console_errors,
        data_ui_ids=data_ui_ids,
        text_by_id=text_by_id,
        scene_text_by_id=scene_text_by_id,
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


def read_state_list_input(path: Path | None) -> StateListInput:
    if path is None:
        return StateListInput(provided=False)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return StateListInput(provided=True, issue="state list 无法读取，未核对。")
    match = re.search(r"(?ms)^## State list\s*\n.*?(?=^## |\Z)", text)
    if not match:
        return StateListInput(provided=True, issue="state list 没有 `## State list`，未核对。")
    return StateListInput(provided=True, section=match.group(0).rstrip())


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
                # The name ends at the first space, colon (ASCII or full-width `：`),
                # or spaced dash; state lists written in Chinese use `name：description`.
                value = re.split(r"\s+(?:—|–|-)\s+|\s*[:：]\s*|\s+", raw, maxsplit=1)[0]
            if value:
                regions[current].append(value)
    return regions


def page_inventory(
    pages: list[PageInfo],
) -> tuple[dict[str, set[str]], dict[str, set[str]], list[str]]:
    scene_values = {
        page.path: set(page.scene_values)
        for page in pages
        if page.scene_values is not None
    }
    excluded_values = {
        page.path: set(page.out_of_scope)
        for page in pages
        if page.scene_values is not None
    }
    # Pages without a `Component · ` or `App · ` prefix are notes or explorations,
    # never accepted, so a missing `scene` there is not reported.
    no_scene = [
        page.path for page in pages
        if page.scene_values is None
        and PurePosixPath(page.path).name.startswith(("Component · ", "App · "))
    ]
    return scene_values, excluded_values, no_scene


STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)


def selector_audit(root: Path) -> SelectorAudit:
    """Selectors the Claude Design editor cannot reach, in the CSS the pages own: each
    `.css` outside `_ds/` and each page's `<style>` blocks. The bound design system
    under `_ds/` is copied from its source and not edited in the editor, so it is
    not audited."""
    sources: list[tuple[str, str]] = []
    try:
        for path in sorted(root.rglob("*.css")):
            rel = path.relative_to(root)
            if rel.parts[0] == "_ds":
                continue
            sources.append((rel.as_posix(), path.read_text(encoding="utf-8")))
        for path in sorted(root.glob("*.dc.html")):
            blocks = STYLE_BLOCK.findall(path.read_text(encoding="utf-8"))
            if blocks:
                sources.append((f"{path.name} <style>", "\n".join(blocks)))
    except (OSError, UnicodeError) as exc:
        return SelectorAudit(
            False, (), f"选择器检查未完成：{type(exc).__name__}，未核对。",
        )
    if not sources:
        return SelectorAudit(False, (), "页面没有自己的样式（`_ds/` 以外的 `.css` 或 `<style>`），选择器未核对。")
    check = Path(__file__).with_name("check_editable_selectors.py")
    try:
        checker = _load_module("_pull_design_selectors", check)
    except (OSError, ImportError) as exc:
        return SelectorAudit(
            False, (), f"选择器检查未完成：{type(exc).__name__}，未核对。",
        )
    findings = []
    for name, css in sources:
        for selector in checker.selectors(css):
            reason = checker.why(selector)
            if reason:
                findings.append(f"{name}: {selector}  ({reason})")
    return SelectorAudit(True, tuple(findings))


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


def changed_pages(previous: Path, current: Path) -> tuple[list[str], bool]:
    old = {path.relative_to(previous).as_posix(): path for path in previous.rglob("*.dc.html")}
    new = {path.relative_to(current).as_posix(): path for path in current.rglob("*.dc.html")}
    changed = []
    for name in sorted(set(old) | set(new)):
        if name not in old or name not in new or old[name].read_bytes() != new[name].read_bytes():
            changed.append(name)
    return changed, set(old) != set(new)


def contract_input(path: Path | None, tools: Path | None) -> ContractInput:
    if path is None:
        return ContractInput(provided=False)
    try:
        doc = load_design_render(tools).load_yaml(path)
    except (OSError, UnicodeError, SystemExit, ValueError) as exc:
        return ContractInput(
            provided=True,
            issue=f"screen contract 无法读取（{type(exc).__name__}），合同行文字未核对。",
        )
    rows = doc.get("rows") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return ContractInput(
            provided=True, issue="screen contract 没有 `rows`，合同行文字未核对。",
        )
    references = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("id"), str):
            continue
        trigger = row.get("trigger")
        if not isinstance(trigger, str) or not trigger.strip():
            continue
        scenes = row.get("scenes")
        references.append(ContractReference(
            row_id=row["id"],
            data_id=trigger.strip(),
            scenes=tuple(str(scene) for scene in scenes) if isinstance(scenes, list) else (),
        ))
    if rows and not references:
        return ContractInput(
            provided=True,
            issue="screen contract 的 `rows` 没有可核对的 `trigger`，合同行文字未核对。",
        )
    return ContractInput(provided=True, references=tuple(references))


def saved_scene_audit(root: Path) -> RenderAudit:
    path = root / "scenes.json"
    try:
        scenes = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"scenes.json {type(exc).__name__}") from exc
    if not isinstance(scenes, list):
        raise ValueError("scenes.json 不是列表")
    data_ui_ids, text_by_id, scene_text_by_id = scene_data_audit(scenes)
    return RenderAudit(
        rendered=len(scenes),
        empty_scenes=[],
        console_errors=[],
        data_ui_ids=data_ui_ids,
        text_by_id=text_by_id,
        scene_text_by_id=scene_text_by_id,
        text_without_id=[],
        controls_without_id=[],
    )


def inspect_previous(root: Path, locally_edited: bool) -> PreviousPackage:
    issues = []
    try:
        pages = design_pages(root)
    except PullRefused as exc:
        pages = None
        issues.append(f"上次提交的 design page 无法读取（{exc.what}），页面与 `scene` 未核对。")
    try:
        audit = saved_scene_audit(root)
    except ValueError as exc:
        audit = None
        issues.append(f"上次提交的 {exc}，`data-ui` 与显示文字未核对。")
    return PreviousPackage(
        root=root,
        locally_edited=locally_edited,
        pages=pages,
        audit=audit,
        issue=" ".join(issues) or None,
    )


def _texts_for(
    audit: RenderAudit, data_id: str, scenes: tuple[str, ...],
) -> list[str]:
    names = scenes or tuple(audit.scene_text_by_id)
    values = []
    for scene in names:
        for value in audit.scene_text_by_id.get(scene, {}).get(data_id, []):
            if value not in values:
                values.append(value)
    return values


def contract_copy_changes(
    contract: ContractInput, previous: RenderAudit, current: RenderAudit,
) -> tuple[list[tuple[str, str, str]], list[str]]:
    changes = []
    unmatched = []
    for reference in contract.references:
        old_values = _texts_for(previous, reference.data_id, reference.scenes)
        if not old_values:
            unmatched.append(reference.row_id)
            continue
        new_values = _texts_for(current, reference.data_id, reference.scenes)
        if old_values != new_values:
            changes.append((
                reference.row_id,
                " | ".join(old_values) or "(无)",
                " | ".join(new_values) or "(无)",
            ))
    return changes, unmatched


def design_check_lines(package: HandoffPackage, audit: RenderAudit) -> list[str]:
    selectors = selector_audit(package.root)
    lines = []
    if selectors.issue:
        lines.append(f"- {selectors.issue}")
    for finding in selectors.findings:
        lines.append(f"- 编辑器点不中的选择器：{finding}")
    for scene in audit.empty_scenes:
        lines.append(f"- 渲染为空：`{scene}`")
    for scene, message in audit.console_errors:
        lines.append(f"- 控制台报错：`{scene}` — {message}")
    if selectors.checked and not selectors.findings and not audit.empty_scenes and not audit.console_errors:
        lines.append("- 未发现设计检查问题。")
    return lines


def coverage_lines(
    package: HandoffPackage, audit: RenderAudit, state_list: StateListInput,
) -> list[str]:
    current_scenes, excluded, no_scene = page_inventory(package.pages)
    lines = []
    if not state_list.provided:
        lines.append("- state list 未给出，未核对。")
    elif state_list.issue:
        lines.append(f"- {state_list.issue}")
    else:
        regions = state_list_regions(state_list.section)
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
    return lines


def classification_lines(
    package: HandoffPackage,
    audit: RenderAudit,
    previous: PreviousPackage | None,
    contract: ContractInput,
) -> list[str]:
    contract_note = None
    if not contract.provided:
        contract_note = "screen contract 未给出，合同行文字未核对。"
    elif contract.issue:
        contract_note = contract.issue
    if previous is None:
        lines = ["- 分类：首次", "- 没有上一次提交的 handoff package 可比较。"]
        if contract_note:
            lines.append(f"- {contract_note}")
        return lines

    pages, page_structure_changed = changed_pages(previous.root, package.root)
    current_scenes, _excluded, _no_scene = page_inventory(package.pages)
    old_scenes = {}
    if previous.pages is not None:
        old_scenes, _old_excluded, _old_no_scene = page_inventory(previous.pages)
    added_ids = []
    removed_ids = []
    if previous.audit is not None:
        added_ids = sorted(audit.data_ui_ids - previous.audit.data_ui_ids)
        removed_ids = sorted(previous.audit.data_ui_ids - audit.data_ui_ids)
    scene_changes = []
    for page in sorted(set(old_scenes) | set(current_scenes)):
        added = sorted(current_scenes.get(page, set()) - old_scenes.get(page, set()))
        removed = sorted(old_scenes.get(page, set()) - current_scenes.get(page, set()))
        if added or removed:
            scene_changes.append((page, added, removed))
    copy_changes = []
    unmatched = []
    if contract.provided and not contract.issue and previous.audit is not None:
        copy_changes, unmatched = contract_copy_changes(contract, previous.audit, audit)
    comparison_incomplete = previous.audit is None or previous.pages is None
    controls_or_flow = bool(
        comparison_incomplete or added_ids or removed_ids or scene_changes
        or page_structure_changed or copy_changes
    )
    category = "增删控件或改流转" if controls_or_flow else "只改外观或文案"
    lines = [
        f"- 分类：{category}",
        "- design page：" + ("、".join(f"`{page}`" for page in pages) if pages else "无变化"),
        "- `data-ui` id 新增：" + ("、".join(f"`{item}`" for item in added_ids) if added_ids else "无"),
        "- `data-ui` id 删除：" + ("、".join(f"`{item}`" for item in removed_ids) if removed_ids else "无"),
    ]
    if previous.issue:
        lines.append(f"- {previous.issue}")
    if contract_note:
        lines.append(f"- {contract_note}")
    for page, added, removed in scene_changes:
        lines.append(
            f"- `scene` 取值变化：`{page}`；新增 {', '.join(added) or '无'}；删除 {', '.join(removed) or '无'}。"
        )
    for row_id, old, new in copy_changes:
        lines.append(f"- 合同行引用的文字变化：`{row_id}`：`{old}` → `{new}`")
    for row_id in unmatched:
        lines.append(f"- 合同行 `{row_id}` 的 `trigger` 在上次渲染结果中没有文字，未核对。")
    return lines


def local_edit_lines(previous: PreviousPackage | None) -> list[str]:
    if previous is None:
        return ["- 没有上一次提交，未作本地改动比较。"]
    if previous.locally_edited:
        return ["- pull 前 handoff package 有本地改动；pull 仍已完成。"]
    return ["- pull 前 handoff package 与上次提交一致。"]


def write_pull_report(
    package: HandoffPackage,
    audit: RenderAudit,
    previous: PreviousPackage | None,
    state_list: StateListInput,
    contract: ContractInput,
) -> None:
    sections = (
        ("设计检查", design_check_lines(package, audit)),
        ("覆盖", coverage_lines(package, audit, state_list)),
        ("改动分类", classification_lines(package, audit, previous, contract)),
        ("本地改过的说明", local_edit_lines(previous)),
    )
    lines = ["# Pull report"]
    for heading, body in sections:
        lines.extend(["", f"## {heading}", "", *body])
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
    state_list_input = read_state_list_input(requested_state_list)
    contract = contract_input(Path(args.contract) if args.contract else None, tools)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{target.name}.pull-", dir=target.parent) as temp:
        temp_root = Path(temp)
        previous_root, locally_edited = committed_snapshot(target, temp_root / "previous")
        previous = (
            inspect_previous(previous_root, locally_edited)
            if previous_root is not None else None
        )
        staged = temp_root / "package"
        preserved_state_list = prepare_staging(target, staged, files)
        write_project_files(files, preview, reread, target, staged)
        vendor = pull_vendor(staged)
        pages = design_pages(staged)
        package = scenes_from_pages(staged, preserved_state_list, pages)
        audit = render_scenes(package, vendor, tools)
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
            state_list_input,
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
        for path in exc.paths:
            print(path, file=sys.stderr)
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
