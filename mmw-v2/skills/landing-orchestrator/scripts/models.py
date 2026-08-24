#!/usr/bin/env python3
"""解析消费仓库 docs/agents/models.md 的角色表，输出 JSON。

用法：models.py <models.md 路径>
  成功：stdout 一行 JSON {"orchestrator": {"kind","model","effort"}, ...}，退出 0
  失败：stderr 一行原因，退出 1

只判机器能判的事：六个角色齐全且顺序固定、三列非空、强度在集合内。
"""

import json
import re
import sys
from pathlib import Path

ROLES = [
    ("编排者", "orchestrator"),
    ("规划者", "planner"),
    ("初级工人", "junior-worker"),
    ("高级工人", "senior-worker"),
    ("复验者", "verifier"),
    ("升级顾问", "advisor"),
]
EFFORTS = {"low", "medium", "high", "xhigh", "max"}
HEADER = ["角色", "宿主 kind", "模型串", "思考强度"]


def fail(msg: str) -> int:
    print(f"models.md: {msg}", file=sys.stderr)
    return 1


def parse(text: str) -> dict:
    rows = []
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        rows.append(cells)
    if not rows:
        raise ValueError("没有找到表")
    if rows[0] != HEADER:
        raise ValueError(f"表头应为 {' | '.join(HEADER)}，实际 {' | '.join(rows[0])}")
    body = rows[1:]
    names = [r[0] for r in body]
    want = [zh for zh, _ in ROLES]
    if names != want:
        raise ValueError(f"左列应固定为 {'、'.join(want)}，实际 {'、'.join(names)}")
    out = {}
    for (zh, en), cells in zip(ROLES, body):
        if len(cells) != 4:
            raise ValueError(f"{zh} 行应有 4 列，实际 {len(cells)}")
        kind, model, effort = cells[1], cells[2], cells[3]
        if not kind or not model or not effort:
            raise ValueError(f"{zh} 行有空单元格")
        if effort not in EFFORTS:
            raise ValueError(f"{zh} 的思考强度 {effort!r} 不在 {sorted(EFFORTS)} 内")
        out[en] = {"kind": kind, "model": model, "effort": effort}
    return out


def main() -> int:
    if len(sys.argv) != 2:
        return fail("用法 models.py <models.md>")
    path = Path(sys.argv[1])
    if not path.is_file():
        return fail(f"文件不存在 {path}")
    try:
        table = parse(path.read_text(encoding="utf-8"))
    except ValueError as e:
        return fail(str(e))
    print(json.dumps(table, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
