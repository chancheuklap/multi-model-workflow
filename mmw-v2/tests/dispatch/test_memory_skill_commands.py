"""Execute the worker Memory save example against a fake nmem, never live Mem.

    python3 -m unittest discover -s mmw-v2/tests/dispatch -p test_memory_skill_commands.py
"""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SKILL = HERE.parents[1] / "upstream" / "skills" / "engineering" / "implement" / "SKILL.md"


class WorkerMemoryCommandTest(unittest.TestCase):
    def save_example(self, task_scope):
        text = SKILL.read_text(encoding="utf-8")
        section = text.split("## Save or correct shared experience\n", 1)[1]
        command = section.split("```sh\n", 1)[1].split("\n```", 1)[0]
        with tempfile.TemporaryDirectory(prefix="mmw-memory-command-") as tmp:
            root = Path(tmp)
            binary = root / "bin" / "nmem"
            binary.parent.mkdir()
            binary.write_text(
                "#!/usr/bin/env python3\n"
                "import json, os, sys\n"
                "from pathlib import Path\n"
                "Path(os.environ['MMW_MEMORY_CAPTURE']).write_text(json.dumps({"
                "'args': sys.argv[1:], 'body': sys.stdin.read()}, ensure_ascii=False))\n"
                "print(json.dumps({'id': 'fixture-memory'}))\n",
                encoding="utf-8",
            )
            binary.chmod(0o755)
            capture = root / "capture.json"
            env = dict(os.environ)
            env.update({
                "PATH": str(binary.parent) + os.pathsep + env.get("PATH", ""),
                "MMW_MEMORY_CAPTURE": str(capture),
                "NMEM_SPACE": "o__r",
                "NMEM_AGENT_ID": "mmw-worker",
                "MMW_TASK_SCOPE": task_scope,
                "MMW_SPEC": "76",
                "MMW_TICKET": "61",
            })
            result = subprocess.run(["bash", "-c", command], env=env, text=True,
                                    capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(capture.read_text(encoding="utf-8"))

    def test_map_save_carries_repository_identity_and_all_task_labels(self):
        saved = self.save_example("mmw-map-18")
        args = saved["args"]
        self.assertEqual(args[:4], ["--json", "memories", "add", "--stdin"])
        self.assertEqual(args[args.index("--space") + 1], "o__r")
        self.assertEqual(args[args.index("--agent-id") + 1], "mmw-worker")
        self.assertEqual(args[args.index("--unit-type") + 1], "learning")
        self.assertEqual([args[i + 1] for i, arg in enumerate(args[:-1])
                          if arg == "--label"],
                         ["mmw-experience", "mmw-spec-76", "mmw-ticket-61", "mmw-map-18"])
        self.assertEqual([line.split("：", 1)[0] for line in saved["body"].splitlines()],
                         ["适用条件", "问题", "有效做法", "证据", "发生位置"])

    def test_standalone_save_uses_spec_as_the_only_task_label(self):
        saved = self.save_example("mmw-spec-76")
        args = saved["args"]
        self.assertEqual([args[i + 1] for i, arg in enumerate(args[:-1])
                          if arg == "--label"],
                         ["mmw-experience", "mmw-spec-76", "mmw-ticket-61"])


if __name__ == "__main__":
    unittest.main()
