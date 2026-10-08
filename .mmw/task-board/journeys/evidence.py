"""What a journey of this repository writes when it fails, shared by every journey here.

The four file names are the ones `references/journey.md` of the ui-acceptance skill asks for.
"""

from __future__ import annotations

import os
from pathlib import Path


def first_line(exc: BaseException) -> str:
    text = str(exc).strip()
    return text.splitlines()[0] if text else type(exc).__name__


def write_evidence(page, context, console_errors: list[str], failed_requests: list[str]) -> None:
    """Write the four failure files while the page is still open.

    A capture that fails is absent from the directory. The other files are still written.
    """
    raw = os.environ.get("MMW_EVIDENCE_DIR")
    if not raw:
        return
    dest = Path(raw)
    if page is not None:
        try:
            page.screenshot(path=str(dest / "screenshot.png"))
        except Exception:
            pass
    if context is not None:
        try:
            context.tracing.stop(path=str(dest / "trace.zip"))
        except Exception:
            pass
    console_text = "\n".join(console_errors)
    request_text = "\n".join(failed_requests)
    (dest / "console.txt").write_text(
        console_text + ("\n" if console_text else ""), encoding="utf-8")
    (dest / "requests.txt").write_text(
        request_text + ("\n" if request_text else ""), encoding="utf-8")


def watch(page, console_errors: list[str], failed_requests: list[str]) -> None:
    page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
    page.on(
        "response",
        lambda response: failed_requests.append(
            f"{response.status} {response.request.method} {response.url}"
        ) if response.status >= 400 else None,
    )
    page.on(
        "requestfailed",
        lambda request: failed_requests.append(
            f"failed {request.method} {request.url} {request.failure or ''}".rstrip()
        ),
    )
