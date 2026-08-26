"""TypeScript 的词法扫描。

不接完整解析器：跨语言边只要认出「谁在调什么」，而完整解析器要跟着 TypeScript
语法演进走。这一层只做一件事——把注释和字符串字面量摘干净，剩下的按标识符与
标点切开。摘干净这件事本身是必需的：注释里写着 `ipcMain.handle(...)` 的示例，
按正则去抓就会当成真调用点。
"""

from __future__ import annotations

import re

from .fragment import CrossEdgeBuildError

# (类型, 值, 起始偏移)。类型是 "str" / "id" / "punct"。
Token = tuple[str, str, int]


def tokens(text: str) -> list[Token]:
    out: list[Token] = []
    i = 0
    while i < len(text):
        if text.startswith("//", i):
            i = text.find("\n", i)
            i = len(text) if i < 0 else i
            continue
        if text.startswith("/*", i):
            i = text.find("*/", i + 2)
            i = len(text) if i < 0 else i + 2
            continue
        if text[i] in "'\"`":
            quote = text[i]
            start = i
            i += 1
            value = ""
            while i < len(text) and text[i] != quote:
                if text[i] == "\\" and i + 1 < len(text):
                    value += text[i + 1]
                    i += 2
                else:
                    value += text[i]
                    i += 1
            i += 1
            out.append(("str", value, start))
            continue
        m = re.match(r"[A-Za-z_$][\w$]*|\S", text[i:])
        if m:
            out.append(
                ("id" if re.match(r"[A-Za-z_$]", m.group()) else "punct", m.group(), i)
            )
            i += len(m.group())
        else:
            i += 1
    return out


def constant_object(
    text: str, source: str, object_name: str
) -> dict[str, tuple[str, int]]:
    """读出 `const <object_name> = { key: "value", ... }` 这张表。

    只认字符串字面量的值。表里出现计算值时那一项被跳过，后面引用它的调用点会报
    「不认识的键」——比静默连到错误的频道好。
    """
    toks = tokens(text)
    starts = [
        i
        for i, t in enumerate(toks)
        if t[1] == object_name and i > 0 and toks[i - 1][1] == "const"
    ]
    if len(starts) != 1:
        raise CrossEdgeBuildError(
            "ipc", f"{object_name} 权威表缺失或不唯一：{source}"
        )
    i = starts[0]
    while i < len(toks) and toks[i][1] != "{":
        i += 1
    if i == len(toks):
        raise CrossEdgeBuildError("ipc", f"{object_name} 对象体缺失：{source}")
    depth = 1
    i += 1
    result: dict[str, tuple[str, int]] = {}
    while i < len(toks) and depth:
        if toks[i][1] == "{":
            depth += 1
        elif toks[i][1] == "}":
            depth -= 1
        elif (
            depth == 1
            and i + 2 < len(toks)
            and toks[i][0] in {"id", "str"}
            and toks[i + 1][1] == ":"
            and toks[i + 2][0] == "str"
        ):
            key, value = toks[i][1], toks[i + 2][1]
            if key in result:
                raise CrossEdgeBuildError("ipc", f"{object_name} 键重复 {key}：{source}")
            result[key] = (value, text.count("\n", 0, toks[i][2]) + 1)
            i += 2
        i += 1
    if depth or not result:
        raise CrossEdgeBuildError("ipc", f"{object_name} 为空或结构不完整：{source}")
    return result


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def column_of(text: str, offset: int) -> int:
    return offset - text.rfind("\n", 0, offset)
