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

    def test_an_empty_offline_root_refuses_without_changing_the_target(self):
        page = self.preview.files["Component · Demo.dc.html"]
        start = page.index(b'<main data-ui="root">')
        end = page.index(b"</main>", start) + len(b"</main>")
        self.preview.files["Component · Demo.dc.html"] = page[:start] + page[end:]
        self.write_manifest()
        self.target.mkdir()
        (self.target / "existing.txt").write_text("unchanged", encoding="utf-8")
        result = self.pull()
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual((self.target / "existing.txt").read_text(), "unchanged")

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


if __name__ == "__main__":
    unittest.main()
