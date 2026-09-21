#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58"]
# ///
"""Pull one Claude Design project into a complete handoff package.

Usage: pull_design.py <handoff-dir> --pages <page.dc.html>... [--tools <dir>]
                      [--state-list <README.md>] [--contract <screen-contract.yaml>]
       pull_design.py <list_files.json> <handoff-dir> [the same options]

The pages are the `.dc.html` files at the project root, by name; a saved
`mcp__claude-design__list_files` result may give them instead (its root `.dc.html`
paths are taken, everything else in it is ignored). Every other file is found from
the pages: the files they and their stylesheets reference, then every project file
the offline render requests. The short-lived preview address is read only from
`MMW_DESIGN_PREVIEW_URL`; it is never printed or persisted.
"""

from __future__ import annotations

import argparse
import http.client
import importlib.util
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


VENDOR_CONSTANTS = ("REACT_URL", "REACT_DOM_URL", "BABEL_URL")
# Renders of the whole scene set before the inventory must stop growing. Each render
# after the first exists only because the one before requested a file not yet pulled.
RENDER_ROUNDS = 5
RENDER_REQUEST = "渲染时请求"


@dataclass
class HandoffPackage:
    root: Path
    scenes: list[dict]
    sizes: dict[str, tuple[int, int]]
    pages: list[PageInfo]
    state_list: str = ""
    # Referenced or requested paths the project does not have (HTTP 404), each with
    # the file that referenced it or `RENDER_REQUEST`.
    missing: dict[str, str] = field(default_factory=dict)


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
    def __init__(self, status: str, http_code: int | None = None):
        super().__init__(status)
        self.status = status
        self.http_code = http_code


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
            f"project path is unsafe: {raw!r}.",
            "A project file must be a non-empty project-relative path.",
            "Name the page by its project-relative path and rerun.",
        )
    return pure.as_posix()


def page_name(raw: str) -> str:
    path = safe_path(raw)
    if not path.endswith(".dc.html"):
        raise PullRefused(
            f"{raw!r} is not a design page.",
            "--pages takes the project's `.dc.html` pages by name.",
            "Pass the `.dc.html` names list_files shows at the project root and rerun.",
        )
    return path


def pages_from_list_files(path: Path) -> list[str]:
    """The root `.dc.html` paths of a saved list_files result; nothing else in it is
    read."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PullRefused(
            f"list_files result cannot be read: {path} ({type(exc).__name__}).",
            "The pages to pull are unknown.",
            "Pass the pages with --pages <name>... instead, and rerun.",
        ) from exc
    if isinstance(raw, dict):
        raw = raw.get("files", raw.get("entries"))
    if not isinstance(raw, list):
        raise PullRefused(
            f"{path} is not a list_files array.",
            "The pages to pull are unknown.",
            "Pass the pages with --pages <name>... instead, and rerun.",
        )
    pages = []
    for row in raw:
        if not isinstance(row, dict) or str(row.get("type") or "").lower() == "directory":
            continue
        name = str(row.get("path") or "")
        while name.startswith("./"):
            name = name[2:]
        if name.endswith(".dc.html") and "/" not in name and name not in pages:
            pages.append(name)
    return pages


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


# A connection error or a short read is retried; an HTTP status is an answer and is
# not. On 2026-09-21 one download of about two hundred failed once with URLError and
# succeeded on the next run.
FETCH_ATTEMPTS = 3


def fetch(url: str, attempts: int = FETCH_ATTEMPTS, pause: float = 1.0) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "mmw-pull-design/1"})
    for attempt in range(1, attempts + 1):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            raise DownloadFailed(f"HTTP {exc.code}", exc.code) from exc
        except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError) as exc:
            if attempt == attempts:
                raise DownloadFailed(type(exc).__name__) from exc
            time.sleep(pause * attempt)
    raise AssertionError("unreachable")


HEAD = re.compile(br"<head\b[^>]*>", re.IGNORECASE)
INJECTED_TAG = re.compile(
    br"<(style|script)\b(?=[^>]*\bdata-omelette-injected\b)[^>]*>.*?</\1>",
    re.IGNORECASE | re.DOTALL,
)
INJECTED_MARKER = b"data-omelette-injected"


def strip_injected_head(raw: bytes) -> bytes:
    """Remove the preview server's injected `<style>`/`<script>` right after `<head>`.

    Measured 2026-09-21 on a live project, the injection is `\\n<style …></style><script
    …></script>\\n`, both newlines its own: that exact shape is removed whole. Any other
    run of injected tags after `<head>`, with whitespace between them, is removed up to
    the end of its last tag; whitespace the injection brought and that removal leaves
    behind is not an error.
    """
    head = HEAD.search(raw)
    if head is None:
        return raw
    cursor = head.end()
    if raw[cursor:cursor + 1] == b"\n":
        end = cursor + 1
        tags = 0
        while (tag := INJECTED_TAG.match(raw, end)) is not None:
            end = tag.end()
            tags += 1
        if tags and raw[end:end + 1] == b"\n":
            return raw[:cursor] + raw[end + 1:]
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


# ---------------------------------------------------------------- discovery
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
CSS_URL = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)'"\s]*))\s*\)""", re.I)
CSS_IMPORT = re.compile(r"""@import\s+(?:"([^"]*)"|'([^']*)')""", re.I)
# Attributes that make the browser load a file. `<a href>` is a link, not a load.
LOADING_ATTRS = {"src", "poster", "data", "xlink:href"}
HREF_LOADS = {"link", "use", "image", "feimage"}
IMPORT_TAGS = {"dc-import", "x-import"}


def css_references(text: str) -> list[str]:
    text = CSS_COMMENT.sub("", text)
    refs = [next(g for g in match.groups() if g is not None) for match in CSS_IMPORT.finditer(text)]
    refs += [next(g for g in match.groups() if g is not None) for match in CSS_URL.finditer(text)]
    return refs


class _ReferenceParser(HTMLParser):
    """Relative references a page loads: resource attributes, `srcset`, inline and
    `<style>` CSS, and the page each `dc-import`/`x-import` names."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.refs: list[str] = []
        self.pages: list[str] = []
        self._in_style = False

    def handle_starttag(self, tag, attrs):
        self._in_style = tag == "style"
        for name, value in attrs:
            if value is None:
                continue
            if name in LOADING_ATTRS or (name == "href" and tag in HREF_LOADS):
                self.refs.append(value)
            elif name == "srcset":
                self.refs.extend(
                    part.strip().split()[0] for part in value.split(",") if part.strip()
                )
            elif name == "style":
                self.refs.extend(css_references(value))
            elif name == "name" and tag in IMPORT_TAGS and "{{" not in value:
                self.pages.append(value if value.endswith(".dc.html") else value + ".dc.html")

    def handle_endtag(self, tag):
        if tag == "style":
            self._in_style = False

    def handle_data(self, data):
        if self._in_style:
            self.refs.extend(css_references(data))


def resolve_reference(base: str, raw: str) -> str | None:
    """The project path a reference in `base` points to, or None when it leaves the
    project (another origin, a scheme, a fragment, a template expression)."""
    raw = raw.strip()
    if not raw or raw.startswith("#") or "{{" in raw:
        return None
    parts = urllib.parse.urlsplit(raw)
    if parts.scheme or parts.netloc:
        return None
    path = urllib.parse.unquote(parts.path)
    if not path:
        return None
    joined = path.lstrip("/") if path.startswith("/") else posixpath.join(posixpath.dirname(base), path)
    norm = posixpath.normpath(joined)
    if norm in ("", ".") or norm == ".." or norm.startswith("../"):
        return None
    return norm


def file_references(path: str, body: bytes) -> list[str]:
    lower = path.lower()
    text = body.decode("utf-8", "replace")
    refs: list[str] = []
    if lower.endswith((".html", ".htm")):
        parser = _ReferenceParser()
        parser.feed(text)
        parser.close()
        refs = [ref for raw in parser.refs if (ref := resolve_reference(path, raw))]
        refs += [ref for raw in parser.pages if (ref := resolve_reference("", raw))]
    elif lower.endswith(".css"):
        refs = [ref for raw in css_references(text) if (ref := resolve_reference(path, raw))]
    return refs


@dataclass
class Inventory:
    """The project files pulled so far, found from the pages outward."""
    preview: str
    staged: Path
    pulled: set[str] = field(default_factory=set)
    missing: dict[str, str] = field(default_factory=dict)

    def known(self, path: str) -> bool:
        return path in self.pulled or path in self.missing

    def download(self, path: str) -> bytes:
        body = fetch(preview_file_url(self.preview, path))
        if path.lower().endswith((".html", ".htm")):
            body = strip_injected_head(body)
            if INJECTED_MARKER in body:
                raise PullRefused(
                    f"{INJECTED_MARKER.decode()} is still in the page printed above after "
                    "the preview's injection was removed.",
                    "The preview injects in a shape pull does not know, or the page holds "
                    "that attribute; the bytes would not be the stored page.",
                    "Tell the user which page; the target was not changed.",
                    paths=[path],
                )
        return body

    def pull(self, paths: list[str], referrer: str | None) -> int:
        """Download `paths` and everything they reference, transitively. A path that
        answers 404 is recorded as missing, except a page named on the command line,
        which is refused. Returns how many files were added."""
        added = 0
        queue = [(path, referrer) for path in paths]
        while queue:
            path, source = queue.pop(0)
            if self.known(path):
                continue
            try:
                body = self.download(path)
            except DownloadFailed as exc:
                if exc.http_code == 404 and source is not None:
                    self.missing[path] = source
                    continue
                what = (
                    f"page {path} is not in the project (HTTP 404)."
                    if exc.http_code == 404 else
                    f"download failed for {path} ({exc.status})."
                )
                raise PullRefused(
                    what,
                    "The handoff package would be incomplete.",
                    "Check the page name against list_files, or restore the preview "
                    "download, then rerun; the target was not changed.",
                    paths=[path],
                ) from exc
            dest = self.staged.joinpath(*PurePosixPath(path).parts)
            if dest.is_dir():
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            self.pulled.add(path)
            added += 1
            for ref in file_references(path, body):
                if not self.known(ref):
                    queue.append((ref, path))
        return added


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


class _RootParser(HTMLParser):
    """The page's root: the first element inside `<x-dc>` outside its `<helmet>`."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_xdc = False
        self.in_helmet = False
        self.root: tuple[str, str] | None = None

    def handle_endtag(self, tag: str) -> None:
        if tag == "helmet":
            self.in_helmet = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "x-dc":
            self.in_xdc = True
        elif tag == "helmet":
            self.in_helmet = True
        elif self.in_xdc and not self.in_helmet and self.root is None:
            self.root = (tag, str(dict(attrs).get("data-ui") or "").strip())


def page_root(path: Path) -> tuple[str, str] | None:
    parser = _RootParser()
    try:
        parser.feed(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return None
    return parser.root


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
    requested: set[str] | None = None,
) -> RenderAudit:
    """Render every scene with external requests blocked. Each same-origin path the
    render asks for, other than the scene wrappers, is added to `requested`."""
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

    wrappers = {path.lstrip("/") for path in pages}

    def route_offline(route, request):
        if request.url.startswith(origin):
            if requested is not None:
                path = urllib.parse.unquote(urllib.parse.urlsplit(request.url).path)
                path = posixpath.normpath(path.lstrip("/")) if path.strip("/") else ""
                if path and path not in wrappers and not path.startswith(".."):
                    requested.add(path)
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


def manifest_for_package(project: str, pages: list[str], inventory: Inventory) -> dict:
    """What this pull brought down. The next pull reads `files` to remove what the
    project no longer serves; the re-pull comparison reads the committed package
    itself, not this file."""
    return {
        "project_id": project,
        "pages": pages,
        "files": sorted(inventory.pulled),
        "missing": dict(sorted(inventory.missing.items())),
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
        new_values = _texts_for(current, reference.data_id, reference.scenes)
        if not old_values and not new_values:
            # An icon button or a card whose text sits on child ids has no text of
            # its own to compare; only a control the last render never drew is news.
            if reference.data_id not in previous.data_ui_ids:
                unmatched.append(reference.row_id)
            continue
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
    for path, source in sorted(package.missing.items()):
        by = "渲染时请求" if source == RENDER_REQUEST else f"`{source}` 引用"
        lines.append(f"- 项目里没有的文件：`{path}`（{by}）")
    for scene in audit.empty_scenes:
        lines.append(f"- 渲染为空：`{scene}`")
    for scene, message in audit.console_errors:
        lines.append(f"- 控制台报错：`{scene}` — {message}")
    if (
        selectors.checked and not selectors.findings and not package.missing
        and not audit.empty_scenes and not audit.console_errors
    ):
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
    for page in package.pages:
        if not PurePosixPath(page.path).name.startswith(("Component · ", "App · ")):
            continue
        found = page_root(package.root / page.path)
        if found is not None and not found[1]:
            lines.append(f"- 页面根元素 `<{found[0]}>` 没有 `data-ui` id：`{page.path}`"
                         "（产品 story 的根元素与它按 id 配对）")
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
        lines.append(f"- 合同行 `{row_id}` 的 `trigger` 不在上次渲染结果里，文字未核对。")
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
    """The project files the last pull wrote, from its `design-manifest.json`: `files`
    is a list of paths, or of `{"path": …}` rows in a package pulled before that."""
    path = target / "design-manifest.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return set()
    rows = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return set()
    paths = set()
    for row in rows:
        value = row.get("path") if isinstance(row, dict) else row
        if isinstance(value, str):
            paths.add(value)
    return paths


def prepare_staging(target: Path, staged: Path) -> str:
    """Copy the target to `staged` without the files the last pull wrote, so every
    project file in the result comes from this pull and a file the project no longer
    serves is gone. Files beside the package (a prototype, the state list in
    README.md) stay."""
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

    for stale in old_paths:
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


def render_until_settled(
    inventory: Inventory, vendor: dict[str, Path], state_list: str, tools: Path | None,
) -> tuple[HandoffPackage, RenderAudit]:
    """Render, pull every project file the render requested that is not pulled yet,
    and render again, until a render requests nothing new."""
    for _round in range(RENDER_ROUNDS):
        package = scenes_from_pages(inventory.staged, state_list, design_pages(inventory.staged))
        requested: set[str] = set()
        audit = render_scenes(package, vendor, tools, requested)
        new = sorted(path for path in requested if not inventory.known(path))
        if not new or not inventory.pull(new, RENDER_REQUEST):
            package.missing = dict(inventory.missing)
            return package, audit
    raise PullRefused(
        f"the offline render still requested new files after {RENDER_ROUNDS} renders "
        "(the last ones are printed above).",
        "The file set did not settle, so the package cannot be shown complete.",
        "Tell the user which files; the target was not changed.",
        paths=new,
    )


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


USAGE = (
    "Run: pull_design.py <handoff dir> --pages <page.dc.html>... [--tools <dir>] "
    "[--state-list <README.md>] [--contract <screen-contract.yaml>]."
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("positional", nargs="*")
    parser.add_argument("--pages", nargs="+")
    parser.add_argument("--tools")
    parser.add_argument("--state-list")
    parser.add_argument("--contract")
    try:
        args, unknown = parser.parse_known_args(argv)
    except SystemExit as exc:
        raise PullRefused(
            "pull_design.py arguments could not be parsed.",
            "The command shape is fixed.",
            USAGE,
        ) from exc
    expected = 1 if args.pages else 2
    if unknown or len(args.positional) != expected:
        raise PullRefused(
            f"pull_design.py received {len(argv)} arguments.",
            "It needs a handoff directory and the pages (or a list_files JSON before it).",
            USAGE,
        )
    args.list_files = None if args.pages else args.positional[0]
    args.target = args.positional[-1]
    return args


def run(args: argparse.Namespace) -> None:
    preview = os.environ.get("MMW_DESIGN_PREVIEW_URL")
    if not preview:
        raise PullRefused(
            "MMW_DESIGN_PREVIEW_URL is not set.",
            "The pull has no short-lived Claude Design preview address.",
            "Set MMW_DESIGN_PREVIEW_URL from render_preview serve_url and rerun.",
        )
    target = Path(args.target)
    tools = Path(args.tools) if args.tools else None
    project = project_id_from_preview(preview)
    names = args.pages if args.pages else pages_from_list_files(Path(args.list_files))
    pages = list(dict.fromkeys(page_name(name) for name in names))
    if not pages:
        raise PullRefused(
            f"{args.list_files} lists 0 `.dc.html` pages at the project root.",
            "A pull starts from the project's pages.",
            "Pass the pages with --pages <name>... and rerun.",
        )
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
        preserved_state_list = prepare_staging(target, staged)
        inventory = Inventory(preview, staged)
        inventory.pull(pages, None)
        vendor = pull_vendor(staged)
        package, audit = render_until_settled(inventory, vendor, preserved_state_list, tools)
        (staged / "scenes.json").write_text(
            json.dumps(package.scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (staged / "design-manifest.json").write_text(
            json.dumps(manifest_for_package(project, pages, inventory), ensure_ascii=False, indent=2)
            + "\n",
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
    print(f"pulled {len(inventory.pulled)} files and rendered {audit.rendered} scenes")


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
