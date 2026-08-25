#!/usr/bin/env python3
"""frontier 判定：从 stdin 读子票 JSON 数组，输出可派发的票。

输入是 `gh api repos/<owner>/<repo>/issues/<父票>/sub_issues --paginate` 的原样输出
（每个元素含 number、state、assignees、labels、issue_dependencies_summary.blocked_by）。

frontier = 开放（state == "open"）、无阻塞（blocked_by == 0）、无认领（assignees 为空）、
不带 blocked:decision 标签。编号升序（tracker 的 map 顺序）。每行：<编号> <定级标签或 ungraded>。
输入不是 JSON 数组、元素缺字段：stderr 报原因，退出 1。frontier 为空：不输出，退出 0。
"""

import json
import sys

GRADES = ("worker:junior", "worker:senior")
# 停车 issue 挂在同一个任务父 issue 下，本身开放、无阻塞、无认领。不按标签排除，
# 它会被当成一张 ungraded 票派给工人。
PARKING = "blocked:decision"


def main() -> int:
    try:
        issues = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"frontier: stdin 不是 JSON（{e}）", file=sys.stderr)
        return 1
    if not isinstance(issues, list):
        print("frontier: 顶层应为数组", file=sys.stderr)
        return 1
    out = []
    for it in issues:
        try:
            number = it["number"]
            state = it["state"]
            assignees = it["assignees"]
            blocked_by = it["issue_dependencies_summary"]["blocked_by"]
            labels = [l["name"] for l in it["labels"]]
        except (KeyError, TypeError) as e:
            print(f"frontier: 元素缺字段 {e}（{it.get('number', '?') if isinstance(it, dict) else it!r}）", file=sys.stderr)
            return 1
        if state != "open" or blocked_by != 0 or assignees or PARKING in labels:
            continue
        grade = next((g for g in GRADES if g in labels), "ungraded")
        out.append((number, grade))
    for number, grade in sorted(out):
        print(f"{number} {grade}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
