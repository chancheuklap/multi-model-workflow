#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58"]
# ///
"""Pull named Claude Design pages and their dependencies into a design package.

Usage: pull_design.py <package dir> --pages <page.dc.html>...
MMW_DESIGN_PREVIEW_URL supplies the preview address; it is never printed or saved.
Exit 0: the pages passed their offline checks and the downloaded files were written.
Exit 2: the pull was refused; the package is unchanged.
Never deletes package files, edits the design, or generates reports or metadata.
"""

from __future__ import annotations

import argparse
import http.client
import http.server
import os
import posixpath
import re
import shutil
import sys
import tempfile
import threading
import time
import traceback
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath


VENDOR_CONSTANTS = ("REACT_URL", "REACT_DOM_URL", "BABEL_URL")
FETCH_ATTEMPTS = 3
HEAD = re.compile(br"<head\b[^>]*>", re.IGNORECASE)
INJECTED_TAG = re.compile(br"<(style|script)\b(?=[^>]*\bdata-omelette-injected\b)[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
INJECTED_MARKER = b"data-omelette-injected"
CSS_COMMENT = re.compile(r"/\*.*?\*/", re.S)
CSS_URL = re.compile(r"""url\(\s*(?:"([^"]*)"|'([^']*)'|([^)'"\s]*))\s*\)""", re.I)
CSS_IMPORT = re.compile(r"""@import\s+(?:"([^"]*)"|'([^']*)')""", re.I)
LOADING_ATTRS = {"src", "poster", "data", "xlink:href"}
HREF_LOADS = {"link", "use", "image", "feimage"}
IMPORT_TAGS = {"dc-import", "x-import"}


class PullRefused(Exception):
    def __init__(self, what: str, why: str, next_step: str,
                 paths: list[str] | None = None):
        super().__init__(what)
        self.what = what
        self.why = why
        self.next_step = next_step
        self.paths = paths or []


class DownloadFailed(Exception):
    def __init__(self, status: str, http_code: int | None = None):
        super().__init__(status)
        self.status = status
        self.http_code = http_code


def preview_secrets(preview: str) -> list[str]:
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(preview).query)
    return [preview, *query.get("token", [])]


def redact(text: str) -> str:
    preview = os.environ.get("MMW_DESIGN_PREVIEW_URL")
    if preview:
        for secret in preview_secrets(preview):
            if secret:
                text = text.replace(secret, "<REDACTED>")
    return text


def refuse_preview_bytes(body: bytes, path: str) -> None:
    preview = os.environ.get("MMW_DESIGN_PREVIEW_URL", "")
    if preview and any(secret.encode() in body for secret in preview_secrets(preview) if secret):
        raise PullRefused(f"Preview credentials occur in {path}.",
                          "Saving the response would persist the preview address or its token.",
                          "Remove the preview address from that project file and re-run.", paths=[path])


def safe_path(raw: object) -> str:
    path = str(raw or "").replace("\\", "/")
    while path.startswith("./"):
        path = path[2:]
    pure = PurePosixPath(path)
    if not path or pure.is_absolute() or ".." in pure.parts:
        raise PullRefused(
            f"project path is unsafe: {raw!r}.",
            "A project file must be a non-empty project-relative path.",
            "Name the page by its project-relative path and re-run.",
        )
    return pure.as_posix()


def page_name(raw: str) -> str:
    path = safe_path(raw)
    if not path.endswith(".dc.html"):
        raise PullRefused(
            f"{raw!r} is not a design page.",
            "--pages takes the project's `.dc.html` pages by name.",
            "Pass the `.dc.html` names list_files shows at the project root and re-run.",
        )
    return path


def preview_file_url(preview: str, path: str) -> str:
    parsed = urllib.parse.urlsplit(preview)
    marker = "/serve/"
    if marker not in parsed.path:
        raise PullRefused(
            "MMW_DESIGN_PREVIEW_URL has no /serve/ file path.",
            "render_preview serve_url identifies one project file under /serve/.",
            "Set MMW_DESIGN_PREVIEW_URL to the current render_preview serve_url and re-run.",
        )
    base = parsed.path.partition(marker)[0] + marker
    quoted = "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, base + quoted, parsed.query, "")
    )


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


def strip_injected_head(raw: bytes) -> bytes:
    head = HEAD.search(raw)
    if head is None:
        return raw
    cursor = head.end()
    if raw[cursor:cursor + 1] == b"\n":
        injected_end = cursor + 1
        injected_count = 0
        while (tag := INJECTED_TAG.match(raw, injected_end)) is not None:
            injected_end = tag.end()
            injected_count += 1
        if injected_count and raw[injected_end:injected_end + 1] == b"\n":
            return raw[:cursor] + raw[injected_end + 1:]
    whitespace_tolerant_end = cursor
    while True:
        start = cursor
        while start < len(raw) and raw[start:start + 1].isspace():
            start += 1
        tag = INJECTED_TAG.match(raw, start)
        if tag is None:
            break
        whitespace_tolerant_end = tag.end()
        cursor = tag.end()
    if whitespace_tolerant_end == head.end():
        return raw
    return raw[:head.end()] + raw[whitespace_tolerant_end:]


def css_references(text: str) -> list[str]:
    text = CSS_COMMENT.sub("", text)
    refs = [next(g for g in match.groups() if g is not None) for match in CSS_IMPORT.finditer(text)]
    refs += [next(g for g in match.groups() if g is not None) for match in CSS_URL.finditer(text)]
    return refs


class _ReferenceParser(HTMLParser):
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
    preview: str
    staged: Path
    pulled: set[str] = field(default_factory=set)

    def download(self, path: str) -> bytes:
        body = fetch(preview_file_url(self.preview, path))
        if path.lower().endswith((".html", ".htm")):
            body = strip_injected_head(body)
            if INJECTED_MARKER in body:
                raise PullRefused(
                    f"{INJECTED_MARKER.decode()} is still in the page listed below after "
                    "the preview's injection was removed.",
                    "The preview injects in a shape pull does not know, or the page holds "
                    "that attribute; the bytes would not be the stored page.",
                    "Tell the user which page; the target was not changed.",
                    paths=[path],
                )
        refuse_preview_bytes(body, path)
        return body

    def pull(self, paths: list[str], referrer: str | None, missing_ok: bool = False) -> None:
        queue = [(path, referrer) for path in paths]
        while queue:
            path, source = queue.pop(0)
            if path in self.pulled:
                continue
            try:
                body = self.download(path)
            except DownloadFailed as exc:
                if exc.http_code == 404 and missing_ok and source is None:
                    continue
                if exc.http_code == 404:
                    if source and source.startswith("bound design system "):
                        why = f"The {source} must include its readme."
                        next_step = f"Restore {path} in that design system and re-run."
                    elif source:
                        why = f"{source} requires this file; the design package would be incomplete."
                        next_step = f"Restore {path} in the project and re-run."
                    else:
                        why = "The listed page cannot be downloaded."
                        next_step = f"Check {path} against list_files and re-run."
                    what = f"Project file {path} is missing (HTTP 404)."
                else:
                    what = f"Download failed for {path} ({exc.status})."
                    why = f"{source or 'The listed page'} could not be included in the design package."
                    next_step = "Restore the preview download and re-run."
                raise PullRefused(what, why, next_step, paths=[path]) from exc
            dest = self.staged.joinpath(*PurePosixPath(path).parts)
            if dest.is_dir():
                shutil.rmtree(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            self.pulled.add(path)
            parts = PurePosixPath(path).parts
            if len(parts) > 2 and parts[0] == "_ds":
                readme = "/".join(parts[:2]) + "/readme.md"
                if readme not in self.pulled:
                    queue.append((readme, "bound design system " + "/".join(parts[:2])))
            for ref in file_references(path, body):
                if ref not in self.pulled:
                    queue.append((ref, path))


def vendor_urls(support: Path) -> dict[str, str]:
    try:
        text = support.read_text(encoding="utf-8")
    except OSError as exc:
        raise PullRefused(
            f"support.js cannot be read: {type(exc).__name__}.",
            "The vendor script addresses are unknown.",
            "Restore support.js in the project and re-run.",
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
                f"Restore {name} in support.js and re-run.",
            )
        out[name] = match.group(2)
    return out


def pull_vendor(staged: Path) -> dict[str, Path]:
    if not (staged / "support.js").exists():
        return {}
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
                "Fix the three support.js URL constants and re-run.",
            )
        names.add(name)
        try:
            body = fetch(url)
        except DownloadFailed as exc:
            raise PullRefused(
                f"vendor download failed for {name} ({exc.status}).",
                "The design package would not render with the network off.",
                "Restore that vendor address and re-run; the target was not changed.",
            ) from exc
        path = vendor / name
        refuse_preview_bytes(body, name)
        path.write_bytes(body)
        by_url[url] = path
    return by_url


@dataclass
class RenderAudit:
    requested: set[str] = field(default_factory=set)
    referrers: dict[str, str] = field(default_factory=dict)
    errors: list[tuple[str, str]] = field(default_factory=list)
    empty: list[str] = field(default_factory=list)
    blocked: set[str] = field(default_factory=set)


def serve_package(root: Path):
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(root), **kwargs)

        def log_message(self, *_args):
            pass

        def list_directory(self, path):
            self.send_error(404)
            return None

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def render_pages(inventory: Inventory, pages: list[str], vendor: dict[str, Path]) -> RenderAudit:
    from playwright.sync_api import TimeoutError as RenderTimeout, sync_playwright
    audit = RenderAudit()
    server = serve_package(inventory.staged)
    origin = f"http://127.0.0.1:{server.server_port}"

    def route_offline(route, request, name):
        if urllib.parse.urlsplit(request.url).netloc == urllib.parse.urlsplit(origin).netloc:
            path = resolve_reference("", urllib.parse.urlsplit(request.url).path)
            if path:
                audit.requested.add(path)
                audit.referrers.setdefault(path, name)
            route.continue_()
        elif request.url in vendor:
            route.fulfill(path=str(vendor[request.url]), content_type="application/javascript")
        else:
            audit.blocked.add(request.url)
            route.abort()

    try:
        with sync_playwright() as pw:
            try:
                browser = pw.chromium.launch()
            except Exception as exc:
                raise PullRefused("Chromium could not start.",
                                  "The offline pages cannot be checked.",
                                  "Install Chromium with `uv run --with playwright python -m playwright install chromium` and re-run.") from exc
            try:
                for name in pages:
                    context = browser.new_context(service_workers="block")
                    context.route("**/*", lambda route, request, name=name: route_offline(route, request, name))
                    page = context.new_page()
                    def console_message(message, name=name):
                        if message.type != "error":
                            return
                        if (message.location.get("url") in audit.blocked
                                and message.text.startswith("Failed to load resource:")):
                            return
                        audit.errors.append((name, message.text))

                    page.on("console", console_message)
                    page.on("pageerror", lambda error, name=name: audit.errors.append((name, str(error))))
                    try:
                        page.goto(origin + "/" + urllib.parse.quote(name), wait_until="networkidle", timeout=15000)
                        visible_content = """() => {
                            const root = document.body;
                            if (!root) return false;
                            const range = document.createRange();
                            const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
                            while (walker.nextNode()) {
                                const node = walker.currentNode;
                                if (!node.textContent.trim() || node.parentElement.closest('script,style,template,helmet')) continue;
                                if (!node.parentElement.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})) continue;
                                range.selectNodeContents(node);
                                if ([...range.getClientRects()].some(r => r.width > 0 && r.height > 0)) return true;
                            }
                            return [...root.querySelectorAll('*')].some(el => {
                                const s = getComputedStyle(el), r = el.getBoundingClientRect();
                                if (r.width <= 0 || r.height <= 0 || !el.checkVisibility({checkOpacity: true, checkVisibilityCSS: true})) return false;
                                return el.matches('img,svg,canvas,video,input,button,select,textarea')
                                  || s.backgroundImage !== 'none'
                                  || (s.backgroundColor !== 'transparent' && s.backgroundColor !== 'rgba(0, 0, 0, 0)');
                            });
                        }"""
                        try:
                            page.wait_for_function(visible_content, timeout=15000)
                        except RenderTimeout:
                            pass
                        page.wait_for_timeout(3000)
                        if not page.evaluate(visible_content):
                            audit.empty.append(name)
                    except Exception as exc:
                        raise PullRefused(f"Offline page could not open: {name}.",
                                          f"Chromium navigation failed ({type(exc).__name__}).",
                                          "Fix that page in Claude Design and re-run.", paths=[name]) from exc
                    finally:
                        context.close()
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
    return audit


def render_until_settled(inventory: Inventory, pages: list[str], vendor: dict[str, Path]):
    blocked = set()
    for _round in range(5):
        audit = render_pages(inventory, pages, vendor)
        blocked.update(audit.blocked)
        new = sorted(audit.requested - inventory.pulled)
        if not new:
            if audit.errors or audit.empty:
                paths = [f"{name}: {message}" for name, message in audit.errors]
                paths.extend(f"{name}: blank page" for name in audit.empty)
                raise PullRefused("Offline page checks failed.",
                                  "A page reported an error or displayed nothing.",
                                  "Fix the pages listed below in Claude Design and re-run.", paths=paths)
            for url in sorted(blocked):
                print(redact(f"External load blocked: {url}"), file=sys.stderr)
            return audit
        for path in new:
            inventory.pull([path], audit.referrers[path])
        if "support.js" in new:
            vendor.update(pull_vendor(inventory.staged))
    raise PullRefused("Offline pages still requested new files after 5 renders.",
                      "The downloaded file set did not settle.",
                      "Fix the page requesting the files listed below and re-run.", paths=new)


def install(staged: Path, target: Path) -> None:
    files = sorted(p for p in staged.rglob("*") if p.is_file())
    for source in files:
        dest = target / source.relative_to(staged)
        for parent in (dest, *list(dest.parents)[:len(source.relative_to(staged).parts)]):
            if parent.is_symlink() or (parent.exists() and (
                parent == dest and not parent.is_file()
                or parent != dest and not parent.is_dir()
            )):
                raise PullRefused(f"Package path cannot be written: {parent}.",
                                  "A downloaded file needs a regular file path inside the package.",
                                  "Move the conflicting path aside and re-run.")
    created_dirs = []
    applied = []
    with tempfile.TemporaryDirectory() as backup_dir:
        backups = Path(backup_dir)
        try:
            for index, source in enumerate(files):
                dest = target / source.relative_to(staged)
                missing = []
                parent = dest.parent
                while not parent.exists():
                    missing.append(parent)
                    parent = parent.parent
                for directory in reversed(missing):
                    directory.mkdir()
                    created_dirs.append(directory)
                backup = backups / str(index) if dest.exists() else None
                if backup is not None:
                    shutil.copy2(dest, backup)
                applied.append((dest, backup))
                with tempfile.NamedTemporaryFile(dir=dest.parent, delete=False) as out:
                    pending = Path(out.name)
                    try:
                        out.write(source.read_bytes())
                        out.close()
                        os.chmod(pending, (dest.stat().st_mode if backup else source.stat().st_mode) & 0o7777)
                        os.replace(pending, dest)
                    finally:
                        pending.unlink(missing_ok=True)
        except Exception:
            for dest, backup in reversed(applied):
                if backup is None:
                    dest.unlink(missing_ok=True)
                else:
                    shutil.copy2(backup, dest)
            for directory in reversed(created_dirs):
                directory.rmdir()
            raise


class CommandParser(argparse.ArgumentParser):
    def error(self, message):
        raise PullRefused("pull_design.py arguments could not be parsed.",
                          "The command shape is fixed; see the script header.",
                          "Pass a package directory and the page names after --pages and re-run.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = CommandParser(add_help=False, allow_abbrev=False)
    parser.add_argument("target")
    parser.add_argument("--pages", nargs="+", required=True)
    return parser.parse_args(argv)


def run(args):
    preview = os.environ.get("MMW_DESIGN_PREVIEW_URL")
    if not preview:
        raise PullRefused("MMW_DESIGN_PREVIEW_URL is not set.", "There is no preview to download.", "Set the variable from render_preview and re-run.")
    pages = [page_name(p) for p in args.pages]
    target = Path(args.target)
    with tempfile.TemporaryDirectory() as temp:
        staged = Path(temp) / "package"
        staged.mkdir()
        inventory = Inventory(preview, staged)
        inventory.pull(pages, None)
        inventory.pull(["设计决策记录.md"], None, missing_ok=True)
        vendor = pull_vendor(staged)
        render_until_settled(inventory, pages, vendor)
        install(staged, target)
    print(f"pulled {len(inventory.pulled)} files")


def main():
    try:
        run(parse_args(sys.argv[1:]))
        return 0
    except PullRefused as exc:
        print(redact(" ".join((exc.what, exc.why, exc.next_step))), file=sys.stderr)
        for path in exc.paths:
            print(redact(path), file=sys.stderr)
        return 2
    except Exception as exc:
        location = traceback.extract_tb(exc.__traceback__)[-1]
        print(redact(f"Pull failed ({type(exc).__name__}): {exc} "
                     f"at {location.filename}:{location.lineno}. "
                     "The design package could not be completed. "
                     "Fix the reported failure and re-run."), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
