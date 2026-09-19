"""pull_design.py: one manifest becomes one complete handoff package.

The command is the seam. A local preview server supplies the exact project files and
the three vendor scripts; assertions observe only its exit, output, and target tree.
"""

from __future__ import annotations

import json
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
SCRIPT = ROOT / "mmw-v2" / "skills" / "design-pages" / "scripts" / "pull_design.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pull"
INJECTED = (
    b'\n    <style data-omelette-injected>body{outline:0}</style>\n    '
    b'<script data-omelette-injected>window.__preview=true</script>'
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
        self.vendors = {
            "react.production.min.js": b"window.__reactVendor = true;\n",
            "react-dom.production.min.js": b"window.__reactDomVendor = true;\n",
            "babel.min.js": b"window.__babelVendor = true;\n",
        }
        self.requests = Counter()
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
                    body = owner.files.get(rel)
                    if body is None:
                        self.send_error(503)
                        return
                    if rel.endswith(".html"):
                        body = body.replace(b"<head>", b"<head>" + INJECTED, 1)
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
        self.manifest = self.work / "manifest.json"
        self.target = self.work / "handoff"
        self.write_manifest()

    def write_manifest(self, extra: list[dict] | None = None):
        files = [
            {"path": path, "type": "file", "size": len(body), "etag": f'etag-{i}'}
            for i, (path, body) in enumerate(self.preview.files.items())
            if body is not None
        ]
        files.extend(extra or [])
        self.manifest.write_text(
            json.dumps(files, indent=2),
            encoding="utf-8",
        )

    def pull(
        self, *extra: str, preview_url: str | None = None,
        unset_preview: bool = False, script: Path = SCRIPT,
    ):
        env = os.environ.copy()
        if unset_preview:
            env.pop("MMW_DESIGN_PREVIEW_URL", None)
        elif preview_url is not None:
            env["MMW_DESIGN_PREVIEW_URL"] = preview_url
        else:
            env["MMW_DESIGN_PREVIEW_URL"] = self.preview.preview_url
        return subprocess.run(
            [sys.executable, str(script), str(self.manifest), str(self.target), *extra],
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
        self.write_manifest()

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

    def test_a_clean_project_pulls_every_file_and_exits_0(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        for path, body in self.preview.files.items():
            self.assertEqual((self.target / path).read_bytes(), body, path)

    def test_injected_head_snippets_are_stripped_before_the_size_check(self):
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        page = (self.target / "Component · Demo.dc.html").read_bytes()
        self.assertNotIn(b"data-omelette-injected", page)
        self.assertEqual(page, self.preview.files["Component · Demo.dc.html"])

    def test_a_text_file_whose_size_differs_exits_1_naming_it(self):
        self.preview.files["styles/app.css"] += b"/* changed in preview */\n"
        result = self.pull()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("styles/app.css", result.stdout + result.stderr)
        self.assertFalse(self.target.exists())

    def test_a_second_run_with_a_reread_directory_uses_those_files(self):
        correct = self.preview.files["styles/app.css"]
        self.preview.files["styles/app.css"] += b"/* changed in preview */\n"
        reread = self.work / "reread" / "styles"
        reread.mkdir(parents=True)
        (reread / "app.css").write_bytes(correct)
        result = self.pull("--reread", str(self.work / "reread"))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "styles/app.css").read_bytes(), correct)

    def test_a_failed_download_over_256_kib_exits_2_and_writes_nothing(self):
        self.target.mkdir()
        (self.target / "existing.txt").write_text("unchanged", encoding="utf-8")
        self.preview.files["data/large.txt"] = None
        self.write_manifest([
            {"path": "data/large.txt", "size": 300 * 1024, "etag": "text-v1"}
        ])
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("data/large.txt", result.stdout + result.stderr)
        self.assertEqual(
            [path.relative_to(self.target).as_posix() for path in self.target.rglob("*")],
            ["existing.txt"],
        )
        self.assertEqual((self.target / "existing.txt").read_text(), "unchanged")

    def test_a_binary_with_the_same_etag_is_kept_from_the_target(self):
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        image = next(row for row in manifest if row["path"] == "assets/logo.png")
        kept = b"existing-image-with-claude-source-metadata"
        (self.target / "assets").mkdir(parents=True)
        (self.target / "assets" / "logo.png").write_bytes(kept)
        (self.target / "design-manifest.json").write_text(
            json.dumps({"project_id": "fixture-project", "files": [image]}),
            encoding="utf-8",
        )
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual((self.target / "assets/logo.png").read_bytes(), kept)
        self.assertEqual(self.preview.requests[SERVE_PREFIX + "assets/logo.png"], 0)

    def test_a_binary_with_a_changed_etag_is_downloaded(self):
        manifest = json.loads(self.manifest.read_text(encoding="utf-8"))
        image = next(row for row in manifest if row["path"] == "assets/logo.png")
        previous = dict(image, etag="older-etag")
        (self.target / "assets").mkdir(parents=True)
        (self.target / "assets" / "logo.png").write_bytes(b"old-image")
        (self.target / "design-manifest.json").write_text(
            json.dumps({"project_id": "fixture-project", "files": [previous]}),
            encoding="utf-8",
        )
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(
            (self.target / "assets/logo.png").read_bytes(),
            self.preview.files["assets/logo.png"],
        )
        self.assertEqual(self.preview.requests[SERVE_PREFIX + "assets/logo.png"], 1)

    def test_a_failed_small_binary_download_exits_2_not_1(self):
        self.preview.files["fonts/body.woff2"] = None
        self.write_manifest([
            {"path": "fonts/body.woff2", "size": 1024, "etag": "font-v1"}
        ])
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("fonts/body.woff2", result.stdout + result.stderr)

    def test_design_handoff_directories_are_skipped(self):
        path = "design_handoff_previous/old.txt"
        self.preview.files[path] = b"must not come down"
        self.write_manifest()
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.target / path).exists())
        self.assertEqual(self.preview.requests[SERVE_PREFIX + path], 0)

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
        self.write_manifest()
        result = self.pull()
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
        self.assertEqual(readme.count("# Claude Design handoff package"), 1)
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
        self.write_manifest()
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

        self.preview.files["styles/app.css"] += b"/* mismatched */\n"
        refused = self.pull()
        self.assertEqual(refused.returncode, 1, refused.stdout + refused.stderr)
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

    def test_the_report_lists_selectors_the_editor_cannot_reach(self):
        self.preview.files["styles/app.css"] += b"\n.a .b .c { color: red; }\n"
        self.write_manifest()
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(".a .b .c", self.report_section("设计检查"))

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
        self.write_manifest()
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        coverage = self.report_section("覆盖")
        self.assertIn("带文字但没有 `data-ui` id：", coverage)
        self.assertIn("p: Unidentified copy", coverage)
        self.assertIn("可点或可输入却没有 `data-ui` id：", coverage)
        self.assertIn("button: Unidentified action", coverage)

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
        self.write_manifest()
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("分类：只改外观或文案", self.report())
        self.assertNotIn("pull 前 handoff package 有本地改动", self.report())
        self.assertIn("screen contract 未给出，合同行文字未核对", self.report())

    def test_a_report_with_problems_still_exits_0(self):
        page = self.preview.files["Component · Demo.dc.html"]
        start = page.index(b'<main data-ui="root">')
        end = page.index(b"</main>", start) + len(b"</main>")
        self.preview.files["Component · Demo.dc.html"] = page[:start] + page[end:]
        self.write_manifest()
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
        self.write_manifest()
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
        self.write_manifest()
        contract = self.work / "screen-contract.yaml"
        contract.write_text(textwrap.dedent("""
            rows:
              - id: demo.open
                trigger: {role: heading, name: "Demo"}
                scenes: ["Component · Demo.ready"]
        """), encoding="utf-8")
        result = self.pull("--contract", str(contract))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = self.report()
        self.assertIn("分类：增删控件或改流转", report)
        self.assertIn("demo.open", report)
        self.assertIn("Demo", report)
        self.assertIn("Updated demo", report)

    def test_a_locally_edited_package_gets_a_note(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        page = self.target / "Component · Demo.dc.html"
        page.write_text(page.read_text(encoding="utf-8") + "\n<!-- local edit -->\n", encoding="utf-8")
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("pull 前 handoff package 有本地改动", self.report())

    def test_an_added_scene_value_is_classified_controls_or_flow(self):
        first = self.pull()
        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.commit_target()
        page = self.preview.files["Component · Demo.dc.html"]
        self.preview.files["Component · Demo.dc.html"] = page.replace(
            b'"options": ["ready", "empty", "future"]',
            b'"options": ["ready", "empty", "added", "future"]',
        )
        self.write_manifest()
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

    def test_without_css_the_report_says_selector_check_was_not_run(self):
        self.preview.files.pop("styles/app.css")
        self.write_manifest()
        result = self.pull()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        design = self.report_section("设计检查")
        self.assertIn("没有 `.css` 文件，选择器未核对", design)
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
        self.write_manifest()
        contract = self.work / "screen-contract.yaml"
        contract.write_text(textwrap.dedent("""
            rows:
              - id: demo.status-copy
                trigger: {role: text, name: "After override"}
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
