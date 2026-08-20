"""P1 派修：写简报，交给驱动 agent；配了后端就走后端。"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "fix_dispatch.py"

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
            "remediation": "add uharfbuzz to the key's include_packages, then rebuild",
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


def _findings_file(tmp_path: Path) -> Path:
    stage_dir = tmp_path / "release-artifacts" / "a3-build"
    stage_dir.mkdir(parents=True)
    path = stage_dir / "build.findings.json"
    path.write_text(json.dumps(FINDINGS), encoding="utf-8")
    return path


def test_writes_a_brief_next_to_the_findings_and_stops(tmp_path):
    """没配后端时：写简报、打印路径、非零退出。

    非零退出是有意的——引擎看到它就 PAUSED:needs-context 并保留现场，驱动 agent 顺着 receipt
    找到简报、改代码、resume。假装修好了才是最坏的结果。
    """
    repo = _repo(tmp_path)
    findings = _findings_file(tmp_path)
    ref_file = tmp_path / "ref"

    result = _run(
        repo,
        {
            "RELEASE_FIX_FINDINGS": str(findings),
            "RELEASE_FIX_WORKER_REF_FILE": str(ref_file),
        },
    )

    assert result.returncode != 0
    brief = findings.parent / "release-fix-brief.md"
    assert f"FIX-BRIEF={brief}" in result.stdout
    text = brief.read_text(encoding="utf-8")
    assert "missing_module:uharfbuzz" in text
    assert "No module named 'uharfbuzz'" in text
    assert "add uharfbuzz to the key's include_packages, then rebuild" in text
    # 简报必须说清楚谁提交。这条路上驱动 agent 在引擎之外，改动不提交就进不了
    # git archive HEAD，到不了构建机。
    assert "Commit to the current branch" in text
    assert "git archive HEAD" in text
    assert ref_file.read_text(encoding="utf-8") == ""


def test_missing_findings_is_an_error_not_a_silent_pass(tmp_path):
    repo = _repo(tmp_path)
    result = _run(repo, {"RELEASE_FIX_FINDINGS": str(tmp_path / "nope.json")})
    assert result.returncode != 0
    assert "RELEASE_FIX_FINDINGS" in result.stderr


def test_backend_gets_the_brief_path_and_its_exit_code_is_kept(tmp_path):
    repo = _repo(tmp_path)
    findings = _findings_file(tmp_path)
    ref_file = tmp_path / "ref"
    backend = tmp_path / "backend.sh"
    backend.write_text(
        "#!/usr/bin/env bash\n"
        'printf "%s\\n" "BRIEF=$RELEASE_FIX_BRIEF" > "$1"\n'
        "echo SESSION=stub-123\n"
        "exit 0\n",
        encoding="utf-8",
    )
    backend.chmod(0o755)
    record = tmp_path / "record"

    result = _run(
        repo,
        {
            "RELEASE_FIX_FINDINGS": str(findings),
            "RELEASE_FIX_WORKER_REF_FILE": str(ref_file),
            "RELEASE_FIX_BACKEND": f"{backend} {record}",
        },
    )

    assert result.returncode == 0
    brief = findings.parent / "release-fix-brief.md"
    assert str(brief) in record.read_text("utf-8")
    assert ref_file.read_text(encoding="utf-8") == "stub-123"
    # 走后端那条路时引擎是唯一 committer，所以简报的措辞相反。
    assert "do not git commit" in brief.read_text(encoding="utf-8")


def test_backend_commits_are_unwound_back_into_the_worktree(tmp_path):
    """外部后端自己提交了也不算数：改动收回工作树，交引擎过路径闸再提交。

    留在分支上的提交没过路径闸——它可能碰了计费、迁移这类受保护路径，而引擎看到干净树
    会以为「什么都没修」。失败路径尤其必须回退：修到一半的提交留在 HEAD，人工 resume
    时会被当成基线出货。
    """
    repo = _repo(tmp_path)
    findings = _findings_file(tmp_path)
    before = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()

    backend = tmp_path / "backend.sh"
    backend.write_text(
        "#!/usr/bin/env bash\n"
        'echo fixed > "$1/fix.txt"\n'
        'git -C "$1" add -A\n'
        'git -C "$1" commit -qm "worker commit"\n'
        "exit 7\n",
        encoding="utf-8",
    )
    backend.chmod(0o755)

    result = _run(
        repo,
        {
            "RELEASE_FIX_FINDINGS": str(findings),
            "RELEASE_FIX_BACKEND": f"{backend} {repo}",
        },
    )

    assert result.returncode == 7, "the backend exit code must not be swallowed"
    after = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert after == before, "the worker commits were not rolled back"
    assert (repo / "fix.txt").read_text(encoding="utf-8") == "fixed\n", "the changes were lost"


@pytest.mark.parametrize("tier", ["P0", "P1", "P2"])
def test_brief_carries_the_tier_it_was_given(tier):
    """分级是引擎判的，这里只如实转述。自己重判等于开出第二套判据。"""
    sys.path.insert(0, str(SCRIPT.parent))
    import fix_dispatch  # noqa: PLC0415

    text = fix_dispatch.brief([{**FINDINGS["findings"][0], "tier": tier}])
    assert f"[{tier}]" in text
