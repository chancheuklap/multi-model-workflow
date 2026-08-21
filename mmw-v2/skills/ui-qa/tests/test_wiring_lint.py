"""接线文件校验器的测试。

判的是它拦不拦得住——尤其两件事：写成明文的 secret，和文件名与 product 字段对不上。
前者是这份校验器存在的理由（正文一句「拒绝并停」拦不住 agent），后者是路径逃逸的唯一
闸门（上一代靠产物路径命令在算路径之前拦，那个命令在 v2 里不存在了）。
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "wiring_lint.py"

GOOD = {
    "version": 1,
    "product": "demo",
    "launch": {"command": ["pnpm", "dev"]},
    "mainWindow": {"titlePattern": "^Demo"},
    "environment": {"kind": "local-server", "endpoint": "http://localhost:3000"},
}


def lint(tmp_path: Path, data: dict, filename: str = "demo.json"):
    target = tmp_path / filename
    target.write_text(json.dumps(data), encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )


def test_good_file_passes(tmp_path):
    assert lint(tmp_path, GOOD).returncode == 0


def test_filename_must_match_product(tmp_path):
    """文件名与 product 字段对不上就拒。

    这一条同时封死路径逃逸：正文按 docs/ui-qa-wiring/<product>.json 拼路径，
    product 带 / 或 .. 时路径会逃出根目录，而那样拼出来的文件名不可能等于该字段。
    """
    r = lint(tmp_path, GOOD, filename="something-else.json")
    assert r.returncode == 1
    assert "demo.json" in r.stderr


def test_escaping_product_id_is_refused(tmp_path):
    data = dict(GOOD, product="../../etc/evil")
    # 逃逸的 id 拼不出合法文件名，两条判定各拦一次
    r = lint(tmp_path, data, filename="evil.json")
    assert r.returncode == 1
    assert "product" in r.stderr


@pytest.mark.parametrize(
    "secret",
    ["hunter2", "env", "keychain", "ENV:TOKEN", "$TOKEN"],
)
def test_plaintext_secret_is_refused(tmp_path, secret):
    data = dict(
        GOOD,
        environment={
            "kind": "test-account",
            "endpoint": "https://staging.example.com",
            "account": {"id": "qa@example.com", "secret": secret},
        },
    )
    assert lint(tmp_path, data).returncode == 1


@pytest.mark.parametrize("ref", ["env:QA_TOKEN", "keychain:qa-login"])
def test_secret_ref_is_accepted(tmp_path, ref):
    data = dict(
        GOOD,
        environment={
            "kind": "test-account",
            "endpoint": "https://staging.example.com",
            "account": {"id": "qa@example.com", "secret": ref},
        },
    )
    assert lint(tmp_path, data).returncode == 0


def test_test_account_requires_account_block(tmp_path):
    data = dict(
        GOOD,
        environment={"kind": "test-account", "endpoint": "https://staging.example.com"},
    )
    assert lint(tmp_path, data).returncode == 1


def test_missing_required_field(tmp_path):
    data = {k: v for k, v in GOOD.items() if k != "launch"}
    r = lint(tmp_path, data)
    assert r.returncode == 1
    assert "launch" in r.stderr


def test_wrong_type(tmp_path):
    data = dict(GOOD, launch={"command": "pnpm dev"})  # 要数组，给了字符串
    assert lint(tmp_path, data).returncode == 1


def test_unknown_enum_value(tmp_path):
    data = dict(
        GOOD,
        environment={"kind": "production", "endpoint": "https://example.com"},
    )
    assert lint(tmp_path, data).returncode == 1


def test_uncompilable_regex(tmp_path):
    data = dict(GOOD, mainWindow={"titlePattern": "^Demo("})
    assert lint(tmp_path, data).returncode == 1


def test_main_window_needs_one_of_two(tmp_path):
    data = dict(GOOD, mainWindow={})
    assert lint(tmp_path, data).returncode == 1


@pytest.mark.parametrize("version", [0, 2, 99])
def test_only_version_one_is_read(tmp_path, version):
    """版本只存在过 1。不是 1 就停，不猜它是旧的还是新的。"""
    r = lint(tmp_path, dict(GOOD, version=version))
    assert r.returncode == 1
    assert "version" in r.stderr


def test_not_json(tmp_path):
    target = tmp_path / "demo.json"
    target.write_text("{ not json", encoding="utf-8")
    r = subprocess.run(
        [sys.executable, str(SCRIPT), str(target)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1


def test_no_argument_is_usage_error(tmp_path):
    r = subprocess.run(
        [sys.executable, str(SCRIPT)], capture_output=True, text=True, check=False
    )
    assert r.returncode == 2
