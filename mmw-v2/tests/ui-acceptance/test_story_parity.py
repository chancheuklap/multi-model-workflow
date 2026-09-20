"""story-parity.py: its negative-control gate and real Chromium fixture seam."""

from __future__ import annotations

import importlib.util
import json
import os
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
        self.assertIsNone(args.scenes)
        self.assertFalse(args.render_only)

    def test_pages_is_required(self):
        with self.assertRaises(SystemExit):
            sp.build_parser().parse_args(["--contract", "c.yaml"])

    def test_no_console_errors_flag(self):
        with self.assertRaises(SystemExit):
            sp.build_parser().parse_args(
                ["--contract", "c.yaml", "--pages", "demo", "--console-errors", "0"])

    def test_max_pct_is_not_an_option(self):
        with self.assertRaises(SystemExit):
            sp.build_parser().parse_args(
                ["--contract", "c.yaml", "--pages", "demo", "--max-pct", "3"])


class TestStoryGate(unittest.TestCase):
    """The two negative controls at the gate, with no browser."""

    FONT = [sp.ElementDifference("root", "font-size", "23px", "16px")]
    MISSING = [sp.ElementDifference("root", "missing")]

    def test_a_control_that_reports_nothing_is_exit_2(self):
        for font, missing, named in (([], self.MISSING, "font-size"),
                                     (self.FONT, [], "data-ui")):
            with self.subTest(named=named):
                code, lines = sp.negative_control_gate(font, missing)
                self.assertEqual(code, 2)
                self.assertTrue(lines[0].startswith("NEGATIVE CONTROL FAILED"))
                self.assertIn(named, lines[0])
                self.assertIn("then rerun", lines[0])

    def test_both_controls_caught_continue(self):
        self.assertEqual(sp.negative_control_gate(self.FONT, self.MISSING), (0, []))

    def test_a_missing_difference_satisfies_the_design_perturbation_control(self):
        self.assertEqual(sp.negative_control_gate(self.MISSING, self.MISSING), (0, []))


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
                  contract=None, extra_args=None, out=None):
        return run_story_cmd(
            self.home, extra_env=extra_env, timeout=timeout, cwd=cwd,
            pages=pages, contract=contract, extra_args=extra_args, out=out)

    def copied_fixture(self) -> Path:
        """A writable copy of the fixture repository, removed when the test ends."""
        return copy_fixture(self.addCleanup)

    def test_three_equal_scenes_print_story_ok(self):
        proc = self.run_story()
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "STORY OK 3/3")
        self.assertNotIn("NEGATIVE CONTROL FAILED", proc.stdout)

    def test_a_13px_value_against_26px_is_one_font_size_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "font-size"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 metric font-size "
                         "design=13px product=26px")

    def test_an_element_moved_alone_is_one_position_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "move-alone"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 body position "
                         "design=16,48 product=16,78")

    def test_a_block_moved_down_as_a_whole_is_no_diff(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "block-down"})
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "STORY OK 3/3")

    def test_a_moved_parent_is_one_position_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "move-parent"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 group position "
                         "design=16,84 product=16,114")

    def test_a_sibling_pushed_by_a_taller_one_is_not_reported(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "taller-previous"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 title size "
                         "design=288x24 product=288x54")

    def test_size_beyond_two_pixels_is_a_size_line(self):
        ten = self.run_story(extra_env={"STORY_MUTATE": "size-10"})
        self.assertEqual(ten.returncode, 1, ten.stderr + ten.stdout)
        self.assertEqual(ten.stdout.strip(),
                         "DIFF demo alpha 400x300 swatch size "
                         "design=80x80 product=90x80")
        two = self.run_story(extra_env={"STORY_MUTATE": "size-2"})
        self.assertEqual(two.returncode, 0, two.stderr + two.stdout)
        self.assertEqual(two.stdout.strip(), "STORY OK 3/3")

    def test_an_element_the_product_lacks_is_missing(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "missing"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 metric missing")

    def test_an_element_only_the_product_has_is_extra(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "extra"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 product-only extra")

    def test_a_product_without_data_ui_reports_missing_elements(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "no-ids"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertNotIn("NEGATIVE CONTROL FAILED", proc.stdout)
        self.assertIn("DIFF demo alpha 400x300 root missing", proc.stdout.splitlines())

    def test_a_wrapper_the_product_adds_is_no_diff(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "wrapper"})
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "STORY OK 3/3")

    def test_an_element_drawn_hidden_is_one_visible_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "hidden-parent"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 group visible "
                         "design=yes product=no")

    def test_an_element_under_another_parent_is_a_parent_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "other-parent"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 metric parent "
                         "design=group product=root")

    def test_a_changed_word_is_one_text_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "copy"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 body text "
                         "design=Alpha scene copy product=Alpha scene COPY")

    def test_a_changed_weight_is_a_font_weight_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "weight"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 metric font-weight "
                         "design=700 product=400")

    def test_a_changed_colour_is_a_color_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "color"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 body color "
                         "design=rgb(26, 26, 26) product=rgb(255, 45, 85)")

    def test_a_changed_background_is_a_background_color_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "background"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 root background-color "
                         "design=rgb(244, 241, 236) product=rgb(255, 255, 255)")

    def test_a_changed_radius_is_a_border_radius_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "radius"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 group border-radius "
                         "design=0px product=8px")

    def test_repeated_ids_pair_in_document_order(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "repeat-missing"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 repeat#3 missing")

    def test_repeated_ids_pair_in_document_order_when_product_has_one(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "repeat-one"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip().splitlines(), [
            "DIFF demo alpha 400x300 repeat#2 missing",
            "DIFF demo alpha 400x300 repeat#3 missing",
        ])

    def test_a_pixel_only_difference_keeps_story_ok_and_writes_the_diff_image(self):
        out = Path(tempfile.mkdtemp(prefix="story-pixel-evidence-"))
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        proc = self.run_story(extra_env={"STORY_MUTATE": "pixel-only"}, out=out)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "STORY OK 3/3")
        diff = out / "media" / "alpha-400x300-diff.png"
        self.assertTrue(diff.is_file(), f"missing {diff}")
        self.assertGreater(diff.stat().st_size, 0)
        from PIL import Image
        with Image.open(diff) as image:
            self.assertIsNotNone(image.getbbox())

    def test_an_app_page_mount_is_compared(self):
        proc = self.run_story(pages="app")
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "STORY OK 1/1")

    def test_a_design_page_without_data_ui_fails_the_negative_control(self):
        proc = self.run_story(pages="legacy")
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertTrue(proc.stdout.startswith("NEGATIVE CONTROL FAILED"), proc.stdout)
        self.assertNotIn("STORY OK", proc.stdout)

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

    def _rewrite_contract(self, root: Path, transform) -> None:
        path = root / CONTRACT
        path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8")

    def _drop_contract_key(self, root: Path, key: str) -> None:
        prefix = f"{key}:"
        self._rewrite_contract(
            root,
            lambda text: "".join(
                line for line in text.splitlines(True) if not line.startswith(prefix)))

    def test_a_product_frame_drawn_wrong_is_a_size_line(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "narrow-frame"})
        self.assertEqual(proc.returncode, 1, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(),
                         "DIFF demo alpha 400x300 root size "
                         "design=320x200 product=300x200")

    def test_a_contract_without_viewports_exits_2_naming_it(self):
        root = self.copied_fixture()
        self._drop_contract_key(root, "viewports")
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("viewports", proc.stderr)
        self.assertIn("then rerun", proc.stderr)

    def test_a_contract_without_locale_exits_2_naming_it(self):
        root = self.copied_fixture()
        self._drop_contract_key(root, "locale")
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("locale", proc.stderr)
        self.assertIn("story-parity.md", proc.stderr)
        self.assertIn("then rerun", proc.stderr)

    def test_the_contract_locale_reaches_both_sides(self):
        root = self.copied_fixture()
        self._rewrite_contract(root, lambda text: text.replace(
            "locale: zh-CN\n", "locale: en-US\n"))
        design = (root / "docs" / "prototypes" / "story" / "claude-design"
                  / "Component · Demo.dc.html")
        design.write_text(
            design.read_text(encoding="utf-8").replace(
                '<span data-ui="hidden"',
                '<span data-ui="locale-probe" style="position:absolute;left:0;top:0;'
                'width:48px;height:12px;font-size:10px;line-height:12px;'
                'overflow:hidden"></span>\n        <span data-ui="hidden"',
                1),
            encoding="utf-8")
        support = (root / "docs" / "prototypes" / "story" / "claude-design"
                   / "support.js")
        support.write_text(
            support.read_text(encoding="utf-8")
            + "\n(function () {\n"
              "  const apply = () => {\n"
              "    const els = document.querySelectorAll('[data-ui=\"locale-probe\"]');\n"
              "    if (!els.length) return false;\n"
              "    for (const el of els) {\n"
              "      if (el.getAttribute('data-filled') === '1') continue;\n"
              "      el.textContent = navigator.language;\n"
              "      el.setAttribute('data-filled', '1');\n"
              "    }\n"
              "    return true;\n"
              "  };\n"
              "  if (apply()) return;\n"
              "  const obs = new MutationObserver(() => { if (apply()) obs.disconnect(); });\n"
              "  obs.observe(document.documentElement, {subtree: true, childList: true});\n"
              "})();\n",
            encoding="utf-8")
        page = root / "stories" / "index.html"
        page.write_text(
            page.read_text(encoding="utf-8").replace(
                "'<span data-ui=\"hidden\"",
                "'<span data-ui=\"locale-probe\" style=\"position:absolute;left:0;top:0;"
                "width:48px;height:12px;font-size:10px;line-height:12px;overflow:hidden\">'"
                " + navigator.language + '</span>' +\n        '<span data-ui=\"hidden\"",
                1),
            encoding="utf-8")
        out = Path(tempfile.mkdtemp(prefix="story-locale-"))
        self.addCleanup(shutil.rmtree, out, ignore_errors=True)
        rendered = self.run_story(
            cwd=root, extra_args=["--render-only", "--scenes", "alpha"], out=out)
        self.assertEqual(rendered.returncode, 0, rendered.stderr + rendered.stdout)
        values = json.loads(
            (out / "values" / "demo" / "alpha-400x300.json").read_text(encoding="utf-8"))
        probe = next(item for item in values if item["id"] == "locale-probe")
        self.assertEqual(probe["text"], "en-US")
        compared = self.run_story(
            cwd=root, extra_args=["--scenes", "alpha"], out=out)
        self.assertEqual(compared.returncode, 0, compared.stderr + compared.stdout)
        self.assertEqual(compared.stdout.strip(), "STORY OK 1/1")
        product_aria = (out / "media" / "alpha-400x300-impl.aria.yml").read_text(
            encoding="utf-8")
        self.assertIn("en-US", product_aria)

    def test_volatile_values_in_the_contract_exits_2_naming_it(self):
        root = self.copied_fixture()
        self._rewrite_contract(root, lambda text: text.replace(
            "rows: []\n",
            "volatile_values:\n"
            "  - page: \"Component · Demo.dc.html\"\n"
            "    trigger: { role: text, name: \"13\" }\n"
            "    reason: \"test\"\n"
            "rows: []\n",
            1))
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("volatile_values", proc.stderr)
        self.assertIn("这个键已不被 judge 执行", proc.stderr)
        self.assertIn("删掉它或把控件改回 Claude Design", proc.stderr)
        self.assertIn("then rerun", proc.stderr)

    def test_an_empty_volatile_values_list_still_passes(self):
        root = self.copied_fixture()
        self._rewrite_contract(root, lambda text: text.replace(
            "rows: []\n", "volatile_values: []\nrows: []\n", 1))
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "STORY OK 3/3")

    def test_a_retired_id_with_a_trigger_exits_2_naming_it(self):
        root = self.copied_fixture()
        self._rewrite_contract(root, lambda text: text.replace(
            "rows: []\n",
            "retired_ids:\n"
            "  - id: demo.old\n"
            "    note: \"retired\"\n"
            "    page: \"Component · Demo.dc.html\"\n"
            "    trigger: { role: button, name: \"Continue\" }\n"
            "rows: []\n",
            1))
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("retired_ids", proc.stderr)
        self.assertIn("这个键已不被 judge 执行", proc.stderr)
        self.assertIn("删掉它或把控件改回 Claude Design", proc.stderr)
        self.assertIn("then rerun", proc.stderr)

    def test_a_retired_id_without_a_trigger_still_passes(self):
        root = self.copied_fixture()
        self._rewrite_contract(root, lambda text: text.replace(
            "rows: []\n",
            "retired_ids:\n"
            "  - id: demo.old\n"
            "    note: \"retired\"\n"
            "rows: []\n",
            1))
        proc = self.run_story(cwd=root)
        self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)
        self.assertEqual(proc.stdout.strip(), "STORY OK 3/3")

    def test_a_story_page_carrying_sc_interp_exits_2(self):
        proc = self.run_story(extra_env={"STORY_MUTATE": "sc-interp"})
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("sc-interp", proc.stderr)
        self.assertIn("alpha", proc.stderr)
        self.assertIn("then rerun", proc.stderr)

    def test_each_claude_design_runtime_trace_exits_2(self):
        for mutate, named in (("dc-tpl", "data-dc-tpl"),
                              ("dc-script", "data-dc-script"),
                              ("dc-root", "dc-root")):
            with self.subTest(mutate=mutate):
                proc = self.run_story(extra_env={"STORY_MUTATE": mutate})
                self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
                self.assertIn(named, proc.stderr)
                self.assertIn("alpha", proc.stderr)
                self.assertIn("then rerun", proc.stderr)

    def test_render_only_refuses_a_contract_without_locale(self):
        root = self.copied_fixture()
        self._drop_contract_key(root, "locale")
        proc = self.run_story(cwd=root, extra_args=["--render-only"])
        self.assertEqual(proc.returncode, 2, proc.stderr + proc.stdout)
        self.assertIn("locale", proc.stderr)
        self.assertIn("story-parity.md", proc.stderr)
        self.assertIn("then rerun", proc.stderr)

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
                    {"id", "interactive", "visible", "text", "size", "ancestor", "offset",
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
