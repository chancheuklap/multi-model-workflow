"""pull_design.py: a project's pages become one complete design package.

The command is the seam. A local preview server supplies the project files and the
three vendor scripts; assertions observe only its exit, output, the target tree, and
which paths the server was asked for.
"""

from __future__ import annotations

import json
import os
import re
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
SCRIPT = ROOT / "mmw-v2" / "skills" / "design-pages" / "scripts" / "pull_design.py"


def load_script_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_pull_design_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module
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
            "Component · Demo.dc.html": (FIXTURE / "Component · Demo.dc.html").read_bytes(),
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

    def report(self) -> str:
        return (self.target / "pull-report.md").read_text(encoding="utf-8")

    def report_section(self, heading: str) -> str:
        report = self.report()
        start = report.index(f"## {heading}")
        end = report.find("\n## ", start + 3)
        return report[start:end if end >= 0 else None]

    def state_list(self, body: str) -> Path:
        path = self.work / "prototype-readme.md"
        path.write_text("# Prototype\n\n## State list\n\n" + body, encoding="utf-8")
        return path

    def add_page(self, name: str, body: str) -> None:
        self.preview.files[name] = textwrap.dedent(body).encode("utf-8")

    def refer_from_demo(self, markup: bytes) -> None:
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"</head>", markup + b"\n  </head>", 1)

    def pulled_tree(self) -> list[str]:
        return sorted(p.relative_to(self.target).as_posix() for p in self.target.rglob("*") if p.is_file())

    def commit_target(self) -> None:
        subprocess.run(
            ["git", "-c", "init.templateDir=", "init", "-q"], cwd=self.work, check=True,
        )
        subprocess.run(["git", "config", "user.email", "tests@example.invalid"], cwd=self.work, check=True)
        subprocess.run(["git", "config", "user.name", "MMW tests"], cwd=self.work, check=True)
        subprocess.run(["git", "config", "commit.gpgsign", "false"], cwd=self.work, check=True)
        subprocess.run(["git", "config", "core.hooksPath", "/dev/null"], cwd=self.work, check=True)
        subprocess.run(["git", "add", "handoff"], cwd=self.work, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline handoff"], cwd=self.work, check=True)

    def test_a_clean_project_pulls_every_referenced_file_and_exits_0(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path, body in self.preview.files.items():
            self.assertEqual((self.target / path).read_bytes(), body, path)
        self.assertIn("pulled 5 files", result.stdout)

    def test_injected_head_snippets_are_stripped(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        page = (self.target / "Component · Demo.dc.html").read_bytes()
        self.assertNotIn(b"data-omelette-injected", page)
        self.assertEqual(page, self.preview.files["Component · Demo.dc.html"])

    def test_the_live_injection_shape_is_stripped_to_the_stored_bytes(self):
        self.preview.injected = INJECTED_LIVE
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        page = (self.target / "Component · Demo.dc.html").read_bytes()
        self.assertEqual(page, self.preview.files["Component · Demo.dc.html"])

    def test_an_injection_marker_left_in_a_page_exits_2_naming_it(self):
        self.target.mkdir()
        (self.target / "existing.txt").write_text("unchanged", encoding="utf-8")
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"<body>", b"<body><style data-omelette-injected>x{}</style>", 1)
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Component · Demo.dc.html", result.stderr.splitlines())
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

    def test_a_file_requested_only_by_a_script_at_render_time_is_pulled(self):
        # A data: image is never pulled; its onload fetch is the only thing that names
        # the JSON, so nothing but the render can find it.
        pixel = b"data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b'<main data-ui="root">',
            b'<main data-ui="root"><img alt="" src="' + pixel
            + b'" onload="fetch(\'./data/late.json\')">',
            1,
        )
        self.preview.files["data/late.json"] = b'{"rows": []}\n'
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "data/late.json").read_bytes(), b'{"rows": []}\n')
        manifest = json.loads((self.target / "design-manifest.json").read_text(encoding="utf-8"))
        self.assertIn("data/late.json", manifest["files"])
        self.assertNotIn("data/late.json", self.report_section("设计检查"))

    def test_a_render_that_never_stops_requesting_new_files_exits_2(self):
        self.target.mkdir()
        (self.target / "existing.txt").write_text("unchanged", encoding="utf-8")
        self.preview.any_name_prefix = "data/r-"
        pixel = b"data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b'<main data-ui="root">',
            b'<main data-ui="root"><img alt="" src="' + pixel
            + b'" onload="fetch(\'./data/r-\' + Math.random() + \'.json\')">',
            1,
        )
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("after 5 renders", result.stderr)
        self.assertTrue(any(line.startswith("data/r-") for line in result.stderr.splitlines()))
        self.assertEqual(self.pulled_tree(), ["existing.txt"])

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
        result = self.pull(pages=["Component · Demo.dc.html", "Shell.dc.html"])
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

    def test_a_referenced_file_the_project_lacks_is_reported_not_refused(self):
        self.refer_from_demo(b'<script src="./lib/gone.js"></script>')
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(
            "项目里没有的文件：`lib/gone.js`（`Component · Demo.dc.html` 引用）",
            self.report_section("设计检查"),
        )
        self.assertNotIn("未发现设计检查问题", self.report_section("设计检查"))

    def test_a_failed_download_of_a_referenced_file_exits_2_and_writes_nothing(self):
        self.target.mkdir()
        (self.target / "existing.txt").write_text("unchanged", encoding="utf-8")
        self.preview.files["styles/app.css"] = b"body { background: url(../fonts/body.woff2); }\n"
        self.preview.files["fonts/body.woff2"] = None
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("fonts/body.woff2", result.stderr.splitlines())
        self.assertIn("HTTP 503", result.stderr)
        self.assertEqual(self.pulled_tree(), ["existing.txt"])
        self.assertEqual((self.target / "existing.txt").read_text(), "unchanged")

    def test_a_named_page_the_project_lacks_exits_2(self):
        result = self.pull(pages=["Component · Demo.dc.html", "Component · Gone.dc.html"])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("Component · Gone.dc.html", result.stderr.splitlines())
        self.assertFalse(self.target.exists())

    def test_a_name_that_is_not_a_page_exits_2(self):
        result = self.pull(pages=["styles/app.css"])
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("is not a design page", result.stderr)

    def test_a_saved_list_files_result_gives_the_root_pages_and_nothing_else(self):
        self.preview.files["notes/Draft.dc.html"] = b"<html><head></head><body></body></html>"
        listing = self.work / "list_files.json"
        listing.write_text(json.dumps([
            {"path": "Component · Demo.dc.html", "type": "file", "size": 1, "etag": "x"},
            {"path": "Overview.dc.html", "type": "file", "size": 99999},
            {"path": "notes/Draft.dc.html", "type": "file", "size": 5},
            {"path": "styles", "type": "directory"},
            {"path": "styles/app.css", "type": "file", "size": 0},
        ]), encoding="utf-8")
        result = self.pull(args=[str(listing), str(self.target)])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        manifest = json.loads((self.target / "design-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["pages"], ["Component · Demo.dc.html", "Overview.dc.html"])
        self.assertFalse((self.target / "notes/Draft.dc.html").exists())
        self.assertEqual(
            (self.target / "styles/app.css").read_bytes(), self.preview.files["styles/app.css"])

    def test_the_manifest_records_pages_and_pulled_paths_and_a_repull_drops_stale_ones(self):
        self.preview.files["styles/extra.css"] = b"p { color: red; }\n"
        self.refer_from_demo(b'<link rel="stylesheet" href="./styles/extra.css" />')
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        manifest = json.loads((self.target / "design-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["project_id"], "fixture-project")
        self.assertEqual(manifest["pages"], self.root_pages())
        self.assertIn("styles/extra.css", manifest["files"])
        self.assertNotIn("vendor/babel.min.js", manifest["files"])
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b'<link rel="stylesheet" href="./styles/extra.css" />', b"")
        second = self.pull()
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertFalse((self.target / "styles/extra.css").exists())

    def test_scenes_json_is_generated_from_each_page_scene_prop(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((self.target / "scenes.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [row["name"] for row in rows],
            ["Component · Demo.ready", "Component · Demo.empty"],
        )
        self.assertTrue(all(row["page"] == "Component · Demo.dc.html" for row in rows))
        self.assertEqual(
            [row["props"] for row in rows],
            [{"scene": "ready"}, {"scene": "empty"}],
        )
        self.assertTrue(all("/" not in row["name"] for row in rows))
        self.assertFalse(any(row["page"] == "Overview.dc.html" for row in rows))

    def test_out_of_scope_values_are_not_scenes(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((self.target / "scenes.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [row["name"] for row in rows],
            ["Component · Demo.ready", "Component · Demo.empty"],
        )

    def test_a_page_in_a_subfolder_uses_only_its_filename_in_scene_names(self):
        body = self.preview.files.pop("Component · Demo.dc.html")
        self.preview.files["pages/Component · Demo.dc.html"] = body
        result = self.pull(pages=["pages/Component · Demo.dc.html", "Overview.dc.html"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((self.target / "scenes.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [row["name"] for row in rows],
            ["Component · Demo.ready", "Component · Demo.empty"],
        )
        self.assertTrue(all(row["page"].startswith("pages/") for row in rows))

    def test_scene_data_is_keyed_by_data_ui_id_with_nesting_and_lists(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((self.target / "scenes.json").read_text(encoding="utf-8"))
        data = rows[0]["data"]
        self.assertEqual(data["root"]["_text"], "Root copy")
        self.assertEqual(data["root"]["title"], "Demo")
        self.assertEqual(
            data["root"]["group"],
            {"_text": "Group copy", "child": "Nested"},
        )
        self.assertEqual(data["root"]["repeat"], ["First", "Second"])

    def test_scene_data_follows_the_editor_override_block(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        rows = json.loads((self.target / "scenes.json").read_text(encoding="utf-8"))
        self.assertEqual(rows[0]["data"]["root"]["status"], "After override")
        self.assertNotIn("Before override", json.dumps(rows, ensure_ascii=False))

    def test_vendor_holds_the_three_scripts_support_js_names(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for name, body in self.preview.vendors.items():
            self.assertEqual((self.target / "vendor" / name).read_bytes(), body)
            self.assertEqual(self.preview.requests[f"/assets/{name}"], 1)

    def test_readme_has_the_fixed_headings_and_the_offline_render_result(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        readme = (self.target / "README.md").read_text(encoding="utf-8")
        self.assertEqual(readme.count("# Claude Design design package"), 1)
        self.assertEqual(readme.count("## Viewport and size source"), 1)
        self.assertEqual(readme.count("## Offline render check"), 1)
        self.assertEqual(readme.count("## Pull provenance"), 1)
        self.assertIn("`320x200` from `$preview.width` and `$preview.height`", readme)
        self.assertIn("Passed: 2/2 scenes", readme)
        self.assertIn("Claude Design project id: `fixture-project`", readme)

    def test_a_successful_pull_preserves_non_package_files_and_the_state_list(self):
        self.target.mkdir()
        (self.target / "prototype.tsx").write_text("keep me", encoding="utf-8")
        (self.target / "README.md").write_text(
            "# Prototype\n\n## State list\n\n### Header\n- ready\n",
            encoding="utf-8",
        )
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "prototype.tsx").read_text(), "keep me")
        readme = (self.target / "README.md").read_text(encoding="utf-8")
        self.assertIn("## State list\n\n### Header\n- ready", readme)

    def test_an_empty_offline_root_is_reported_without_blocking_the_pull(self):
        page = self.preview.files["Component · Demo.dc.html"]
        start = page.index(b'<main data-ui="root">')
        end = page.index(b"</main>", start) + len(b"</main>")
        self.preview.files["Component · Demo.dc.html"] = page[:start] + page[end:]
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("渲染为空", self.report())
        self.assertIn("Passed: 0/2 scenes", (self.target / "README.md").read_text())

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

        refused = self.pull(pages=["Component · Missing.dc.html"])
        self.assertEqual(refused.returncode, 2, refused.stdout + refused.stderr)
        self.assertNotIn(secret.decode(), refused.stdout + refused.stderr)

    def test_tools_override_supplies_refusal_and_renderer_modules(self):
        isolated = self.work / "isolated" / "pull_design.py"
        isolated.parent.mkdir()
        isolated.write_bytes(SCRIPT.read_bytes())
        tools = ROOT / "mmw-v2" / "skills" / "ui-acceptance" / "scripts"
        result = self.pull(
            "--tools", str(tools), unset_preview=True, script=isolated,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("MMW_DESIGN_PREVIEW_URL", result.stdout + result.stderr)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_every_pull_writes_the_report_with_its_four_sections(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        for heading in ("## 设计检查", "## 覆盖", "## 改动分类", "## 本地改过的说明"):
            self.assertEqual(report.count(heading), 1)

    def test_a_connection_error_is_retried_and_an_http_status_is_not(self):
        module = load_script_module()
        calls = []

        class Body:
            def __enter__(self):
                return self
            def __exit__(self, *_):
                return False
            def read(self):
                return b"ok"

        def flaky(request, timeout):
            calls.append(request.full_url)
            if len(calls) == 1:
                raise module.urllib.error.URLError("reset")
            return Body()

        original = module.urllib.request.urlopen
        module.urllib.request.urlopen = flaky
        try:
            self.assertEqual(module.fetch("http://x/a", pause=0), b"ok")
            self.assertEqual(len(calls), 2)
            calls.clear()

            def gone(request, timeout):
                calls.append(request.full_url)
                raise module.urllib.error.HTTPError(request.full_url, 404, "x", {}, None)

            module.urllib.request.urlopen = gone
            with self.assertRaises(module.DownloadFailed):
                module.fetch("http://x/b", pause=0)
            self.assertEqual(len(calls), 1)
        finally:
            module.urllib.request.urlopen = original

    def test_a_textless_trigger_is_not_reported_and_a_missing_one_is(self):
        module = load_script_module()
        audit = module.RenderAudit(
            rendered=1, empty_scenes=[], console_errors=[],
            data_ui_ids={"bar.icon", "bar.title"}, text_by_id={"bar.title": ["Hi"]},
            scene_text_by_id={"s": {"bar.title": ["Hi"]}},
            text_without_id=[], controls_without_id=[])
        contract = module.ContractInput(provided=True, references=(
            module.ContractReference("bar.icon-row", "bar.icon", ("s",)),
            module.ContractReference("bar.gone-row", "bar.gone", ("s",)),
            module.ContractReference("bar.title-row", "bar.title", ("s",)),
        ))
        changes, unmatched = module.contract_copy_changes(contract, audit, audit)
        self.assertEqual(changes, [])
        self.assertEqual(unmatched, ["bar.gone-row"])

    def test_a_state_name_ends_at_a_full_width_colon(self):
        module = load_script_module()
        regions = module.state_list_regions(
            "### 顶栏\n\n- morning：一夜之后 · 四盏灯\n- bad-data: 读 GitHub 失败\n- `empty` 还没有\n")
        self.assertEqual(regions, {"顶栏": ["morning", "bad-data", "empty"]})

    def test_a_page_root_without_data_ui_is_reported(self):
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b'<main data-ui="root">', b'<main>', 1)
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("页面根元素 `<main>` 没有 `data-ui` id：`Component · Demo.dc.html`",
                      self.report_section("覆盖"))

    def test_only_prefixed_pages_without_scene_are_reported(self):
        self.preview.files["Component · Bare.dc.html"] = (
            b"<!doctype html><html><body><x-dc><p>Bare</p></x-dc></body></html>")
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        coverage = self.report_section("覆盖")
        self.assertIn("没有 `scene` prop 的页面：`Component · Bare.dc.html`", coverage)
        self.assertNotIn("Overview.dc.html", coverage)

    def test_the_report_lists_selectors_the_editor_cannot_reach(self):
        self.preview.files["styles/app.css"] += b"\n.a .b .c { color: red; }\n"
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(".a .b .c", self.report_section("设计检查"))

    def test_the_selector_check_reads_page_style_blocks_and_skips_the_design_system(self):
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"</style>", b"  .p .q .r { color: red; }\n</style>", 1)
        self.preview.files["_ds/kit-1/components/x.css"] = b".d .e .f { color: red; }\n"
        self.refer_from_demo(b'<link rel="stylesheet" href="./_ds/kit-1/components/x.css" />')
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        design = self.report_section("设计检查")
        self.assertIn(".p .q .r", design)
        self.assertNotIn(".d .e .f", design)

    def test_the_report_lists_scenes_that_render_empty_or_log_errors(self):
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"<main data-ui=\"root\">",
            b'''<main data-ui="root"><img data-ui="broken" src="missing.png" onerror="console.error('fixture boom')">''',
            1,
        )
        self.add_page("Component · Empty.dc.html", """
            <!doctype html><html><head><script src="./support.js"></script></head><body>
            <x-dc></x-dc>
            <script type="text/x-dc" data-dc-script data-props='{
              "$preview":{"width":320,"height":200},
              "scene":{"editor":"enum","options":["empty"]}
            }'></script></body></html>
        """)
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report_section("设计检查")
        self.assertIn("渲染为空：`Component · Empty.empty`", report)
        self.assertIn("控制台报错：`Component · Demo.ready` — fixture boom", report)

    def test_the_report_lists_states_missing_from_the_scene_prop(self):
        state_list = self.state_list("### Demo\n- ready\n- empty\n- loading\n")
        result = self.pull("--state-list", str(state_list))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        coverage = self.report_section("覆盖")
        self.assertIn("state list 状态缺失：`Demo` 的 `loading`", coverage)
        self.assertNotIn("`Demo` 的 `ready`", coverage)
        self.assertNotIn("`Demo` 的 `empty`", coverage)
        self.assertNotIn("### Demo", (self.target / "README.md").read_text())

    def test_the_report_lists_elements_and_controls_without_data_ui(self):
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"</main>", b"<p>Unidentified copy</p><button>Unidentified action</button></main>", 1,
        )
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        coverage = self.report_section("覆盖")
        self.assertIn("带文字但没有 `data-ui` id：", coverage)
        self.assertIn("p: Unidentified copy", coverage)
        self.assertIn("可点或可输入却没有 `data-ui` id：", coverage)
        self.assertIn("button: Unidentified action", coverage)

    def test_the_report_lists_classes_no_stylesheet_defines(self):
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"</main>", b'<p class="lane-label" data-ui="lane">Lane</p></main>', 1)
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        design = self.report_section("设计检查")
        self.assertIn("样式表里没有的类名：`Component · Demo.dc.html` — `.lane-label`（在 `lane`）", design)
        self.assertNotIn("`.old-value`", design)

    def test_the_report_lists_hand_written_lengths_off_the_design_system(self):
        self.preview.files["_ds/kit-1/tokens/spacing.css"] = b":root { --sp-8: 8px; --sp-16: 16px; }\n"
        self.refer_from_demo(b'<link rel="stylesheet" href="./_ds/kit-1/tokens/spacing.css" />')
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"</main>",
            b'<p data-ui="a" style="padding: 8px 16px; top: 14px">A</p>'
            b'<p data-ui="b" style="font-size: 10px; width: 236px">B</p>'
            b'<p data-ui="c" style="left: {{ x }}; margin: 0">C</p></main>', 1)
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        design = self.report_section("设计检查")
        self.assertIn("写死的数值不在 design system 的变量里：`Component · Demo.dc.html` — `top: 14px`", design)
        self.assertIn("— `font-size: 10px`", design)
        self.assertNotIn("padding: 8px 16px", design)
        self.assertNotIn("width: 236px", design)
        self.assertNotIn("left:", design)

    def test_a_bound_design_system_brings_its_readme(self):
        self.preview.files["_ds/kit-1/components/x.css"] = b".x { color: red; }\n"
        self.preview.files["_ds/kit-1/readme.md"] = b"## Unifications\n"
        self.refer_from_demo(b'<link rel="stylesheet" href="./_ds/kit-1/components/x.css" />')
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "_ds" / "kit-1" / "readme.md").read_bytes(), b"## Unifications\n")

    def test_interpolated_text_belongs_to_the_element_that_holds_it(self):
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"</main>",
            b'<p data-ui="demo.count">#<span class="sc-interp">98</span> \xc2\xb7 map</p>'
            b'<p>Loose <span class="sc-interp">value</span></p></main>',
            1,
        )
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        coverage = self.report_section("覆盖")
        self.assertNotIn("span.sc-interp", coverage)
        self.assertNotIn("98", coverage)
        self.assertIn("p: Loose value", coverage)

    def test_the_report_lists_pages_without_a_scene_prop(self):
        self.add_page("Component · Static.dc.html", """
            <!doctype html><html><body><x-dc><p data-ui="static.copy">Static</p></x-dc>
            <script type="text/x-dc" data-dc-script data-props='{"$preview":{"width":320,"height":200}}'></script>
            </body></html>
        """)
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Component · Static.dc.html", self.report_section("覆盖"))

    def test_the_report_lists_out_of_scope_values(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report_section("覆盖")
        self.assertIn("out_of_scope", report)
        self.assertIn("future", report)

    def test_without_a_state_list_the_report_says_it_was_not_checked(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertIn("state list 未给出，未核对", report)
        self.assertNotIn("state list 没有缺失", report)

    def test_a_first_pull_is_classified_as_first(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("分类：首次", self.report())

    def test_a_colour_change_is_classified_look_or_copy_only(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        self.preview.files["styles/app.css"] = b"body { color: #456; }\n"
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("分类：只改外观或文案", self.report())
        self.assertNotIn("pull 前 design package 有本地改动", self.report())
        self.assertIn("screen contract 未给出，合同行文字未核对", self.report())

    def test_a_report_with_problems_still_exits_0(self):
        page = self.preview.files["Component · Demo.dc.html"]
        start = page.index(b'<main data-ui="root">')
        end = page.index(b"</main>", start) + len(b"</main>")
        self.preview.files["Component · Demo.dc.html"] = page[:start] + page[end:]
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("渲染为空", self.report())

    def test_an_added_control_is_classified_controls_or_flow(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b"</main>", b'<button data-ui="demo.add">Add</button></main>', 1,
        )
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertIn("分类：增删控件或改流转", report)
        self.assertIn("demo.add", report)

    def test_a_changed_contract_row_text_is_reported(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(b">Demo</h1>", b">Updated demo</h1>")
        contract = self.work / "screen-contract.yaml"
        contract.write_text(textwrap.dedent("""
            rows:
              - id: demo.open
                trigger: title
                scenes: ["Component · Demo.ready"]
        """), encoding="utf-8")
        result = self.pull("--contract", str(contract))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertIn("分类：增删控件或改流转", report)
        self.assertIn("demo.open", report)
        self.assertIn("Demo", report)
        self.assertIn("Updated demo", report)

    def add_app_page(self, logic: str, props: str) -> None:
        self.add_page("App · Shell.dc.html", f"""
            <!doctype html><html><head><script src="./support.js"></script></head><body>
            <x-dc><main data-ui="shell"><dc-import name="Inner" props='{props}'></dc-import></main></x-dc>
            <script type="text/x-dc" data-dc-script data-props='{{}}'>{logic}</script></body></html>
        """)
        self.preview.files["Inner.dc.html"] = (
            b"<!doctype html><html><head></head><body><x-dc><p>Inner</p></x-dc></body></html>")

    def pull_app_twice(self, logic: str, props: str) -> str:
        self.add_app_page("class App extends DCLogic { open() { this.props.onOpen(); } }",
                          '{"onPick": "open"}')
        pages = ["Component · Demo.dc.html", "App · Shell.dc.html"]
        first = self.pull(pages=pages)
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        self.add_app_page(logic, props)
        result = self.pull(pages=pages)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return self.report_section("改动分类")

    def test_a_changed_app_logic_block_is_classified_controls_or_flow(self):
        section = self.pull_app_twice(
            "class App extends DCLogic { open() { this.props.onClose(); } }",
            '{"onPick": "open"}')
        self.assertIn("分类：增删控件或改流转", section)
        self.assertIn("- `App · ` 页接线变化：`App · Shell.dc.html` — "
                      "`data-dc-script` 逻辑块与上次不同。", section)

    def test_changed_dc_import_props_on_an_app_page_are_classified_controls_or_flow(self):
        section = self.pull_app_twice(
            "class App extends DCLogic { open() { this.props.onOpen(); } }",
            '{"onPick": "close"}')
        self.assertIn("分类：增删控件或改流转", section)
        self.assertIn("`App · Shell.dc.html` — `dc-import` 属性与上次不同。", section)

    def test_whitespace_in_app_wiring_is_not_a_change(self):
        section = self.pull_app_twice(
            "class App extends DCLogic {\n  open() {  this.props.onOpen(); }\n}",
            '{"onPick":  "open"}')
        self.assertIn("分类：只改外观或文案", section)
        self.assertNotIn("接线变化", section)

    def test_a_locally_edited_package_gets_a_note(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        page = self.target / "Component · Demo.dc.html"
        page.write_text(page.read_text(encoding="utf-8") + "\n<!-- local edit -->\n", encoding="utf-8")
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("pull 前 design package 有本地改动", self.report())

    def test_an_added_scene_value_is_classified_controls_or_flow(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b'"options": ["ready", "empty", "future"]',
            b'"options": ["ready", "empty", "added", "future"]',
        )
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertIn("分类：增删控件或改流转", report)
        self.assertIn("`scene` 取值变化：`Component · Demo.dc.html`；新增 added", report)

    def test_a_state_missing_from_its_own_page_is_reported_even_if_another_page_has_it(self):
        self.add_page("Component · Other.dc.html", """
            <!doctype html><html><head><script src="./support.js"></script></head><body>
            <x-dc><main data-ui="other.root">Other</main></x-dc>
            <script type="text/x-dc" data-dc-script data-props='{
              "$preview":{"width":320,"height":200},
              "scene":{"editor":"enum","options":["loading"]}
            }'></script></body></html>
        """)
        state_list = self.state_list("### Demo\n- loading\n\n### Missing page\n- ready\n")
        result = self.pull("--state-list", str(state_list))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertIn("state list 状态缺失：`Demo` 的 `loading`", report)
        self.assertIn("找不到同名页", report)
        self.assertIn("Missing page", report)

    def test_unreadable_state_list_is_reported_as_not_checked_and_does_not_replace_readme(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        readme = self.target / "README.md"
        readme.write_text(readme.read_text() + "\n## State list\n\n### Kept\n- ready\n")
        result = self.pull("--state-list", str(self.work / "missing-readme.md"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("state list 无法读取，未核对", self.report_section("覆盖"))
        self.assertIn("### Kept\n- ready", readme.read_text())

    def test_contract_without_rows_is_reported_as_not_checked(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        contract = self.work / "screen-contract.yaml"
        contract.write_text("target: {kind: web-spa}\n", encoding="utf-8")
        result = self.pull("--contract", str(contract))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("screen contract 没有 `rows`，合同行文字未核对", self.report())

    def test_without_css_the_report_says_the_editor_check_was_not_run(self):
        self.preview.files.pop("styles/app.css")
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = re.sub(
            rb"<style\b[^>]*>.*?</style>|<link rel=\"stylesheet\"[^>]*>", b"", page, flags=re.S)
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        design = self.report_section("设计检查")
        self.assertIn("选择器未核对", design)
        self.assertNotIn("未发现设计检查问题", design)

    def test_a_legacy_committed_package_does_not_block_the_next_pull(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        (self.target / "support.js").unlink()
        page = self.target / "Component · Demo.dc.html"
        page.write_text(page.read_text().replace('"$preview": {"width": 320, "height": 200},', ""))
        subprocess.run(["git", "add", "handoff"], cwd=self.work, check=True)
        subprocess.run(["git", "commit", "-qm", "legacy package"], cwd=self.work, check=True)
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.target / "pull-report.md").is_file())

    def test_editor_override_copy_change_is_classified_from_rendered_text(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b".old-value { display: none !important; }\n          .new-value { display: block !important; }",
            b".old-value { display: block !important; }\n          .new-value { display: none !important; }",
        )
        contract = self.work / "screen-contract.yaml"
        contract.write_text(textwrap.dedent("""
            rows:
              - id: demo.status-copy
                trigger: status
                scenes: ["Component · Demo.ready"]
        """), encoding="utf-8")
        result = self.pull("--contract", str(contract))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report_section("改动分类")
        self.assertIn("分类：增删控件或改流转", report)
        self.assertIn("demo.status-copy", report)
        self.assertIn("After override", report)
        self.assertIn("Before override", report)

    def test_executable_loads_its_pep_723_dependencies(self):
        result = subprocess.run([str(SCRIPT)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("pull_design.py received 0 arguments", result.stdout + result.stderr)
        self.assertNotIn("ModuleNotFoundError", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
