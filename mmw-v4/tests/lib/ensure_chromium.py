"""Give the Playwright this interpreter resolved to the Chromium build it needs, and prove it starts.

Usage, under the same `uv run --with playwright…` the suite runs its browser tests with:

    uv run --with playwright python mmw-v4/tests/lib/ensure_chromium.py

`playwright install chromium` downloads the build only when it is absent, so a second run
costs a fraction of a second. PLAYWRIGHT_SKIP_BROWSER_GC keeps the installer from deleting
builds it believes unused: another checkout's Playwright may still need them.

Exit 0: Chromium starts. Exit 2: it cannot start on this machine, which is the environment,
not the product; the suite exits 2 in turn and scripts/check reports CHECK CANNOT RUN.
"""
import os
import subprocess
import sys
from importlib.metadata import version


def main() -> int:
    playwright = version("playwright")
    env = {**os.environ, "PLAYWRIGHT_SKIP_BROWSER_GC": "1"}
    install = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                             env=env, capture_output=True, text=True)
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as pw:
            pw.chromium.launch(headless=True).close()
    except Exception as exc:
        reason = (str(exc).strip().splitlines() or [type(exc).__name__])[0]
        installer = [line.strip() for line in (install.stdout + install.stderr).splitlines()
                     if "Error" in line or "Failed" in line]
        print(f"ENVIRONMENT: Chromium for Playwright {playwright} cannot start: {reason}", file=sys.stderr)
        if install.returncode != 0:
            print(f"`python -m playwright install chromium` exited {install.returncode}:", file=sys.stderr)
            for line in installer[:4]:
                print(f"    {line}", file=sys.stderr)
        print("Install that build (network needed), then re-run the suite.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
