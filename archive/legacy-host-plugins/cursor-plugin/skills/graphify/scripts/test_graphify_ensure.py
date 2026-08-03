#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
HELPER = HERE / "graphify_ensure.py"


def run(args: list[str], cwd: Path, *, env: dict[str, str] | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True, env=env, check=False)
    if check and proc.returncode != 0:
        raise AssertionError(f"command failed:{args}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    return proc


class EnsureGraphTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        run(["git", "init", "-q"], self.repo)
        run(["git", "config", "user.email", "test@example.com"], self.repo)
        run(["git", "config", "user.name", "Test"], self.repo)
        (self.repo / ".gitignore").write_text("graphify-out/\n", encoding="utf-8")
        (self.repo / "src").mkdir()
        (self.repo / "src" / "app.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
        run(["git", "add", "."], self.repo)
        run(["git", "commit", "-qm", "seed"], self.repo)

        self.counter = self.root / "counter"
        self.fake = self.root / "graphify"
        self.fake.write_text(
            """#!/usr/bin/env python3
import json, os
from pathlib import Path
import sys
if sys.argv[1:] == ['--version']:
    print('graphify 0.test')
    raise SystemExit(0)
if len(sys.argv) >= 3 and sys.argv[1] == 'update':
    repo=Path(sys.argv[2]).resolve()
    counter=Path(os.environ['FAKE_GRAPHIFY_COUNTER'])
    count=int(counter.read_text() if counter.exists() else '0')+1
    counter.write_text(str(count))
    out=repo/'graphify-out'; out.mkdir(parents=True,exist_ok=True)
    behavior=os.environ.get('FAKE_GRAPHIFY_BEHAVIOR','ok')
    if behavior == 'invalid':
        (out/'graph.json').write_text('{bad')
    else:
        data={'nodes':[{'id':'app','source_file':'src/app.py'}], 'links':[]}
        (out/'graph.json').write_text(json.dumps(data))
    if behavior == 'hard-warning':
        print('warning: 1 .sql file(s) contributed nothing to the graph because a dependency is missing: tree-sitter-sql not installed. (#1745)')
    raise SystemExit(0)
print('unsupported',sys.argv,file=sys.stderr)
raise SystemExit(2)
""",
            encoding="utf-8",
        )
        self.fake.chmod(0o755)
        self.env = os.environ.copy()
        self.env.update(
            {
                "PI_GRAPHIFY_BIN": str(self.fake),
                "FAKE_GRAPHIFY_COUNTER": str(self.counter),
            }
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def ensure(self, repo: Path | None = None, source: Path | None = None, *, check: bool = True, behavior: str = "ok") -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        env["FAKE_GRAPHIFY_BEHAVIOR"] = behavior
        args = [sys.executable, str(HELPER), "--repo", str(repo or self.repo)]
        if source is not None:
            args += ["--source", str(source)]
        return run(args, repo or self.repo, env=env, check=check)

    def test_build_then_fresh_does_not_rebuild(self) -> None:
        first = self.ensure()
        second = self.ensure()
        self.assertIn("BUILT", first.stdout)
        self.assertIn("FRESH", second.stdout)
        self.assertEqual(self.counter.read_text(), "1")
        meta = json.loads((self.repo / "graphify-out/.pi-freshness.json").read_text())
        self.assertEqual(meta["graphify_version"], "graphify 0.test")
        self.assertEqual(meta["warnings"], [])

    def test_same_commit_worktree_reuses_source_graph(self) -> None:
        self.ensure()
        target = self.root / "target"
        run(["git", "worktree", "add", "--detach", str(target), "HEAD"], self.repo)
        try:
            result = self.ensure(target, self.repo)
            self.assertIn("REUSED", result.stdout)
            self.assertEqual(self.counter.read_text(), "1")
            self.assertTrue((target / "graphify-out/graph.json").is_file())
        finally:
            run(["git", "worktree", "remove", str(target)], self.repo)

    def test_dirty_change_rebuilds_and_refreshes_fingerprint(self) -> None:
        self.ensure()
        (self.repo / "src/app.py").write_text("def hello():\n    return 'changed'\n", encoding="utf-8")
        result = self.ensure()
        self.assertIn("BUILT", result.stdout)
        self.assertEqual(self.counter.read_text(), "2")
        self.assertIn("FRESH", self.ensure().stdout)
        self.assertEqual(self.counter.read_text(), "2")

    def test_hard_parser_warning_fails_and_restores_previous_graph(self) -> None:
        self.ensure()
        graph = self.repo / "graphify-out/graph.json"
        meta = self.repo / "graphify-out/.pi-freshness.json"
        old_graph = graph.read_bytes()
        old_meta = meta.read_bytes()
        (self.repo / "src/app.py").write_text("def changed():\n    return 1\n", encoding="utf-8")
        result = self.ensure(check=False, behavior="hard-warning")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("缺少源码解析能力", result.stderr)
        self.assertEqual(graph.read_bytes(), old_graph)
        self.assertEqual(meta.read_bytes(), old_meta)

    def test_interrupted_build_backup_wins_over_half_written_graph(self) -> None:
        self.ensure()
        out = self.repo / "graphify-out"
        graph = out / "graph.json"
        meta = out / ".pi-freshness.json"
        old_graph = graph.read_bytes()
        old_meta = meta.read_bytes()
        (out / ".pi-backup.graph.json").write_bytes(old_graph)
        (out / ".pi-backup.freshness.json").write_bytes(old_meta)
        graph.write_text(json.dumps({"nodes": [{"id": "half"}], "links": []}), encoding="utf-8")
        meta.write_text(json.dumps({"schema_version": 0}), encoding="utf-8")
        (self.repo / "src/app.py").write_text("def changed():\n    return 2\n", encoding="utf-8")
        result = self.ensure(check=False, behavior="hard-warning")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(graph.read_bytes(), old_graph)
        self.assertEqual(meta.read_bytes(), old_meta)

    def test_invalid_new_graph_fails_and_restores_previous_graph(self) -> None:
        self.ensure()
        graph = self.repo / "graphify-out/graph.json"
        old_graph = graph.read_bytes()
        (self.repo / "src/app.py").write_text("def changed():\n    return 3\n", encoding="utf-8")
        result = self.ensure(check=False, behavior="invalid")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(graph.read_bytes(), old_graph)


if __name__ == "__main__":
    unittest.main()
