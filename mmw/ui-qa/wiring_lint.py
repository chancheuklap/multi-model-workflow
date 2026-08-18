#!/usr/bin/env python3
"""按 wiring.schema.json 校验一份界面 QA 接线文件。

技能正文原先写着一张六十行的字段表，让 agent 读完再自己逐字段比对。比对是
机械判定，agent 做它只会漏——尤其 secret 那一条：接线文件里写成明文的密码，
靠正文里一句「拒绝并停」拦不住。这里改成代码判，agent 只看退出码和这里打印
的行。

判得出来的都在这里：字段在不在、类型对不对、取值在不在枚举里、正则编不编得
过、secret 是不是引用。判不出来的留在技能正文，那部分是流程决策——比如缺
designSystem 之后跳过哪两种 check、报告头怎么写。

退出码：0 全过或只有告警，1 有错误或文件读不了，2 用法错。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_NAME = "wiring.schema.json"

MISSING = object()  # 与 JSON 里的 null 区分开：null 是写了但写空，缺失是没写


def walk(data: Any, path: str) -> Any:
    """按点分路径取值。中途遇到非对象或键不存在都返回 MISSING。"""
    cur = data
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return MISSING
        cur = cur[part]
    return cur


def type_ok(value: Any, kind: str) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "integer":
        # JSON 里 true 也是 int 的子类，这里不接受它。
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "object":
        return isinstance(value, dict)
    if kind == "string-array":
        return isinstance(value, list) and all(isinstance(x, str) for x in value)
    if kind == "string-map":
        return isinstance(value, dict) and all(
            isinstance(k, str) and isinstance(v, str) for k, v in value.items()
        )
    if kind == "object-array":
        return isinstance(value, list) and all(isinstance(x, dict) for x in value)
    raise ValueError(f"schema 里有认不出的类型：{kind}")


TYPE_NAMES = {
    "string": "字符串",
    "integer": "整数",
    "object": "对象",
    "string-array": "字符串数组",
    "string-map": "字符串到字符串的映射",
    "object-array": "对象数组",
}


class Report:
    def __init__(self) -> None:
        self.lines: list[tuple[str, str, str]] = []

    def error(self, path: str, msg: str) -> None:
        self.lines.append(("错误", path, msg))

    def warn(self, path: str, msg: str) -> None:
        self.lines.append(("告警", path, msg))

    @property
    def errors(self) -> int:
        return sum(1 for sev, _, _ in self.lines if sev == "错误")

    def print(self, stream) -> None:
        for sev, path, msg in self.lines:
            print(f"{sev}  {path}：{msg}", file=stream)


def required_here(field: dict, data: Any) -> bool:
    """这一条在这份文件里到底必不必填。"""
    if field.get("required"):
        return True
    cond = field.get("requiredWhen")
    if not cond:
        return False
    other = walk(data, cond["path"])
    if "equals" in cond:
        return other == cond["equals"]
    if cond.get("exists"):
        return other is not MISSING
    raise ValueError(f"schema 的 requiredWhen 认不出：{cond}")


def why_required(field: dict) -> str:
    cond = field.get("requiredWhen")
    if not cond:
        return "必填"
    if "equals" in cond:
        return f"{cond['path']} 是 {cond['equals']} 时必填"
    return f"写了 {cond['path']} 就必填"


def check_field(field: dict, data: Any, rep: Report, schema: dict) -> None:
    path = field["path"]
    value = walk(data, path)

    if value is MISSING:
        if required_here(field, data):
            # 父层也缺时只报父层。三行说同一件事，agent 转述给用户就变成三个问题。
            parent = path.rsplit(".", 1)[0] if "." in path else ""
            if parent and walk(data, parent) is MISSING:
                return
            rep.error(path, f"缺这个字段（{why_required(field)}）")
        return

    kind = field["type"]
    if not type_ok(value, kind):
        rep.error(path, f"要{TYPE_NAMES[kind]}，现在是 {json.dumps(value, ensure_ascii=False)}")
        return

    if "enum" in field and value not in field["enum"]:
        allowed = "、".join(field["enum"])
        rep.error(path, f"取值只能是 {allowed}，现在是 {value}")

    if "pattern" in field and not re.match(field["pattern"], value):
        rep.error(path, f"不符合 {field['pattern']}，现在是 {value}")

    if field.get("minItems") and len(value) < field["minItems"]:
        rep.error(path, f"至少要 {field['minItems']} 项，现在是 {len(value)} 项")

    if field.get("regex"):
        try:
            re.compile(value)
        except re.error as exc:
            rep.error(path, f"不是能编译的正则：{exc}")

    if field.get("secretRef") and not re.match(schema["secretRefPattern"], value):
        rep.error(
            path,
            "是明文。secret 只能写成 env:<环境变量名> 或 keychain:<条目名>，"
            "由运行时按前缀解析",
        )

    for sub in field.get("itemFields", []):
        for i, item in enumerate(value):
            sub_path = f"{path}[{i}].{sub['name']}"
            if sub["name"] not in item:
                if sub.get("required"):
                    rep.error(sub_path, "缺这个字段（必填）")
                continue
            sub_value = item[sub["name"]]
            if not type_ok(sub_value, sub["type"]):
                rep.error(
                    sub_path,
                    f"要{TYPE_NAMES[sub['type']]}，"
                    f"现在是 {json.dumps(sub_value, ensure_ascii=False)}",
                )
            elif sub.get("minItems") and len(sub_value) < sub["minItems"]:
                rep.error(sub_path, f"至少要 {sub['minItems']} 项，现在是 {len(sub_value)} 项")


def check_version(data: Any, schema: dict, rep: Report) -> None:
    """版本不对时说清是哪一种不对，不要笼统说格式错。"""
    known = schema["knownVersion"]
    value = walk(data, "version")
    if value is MISSING or not type_ok(value, "integer"):
        return  # 字段本身的报错由 check_field 出，这里不重复
    if value > known:
        rep.error(
            "version",
            f"是 {value}，这个版本的技能只认到 {known}。写这份文件的是更新的技能",
        )
    elif value < known:
        rep.warn("version", f"是 {value}，比当前的 {known} 旧。按 {known} 读，报告里留一行")


def check_unknown_top_keys(data: Any, schema: dict, rep: Report) -> None:
    known = {f["path"].split(".")[0] for f in schema["fields"]}
    for key in data:
        if key not in known:
            rep.warn(key, "这份 schema 里没有这个顶层字段，本次运行不读它")


def check_one_of(data: Any, schema: dict, rep: Report) -> None:
    for group in schema.get("oneOf", []):
        if all(walk(data, p) is MISSING for p in group["paths"]):
            names = "、".join(group["paths"])
            rep.error(names, f"这几个至少要有一个（{group['note']}）")


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("用法：mmw-ui-qa wiring-lint <接线文件>", file=sys.stderr)
        return 2

    target = Path(argv[0])
    schema_path = Path(__file__).resolve().parent / SCHEMA_NAME
    try:
        schema = json.loads(schema_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"读不出字段声明 {schema_path}：{exc}", file=sys.stderr)
        return 1

    try:
        raw = target.read_text()
    except OSError as exc:
        print(f"读不了接线文件：{exc}", file=sys.stderr)
        return 1

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        # 原样打解析器的报错，不改写成「格式有问题」——行号列号是用户要的。
        print(f"接线文件不是合法 JSON：{exc}", file=sys.stderr)
        return 1

    if not isinstance(data, dict):
        print("接线文件的顶层必须是对象", file=sys.stderr)
        return 1

    rep = Report()
    check_version(data, schema, rep)
    for field in schema["fields"]:
        check_field(field, data, rep, schema)
    check_one_of(data, schema, rep)
    check_unknown_top_keys(data, schema, rep)

    if rep.errors:
        rep.print(sys.stderr)
        print(f"接线文件有 {rep.errors} 处错误，不能开跑", file=sys.stderr)
        return 1

    rep.print(sys.stderr)
    print(f"接线文件判过：{len(schema['fields'])} 个字段，没有错误")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
