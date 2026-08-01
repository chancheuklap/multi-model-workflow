#!/usr/bin/env python3
"""按 adapters/<宿主>/fields.json 把 roles/*.md 翻成那一家认识的角色文件。

源角色文件的 frontmatter 是我们自己的中间格式：model / effort / write / mcp / skills。
这里只输出目标宿主认识的字段——翻译表里没出现的键一律不带进产物，skills 只给安装脚本读。

model 在表里翻出 null 的角色不生成：那几个本宿主派不了，走无头，由 dispatch.sh 直接读源文件。
翻出「待实测」的当场停——模型名是全表唯一会当场失败的一格，猜一个等于把失败推到运行时。
其余字段翻不出来就跳过并在 stderr 说明，那一条边界降级成角色正文里的一句话。

用法：
    render-roles.py --fields <fields.json> --roles-dir <dir> --out-dir <dir> [--check]
    render-roles.py --fields <fields.json> --roles-dir <dir> --list native|headless
"""

import argparse
import json
import pathlib
import re
import sys

PENDING = "待实测"


def parse_role(path):
    """把一份源角色文件拆成 frontmatter 字典与正文。

    正文只取到「线下」那一节之前——那一节明确标着不是技能内容，
    送进子代理的上下文里与它自己那句标注自相矛盾。
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or "\n---\n" not in text:
        raise SystemExit(f"ERROR: {path} 没有 frontmatter")
    front, rest = text[4:].split("\n---\n", 1)

    meta, key = {}, None
    for line in front.splitlines():
        if not line.strip():
            continue
        m = re.match(r"^([A-Za-z][\w-]*):\s*(.*)$", line)
        if m:
            key, val = m.group(1), m.group(2).strip()
            if val == "":
                meta[key] = []
            elif val.startswith("[") and val.endswith("]"):
                meta[key] = [x.strip() for x in val[1:-1].split(",") if x.strip()]
            else:
                meta[key] = val
        elif line.lstrip().startswith("- ") and isinstance(meta.get(key), list):
            meta[key].append(line.lstrip()[2:].strip())

    body_lines = []
    for line in rest.splitlines():
        if line.startswith("## 线下"):
            break
        body_lines.append(line)
    # 掐掉线下那一节之前的分隔线与尾部空行
    while body_lines and body_lines[-1].strip() in ("", "---"):
        body_lines.pop()
    return meta, "\n".join(body_lines)


def translate(meta, fields, warn):
    """把中间格式翻成目标宿主的 frontmatter。本宿主派不了这个模型就回 None。"""
    role = meta.get("name", "?")
    model_table = {k: v for k, v in fields.get("model", {}).items() if k != "_"}
    src_model = meta.get("model")
    if src_model not in model_table:
        raise SystemExit(f"ERROR: 角色 {role} 的模型 {src_model} 不在 {fields['host']} 的翻译表里")
    model_val = model_table[src_model]
    if model_val is None:
        return None
    if model_val == PENDING:
        raise SystemExit(
            f"ERROR: {fields['host']} 还没实测 {src_model} 该怎么写。"
            f"起一个子代理试一次，把结果填进 fields.json 再装。"
        )

    out = {"name": role, "description": meta.get("description", "")}

    eff = {k: v for k, v in fields.get("effort", {}).items() if k != "_"}
    if eff.get("mergeInto") == "model":
        model_val = eff["pattern"].format(model=model_val, effort=meta.get("effort", ""))
    out["model"] = model_val
    if eff.get("field") and eff["field"] != PENDING:
        out[eff["field"]] = meta.get("effort", "")
    elif eff.get("field") == PENDING:
        warn(f"{fields['host']}：思考档字段待实测，{role} 不带这一项")

    wf = {k: v for k, v in fields.get("write", {}).items() if k != "_"}
    field = wf.get("field")
    writable = meta.get("write") == "true"
    if field == PENDING:
        warn(f"{fields['host']}：写盘字段待实测，{role} 的只读边界只剩角色正文那句话")
    elif field:
        if wf.get("invert"):
            out[field] = "false" if writable else "true"
        elif "whenFalse" in wf and not writable:
            out[field] = list(wf["whenFalse"])

    mc = {k: v for k, v in fields.get("mcp", {}).items() if k != "_"}
    servers = meta.get("mcp", [])
    if mc.get("field") and mc["field"] != PENDING and servers:
        style = mc.get("style", "")
        out[mc["field"]] = (
            [style.replace("{server}", s) for s in servers] if "{server}" in style else list(servers)
        )
    return out


def emit(front, body):
    lines = ["---"]
    for k, v in front.items():
        lines.append(f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body.strip() + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields", required=True)
    ap.add_argument("--roles-dir", required=True)
    ap.add_argument("--out-dir")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--list", choices=["native", "headless"])
    args = ap.parse_args()

    fields = json.loads(pathlib.Path(args.fields).read_text(encoding="utf-8"))
    roles = sorted(pathlib.Path(args.roles_dir).glob("*.md"))
    if not roles:
        raise SystemExit(f"ERROR: {args.roles_dir} 下没有角色文件")

    warned = []

    def warn(msg):
        warned.append(msg)

    rendered, headless = {}, []
    for rf in roles:
        meta, body = parse_role(rf)
        front = translate(meta, fields, warn)
        if front is None:
            headless.append(meta["name"])
        else:
            rendered[meta["name"]] = emit(front, body)

    if args.list:
        names = headless if args.list == "headless" else sorted(rendered)
        print("\n".join(sorted(names)))
        return 0

    if not args.out_dir:
        raise SystemExit("ERROR: 要生成角色文件就得给 --out-dir")
    out = pathlib.Path(args.out_dir).expanduser()

    rc = 0
    for name, text in sorted(rendered.items()):
        dst = out / f"{name}.md"
        if args.check:
            if not dst.exists():
                print(f"未装  {name}", file=sys.stderr)
                rc = 1
            elif dst.read_text(encoding="utf-8") != text:
                print(f"过期  {name}（源角色文件改过，重装）", file=sys.stderr)
                rc = 1
            else:
                print(f"已装  {name}")
        else:
            out.mkdir(parents=True, exist_ok=True)
            dst.write_text(text, encoding="utf-8")
            print(f"生成  {name}")

    for m in dict.fromkeys(warned):
        print(f"注意  {m}", file=sys.stderr)
    if headless:
        print(f"走无头  {'、'.join(sorted(headless))}（不生成角色文件，由 dispatch.sh 读源文件）")
    return rc


if __name__ == "__main__":
    sys.exit(main())
