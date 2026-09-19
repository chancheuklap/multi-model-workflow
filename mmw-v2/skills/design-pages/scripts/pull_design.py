#!/usr/bin/env python3
"""Pull one Claude Design project into a complete handoff package.

Usage: pull_design.py <manifest.json> <handoff-dir> [--reread <dir>] [--tools <dir>]

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
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
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
    ".css", ".csv", ".html", ".js", ".json", ".md", ".mjs", ".svg",
    ".txt", ".xml", ".yaml", ".yml",
}
VENDOR_CONSTANTS = ("REACT_URL", "REACT_DOM_URL", "BABEL_URL")


@dataclass(frozen=True)
class ManifestFile:
    path: str
    size: int
    etag: str | None


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


def refusal_text(what: str, why: str, next_step: str) -> str:
    refusal = _load_module(
        "_pull_design_refusal",
        Path(__file__).resolve().parents[2] / "ui-acceptance" / "scripts" / "refusal.py",
    )
    return refusal.refusal(what, why, next_step)


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


def manifest_payload(doc: object) -> dict:
    if not isinstance(doc, dict):
        raise PullRefused(
            "the manifest root is not an object.",
            "The command needs the JSON result of list_files.",
            "Save the list_files result as JSON and rerun.",
        )
    structured = doc.get("structuredContent")
    if isinstance(structured, dict):
        return structured
    return doc


def load_manifest(path: Path) -> tuple[str, list[ManifestFile], dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PullRefused(
            f"manifest cannot be read: {path} ({type(exc).__name__}).",
            "The pull has no trustworthy file inventory.",
            "Save a readable list_files JSON result at that path and rerun.",
        ) from exc
    doc = manifest_payload(raw)
    project = doc.get("project_id") or doc.get("projectId") or doc.get("project")
    if isinstance(project, dict):
        project = project.get("id") or project.get("project_id")
    if not project:
        raise PullRefused(
            f"manifest {path} has no project id.",
            "README.md must identify the Claude Design project that was pulled.",
            "Save the list_files result with its project_id and rerun.",
        )
    rows = doc.get("files") or doc.get("entries") or doc.get("items")
    if not isinstance(rows, list):
        raise PullRefused(
            f"manifest {path} has no file list.",
            "The pull cannot know which project files must arrive.",
            "Run list_files with depth -1, save its JSON result, and rerun.",
        )
    files = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        kind = str(row.get("type") or row.get("kind") or "").lower()
        if kind in {"directory", "dir", "folder"}:
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
            safe_path(row.get("path") or row.get("name")),
            size,
            str(row["etag"]) if row.get("etag") is not None else None,
        ))
    if not files:
        raise PullRefused(
            f"manifest {path} contains 0 files.",
            "A silent empty pull cannot produce a handoff package.",
            "Run list_files with depth -1 for the intended project and rerun.",
        )
    return str(project), files, raw


def handoff_path(path: str) -> bool:
    return any(part.startswith("design_handoff_") for part in PurePosixPath(path).parts)


def preview_file_url(preview: str, path: str) -> str:
    parsed = urllib.parse.urlsplit(preview)
    base = parsed.path if parsed.path.endswith("/") else parsed.path + "/"
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, base + quoted, parsed.query, "")
    )


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
                if entry.size <= READ_FILE_LIMIT and not is_media(entry.path):
                    needs_reread.append(entry.path)
                    continue
                raise PullRefused(
                    f"download failed for {entry.path} ({exc.status}).",
                    f"The {entry.size}-byte file has no faithful read_file fallback.",
                    "Restore the preview download, then rerun; the target was not changed.",
                ) from exc
        if entry.path.lower().endswith((".html", ".dc.html")):
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


def scenes_from_pages(staged: Path) -> tuple[list[dict], dict[str, tuple[int, int]]]:
    scenes = []
    sizes = {}
    for page in sorted(staged.rglob("*.dc.html")):
        rel = page.relative_to(staged).as_posix()
        name = rel.removesuffix(".dc.html")
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
    return scenes, sizes


def load_design_render(tools: Path | None):
    scripts = tools or (
        Path(__file__).resolve().parents[2] / "ui-acceptance" / "scripts"
    )
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
    staged: Path, scenes: list[dict], sizes: dict[str, tuple[int, int]],
    vendor: dict[str, Path], tools: Path | None,
) -> None:
    dr = load_design_render(tools)
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise PullRefused(
            "playwright is not importable.",
            "The offline render check cannot start Chromium.",
            "Run pull_design.py in the design-pages test runtime with Playwright, then rerun.",
        ) from exc
    pages = {
        dr.wrapper_path(scene["name"]): dr.wrapper_page(
            dr.component_of(scene["page"]), scene["props"]
        )
        for scene in scenes
    }
    server, port = dr.serve_baseline(staged, pages)
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
                for scene in scenes:
                    dr.resize(page, sizes[scene["page"]])
                    dr.navigate(page, f"{origin}{dr.wrapper_path(scene['name'])}")
                    dr.wait_for_mount(page, "#dc-root")
                    root = page.locator("#dc-root").first
                    if not root.inner_html().strip():
                        raise PullRefused(
                            f"offline render produced an empty root for {scene['name']}.",
                            "A handoff scene that renders nothing is not a usable baseline.",
                            "Fix that design page and rerun; the target was not changed.",
                        )
                    scene["data"] = dr.nest_ui_values(dr.read_ui_values(page, "#dc-root"))
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


def manifest_for_package(project: str, files: list[ManifestFile]) -> dict:
    return {
        "project_id": project,
        "files": [
            {"path": row.path, "size": row.size, "etag": row.etag}
            for row in files
        ],
    }


def write_readme(
    staged: Path, project: str, scenes: list[dict], sizes: dict[str, tuple[int, int]],
) -> None:
    lines = [
        "# Claude Design handoff package",
        "",
        "## Viewport and size source",
        "",
    ]
    for page, (width, height) in sorted(sizes.items()):
        lines.append(f"- `{page}`: `{width}x{height}` from `$preview.width` and `$preview.height`.")
    if not sizes:
        lines.append("- No page declared a `scene` prop; no scene viewport was required.")
    lines.extend([
        "",
        "## Offline render check",
        "",
        f"- Passed: {len(scenes)}/{len(scenes)} scenes rendered with external network requests blocked.",
        "",
        "## Pull provenance",
        "",
        f"- Pulled at: `{datetime.now(timezone.utc).isoformat(timespec='seconds')}`.",
        f"- Claude Design project id: `{project}`.",
        "",
    ])
    (staged / "README.md").write_text("\n".join(lines), encoding="utf-8")


def install(staged: Path, target: Path) -> None:
    backup = None
    if target.exists():
        backup = target.parent / f".{target.name}.before-pull-{uuid.uuid4().hex}"
        os.replace(target, backup)
    try:
        os.replace(staged, target)
    except Exception:
        if backup is not None and backup.exists() and not target.exists():
            os.replace(backup, target)
        raise
    if backup is not None:
        if backup.is_dir():
            shutil.rmtree(backup)
        else:
            backup.unlink()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("manifest", nargs="?")
    parser.add_argument("target", nargs="?")
    parser.add_argument("--reread")
    parser.add_argument("--tools")
    try:
        args, unknown = parser.parse_known_args(argv)
    except SystemExit as exc:
        raise PullRefused(
            "pull_design.py arguments could not be parsed.",
            "The command shape is fixed.",
            "Run: pull_design.py <manifest.json> <handoff dir> [--reread <dir>] [--tools <dir>].",
        ) from exc
    if unknown or not args.manifest or not args.target:
        raise PullRefused(
            f"pull_design.py received {len(argv)} arguments.",
            "The command needs a manifest and a handoff directory.",
            "Run: pull_design.py <manifest.json> <handoff dir> [--reread <dir>] [--tools <dir>].",
        )
    return args


def run(argv: list[str]) -> None:
    args = parse_args(argv)
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
    project, files, _raw = load_manifest(manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f".{target.name}.pull-", dir=target.parent) as temp:
        staged = Path(temp) / "package"
        staged.mkdir()
        write_project_files(files, preview, reread, target, staged)
        vendor = pull_vendor(staged)
        scenes, sizes = scenes_from_pages(staged)
        render_scenes(staged, scenes, sizes, vendor, tools)
        (staged / "scenes.json").write_text(
            json.dumps(scenes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        (staged / "design-manifest.json").write_text(
            json.dumps(manifest_for_package(project, files), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        write_readme(staged, project, scenes, sizes)
        install(staged, target)
    print(f"pulled {len(files)} files and rendered {len(scenes)} scenes")


def main() -> int:
    try:
        run(sys.argv[1:])
        return 0
    except PullRefused as exc:
        print(refusal_text(exc.what, exc.why, exc.next_step), file=sys.stderr)
        return exc.code
    except Exception as exc:
        print(refusal_text(
            f"pull_design.py failed ({type(exc).__name__}).",
            "The handoff package could not be completed atomically.",
            "Fix the reported local failure and rerun; the target was not changed.",
        ), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
