#!/usr/bin/env python3
"""Read every page of one GitHub REST list with per-page conditional requests."""

from __future__ import annotations

import copy
import json
import os
import subprocess
from typing import Callable
from urllib.parse import parse_qs, urlsplit


GH_TIMEOUT = 120


class ListReadError(RuntimeError):
    """A GitHub list address did not produce one complete JSON list."""


def _quiet_env() -> dict[str, str]:
    env = dict(os.environ)
    env.pop("CLICOLOR_FORCE", None)
    env.pop("CLICOLOR", None)
    return env


def run_gh(args: list[str]) -> tuple[int, str, str]:
    try:
        run = subprocess.run(["gh", *args], capture_output=True, text=True,
                             env=_quiet_env(), timeout=GH_TIMEOUT)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ListReadError(f"gh could not be run: {exc}") from None
    return run.returncode, run.stdout, run.stderr


def _parse_response(output: str) -> tuple[int, dict[str, str], str]:
    normal = output.replace("\r\n", "\n")
    head, separator, body = normal.partition("\n\n")
    if not separator:
        raise ValueError("the response had no HTTP headers")
    lines = head.splitlines()
    try:
        status = int(lines[0].split()[1])
    except (IndexError, ValueError) as exc:
        raise ValueError("the response had no HTTP status") from exc
    headers: dict[str, str] = {}
    for line in lines[1:]:
        name, found, value = line.partition(":")
        if found:
            headers[name.strip().lower()] = value.strip()
    return status, headers, body


def _next(headers: dict[str, str]) -> str | None:
    for part in headers.get("link", "").split(","):
        if 'rel="next"' not in part:
            continue
        start = part.find("<")
        end = part.find(">", start + 1)
        if start >= 0 and end > start:
            return part[start + 1:end]
    return None


def _page_size(address: str) -> int | None:
    values = parse_qs(urlsplit(address).query).get("per_page")
    try:
        value = int(values[0]) if values else None
    except (TypeError, ValueError):
        return None
    return value if value and value > 0 else None


def _reason(code: int, out: str, err: str) -> str:
    said = " ".join((err or out or "").split())[:300]
    return f"gh exited {code}: {said or 'nothing on stderr'}"


class _Cache:
    def __init__(self):
        self.pages: dict[str, list] = {}
        self.etags: dict[str, str] = {}
        self.next_pages: dict[str, str | None] = {}


class ConditionalListReader:
    """A process-local cache of complete GitHub REST list addresses."""

    def __init__(self, gh: Callable[[list[str]], tuple[int, str, str]] = run_gh):
        self.gh = gh
        self._addresses: dict[str, _Cache] = {}
        self._reads = {"billed": 0, "not_modified": 0}

    @property
    def reads(self) -> dict[str, int]:
        return dict(self._reads)

    def clone(self) -> "ConditionalListReader":
        other = ConditionalListReader(self.gh)
        other._addresses = copy.deepcopy(self._addresses)
        other._reads = dict(self._reads)
        return other

    def discard(self, address: str) -> None:
        self._addresses.pop(address, None)

    def read(self, address: str) -> list:
        cache = self._addresses.setdefault(address, _Cache())
        endpoint: str | None = address
        visited: list[str] = []
        page_size = _page_size(address)
        while endpoint:
            etag = cache.etags.get(endpoint)
            if (page_size is not None and cache.next_pages.get(endpoint) is None
                    and len(cache.pages.get(endpoint, [])) == page_size):
                etag = None
            args = ["api", "-i", endpoint, "-H", "Accept: application/vnd.github+json"]
            if etag:
                args += ["-H", f"If-None-Match: {etag}"]
            try:
                code, out, err = self.gh(args)
            except ListReadError as exc:
                raise ListReadError(f"{address}: {exc}") from None
            except Exception as exc:
                raise ListReadError(f"{address}: gh could not be run: {exc}") from None
            try:
                status, headers, body = _parse_response(out)
            except ValueError as exc:
                raise ListReadError(f"{address}: {_reason(code, out, err) if code else exc}") from None

            if status == 304:
                self._reads["not_modified"] += 1
                if endpoint not in cache.pages:
                    raise ListReadError(f"{address}: returned 304 without a cached page ({endpoint})")
                next_page = cache.next_pages.get(endpoint)
            elif status == 200:
                self._reads["billed"] += 1
                if code != 0:
                    raise ListReadError(f"{address}: {_reason(code, out, err)}")
                try:
                    page = json.loads(body)
                except json.JSONDecodeError:
                    raise ListReadError(f"{address}: answered with something that is not JSON") from None
                if not isinstance(page, list):
                    raise ListReadError(f"{address}: answered with JSON that is not a list")
                cache.pages[endpoint] = page
                next_page = _next(headers)
                cache.next_pages[endpoint] = next_page
                if headers.get("etag"):
                    cache.etags[endpoint] = headers["etag"]
                else:
                    cache.etags.pop(endpoint, None)
            else:
                raise ListReadError(f"{address}: HTTP {status}; {_reason(code, out, err)}")
            visited.append(endpoint)
            endpoint = next_page

        cache.pages = {url: cache.pages[url] for url in visited}
        cache.etags = {url: cache.etags[url] for url in visited if url in cache.etags}
        cache.next_pages = {url: cache.next_pages.get(url) for url in visited}
        return [item for url in visited for item in cache.pages[url]]
