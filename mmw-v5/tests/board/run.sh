#!/usr/bin/env bash
# Exercise the V5 board with temporary homes and fake external services.
# Browser tests use an already cached Playwright and Chromium, without downloading.
set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if ! uv run --offline --quiet --with playwright python -c 'from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    browser.close()'; then
  echo 'cannot run: cached Playwright or Chromium is unavailable; prepare the browser test environment before retrying' >&2
  exit 2
fi
uv run --offline --quiet --with playwright python -m unittest discover -s "$HERE"
node --test --test-reporter=tap "$HERE"/*.test.mjs
