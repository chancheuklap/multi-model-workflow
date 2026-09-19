"""story-parity.py: the gate without a browser, and the fixture through Chromium.

The gate tests are the shape of `test_pixel_diff.py`'s `TestNegativeControl`.
The fixture tests are the seam this ticket is tested at: real Chromium, real
files under `fixtures/story/`.
"""

from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / "skills" / "ui-acceptance" / "scripts" / "story-parity.py"
)
REPO = Path(__file__).resolve().parent / "fixtures" / "story" / "repo"
CONTRACT = "docs/specs/story/screen-contract.yaml"


def load():
    spec = importlib.util.spec_from_file_location("story_parity", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["story_parity"] = module
    spec.loader.exec_module(module)
    return module


sp = load()


def story_env(home, extra_env=None):
    env = dict(os.environ)
    # The story judge takes no lease — the story service picks its own port — and
    # this home is here so that a run which did take one could not reach the
    # machine's registry.
    env["MMW_HOME"] = home
    env.pop("STORY_MUTATE", None)
    if extra_env:
        env.update(extra_env)
    return env


def run_story_cmd(home, extra_env=None, timeout=180, cwd=None, pages="demo",
                  contract=None, extra_args=None, out=None):
    env = story_env(home, extra_env)
    owned = out is None
    if owned:
        out = tempfile.mkdtemp(prefix="story-out-")
    argv = ["uv", "run", "python", str(SCRIPT),
            "--contract", contract or CONTRACT, "--pages", pages,
            "--out", str(out)]
    if extra_args:
        argv.extend(extra_args)
    try:
        return subprocess.run(
            argv,
            cwd=cwd or REPO, capture_output=True, text=True, env=env,
            timeout=timeout,
        )
    finally:
        if owned:
            shutil.rmtree(out, ignore_errors=True)


def copy_fixture(cleanup) -> Path:
    """A writable copy of the fixture repository; `cleanup` removes it."""
    tmp = Path(tempfile.mkdtemp(prefix="story-copy-"))
    cleanup(shutil.rmtree, tmp, ignore_errors=True)
    shutil.copytree(REPO, tmp / "repo", dirs_exist_ok=True)
    return tmp / "repo"


def comparison(pixel=None, aria=None, scene="default", viewport="400x300"):
    return sp.Comparison(
        scene, viewport,
        pixel or {"size_equal": True, "pct": 0.0, "pct_unaligned": 0.0,
                  "count": 0, "total": 100, "box": None,
                  "size_a": (10, 10), "size_b": (10, 10)},
        aria or {"changed": 0, "lines_a": 5, "lines_b": 5, "diff": ""},
        [], [], [])


class TestParseOrigin(unittest.TestCase):
    def test_origin_equals_form(self):
        self.assertEqual(sp.parse_origin("origin=http://127.0.0.1:21020\n"),
                         "http://127.0.0.1:21020")

    def test_json_form(self):
        self.assertEqual(sp.parse_origin('{"origin": "http://127.0.0.1:9"}\n'),
                         "http://127.0.0.1:9")

    def test_bare_url(self):
        self.assertEqual(sp.parse_origin("http://127.0.0.1:8\n"),
                         "http://127.0.0.1:8")

    def test_empty(self):
        self.assertIsNone(sp.parse_origin(""))
        self.assertIsNone(sp.parse_origin("listening\n"))


class TestArguments(unittest.TestCase):
    def test_defaults(self):
        args = sp.build_parser().parse_args(
            ["--contract", "c.yaml", "--pages", "demo"])
        self.assertEqual(args.max_pct, 5.0)
        self.assertIsNone(args.scenes)
        self.assertFalse(args.render_only)

    def test_pages_is_required(self):
        with self.assertRaises(SystemExit):
            sp.build_parser().parse_args(["--contract", "c.yaml"])

    def test_no_console_errors_flag(self):
        with self.assertRaises(SystemExit):
            sp.build_parser().parse_args(
                ["--contract", "c.yaml", "--pages", "demo", "--console-errors", "0"])


class TestStoryGate(unittest.TestCase):
    """The printed line and the three exit codes, with no browser."""

    def caught(self):
        return comparison(
            scene="__negative_control__",
            pixel={"size_equal": True, "pct": 23.4, "pct_unaligned": 31.0,
                   "count": 9, "total": 100, "box": [0, 0, 9, 9],
                   "size_a": (10, 10), "size_b": (10, 10)},
            aria={"changed": 28, "lines_a": 30, "lines_b": 2, "diff": ""})

    def test_a_control_that_passed_stops_the_run(self):
        code, lines = sp.story_gate(comparison(scene="__negative_control__"),
                                    [comparison()], 1.0, 0)
        self.assertEqual(code, 2)
        self.assertTrue(lines[0].startswith("NEGATIVE CONTROL FAILED"))
        self.assertFalse(any("STORY" in ln for ln in lines))

    def test_a_control_that_failed_lets_the_scenes_be_read(self):
        self.assertEqual(
            sp.story_gate(self.caught(), [comparison(), comparison(scene="empty")],
                          1.0, 0),
            (0, ["STORY OK 2/2 pixel<=0.0%"]))

    def test_the_ok_line_carries_the_worst_pixel_share(self):
        near = comparison(pixel={"size_equal": True, "pct": 1.52,
                                 "pct_unaligned": 4.0, "count": 3,
                                 "total": 200, "box": [0, 0, 9, 9],
                                 "size_a": (10, 10), "size_b": (10, 10)})
        self.assertEqual(
            sp.story_gate(self.caught(), [comparison(), near], 3.0, 0),
            (0, ["STORY OK 2/2 pixel<=1.52%"]))

    def test_a_diff_line_names_unaligned_and_not_the_class_set(self):
        aria = sp.dr.aria_diff("- paragraph: Alpha scene copy\n",
                               "- paragraph: Alpha scene COPY\n")
        c = comparison(
            pixel={"size_equal": True, "pct": 0.4, "pct_unaligned": 7.2,
                   "count": 1, "total": 250, "box": None,
                   "size_a": (10, 10), "size_b": (10, 10)},
            aria=aria)
        c.classes = {"only_in_baseline": [("btn", 'button "Continue"')],
                     "only_in_impl": [], "changed": 1}
        c.console_impl = ["error: Uncaught TypeError"]
        code, lines = sp.story_gate(self.caught(), [c], 3.0, 0)
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith(
            "DIFF default 400x300 0.4% (unaligned 7.2%)"))
        self.assertIn("aria 2 changed lines", lines[0])
        self.assertNotIn("classes", lines[0])
        self.assertNotIn("console", lines[0])
        self.assertNotIn("class only", "\n".join(lines))
        self.assertEqual(lines[1:], [
            "  baseline  paragraph Alpha scene copy",
            "  impl      paragraph Alpha scene COPY",
        ])

    @unittest.skipUnless(
        importlib.util.find_spec("numpy") is not None,
        "around ranks a numpy mask")
    def test_a_pixel_failure_uses_the_shared_around(self):
        import numpy as np
        mask = np.zeros((50, 80), dtype=bool)
        mask[5, 10] = True
        c = comparison(
            pixel={"size_equal": True, "pct": 12.5, "pct_unaligned": 31.0,
                   "count": 100, "total": 800, "box": [40, 20, 79, 59],
                   "mask": mask, "scale": 4,
                   "size_a": (10, 10), "size_b": (10, 10)})
        c.impl_elements = [
            {"label": 'heading "Demo card"', "x": 0, "y": 0, "w": 320, "h": 200},
            {"label": 'button "Continue"', "x": 40, "y": 20, "w": 80, "h": 24},
        ]
        code, lines = sp.story_gate(self.caught(), [c], 3.0, 0)
        self.assertEqual(code, 1)
        self.assertEqual(lines, [
            "DIFF default 400x300 12.5% (unaligned 31.0%) "
            "— pixel 12.5% > 3.0% (unaligned 31.0%) "
            "around: button \"Continue\", heading \"Demo card\"",
        ])

    def test_class_or_console_alone_does_not_fail_a_scene(self):
        c = comparison()
        c.classes = {"only_in_baseline": [("btn", 'button "Continue"')],
                     "only_in_impl": [], "changed": 1}
        c.console_impl = ["error: Uncaught TypeError"]
        code, lines = sp.story_gate(self.caught(), [c], 3.0, 0)
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["STORY OK 1/1 pixel<=0.0%"])
        vp_code, _ = sp.vp.gate(self.caught(), [c], 3.0, 0)
        self.assertEqual(vp_code, 1)


class TestStoryFixture(unittest.TestCase):
    """Real Chromium against the committed fixture. Precedent: TestShrunkPixels."""

    @classmethod
    def setUpClass(cls):
        if not shutil.which("uv"):
            raise AssertionError(
                "uv is missing; the story fixture cannot run and AC4 must not "
                "print all passed")
        cls.home = tempfile.mkdtemp(prefix="mmw-story-parity-home-")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)

    def run_story(self, extra_env=None, timeout=180, cwd=None, pages="demo",
                  contract=None, extra_args=None):
        return run_story_cmd(
            self.home, extra_env=extra_env, timeout=timeout, cwd=cwd,
            pages=pages, contract=contract, extra_args=extra_args)

    def copied_fixture(self) -> Path:
        """A writable copy of the fixture repository, removed when the test ends."""
        return copy_fixture(self.addCleanup)

    def test_three_equal_scenes_print_story_ok(self):
        proc = self.run_story()
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertRegex(proc.stdout, r"^STORY OK 3/3 pixel<=")
        self.assertNotIn("NEGATIVE CONTROL FAILED", proc.stdout)

    def test_a_changed_word_prints_two_tree_lines_and_exits_1(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "copy"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        diffs = [ln for ln in proc.stdout.splitlines() if ln.startswith("DIFF ")]
        self.assertEqual(len(diffs), 1, proc.stdout)
        self.assertIn("alpha", diffs[0])
        self.assertIn("aria 2 changed lines", diffs[0])
        self.assertIn("Alpha scene copy", proc.stdout)
        self.assertIn("Alpha scene COPY", proc.stdout)

    def test_a_changed_colour_fails_on_pixels(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "color"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        diffs = [ln for ln in proc.stdout.splitlines() if ln.startswith("DIFF ")]
        self.assertEqual(len(diffs), 3, proc.stdout)
        for line in diffs:
            self.assertRegex(line, rf"pixel [0-9.]+% > {re.escape(str(sp.DEFAULT_MAX_PCT))}%")
            self.assertNotIn("aria", line)

    def test_a_mount_the_contract_does_not_declare_exits_2(self):
        proc = self.run_story(pages="no-such-page")
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("does not declare", proc.stderr)

    def test_no_target_json_exits_2(self):
        root = self.copied_fixture()
        shutil.rmtree(root / ".mmw")
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("target.json", proc.stderr)

    def test_target_json_without_stories_exits_2(self):
        root = self.copied_fixture()
        (root / ".mmw" / "target.json").write_text("{}\n", encoding="utf-8")
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("stories", proc.stderr)

    def test_an_unknown_scene_the_stories_server_answers_404_exits_2(self):
        """fixtures/story/repo/stories/serve.py 404s an unknown scene; this is
        the path that raises SystemExit('story page 404: …') and returns 2."""
        root = self.copied_fixture()
        contract = root / CONTRACT
        text = contract.read_text(encoding="utf-8")
        text = text.replace(
            '  gamma:\n    page: "Component · Demo.dc.html"\n',
            '  gamma:\n    page: "Component · Demo.dc.html"\n'
            '  missing:\n    page: "Component · Demo.dc.html"\n',
        )
        contract.write_text(text, encoding="utf-8")
        self.assertIn("missing:", contract.read_text(encoding="utf-8"))
        proc = self.run_story(cwd=root, extra_args=["--scenes", "missing"])
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("story page 404", proc.stderr)
        self.assertIn("scene=missing", proc.stderr)

    def test_a_server_the_stories_command_started_is_gone_after_the_run(self):
        """fixtures/story/repo/stories/launch.py holds serve.py as a child and forwards
        no signal, so ending only the stories command would leave serve.py running."""
        root = self.copied_fixture()
        (root / ".mmw" / "target.json").write_text(
            '{"stories": "python3 -u stories/launch.py"}\n', encoding="utf-8")
        pid_file = root / "child.pid"
        proc = self.run_story(cwd=root, extra_env={"STORY_CHILD_PID": str(pid_file)})
        pid = int(pid_file.read_text(encoding="utf-8"))
        self.addCleanup(end_if_running, pid)
        self.assertFalse(running(pid), f"serve.py (pid {pid}) outlived story-parity.py")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)


class TestRenderOnlyValues(unittest.TestCase):
    """`--render-only` writes one design-values file per scene and viewport.

    Numbers come from the fixture CSS: `.demo` is 320×200 with 16px padding;
    `h1` is 20px/700 with 8px bottom margin and 24px line-height; `p` has 12px
    bottom margin. The nested inner and the hidden node are out of flow so they
    take no layout.
    """

    VIEWPORT = "400x300"
    SCENES = ("alpha", "beta", "gamma")

    @classmethod
    def setUpClass(cls):
        if not shutil.which("uv"):
            raise AssertionError(
                "uv is missing; the story fixture cannot run and AC1 must not "
                "print all passed")
        cls.home = tempfile.mkdtemp(prefix="mmw-render-only-home-")
        cls.out = tempfile.mkdtemp(prefix="mmw-render-only-out-")
        cls.proc = run_story_cmd(
            cls.home, extra_args=["--render-only"], out=cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.home, ignore_errors=True)
        shutil.rmtree(cls.out, ignore_errors=True)

    def values_path(self, scene, viewport=None):
        tag = viewport or self.VIEWPORT
        return Path(self.out) / "values" / "demo" / f"{scene}-{tag}.json"

    def values(self, scene="alpha"):
        path = self.values_path(scene)
        self.assertTrue(path.is_file(), f"missing {path}: {self.proc.stderr}{self.proc.stdout}")
        return json.loads(path.read_text(encoding="utf-8"))

    def by_id(self, uid, scene="alpha"):
        for item in self.values(scene):
            if item["id"] == uid:
                return item
        self.fail(f"no data-ui {uid!r} in {scene}: {[i['id'] for i in self.values(scene)]}")

    def test_render_only_writes_one_values_file_per_scene_and_viewport(self):
        self.assertEqual(self.proc.returncode, 0, self.proc.stderr + self.proc.stdout)
        values_root = Path(self.out) / "values"
        written = sorted(
            p.relative_to(values_root).as_posix() for p in values_root.rglob("*.json"))
        self.assertEqual(written, [
            "demo/alpha-400x300.json",
            "demo/beta-400x300.json",
            "demo/gamma-400x300.json",
        ])
        self.assertFalse((values_root / "demo-card").exists())
        for scene in self.SCENES:
            rows = json.loads(self.values_path(scene).read_text(encoding="utf-8"))
            self.assertIsInstance(rows, list)
            self.assertGreater(len(rows), 0)
            for row in rows:
                self.assertEqual(
                    set(row),
                    {"id", "visible", "text", "size", "ancestor", "offset",
                     "previous", "gap", "style"})

    def test_render_only_values_carry_the_design_numbers(self):
        title = self.by_id("title")
        self.assertEqual(title["style"]["font-size"], "20px")
        self.assertEqual(title["style"]["font-weight"], "700")

    def test_text_is_read_from_the_interpolated_layer(self):
        self.assertEqual(self.by_id("body", "alpha")["text"], "Alpha scene copy")
        self.assertEqual(self.by_id("body", "beta")["text"], "Beta scene copy")
        self.assertEqual(self.by_id("body", "gamma")["text"], "Gamma scene copy")

    def test_text_excludes_deeper_data_ui_elements(self):
        body = self.by_id("body")
        inner = self.by_id("inner")
        self.assertGreater(inner["size"][0] * inner["size"][1], 0)
        self.assertEqual(inner["text"], "inner copy")
        self.assertNotIn("inner copy", body["text"])
        self.assertEqual(body["text"], "Alpha scene copy")

    def test_values_record_ancestor_offset_and_previous_gap(self):
        title = self.by_id("title")
        body = self.by_id("body")
        self.assertEqual(title["ancestor"], "root")
        self.assertEqual(title["offset"], [16, 16])
        self.assertEqual(body["ancestor"], "root")
        self.assertEqual(body["previous"], "title")
        self.assertEqual(body["gap"], [-288, 8])

    def test_a_hidden_element_reads_not_visible(self):
        hidden = self.by_id("hidden")
        self.assertEqual(hidden["visible"], False)
        self.assertGreater(hidden["size"][0] * hidden["size"][1], 0)
        self.assertEqual(hidden["text"], "hidden copy")
        inner = self.by_id("inner")
        self.assertEqual(inner["visible"], False)
        self.assertGreater(inner["size"][0] * inner["size"][1], 0)

    def test_a_top_level_element_has_no_ancestor_offset(self):
        root = self.by_id("root")
        self.assertIsNone(root["ancestor"])
        self.assertIsNone(root["offset"])
        self.assertIsNone(root["previous"])
        self.assertIsNone(root["gap"])

    def test_render_only_needs_no_target_json(self):
        root = copy_fixture(self.addCleanup)
        shutil.rmtree(root / ".mmw")
        out = Path(tempfile.mkdtemp(prefix="story-render-only-"))
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        proc = run_story_cmd(
            self.home, cwd=root, extra_args=["--render-only"], out=out)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertTrue((out / "values" / "demo" / "alpha-400x300.json").is_file())


def running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True


def end_if_running(pid: int) -> None:
    if running(pid):
        os.kill(pid, signal.SIGKILL)


if __name__ == "__main__":
    unittest.main()
