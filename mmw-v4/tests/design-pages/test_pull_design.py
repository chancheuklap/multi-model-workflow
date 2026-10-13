"""pull_design.py: a project's pages become one complete design package.

The command is the seam. A local preview server supplies the project files and the
three vendor scripts; assertions observe only its exit, output, the target tree, and
which paths the server was asked for.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import textwrap
import threading
import unittest
import urllib.parse
from collections import Counter
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "mmw-v4" / "skills" / "design-pages" / "scripts" / "pull_design.py"


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pull"
INJECTED = (
    b'\n    <style data-omelette-injected>body{outline:0}</style>\n    '
    b'<script data-omelette-injected>window.__preview=true</script>'
)
# The shape measured on a live project on 2026-09-21: tags back to back, wrapped in
# newlines.
INJECTED_LIVE = (
    b'\n<style data-omelette-injected>html,body{background:transparent}</style>'
    b'<script data-omelette-injected>(()=>{})();</script>\n'
)
SERVE_PREFIX = "/v1/design/projects/fixture-project/serve/"


class Preview:
    def __init__(self):
        self.files: dict[str, bytes | None] = {
            "Demo.dc.html": (FIXTURE / "Demo.dc.html").read_bytes(),
            "Overview.dc.html": (FIXTURE / "Overview.dc.html").read_bytes(),
            "styles/app.css": (FIXTURE / "styles" / "app.css").read_bytes(),
            "assets/logo.png": b"fixture-png-with-source-metadata",
        }
        # Paths under this prefix answer 200 with any name, for a page that asks for a
        # new file on every render.
        self.any_name_prefix: str | None = None
        self.vendors = {
            "react.production.min.js": b"window.__reactVendor = true;\n",
            "react-dom.production.min.js": b"window.__reactDomVendor = true;\n",
            "babel.min.js": b"window.__babelVendor = true;\n",
        }
        self.requests = Counter()
        self.disconnects = Counter()
        self.injected = INJECTED
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        self.port = self.server.server_address[1]
        vendor_origin = f"http://localhost:{self.port}"
        template = (FIXTURE / "support.js.template").read_text(encoding="utf-8")
        self.files["support.js"] = template.replace(
            "__VENDOR_ORIGIN__", vendor_origin
        ).encode("utf-8")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def _handler(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                path = urllib.parse.unquote(urllib.parse.urlsplit(self.path).path)
                owner.requests[path] += 1
                if path.startswith(SERVE_PREFIX):
                    rel = path.removeprefix(SERVE_PREFIX)
                    if owner.disconnects[rel] > 0:
                        owner.disconnects[rel] -= 1
                        self.connection.close()
                        self.close_connection = True
                        return
                    if owner.any_name_prefix and rel.startswith(owner.any_name_prefix):
                        body = b"{}"
                    elif rel not in owner.files:
                        self.send_error(404)
                        return
                    else:
                        body = owner.files[rel]
                    if body is None:
                        self.send_error(503)
                        return
                    if rel.endswith(".html"):
                        body = body.replace(b"<head>", b"<head>" + owner.injected, 1)
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                if path.startswith("/assets/"):
                    body = owner.vendors.get(path.rsplit("/", 1)[-1])
                    if body is None:
                        self.send_error(404)
                        return
                    self.send_response(200)
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_error(404)

        return Handler

    @property
    def preview_url(self) -> str:
        return (
            f"http://fixture-project.claudeusercontent.localhost:{self.port}"
            f"{SERVE_PREFIX}Overview.dc.html?token=secret-preview-token&direct=1"
        )

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


class PullDesign(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.preview = Preview()
        self.addCleanup(self.preview.close)
        self.work = Path(self.tmp.name)
        self.target = self.work / "handoff"

    def root_pages(self) -> list[str]:
        return sorted(
            path for path in self.preview.files
            if path.endswith(".dc.html") and "/" not in path
        )

    def pull(
        self, *extra: str, preview_url: str | None = None,
        unset_preview: bool = False, script: Path = SCRIPT,
        pages: list[str] | None = None, args: list[str] | None = None,
    ):
        env = os.environ.copy()
        if unset_preview:
            env.pop("MMW_DESIGN_PREVIEW_URL", None)
        elif preview_url is not None:
            env["MMW_DESIGN_PREVIEW_URL"] = preview_url
        else:
            env["MMW_DESIGN_PREVIEW_URL"] = self.preview.preview_url
        if args is None:
            args = [str(self.target), "--pages", *(pages or self.root_pages())]
        return subprocess.run(
            [sys.executable, str(script), *args, *extra],
            capture_output=True,
            text=True,
            env=env,
        )

    def add_page(self, name: str, body: str) -> None:
        self.preview.files[name] = textwrap.dedent(body).encode("utf-8")

    def refer_from_demo(self, markup: bytes) -> None:
        page = self.preview.files["Demo.dc.html"]
        self.preview.files["Demo.dc.html"] = page.replace(
            b"</head>", markup + b"\n  </head>", 1)

    def pulled_tree(self) -> list[str]:
        return sorted(p.relative_to(self.target).as_posix() for p in self.target.rglob("*") if p.is_file())

    def test_a_clean_project_pulls_every_referenced_file_and_exits_0(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path, body in self.preview.files.items():
            self.assertEqual((self.target / path).read_bytes(), body, path)
        self.assertIn("pulled 5 files", result.stdout)

        self.target = self.work / 'static-package'
        self.preview.files = {'Static.dc.html': b'<html><head></head><body><h1>Static page</h1></body></html>'}
        result = self.pull(pages=['Static.dc.html'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pulled_tree(), ['Static.dc.html'])
        self.assertEqual((self.target / 'Static.dc.html').read_bytes(), self.preview.files['Static.dc.html'])

    def test_the_live_injection_shape_is_stripped_to_the_stored_bytes(self):
        self.preview.injected = INJECTED_LIVE
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        page = (self.target / "Demo.dc.html").read_bytes()
        self.assertEqual(page, self.preview.files["Demo.dc.html"])

    def test_an_injection_marker_left_in_a_page_exits_2_naming_it(self):
        self.target.mkdir()
        (self.target / "existing.txt").write_text("unchanged", encoding="utf-8")
        page = self.preview.files["Demo.dc.html"]
        self.preview.files["Demo.dc.html"] = page.replace(
            b"<body>", b"<body><style data-omelette-injected>x{}</style>", 1)
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Demo.dc.html", result.stderr.splitlines())
        self.assertIn("data-omelette-injected", result.stderr)
        self.assertEqual(self.pulled_tree(), ["existing.txt"])

    def test_a_file_referenced_only_from_css_url_is_pulled(self):
        self.preview.files["styles/app.css"] = (
            b"@font-face { font-family: Body; src: url('../fonts/body.woff2') format('woff2'); }\n")
        self.preview.files["fonts/body.woff2"] = b"wOF2 fixture font"
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "fonts/body.woff2").read_bytes(), b"wOF2 fixture font")

    def test_css_imports_are_followed_recursively(self):
        self.preview.files["styles/app.css"] = b'@import "tokens/colors.css";\nbody { color: #222; }\n'
        self.preview.files["styles/tokens/colors.css"] = b"@import url(fonts.css);\n"
        self.preview.files["styles/tokens/fonts.css"] = b"a { background: url(\"../../img/bg.svg\"); }\n"
        self.preview.files["img/bg.svg"] = b"<svg xmlns='http://www.w3.org/2000/svg'/>"
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path in ("styles/tokens/colors.css", "styles/tokens/fonts.css", "img/bg.svg"):
            self.assertEqual((self.target / path).read_bytes(), self.preview.files[path], path)

    def test_a_dc_imported_page_is_pulled_though_not_named(self):
        self.add_page("Shell.dc.html", """
            <!doctype html><html><head><script src="./support.js"></script></head><body>
            <x-dc><dc-import name="Inner" hint-size="100%,100%"></dc-import></x-dc>
            <script type="text/x-dc" data-dc-script data-props='{}'></script></body></html>
        """)
        self.preview.files["Inner.dc.html"] = (
            b"<!doctype html><html><head><link rel='stylesheet' href='./inner.css'></head>"
            b"<body><x-dc><p>Inner</p></x-dc></body></html>")
        self.preview.files["inner.css"] = b"p { margin: 0; }\n"
        result = self.pull(pages=["Demo.dc.html", "Shell.dc.html"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "Inner.dc.html").read_bytes(), self.preview.files["Inner.dc.html"])
        self.assertEqual((self.target / "inner.css").read_bytes(), b"p { margin: 0; }\n")
        self.assertFalse((self.target / "Overview.dc.html").exists())

    def test_files_nothing_references_are_not_pulled(self):
        for path in ("CLAUDE.md", "state-list.md", "notes/idea.md", ".thumbnail",
                     "design_handoff_previous/old.txt"):
            self.preview.files[path] = b"not part of the package"
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path in ("CLAUDE.md", "state-list.md", "notes/idea.md", ".thumbnail",
                     "design_handoff_previous/old.txt"):
            self.assertFalse((self.target / path).exists(), path)
            self.assertEqual(self.preview.requests[SERVE_PREFIX + path], 0, path)

    def test_vendor_holds_the_three_scripts_support_js_names(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, body in self.preview.vendors.items():
            self.assertEqual((self.target / "vendor" / name).read_bytes(), body)
            self.assertEqual(self.preview.requests[f"/assets/{name}"], 1)

    def test_a_missing_preview_url_exits_2(self):
        result = self.pull(unset_preview=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("MMW_DESIGN_PREVIEW_URL", result.stdout + result.stderr)
        self.assertFalse(self.target.exists())

    def test_the_preview_url_is_never_printed_or_written(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        secret = b"secret-preview-token"
        self.assertNotIn(secret.decode(), result.stdout + result.stderr)
        for path in self.target.rglob("*"):
            if path.is_file():
                self.assertNotIn(secret, path.read_bytes(), str(path.relative_to(self.target)))

        refused = self.pull(pages=["Missing.dc.html"])
        self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
        self.assertNotIn(secret.decode(), refused.stdout + refused.stderr)

        self.refer_from_demo(('<script>console.error("' + self.preview.preview_url + '")</script>').encode())
        logged = self.pull()
        self.assertEqual(logged.returncode, 2, logged.stderr)
        self.assertNotIn(secret.decode(), logged.stdout + logged.stderr)

    def test_a_bound_design_system_brings_its_readme(self):
        self.preview.files["_ds/kit-1/components/x.css"] = b".x { color: red; }\n"
        self.preview.files["_ds/kit-1/readme.md"] = b"## Unifications\n"
        self.refer_from_demo(b'<link rel="stylesheet" href="./_ds/kit-1/components/x.css" />')
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "_ds" / "kit-1" / "readme.md").read_bytes(), b"## Unifications\n")

        self.preview.files['_ds/late/colors.css'] = b'body {color: blue;}'
        self.preview.files['_ds/late/readme.md'] = b'## Unifications\nlate kit\n'
        self.refer_from_demo(b"<script>fetch('./_ds/late/colors.css')</script>")
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(self.target).get('_ds/late/readme.md'), b'## Unifications\nlate kit\n')

    def test_executable_loads_its_pep_723_dependencies(self):
        env = os.environ.copy()
        env['MMW_DESIGN_PREVIEW_URL'] = self.preview.preview_url
        result = subprocess.run([str(SCRIPT), str(self.target), '--pages', 'Demo.dc.html'],
                                capture_output=True, text=True, env=env)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / 'Demo.dc.html').read_bytes(), self.preview.files['Demo.dc.html'])
        self.assertNotIn('ModuleNotFoundError', result.stdout + result.stderr)


    def snapshot(self, root=None):
        root = root or self.work
        return {p.relative_to(root).as_posix(): p.read_bytes()
                for p in root.rglob('*') if p.is_file()}

    def seed_package(self):
        self.target.mkdir()
        (self.target / 'Other.dc.html').write_bytes(b'other page')
        (self.target / 'private.bin').write_bytes(b'\x00private\xff')
        (self.work / 'beside.txt').write_bytes(b'beside package')
        return self.snapshot()

    def test_pulling_listed_pages_leaves_every_other_file_byte_identical(self):
        before = self.seed_package()
        self.preview.files['Other.dc.html'] = b'not signed off'
        self.preview.files['private.bin'] = b'not signed off'
        result = self.pull(pages=['Demo.dc.html'])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        after = self.snapshot()
        for path, body in before.items():
            self.assertEqual(after.get(path), body, path)
        self.assertEqual((self.target / 'Demo.dc.html').read_bytes(), self.preview.files['Demo.dc.html'])
        self.assertEqual(self.preview.requests[SERVE_PREFIX + 'Other.dc.html'], 0)

    def test_a_shared_file_takes_the_bytes_of_the_latest_pull(self):
        first = self.pull(pages=['Demo.dc.html'])
        self.assertEqual(first.returncode, 0, first.stderr)
        before = (self.target / 'Demo.dc.html').read_bytes()
        self.preview.files['styles/app.css'] = b'body {color: red;}\n'
        self.preview.files['Overview.dc.html'] = self.preview.files['Demo.dc.html'].replace(b'Demo', b'Overview')
        self.preview.files['support.js'] += b'\nwindow.updated = true;\n'
        result = self.pull(pages=['Overview.dc.html'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.target / 'Demo.dc.html').read_bytes(), before)
        self.assertEqual((self.target / 'styles/app.css').read_bytes(), b'body {color: red;}\n')
        self.assertEqual((self.target / 'support.js').read_bytes(), self.preview.files['support.js'])

    def test_a_page_the_project_no_longer_has_stays_in_the_package(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stderr)
        before = (self.target / 'Overview.dc.html').read_bytes()
        self.preview.files.pop('Overview.dc.html')
        result = self.pull(pages=['Demo.dc.html'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.target / 'Overview.dc.html').read_bytes(), before)

    def test_the_decision_record_is_pulled_to_the_package_root(self):
        body = '# 设计决策\n\n已确认。\n待确认。\n'.encode()
        self.preview.files['设计决策记录.md'] = body
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(self.target).get('设计决策记录.md'), body)

    def test_a_project_without_a_decision_record_pulls_without_one(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.target / 'Demo.dc.html').read_bytes(), self.preview.files['Demo.dc.html'])
        self.assertFalse((self.target / '设计决策记录.md').exists())

    def test_a_referenced_file_the_project_lacks_exits_2_naming_it(self):
        before = self.seed_package()
        self.refer_from_demo(b'<script src="./lib/gone.js"></script>')
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('lib/gone.js', result.stderr.splitlines())
        self.assertEqual(self.snapshot(), before)

    def test_a_file_requested_only_by_a_script_at_render_time_is_pulled(self):
        self.refer_from_demo(b"<script>fetch('./data/late.json')</script>")
        self.preview.files['data/late.json'] = b'{"rows": []}\n'
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshot(self.target).get('data/late.json'), b'{"rows": []}\n')

    def test_a_render_that_never_stops_requesting_new_files_exits_2(self):
        before = self.seed_package()
        self.preview.any_name_prefix = 'data/r-'
        self.refer_from_demo(b"<script>fetch('./data/r-' + Math.random() + '.json')</script>")
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('5', result.stderr)
        self.assertTrue(any(line.startswith('data/r-') for line in result.stderr.splitlines()))
        self.assertEqual(self.snapshot(), before)

    def test_a_page_that_logs_a_console_error_offline_exits_2_naming_it(self):
        before = self.seed_package()
        self.refer_from_demo(b"<script>console.error('fixture boom')</script>")
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('Demo.dc.html', result.stderr)
        self.assertIn('fixture boom', result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_a_page_that_throws_offline_exits_2_naming_it(self):
        self.refer_from_demo(b"<script>throw new Error('uncaught fixture')</script>")
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('Demo.dc.html', result.stderr)
        self.assertFalse(self.target.exists())

    def test_a_page_that_shows_nothing_offline_exits_2_naming_it(self):
        self.preview.files['Demo.dc.html'] = b'<html><head><script src="support.js"></script></head><body><p hidden>Hidden</p></body></html>'
        result = self.pull(pages=['Demo.dc.html'])
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('Demo.dc.html', result.stderr)
        self.assertFalse(self.target.exists())

    def test_a_failed_external_load_is_named_and_does_not_refuse(self):
        external = 'https://external.invalid/font.css'
        self.refer_from_demo(('<link rel="stylesheet" href="' + external + '">').encode())
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(external, result.stderr)
        self.assertEqual((self.target / 'Demo.dc.html').read_bytes(), self.preview.files['Demo.dc.html'])
        before = self.snapshot()
        self.refer_from_demo(b"<script>console.error('Failed to load resource: net::ERR_FAILED')</script>")
        refused = self.pull()
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertIn('Demo.dc.html', refused.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_a_connection_error_is_retried_and_an_http_status_is_not(self):
        self.preview.disconnects['Demo.dc.html'] = 1
        result = self.pull(pages=['Demo.dc.html'])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.target / 'Demo.dc.html').read_bytes(), self.preview.files['Demo.dc.html'])
        self.assertEqual(self.preview.requests[SERVE_PREFIX + 'Demo.dc.html'], 2)
        before = self.snapshot()
        self.preview.files['Demo.dc.html'] = None
        refused = self.pull(pages=['Demo.dc.html'])
        self.assertEqual(refused.returncode, 2, refused.stderr)
        self.assertEqual(self.preview.requests[SERVE_PREFIX + 'Demo.dc.html'], 3)
        self.assertIn('HTTP 503', refused.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_a_refused_pull_leaves_the_package_byte_identical(self):
        self.seed_package()
        for name in ('Demo.dc.html', 'support.js', 'styles/app.css', 'vendor/react.production.min.js'):
            path = self.target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'old\x00bytes')
        before = self.snapshot()
        self.refer_from_demo(b"<script>console.error('late refusal')</script>")
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('late refusal', result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_no_report_scenes_manifest_or_readme_is_written(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.pulled_tree(), sorted([
            'Demo.dc.html', 'Overview.dc.html', 'assets/logo.png', 'styles/app.css', 'support.js',
            'vendor/babel.min.js', 'vendor/react-dom.production.min.js', 'vendor/react.production.min.js']))

    def test_each_removed_option_exits_2_and_writes_nothing(self):
        before = self.seed_package()
        for option in ('--tools', '--state-list', '--contract'):
            with self.subTest(option=option):
                result = self.pull(option, str(self.work))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.snapshot(), before)
