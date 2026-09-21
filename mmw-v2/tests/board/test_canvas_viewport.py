"""The canvas viewport in a real browser: what a redraw keeps and what it refits.

Pan and zoom belong to the person looking at the canvas, not to the data behind it. A
redraw of the same task — the minute's read of GitHub, a card picked, the detail column
opening beside it — leaves the viewport where the reader put it, and only a different task
is fitted afresh. A card picked anywhere but the canvas (the top bar's 需要你) can land
outside the viewport, so the canvas pans by the smallest amount that brings it in. A read
whose data is identical to what is already on screen rebuilds no column at all.
"""

from __future__ import annotations

import os
import re
import unittest

from playwright.sync_api import sync_playwright

from board_process import RunningBoard
from test_board_data import FAKE_BIN, container, scenario, tree_fixture


WHERE_SELECTED = """() => {
  const card = document.querySelector('[data-ui="画布.ticket-card"].on, [data-ui="画布.decision-card"].on, [data-ui="画布.container-card"].on');
  if (!card) return null;
  const canvas = document.querySelector('[data-ui="画布.root"]').getBoundingClientRect();
  const box = card.getBoundingClientRect();
  return {left: box.left - canvas.left, right: box.right - canvas.left, width: canvas.width};
}"""


def two_tasks():
    """Ticket #12 with its decision child still open, plus a second task to switch to."""
    data = scenario()
    data["comment_active"]["12"] = 1
    spec30 = container(30, "lone spec", [container(31, "its ticket", [], ["mmw:ticket"])],
                       ["mmw:spec"])
    spec30["subIssuesSummary"] = {"total": 1, "completed": 0}
    data["specs"] = [{"number": 10, "title": "first spec", "state": "OPEN",
                      "labels": [{"name": "mmw:spec"}]},
                     {"number": 30, "title": "lone spec", "state": "OPEN",
                      "labels": [{"name": "mmw:spec"}]}]
    data["trees"] = [tree_fixture(), spec30]
    data["tree_by_root"] = {"1": 0, "30": 1}
    return data


def transform(page):
    return page.evaluate("() => document.querySelector('.world').style.transform")


def pan(page, dx, dy):
    """Drag the canvas from a spot clear of the zoom bar and the legend."""
    box = page.locator('[data-ui="画布.root"]').bounding_box()
    start = (box["x"] + 60, box["y"] + box["height"] - 40)
    page.mouse.move(*start)
    page.mouse.down()
    page.mouse.move(start[0] + dx, start[1] + dy, steps=8)
    page.mouse.up()


def read_github(page):
    with page.expect_response("**/api/board/refresh"):
        page.locator('[data-ui="顶栏.refresh"]').click()
    page.wait_for_timeout(300)


def remember_canvas(page):
    page.evaluate("() => { window.__world = document.querySelector('.world'); }")


def canvas_is_the_same_node(page):
    return page.evaluate("() => window.__world === document.querySelector('.world')")


def view(page):
    value = transform(page)
    match = re.fullmatch(
        r"translate\((-?[\d.]+)px, (-?[\d.]+)px\) scale\(([\d.]+)\)", value
    )
    if not match:
        raise AssertionError(f"unexpected canvas transform: {value}")
    return tuple(float(part) for part in match.groups())


class CanvasViewportTest(unittest.TestCase):
    def test_the_viewport_survives_every_redraw_of_the_same_task(self):
        data = two_tasks()
        path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
        with RunningBoard(environment={"PATH": path}, fixture=data) as board, \
                sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(board.origin, wait_until="networkidle")
            page.wait_for_selector(".card", timeout=30_000)

            pan(page, 100, -60)
            panned = transform(page)
            self.assertNotEqual(panned, "translate(20px, 12px) scale(1)")

            page.locator('[data-ui="画布.ticket-card.open"][aria-label="#12 blocked work"]').click()
            page.wait_for_selector('[data-screen="detail"]', timeout=10_000)
            self.assertEqual(transform(page), panned, "picking a card moved the canvas")

            remember_canvas(page)
            read_github(page)
            self.assertEqual(transform(page), panned, "a read of GitHub moved the canvas")
            self.assertTrue(canvas_is_the_same_node(page),
                            "a read that changed nothing rebuilt the canvas anyway")

            board.write_fixture({**data, "comment_active": {**data["comment_active"], "12": 3}})
            read_github(page)
            self.assertEqual(transform(page), panned, "a read with new data moved the canvas")
            self.assertFalse(canvas_is_the_same_node(page),
                             "a read with new data left the old canvas on screen")
            browser.close()

    def test_a_card_picked_off_the_canvas_is_panned_into_view(self):
        path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
        with RunningBoard(environment={"PATH": path}, fixture=two_tasks()) as board, \
                sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(board.origin, wait_until="networkidle")
            page.wait_for_selector(".card", timeout=30_000)

            pan(page, -640, 0)
            zoom = page.locator('[data-ui="画布.zoom.level"]').text_content()
            page.locator("button.counter.hot").click()
            page.wait_for_selector('[data-screen="detail"]', timeout=10_000)
            where = page.evaluate(WHERE_SELECTED)
            self.assertIsNotNone(where, "需要你 selected a card the canvas does not draw")
            self.assertGreaterEqual(where["left"], 0)
            self.assertLessEqual(where["right"], where["width"])
            self.assertEqual(page.locator('[data-ui="画布.zoom.level"]').text_content(), zoom,
                             "bringing a card into view changed the zoom")
            browser.close()

    def test_f_fits_the_whole_tree(self):
        path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
        with RunningBoard(environment={"PATH": path}, fixture=two_tasks()) as board, \
                sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(board.origin, wait_until="networkidle")
            page.wait_for_selector('[data-ui="画布.ticket-card"]', timeout=30_000)

            pan(page, 180, -90)
            moved = transform(page)
            page.keyboard.press("F")
            page.wait_for_timeout(50)
            self.assertNotEqual(transform(page), moved)
            bounds = page.evaluate("""() => {
              const canvas = document.querySelector('[data-ui="画布.root"]').getBoundingClientRect();
              const world = document.querySelector('.world').getBoundingClientRect();
              return {left: world.left - canvas.left, top: world.top - canvas.top,
                right: world.right - canvas.right, bottom: world.bottom - canvas.bottom};
            }""")
            self.assertGreaterEqual(bounds["left"], 0)
            self.assertGreaterEqual(bounds["top"], 0)
            self.assertLessEqual(bounds["right"], 0)
            self.assertLessEqual(bounds["bottom"], 0)
            browser.close()

    def test_cmd_wheel_zoom_stays_between_30_and_160_percent(self):
        path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
        with RunningBoard(environment={"PATH": path}, fixture=two_tasks()) as board, \
                sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(board.origin, wait_until="networkidle")
            canvas = page.locator('[data-ui="画布.root"]')
            canvas.wait_for(timeout=30_000)
            box = canvas.bounding_box()
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

            page.keyboard.down("Meta")
            for _ in range(4):
                page.mouse.wheel(0, -1000)
            page.keyboard.up("Meta")
            self.assertEqual(page.locator('[data-ui="画布.zoom.level"]').inner_text(), "160%")

            page.keyboard.down("Meta")
            for _ in range(4):
                page.mouse.wheel(0, 1000)
            page.keyboard.up("Meta")
            self.assertEqual(page.locator('[data-ui="画布.zoom.level"]').inner_text(), "30%")
            browser.close()

    def test_drag_pans_the_canvas(self):
        path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
        with RunningBoard(environment={"PATH": path}, fixture=two_tasks()) as board, \
                sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(board.origin, wait_until="networkidle")
            page.wait_for_selector('[data-ui="画布.root"]', timeout=30_000)
            before = view(page)
            pan(page, 80, 40)
            after = view(page)
            self.assertAlmostEqual(after[0] - before[0], 80, delta=0.1)
            self.assertAlmostEqual(after[1] - before[1], 40, delta=0.1)
            self.assertEqual(after[2], before[2])
            browser.close()

    def test_another_task_is_fitted_afresh(self):
        path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
        with RunningBoard(environment={"PATH": path}, fixture=two_tasks()) as board, \
                sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(board.origin, wait_until="networkidle")
            page.wait_for_selector(".card", timeout=30_000)

            pan(page, 100, -60)
            panned = transform(page)
            page.locator("nav.tasks button.task", has_text="lone spec").click()
            page.wait_for_timeout(300)
            self.assertNotEqual(transform(page), panned,
                                "another task kept the previous task's viewport")

            pan(page, 80, 40)
            moved = transform(page)
            page.locator("nav.tasks button.task", has_text="#1").click()
            page.wait_for_timeout(300)
            self.assertNotEqual(transform(page), moved,
                                "coming back to a task kept the other task's viewport")
            browser.close()


if __name__ == "__main__":
    unittest.main()
