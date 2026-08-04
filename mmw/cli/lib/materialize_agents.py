#!/usr/bin/env python3
"""把角色真源与 .mmw.json 型号表物化成各宿主原生 subagent 文件。

用法：
  materialize_agents.py --host pi|cursor|all [--check] [--config <path>] [--out <dir>]

--check  只比对，漂移非零退出。
--out    覆盖 profile 默认输出目录（测试用）。
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any, NoReturn


PLUGIN_ROOT = Path(__file__).resolve().parents[2]
AGENTS_ROOT = PLUGIN_ROOT / "agent-src"
ROLES_PATH = AGENTS_ROOT / "roles.json"
PROFILES_DIR = AGENTS_ROOT / "profiles"
BODIES_DIR = AGENTS_ROOT / "bodies"
DEFAULT_CONFIG = PLUGIN_ROOT / "cli" / "mmw.default.json"


def die(msg: str, code: int = 1) -> NoReturn:
    print(f"mmw agents: {msg}", file=sys.stderr)
    raise SystemExit(code)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        die(f"找不到 {path}")
    except json.JSONDecodeError as exc:
        die(f"{path} 不是合法 JSON：{exc}")


def expand_user_path(raw: str) -> Path:
    return Path(os.path.expanduser(raw)).resolve()


def resolve_model(config: dict[str, Any], role: str, host: str) -> dict[str, str]:
    models = config.get("models") or {}
    if role not in models:
        die(f".mmw.json 没有角色 {role} 的 models 条目")
    entry = models[role]
    hosts = entry.get("hosts") or {}
    override = hosts.get(host) or {}
    out: dict[str, str] = {}
    for field in ("family", "id", "effort"):
        if field in override and override[field] not in (None, ""):
            out[field] = str(override[field])
        elif field in entry and entry[field] not in (None, ""):
            out[field] = str(entry[field])
        else:
            die(f"角色 {role} 缺 models 字段 {field}")
    return out


def format_model(profile: dict[str, Any], model: dict[str, str]) -> str:
    provider_map = profile.get("provider_map") or {}
    family = model["family"]
    provider = provider_map.get(family, "")
    template = profile.get("model_format") or "{id}"
    return template.format(
        provider=provider,
        family=family,
        id=model["id"],
        effort=model["effort"],
    )


def coerce_frontmatter_value(raw: Any, values: dict[str, Any]) -> Any | None:
    """渲染单个 frontmatter 值。返回 None 表示省略该键。"""
    if isinstance(raw, bool) or isinstance(raw, (int, float)):
        return raw
    if not isinstance(raw, str):
        die(f"frontmatter 值类型不支持：{type(raw).__name__}")
    rendered = raw.format(**values)
    if raw in ("{skill}", "{skills}") and not str(values.get("skill", "")).strip():
        return None
    if rendered in ("true", "false") and raw in ("{readonly}", "{async}"):
        return rendered == "true"
    # profile 里写的字面量 "true"/"false" 已是 bool；字符串 true 来自 format
    if raw == "{readonly}":
        return str(values.get("readonly")).lower() in {"true", "1", "yes"}
    return rendered


def render_agent_file(profile: dict[str, Any], values: dict[str, Any], body: str) -> str:
    lines = ["---"]
    for key, raw in (profile.get("frontmatter") or {}).items():
        value = coerce_frontmatter_value(raw, values)
        if value is None:
            continue
        if isinstance(value, bool):
            lines.append(f"{key}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{key}: {value}")
        else:
            text = str(value)
            if "\n" in text:
                lines.append(f"{key}: |")
                for line in text.split("\n"):
                    lines.append(f"  {line}")
            elif (
                text == ""
                or text != text.strip()
                or any(c in text for c in '#{}"')
                or ": " in text
                or text.startswith(":")
            ):
                escaped = text.replace("\\", "\\\\").replace('"', '\\"')
                lines.append(f'{key}: "{escaped}"')
            else:
                lines.append(f"{key}: {text}")
    lines.append("---")
    body_text = body if body.endswith("\n") else body + "\n"
    return "\n".join(lines) + "\n\n" + body_text


def output_dir_for(profile: dict[str, Any], out_override: str | None) -> Path:
    if out_override:
        path = Path(out_override)
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
        return path
    output = profile.get("output") or {}
    kind = output.get("kind")
    raw = output.get("path")
    if not isinstance(kind, str) or not kind or not isinstance(raw, str) or not raw:
        die(f"profile {profile.get('host')} 缺 output.kind/path")
    if kind == "package-dir":
        return (PLUGIN_ROOT / raw).resolve()
    if kind == "user-dir":
        return expand_user_path(raw)
    if kind == "repo-dir":
        # 相对当前 git 根；测试可 --out 覆盖
        try:
            import subprocess

            root = subprocess.check_output(
                ["git", "rev-parse", "--show-toplevel"], text=True
            ).strip()
        except Exception as exc:  # noqa: BLE001
            die(f"repo-dir 需要在 git 仓库内：{exc}")
        return (Path(root) / raw).resolve()
    die(f"不认识的 output.kind：{kind}")


def build_values(
    role_name: str,
    role: dict[str, Any],
    profile: dict[str, Any],
    model: dict[str, str],
) -> dict[str, Any]:
    writable = bool(role.get("writable"))
    tools_key = "writable" if writable else "readonly"
    tools_map = profile.get("tools") or {}
    if tools_key not in tools_map:
        die(f"profile {profile.get('host')} 缺 tools.{tools_key}")
    skill = str(role.get("skill") or "")
    return {
        "role": role_name,
        "agent": role["agent"],
        "description": role["description"],
        "skill": skill,
        "skills": skill,
        "tools": tools_map[tools_key],
        "model": format_model(profile, model),
        "effort": model["effort"],
        "family": model["family"],
        "id": model["id"],
        "writable": "true" if writable else "false",
        "readonly": "false" if writable else "true",
        "acceptance_role": "writer" if writable else "read-only",
    }


def materialize_host(
    host: str,
    config: dict[str, Any],
    roles: dict[str, Any],
    *,
    check_only: bool,
    out_override: str | None,
) -> list[str]:
    profile_path = PROFILES_DIR / f"{host}.json"
    if not profile_path.is_file():
        die(f"没有宿主 profile：{profile_path}")
    profile = load_json(profile_path)
    if profile.get("host") != host:
        die(f"{profile_path} 的 host 字段必须是 {host}")

    out_dir = output_dir_for(profile, out_override)
    managed_glob = profile.get("managed_glob") or "mmw-*.md"
    planned: dict[str, str] = {}

    for role_name, role in roles.items():
        body_name = role.get("body")
        if not body_name:
            die(f"角色 {role_name} 缺 body")
        body_path = BODIES_DIR / body_name
        if not body_path.is_file():
            die(f"角色 {role_name} 的 body 不存在：{body_path}")
        body = body_path.read_text(encoding="utf-8")
        model = resolve_model(config, role_name, host)
        values = build_values(role_name, role, profile, model)
        content = render_agent_file(profile, values, body)
        filename = f"{role['agent']}.md"
        planned[filename] = content

    reports: list[str] = []
    if check_only:
        if not out_dir.is_dir():
            die(f"--check 失败：输出目录不存在 {out_dir}")
        existing = {
            p.name: p.read_text(encoding="utf-8")
            for p in out_dir.iterdir()
            if p.is_file() and fnmatch.fnmatch(p.name, managed_glob)
        }
        drift = False
        for name, content in sorted(planned.items()):
            if name not in existing:
                print(f"缺  {out_dir / name}", file=sys.stderr)
                drift = True
            elif existing[name] != content:
                print(f"旧  {out_dir / name}", file=sys.stderr)
                drift = True
            else:
                reports.append(f"齐  {out_dir / name}")
        for name in sorted(existing):
            if name not in planned:
                print(f"多  {out_dir / name}", file=sys.stderr)
                drift = True
        if drift:
            die(f"{host} 生成物与真源不一致", code=1)
        return reports

    out_dir.mkdir(parents=True, exist_ok=True)

    # 清掉本 profile 管理、但本轮不再生成的旧文件
    for path in list(out_dir.iterdir()):
        if path.is_file() and fnmatch.fnmatch(path.name, managed_glob):
            if path.name not in planned:
                path.unlink()
                reports.append(f"删  {path}")

    for name, content in sorted(planned.items()):
        target = out_dir / name
        fd, tmp_name = tempfile.mkstemp(prefix=f".{name}.", dir=str(out_dir), text=True)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(content)
            os.replace(tmp_name, target)
        except Exception:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise
        model_line = next(
            (line for line in content.splitlines() if line.startswith("model:")),
            "model: ?",
        )
        reports.append(f"写  {target}  ({model_line})")
    return reports


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="materialize_agents.py")
    parser.add_argument("--host", required=True, help="pi | cursor | all")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--config", default="", help=".mmw.json 路径；默认插件 default")
    parser.add_argument("--out", default="", help="覆盖输出目录")
    args = parser.parse_args(argv)

    host_arg = args.host.strip()
    if host_arg == "all":
        hosts = sorted(p.stem for p in PROFILES_DIR.glob("*.json"))
        if not hosts:
            die(f"{PROFILES_DIR} 下没有 profile")
    else:
        hosts = [host_arg]

    if args.out and host_arg == "all":
        die("--out 不能与 --host all 同用")

    config_path = Path(args.config) if args.config else DEFAULT_CONFIG
    if not config_path.is_file():
        die(f"配置不存在：{config_path}")
    config = load_json(config_path)
    roles_doc = load_json(ROLES_PATH)
    roles = roles_doc.get("roles") or {}
    if not roles:
        die(f"{ROLES_PATH} 没有 roles")

    # 校验配置覆盖全部角色
    for role_name in roles:
        if role_name not in (config.get("models") or {}):
            die(f"配置缺角色 {role_name} 的 models")

    all_reports: list[str] = []
    for host in hosts:
        all_reports.extend(
            materialize_host(
                host,
                config,
                roles,
                check_only=args.check,
                out_override=args.out or None,
            )
        )

    for line in all_reports:
        print(line)
    action = "检查" if args.check else "物化"
    print(f"{action}完成：{', '.join(hosts)}，{len(all_reports)} 项")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
