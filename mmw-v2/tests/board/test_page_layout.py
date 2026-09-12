"""The whole page in a real browser: which columns the shell shows.

The detail column is not a permanent fixture of the page. With no card picked there is
nothing to put in it, so `app.mjs` leaves its slot empty and the stylesheet takes the
column out of the grid; the canvas has that width instead. Picking a card brings it back.
"""

from __future__ import annotations

import os
import unittest

from playwright.sync_api import sync_playwright

from board_process import RunningBoard
from test_board_data import FAKE_BIN, scenario


def running_board(data):
    path = str(FAKE_BIN) + os.pathsep + os.environ.get("PATH", "")
    return RunningBoard(environment={"PATH": path}, fixture=data)


def shell(page) -> dict:
    return page.evaluate("""() => {
      const root = document.querySelector('.app-shell');
      const slot = document.querySelector('[data-mount="detail"]');
      const canvas = document.querySelector('[data-mount="canvas"]');
      return {
        columns: getComputedStyle(root).gridTemplateColumns.split(' ').length,
        panels: document.querySelectorAll('[data-screen="detail"]').length,
        slotShown: getComputedStyle(slot).display !== 'none',
        canvasWidth: Math.round(canvas.getBoundingClientRect().width),
      };
    }""")


class PageLayoutTest(unittest.TestCase):
    def test_the_detail_column_is_there_only_while_a_card_is_picked(self):
        with running_board(scenario()) as board, sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})
            page.goto(board.origin, wait_until="networkidle")
            page.wait_for_selector(".card", timeout=30_000)

            nothing_picked = shell(page)
            self.assertEqual((nothing_picked["panels"], nothing_picked["slotShown"]), (0, False))
            self.assertEqual(nothing_picked["columns"], 2)

            page.locator(".card-hit").first.click()
            page.wait_for_selector('[data-screen="detail"]', timeout=10_000)
            picked = shell(page)
            self.assertEqual((picked["panels"], picked["slotShown"]), (1, True))
            self.assertEqual(picked["columns"], 3)
            self.assertLess(picked["canvasWidth"], nothing_picked["canvasWidth"])

            page.keyboard.press("Escape")
            page.wait_for_selector('[data-screen="detail"]', state="detached", timeout=10_000)
            self.assertEqual(shell(page)["columns"], 2)
            browser.close()


if __name__ == "__main__":
    unittest.main()
