"""P1 派修：写简报，交给驱动这次出包的 agent，非零退出。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "exe-release" / "scripts" / "fix_dispatch.py"

FINDINGS = {
    "findings": [
        {
            "schema_version": "1",
            "product": "duck",
            "dimension": "build-log",
            "name": "frozen_import_missing",
            "status": "fail",
            "tier": "P1",
            "root_cause_fingerprint": "missing_module:uharfbuzz",
            "detail": "No module named 'uharfbuzz'",
            "remediation": "add uharfbuzz to the release manifest's include_packages, then rebuild",
        }
    ]
}


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(
        ["git", "-C", str(repo), "config", "core.hooksPath", str(repo / ".git/no-hooks")],
        check=True,
    )
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "t@t"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "t"], check=True)
    (repo / "seed.txt").write_text("seed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-qm", "seed"], check=True)
    return repo


def _run(repo: Path, env_extra: dict[str, str]):
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=str(repo),
        capture_output=True,
        text=True,
        env={**os.environ, **env_extra},
    )


def _findings_file(tmp_path: Path, doc: dict = FINDINGS) -> Path:
    stage_dir = tmp_path / "release-artifacts" / "a3-build"
    stage_dir.mkdir(parents=True)
    path = stage_dir / "build.findings.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


def test_writes_a_brief_next_to_the_findings_and_stops(tmp_path):
    """写简报、打印路径。暂停由引擎做，pause 的问题指向这份简报。"""
    repo = _repo(tmp_path)
    findings = _findings_file(tmp_path)

    result = _run(repo, {"RELEASE_FIX_FINDINGS": str(findings)})

    assert result.returncode == 0
    brief = findings.parent / "release-fix-brief.md"
    assert f"FIX-BRIEF={brief}" in result.stdout
    text = brief.read_text(encoding="utf-8")
    assert "missing_module:uharfbuzz" in text
    assert "No module named 'uharfbuzz'" in text
    assert "add uharfbuzz to the release manifest's include_packages, then rebuild" in text
    # 简报在引擎之外被执行：不提交，改动到不了 `git archive HEAD`，下一轮用同一份代码再失败一次。
    assert "commit" in text.lower() and "resume" in text


def test_missing_findings_is_an_error_not_a_silent_pass(tmp_path):
    repo = _repo(tmp_path)
    result = _run(repo, {"RELEASE_FIX_FINDINGS": str(tmp_path / "nope.json")})
    assert result.returncode != 0
    assert "RELEASE_FIX_FINDINGS" in result.stderr


@pytest.mark.parametrize("tier", ["P0", "P1", "P2"])
def test_brief_carries_the_tier_it_was_given(tmp_path, tier):
    """分级是引擎判的，这里只如实转述。自己重判等于开出第二套判据。"""
    repo = _repo(tmp_path)
    findings = _findings_file(
        tmp_path, {"findings": [{**FINDINGS["findings"][0], "tier": tier}]}
    )

    result = _run(repo, {"RELEASE_FIX_FINDINGS": str(findings)})

    assert result.returncode == 0, result.stderr
    text = (findings.parent / "release-fix-brief.md").read_text(encoding="utf-8")
    assert f"[{tier}]" in text
