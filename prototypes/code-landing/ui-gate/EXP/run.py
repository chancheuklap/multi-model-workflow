# /// script
# requires-python = ">=3.11"
# dependencies = ["playwright>=1.58", "numpy>=2", "Pillow>=10"]
# ///
"""UI gate experiment: can a Claude Design page (downloaded .dc.html) be rendered offline,
snapshotted (ARIA tree + screenshot), and compared with a product implementation by two
automatic checks — ARIA tree diff == 0 lines and pixel diff <= threshold %?

Run:  uv run run.py [--out DIR] [--threshold 3] [--cdn DIR]
Serves sample/baseline, sample/impl and sample/mockup on local ports, drives headless
Chromium, writes <out>/index.html (evidence page) + media/.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SAMPLE = HERE / "sample"

# The Claude Design runtime (support.js) loads these from unpkg at page load.
CDN = {
    "https://unpkg.com/react@18.3.1/umd/react.production.min.js": "react.production.min.js",
    "https://unpkg.com/react-dom@18.3.1/umd/react-dom.production.min.js": "react-dom.production.min.js",
    "https://unpkg.com/@babel/standalone@7.29.0/babel.min.js": "babel.min.js",
}

BASELINE_PAGE = "App · 商品项目库.dc.html"
IMPL_PAGE = "index.html?scenario=library-populated"
MOCKUP_PAGE = "index.html?scenario=library-populated"
WRONG_PAGE = "index.html?scenario=library-empty"  # negative control: a deliberately wrong scene must fail
VIEWPORTS = [(1440, 900), (1180, 720)]
PIXEL_TOLERANCE = 16  # per-channel; below this a pixel counts as identical

# Lines the Claude Design runtime adds around a component that no product page has.
ARIA_NOISE = re.compile(r"^\s*- (generic|group)\s*$")


# ---------------------------------------------------------------- helpers
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):  # noqa: D401
        pass


def serve(root: Path, port: int) -> socketserver.TCPServer:
    handler = lambda *a, **k: Quiet(*a, directory=str(root), **k)  # noqa: E731
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", port), handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def ensure_cdn(cdn_dir: Path) -> dict[str, Path]:
    cdn_dir.mkdir(parents=True, exist_ok=True)
    out = {}
    for url, name in CDN.items():
        p = cdn_dir / name
        if not p.exists():
            print(f"fetch {url}")
            urllib.request.urlretrieve(url, p)
        out[url] = p
    return out


def pixel_diff(a: Path, b: Path, out: Path) -> dict:
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    size_equal = ia.size == ib.size
    if not size_equal:
        return {"size_equal": False, "pct": 100.0, "count": None, "total": None, "box": None,
                "size_a": ia.size, "size_b": ib.size}
    na, nb = np.asarray(ia, dtype=np.int16), np.asarray(ib, dtype=np.int16)
    mask = (np.abs(na - nb) > PIXEL_TOLERANCE).any(axis=2)
    count, total = int(mask.sum()), int(mask.size)
    box = None
    if count:
        ys, xs = np.nonzero(mask)
        box = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]
    vis = np.full(na.shape, 24, dtype=np.uint8)
    vis[mask] = (255, 64, 64)
    Image.fromarray(vis).save(out)
    return {"size_equal": True, "pct": round(100 * count / total, 3), "count": count,
            "total": total, "box": box, "size_a": ia.size, "size_b": ib.size}


LANDMARK_NAME = re.compile(r'^(\s*- (?:main|navigation|banner|contentinfo|region|complementary)) "[^"]*"(:?)\s*$')


def normalize_aria(text: str) -> list[str]:
    """Drop what the Claude Design runtime adds and what carries no structure.

    1. blank lines and bare ``- generic`` / ``- group`` lines;
    2. the accessible name on landmark roles (a product page labels its <main>, a
       component page does not — the landmark itself is what matters);
    3. one outer ``- main:`` wrapper when the very next line is another ``main``: the
       Claude Design app page wraps every dc-import in its own <main>.
    """
    lines = []
    for ln in text.splitlines():
        if not ln.strip() or ARIA_NOISE.match(ln):
            continue
        ln = LANDMARK_NAME.sub(r"\1\2", ln.rstrip())
        lines.append(ln)
    return _hoist_nested_main(lines)


def _hoist_nested_main(lines: list[str]) -> list[str]:
    """A ``main`` nested inside another ``main`` (the app page's wrapper around a
    component whose own root is <main>) is removed and its children dedented, so
    both trees put the header content and the tabpanel at the same level."""
    out: list[str] = []
    main_depths: list[int] = []  # indents of open main landmarks
    hoist: list[int] = []        # indents of removed nested mains still in scope
    for ln in lines:
        ind = len(ln) - len(ln.lstrip())
        while main_depths and ind <= main_depths[-1]:
            main_depths.pop()
        while hoist and ind <= hoist[-1]:
            hoist.pop()
        if ln.strip() == "- main:" and main_depths:
            hoist.append(ind)
            continue
        dedent = 2 * len(hoist)
        out.append(ln[dedent:] if dedent and ln.startswith(" " * dedent) else ln)
        if ln.strip() == "- main:":
            main_depths.append(ind - dedent)
    return out


def aria_diff(a: str, b: str, out: Path) -> dict:
    la, lb = normalize_aria(a), normalize_aria(b)
    diff = list(difflib.unified_diff(la, lb, "baseline", "impl", lineterm="", n=1))
    out.write_text("\n".join(diff) + ("\n" if diff else ""), encoding="utf-8")
    changed = sum(1 for d in diff if d[:1] in "+-" and not d.startswith(("+++", "---")))
    return {"lines_a": len(la), "lines_b": len(lb), "changed": changed,
            "raw_lines_a": len(a.splitlines()), "raw_lines_b": len(b.splitlines())}


# ---------------------------------------------------------------- capture
@dataclass
class Shot:
    approach: str
    viewport: tuple[int, int]
    png: Path
    aria: str
    console: list[str] = field(default_factory=list)


def capture(page, url: str, root_sel: str | None, vp: tuple[int, int], png: Path,
            frame_css: str | None) -> Shot:
    console: list[str] = []
    page.on("console", lambda m: console.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
    page.on("pageerror", lambda e: console.append(f"pageerror: {e}"))
    page.set_viewport_size({"width": vp[0], "height": vp[1]})
    page.goto(url, wait_until="networkidle")
    if frame_css:
        page.add_style_tag(content=frame_css)
    page.wait_for_timeout(800)
    target = page.locator(root_sel) if root_sel else page.locator("body")
    if root_sel:
        target.first.wait_for(state="visible", timeout=15000)
        target.first.screenshot(path=str(png))
    else:
        page.screenshot(path=str(png))
    aria = target.first.aria_snapshot()
    return Shot("", vp, png, aria, console)


# ---------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE.parents[3] / ".scratch/code-landing/ui-gate/evidence/round-2"))
    ap.add_argument("--cdn", default=str(HERE.parents[3] / ".scratch/code-landing/ui-gate/cdn"))
    ap.add_argument("--threshold", type=float, default=1.0, help="max diff pixel percent")
    ap.add_argument("--round", default="round-2")
    args = ap.parse_args()

    out = Path(args.out)
    media = out / "media"
    media.mkdir(parents=True, exist_ok=True)
    cdn = ensure_cdn(Path(args.cdn))

    ports = {"baseline": 18771, "impl": 18772, "mockup": 18773}
    servers = [serve(SAMPLE / k, p) for k, p in ports.items()]
    time.sleep(0.3)

    pages = {
        "baseline": (f"http://127.0.0.1:{ports['baseline']}/{BASELINE_PAGE}", "#dc-root"),
        "impl": (f"http://127.0.0.1:{ports['impl']}/{IMPL_PAGE}", None),
        "mockup": (f"http://127.0.0.1:{ports['mockup']}/{MOCKUP_PAGE}", None),
        "wrong": (f"http://127.0.0.1:{ports['impl']}/{WRONG_PAGE}", None),
    }
    commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                            cwd=HERE).stdout.strip()

    results: list[dict] = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for vp in VIEWPORTS:
            ctx = browser.new_context(viewport={"width": vp[0], "height": vp[1]},
                                      device_scale_factor=1, reduced_motion="reduce", locale="zh-CN")
            # Serve the runtime's CDN scripts from the local cache: the baseline renders offline.
            def route_cdn(route, request):
                p = cdn.get(request.url)
                if p:
                    route.fulfill(path=str(p), content_type="application/javascript")
                else:
                    route.abort()
            ctx.route("https://unpkg.com/**", route_cdn)
            shots: dict[str, Shot] = {}
            for name, (url, sel) in pages.items():
                page = ctx.new_page()
                frame_css = (f"#dc-root{{width:{vp[0]}px !important;height:{vp[1]}px !important;margin:0 !important}}"
                             if name == "baseline" else None)
                png = media / f"{name}-{vp[0]}x{vp[1]}.png"
                s = capture(page, url, sel, vp, png, frame_css)
                s.approach = name
                shots[name] = s
                (media / f"{name}-{vp[0]}x{vp[1]}.aria.yml").write_text(s.aria, encoding="utf-8")
                page.close()
            ctx.close()
            for a, b in (("baseline", "impl"), ("mockup", "impl"), ("baseline", "mockup"), ("baseline", "wrong")):
                tag = f"{a}-vs-{b}-{vp[0]}x{vp[1]}"
                pd = pixel_diff(shots[a].png, shots[b].png, media / f"{tag}.diff.png")
                ad = aria_diff(shots[a].aria, shots[b].aria, media / f"{tag}.aria.diff")
                results.append({"pair": f"{a} vs {b}", "a": a, "b": b, "viewport": f"{vp[0]}x{vp[1]}",
                                "pixel": pd, "aria": ad,
                                "console_a": shots[a].console, "console_b": shots[b].console})
        browser.close()
    for s in servers:
        s.shutdown()

    (out / "results.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    write_evidence(out, results, args, commit)

    gate = [r for r in results if r["a"] == "baseline" and r["b"] == "impl"]
    failed = [r for r in gate if r["aria"]["changed"] or not r["pixel"]["size_equal"] or r["pixel"]["pct"] > args.threshold]
    control = [r for r in results if r["b"] == "wrong"]
    control_ok = all(r["aria"]["changed"] > 0 and r["pixel"]["pct"] > args.threshold for r in control)
    for r in control:
        print(f"control baseline-vs-wrong {r['viewport']} aria-changed={r['aria']['changed']} pixel={r['pixel']['pct']}% "
              f"-> {'caught' if r['aria']['changed'] and r['pixel']['pct'] > args.threshold else 'MISSED'}")
    if not control_ok:
        print("NEGATIVE CONTROL FAILED: the checks did not catch a wrong scene; results are not trustworthy")
        return 2
    for r in gate:
        status = "DIFF" if r in failed else "ok"
        print(f"{status} baseline-vs-impl {r['viewport']} aria-changed={r['aria']['changed']} "
              f"pixel={r['pixel']['pct']}% box={r['pixel']['box']}")
    if failed:
        print(f"PARITY FAILED {len(gate) - len(failed)}/{len(gate)} — evidence: {out / 'index.html'}")
        return 1
    print(f"PARITY OK {len(gate)}/{len(gate)} — evidence: {out / 'index.html'}")
    return 0


# ---------------------------------------------------------------- evidence page
def write_evidence(out: Path, results: list[dict], args, commit: str) -> None:
    rows = ""
    for r in results:
        p, a = r["pixel"], r["aria"]
        size = "yes" if p["size_equal"] else f"no {p['size_a']} vs {p['size_b']}"
        count = p["count"] if p["count"] is not None else "—"
        rows += (f"<tr><td>{r['pair']}</td><td>{r['viewport']}</td>"
                 f"<td class=n>{p['pct']}</td><td class=n>{count}</td>"
                 f"<td>{size}</td>"
                 f"<td class=n>{a['changed']}</td><td class=n>{a['lines_a']}/{a['lines_b']}</td>"
                 f"<td class=n>{len(r['console_a'])}/{len(r['console_b'])}</td></tr>")
    body = ""
    for r in results:
        vp, a, b = r["viewport"], r["a"], r["b"]
        tag = f"{a}-vs-{b}-{vp}"
        p = r["pixel"]
        body += f"""<div class=sample><h2>{r['pair']} · {vp}</h2>
<p class=stat>pixel diff {p['pct']}% · box {p['box']} · aria changed lines {r['aria']['changed']} · console errors {len(r['console_a'])}/{len(r['console_b'])}</p>
<p class=look>what to look for: red in the third column is where the two renders differ by more than {PIXEL_TOLERANCE}/255 on any channel; the .aria.diff link lists the tree lines that differ after noise lines are dropped.</p>
<div class=row>
<div><img src="media/{a}-{vp}.png"><div class=cap>{a} · {vp}</div></div>
<div><img src="media/{b}-{vp}.png"><div class=cap>{b} · {vp}</div></div>
<div><img src="media/{tag}.diff.png"><div class=cap>diff · <a href="media/{tag}.aria.diff">aria diff</a> · <a href="media/{a}-{vp}.aria.yml">{a} aria</a> · <a href="media/{b}-{vp}.aria.yml">{b} aria</a></div></div>
</div></div>"""
        if r["console_a"] or r["console_b"]:
            body += "<pre>" + "\n".join([f"[{a}] {x}" for x in r["console_a"]] + [f"[{b}] {x}" for x in r["console_b"]]) + "</pre>"
    html = f"""<!doctype html>
<meta charset="utf-8">
<title>ui-gate · {args.round} · evidence</title>
<style>
  body{{margin:24px;background:#121416;color:#e6e6e3;font:14px/1.6 system-ui,sans-serif}}
  h1{{font-size:20px;margin:0 0 4px}}
  .meta{{color:#9a9fa4;font-size:12px;margin-bottom:20px}}
  .legend{{display:flex;gap:16px;flex-wrap:wrap;margin:0 0 20px;padding:10px 12px;border:1px solid #2b2f33;border-radius:6px}}
  .legend i{{display:inline-block;width:14px;height:14px;border:2px solid currentColor;margin-right:6px;vertical-align:-2px}}
  table{{border-collapse:collapse;margin:0 0 24px}}
  th,td{{padding:4px 10px;border-bottom:1px solid #2b2f33;text-align:left}}
  td.n,th.n{{text-align:right;font-variant-numeric:tabular-nums}}
  .sample{{margin:28px 0 8px}} .sample h2{{font-size:15px;margin:0}}
  .stat{{color:#9a9fa4;font-size:12px;margin:2px 0 8px}} .look{{color:#c8b458;font-size:12px;margin:0 0 8px}}
  .row{{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:12px}}
  img{{width:100%;background:#000;border-radius:4px}} .cap{{color:#8fb8d8;font-size:12px;margin-top:4px}}
  .rules li{{margin:2px 0}} code,pre{{font:12px ui-monospace,monospace;color:#c9d1d9}} a{{color:#8fb8d8}}
</style>
<h1>ui-gate · {args.round}</h1>
<p class=meta>Can a downloaded Claude Design page be rendered offline and compared with the product page by ARIA-tree diff and pixel diff? — bar: baseline vs impl has 0 changed aria lines and ≤ {args.threshold}% differing pixels at both viewports · params: tolerance {PIXEL_TOLERANCE}/255, viewports {VIEWPORTS}, CDN served locally · run: {time.strftime('%Y-%m-%d %H:%M:%S')} · commit: {commit}</p>
<div class=legend><span><i style="color:#ff4040"></i>differing pixel</span><span><i style="color:#181818"></i>identical pixel</span><span>aria changed lines = added + removed lines in unified diff after dropping bare <code>- generic</code>/<code>- group</code> lines</span></div>
<table><tr><th>pair</th><th>viewport</th><th class=n>pixel %</th><th class=n>pixels</th><th>size equal</th><th class=n>aria changed</th><th class=n>aria lines a/b</th><th class=n>console err a/b</th></tr>{rows}</table>
{body}
<h2>How it decided</h2>
<ul class=rules>
<li>Baseline page is served from <code>sample/baseline</code>; the runtime's unpkg scripts are answered from a local cache by <code>route_cdn</code> in <code>run.py</code>, so no network is used.</li>
<li>Baseline screenshot and ARIA snapshot are taken on <code>#dc-root</code>, forced to the viewport size by <code>frame_css</code> in <code>capture()</code>; impl and mockup use the whole viewport.</li>
<li><code>pixel_diff()</code>: a pixel differs when any RGB channel differs by more than {PIXEL_TOLERANCE}; unequal image sizes count as 100%.</li>
<li><code>aria_diff()</code>: <code>normalize_aria()</code> drops blank and bare generic/group lines, strips the accessible name from landmark roles, unwraps one outer <code>main</code> that only wraps another <code>main</code>, then <code>difflib.unified_diff</code>; changed = added + removed lines.</li>
<li>Negative control: baseline vs <code>wrong</code> (impl at scenario=library-empty) must fail both checks first, otherwise exit 2 and nothing is trusted.</li>
<li>Gate (stdout / exit code): every baseline-vs-impl pair needs aria changed = 0 and pixel % ≤ threshold.</li>
</ul>"""
    (out / "index.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
