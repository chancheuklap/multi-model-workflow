#!/usr/bin/env python3
"""Exercise the real installer in disposable homes. Never calls real runners or launchd."""
import importlib.util
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("install_fixture", ROOT / "mmw-v4/tests/install/test_install.py")
fixture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixture)


def probe(runner, state):
    case = fixture.InstallTest()
    case.setUp()
    try:
        for tool in ("python3", "uv", "git"):
            (case.bin / tool).symlink_to(shutil.which(tool))
        env = case.env()
        env["PATH"] = f"{case.bin}:/usr/bin:/bin"
        env["MMW_HOME"] = str(case.home / ".mmw")
        env["CODEX_HOME"] = str(case.home / ".codex")
        env.pop("PASEO_AGENT_ID", None)
        env.pop("PASEO_WORKSPACE_ID", None)
        env.pop("HERDR_ENV", None)
        env["TERM_PROGRAM"] = "orca"
        config = json.loads((case.home / ".mmw/models.json").read_text())
        config["runner"] = runner
        (case.home / ".mmw/models.json").write_text(json.dumps(config))
        if runner == "herdr":
            (case.bin / "herdr").write_text("#!/bin/sh\nexit 0\n")
            (case.bin / "herdr").chmod(0o755)
        if state == "absent":
            (case.bin / "paseo").unlink()
        paseo = case.home / ".paseo/config.json"
        link = case.home / ".local/bin/paseo"
        if state == "existing":
            paseo.parent.mkdir()
            paseo.write_text('{invalid unrelated Paseo settings\n')
            link.parent.mkdir(parents=True)
            link.symlink_to(case.bin / "paseo")
        before = (paseo.read_bytes() if paseo.exists() else None,
                  os.readlink(link) if link.is_symlink() else None)
        for args in ((), ("--check",)):
            result = case.run_install("v4", *args, env=env)
            assert result.returncode == 0, f"{runner}/{state}/{args}: {result.stderr}"
            after = (paseo.read_bytes() if paseo.exists() else None,
                     os.readlink(link) if link.is_symlink() else None)
            assert after == before, f"{runner}/{state}/{args}: Paseo files changed: {before!r} -> {after!r}"
            assert "paseo " not in case.log.read_text(), "unused Paseo was invoked"
    finally:
        case.tearDown()


for selected in ("orca", "herdr", "auto"):
    for initial in ("absent", "existing"):
        probe(selected, initial)
print("PASS optional Paseo isolation")
