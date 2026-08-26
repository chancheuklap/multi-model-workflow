#!/usr/bin/env bash
# 技能源正文里，两样东西只由命令回答，不由正文写死。
#
# 规则一、规则二：产物落点只由 artifact path 回答。
# 规则三：命令输出里的值只由专门回答它的命令给出，不按序号从另一条命令的输出里数。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW="$(cd "$HERE/../.." && pwd)"
ARTIFACTS="$HERE/../artifacts.json"
MODEL="$HERE/../mmw.default.json"

# 只扫技能源。五个宿主装的就是这一份：install-skills.sh 软链过去，中间没有展开
# 模板，也没有产物副本，所以扫源等于扫到了每个宿主读到的正文。
SKILLS="$MMW/skills-src"

python3 - "$SKILLS" "$ARTIFACTS" "$MODEL" <<'PY'
import copy
import io
import json
import pathlib
import re
import sys
import tempfile


# 规则三：按序号从命令输出里取值。
#
# 由来是已废除的工作名。当时十二份技能源都写着「运行 `mmw task state`，取第四字段」，于是那个
# 序号成了一份跨十二个文档的合同。名字段现在由当前任务分支或 `--name` 回答，
# 不再从另一条命令的输出里数。
#
# 只放过一种序号说法：「第一个词」。那一个词就是这条命令要回答的问题本身，
# 不是从一串字段里数出来的。
POSITIONAL_PATTERN = re.compile(r"第\s*(?:[一二三四五六七八九十]+|\d+)\s*个?\s*(?:字段|词|列)")
POSITIONAL_ALLOWED = "第一个词"


def load_config(artifacts_path, model_path):
    try:
        artifacts = json.loads(pathlib.Path(artifacts_path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"读不出 artifacts.json：{exc}"]
    try:
        model = json.loads(pathlib.Path(model_path).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"读不出 mmw.default.json：{exc}"]
    if not isinstance(artifacts, dict):
        return None, ["artifacts.json 顶层必须是对象"]
    if not isinstance(model, dict) or not isinstance(model.get("paths"), dict):
        return None, ["mmw.default.json 的 paths 必须是对象"]

    errors = []
    fixed_roots = []
    for category, record in sorted(artifacts.items()):
        if not isinstance(category, str) or not isinstance(record, dict):
            errors.append("artifacts.json 的类别名与记录必须有效")
            continue
        if record.get("status") != "active":
            continue
        root_kind = record.get("root_kind")
        root = record.get("root")
        if root_kind == "fixed":
            if not isinstance(root, str):
                errors.append(f"类别 {category} 的固定根必须是字符串")
            elif root:
                fixed_roots.append((category, root.rstrip("/") + "/"))

    workdir_defaults = []
    for root in ("scratch", "reviews", "release", "worktrees"):
        default = model["paths"].get(root)
        if not isinstance(default, str) or not default:
            errors.append(f"模型档 paths 缺少工作目录根 {root}")
        else:
            workdir_defaults.append((root, default))

    if not fixed_roots:
        errors.append("artifacts.json 没有可扫描的 active fixed 类别根")
    if not workdir_defaults:
        errors.append("模型档 paths 没有可扫描的工作目录根")
    return (fixed_roots, workdir_defaults), errors


def check(skills_path, artifacts_path, model_path, output):
    config, errors = load_config(artifacts_path, model_path)
    if errors:
        for error in errors:
            print(f"  失败  {error}", file=output)
        return 1

    roots = [pathlib.Path(part) for part in str(skills_path).split(":") if part]
    missing = [root for root in roots if not root.is_dir()]
    if not roots or missing:
        for root in missing or [pathlib.Path(skills_path)]:
            print(f"  失败  技能目录不存在：{root}", file=output)
        return 1

    fixed_roots, workdir_defaults = config
    fixed_rules = [
        (category, root, re.compile(re.escape(root) + r"<[^>\r\n]+>"))
        for category, root in fixed_roots
    ]
    workdir_rules = [
        (category, default, re.compile(
            r"(?<![\\w.-])" + re.escape(default) + r"(?=$|/|<)"))
        for category, default in workdir_defaults
    ]
    findings = []
    scanned = 0
    sources = [
        (root, source)
        for root in roots
        for source in sorted(root.rglob("*.md"))
    ]
    for root, source in sources:
        relative = source.relative_to(root)
        # 一个根扫完接着下一个根，报告路径要带上根名才定位得到是哪一份。
        if len(roots) > 1:
            relative = pathlib.Path(root.name) / relative
        scanned += 1
        try:
            lines = source.read_text().splitlines()
        except OSError as exc:
            findings.append(f"{relative}: 读不出文件：{exc}")
            continue
        for line_number, line in enumerate(lines, 1):
            for category, root, pattern in fixed_rules:
                if pattern.search(line):
                    findings.append(
                        f"{relative}:{line_number} 规则一：类别 {category} 的固定根 "
                        f"{root} 后面紧跟占位符")
            for category, default, pattern in workdir_rules:
                if pattern.search(line):
                    findings.append(
                        f"{relative}:{line_number} 规则二：类别 {category} 的工作目录根 "
                        f"默认值 {default}")
            for match in POSITIONAL_PATTERN.finditer(line):
                if match.group(0) == POSITIONAL_ALLOWED:
                    continue
                findings.append(
                    f"{relative}:{line_number} 规则三：按序号取值 "
                    f"{match.group(0)}")

    for finding in findings:
        print(f"  失败  {finding}", file=output)
    print(file=output)
    print(f"检查 {scanned} 个文件，失败 {len(findings)}", file=output)
    return 1 if findings else 0


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False))


def write_case(root, files):
    skills = root / "skills-src"
    for relative, text in files.items():
        target = skills / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    return skills


def capture_check(skills, artifacts, model):
    output = io.StringIO()
    return check(skills, artifacts, model, output), output.getvalue()


def run_examples(artifacts_path, model_path):
    artifacts = json.loads(pathlib.Path(artifacts_path).read_text())
    model = json.loads(pathlib.Path(model_path).read_text())
    artifacts["context-map-fixture"] = {
        "status": "active",
        "root_kind": "fixed",
        "root": "",
    }

    with tempfile.TemporaryDirectory() as temporary:
        root = pathlib.Path(temporary)
        fixture_artifacts = root / "artifacts.json"
        fixture_model = root / "mmw.default.json"
        write_json(fixture_artifacts, artifacts)
        write_json(fixture_model, model)
        config, errors = load_config(fixture_artifacts, fixture_model)
        if errors:
            print("  失败  内部用例不能解析临时数据：" + "; ".join(errors))
            return 1
        fixed_roots, workdir_defaults = config
        fixed_category, fixed_root = fixed_roots[0]
        cases = []

        skills = write_case(root / "fixed-placeholder", {
            "skill/SKILL.md": fixed_root + "<工作名>\n",
        })
        status, output = capture_check(skills, fixture_artifacts, fixture_model)
        cases.append(("固定类别根后接占位符失败", status == 1 and
                      f"skill/SKILL.md:1 规则一：类别 {fixed_category}" in output))

        skills = write_case(root / "fixed-root-alone", {
            "skill/SKILL.md": fixed_root + "\n",
        })
        status, _ = capture_check(skills, fixture_artifacts, fixture_model)
        cases.append(("固定类别根单独出现通过", status == 0))

        for category, default in workdir_defaults:
            skills = write_case(root / f"workdir-alone-{category}", {
                "skill/SKILL.md": default + "\n",
            })
            status, output = capture_check(skills, fixture_artifacts, fixture_model)
            cases.append((f"工作目录根 {category} 单独出现失败", status == 1 and
                          f"skill/SKILL.md:1 规则二：类别 {category}" in output))

            skills = write_case(root / f"workdir-placeholder-{category}", {
                "skill/SKILL.md": default + "<工作名>\n",
            })
            status, output = capture_check(skills, fixture_artifacts, fixture_model)
            cases.append((f"工作目录根 {category} 后接占位符失败", status == 1 and
                          f"skill/SKILL.md:1 规则二：类别 {category}" in output))

        release_root = model["paths"]["release"]
        worktrees_root = model["paths"]["worktrees"]
        skills = write_case(root / "legacy-workdir-literals", {
            "mmw-release/SKILL.md": release_root + "/delivered/one.json\n",
            "mmw-integrate/SKILL.md": worktrees_root + "/task-a\n",
            "mmw-retrieval/building.md": worktrees_root + "/task-b\n",
        })
        status, output = capture_check(skills, fixture_artifacts, fixture_model)
        cases.append(("规则二覆盖 release 与 worktrees 下的三个历史字面值",
                      status == 1 and
                      "mmw-release/SKILL.md:1 规则二：类别 release" in output and
                      "mmw-integrate/SKILL.md:1 规则二：类别 worktrees" in output and
                      "mmw-retrieval/building.md:1 规则二：类别 worktrees" in output))

        # 反例要以斜杠开头。空 root 没被跳过时，它的正则是 `/<…>`；
        # 一行不带前导斜杠的 `<占位符>` 在有 bug 的代码上也不命中，证明不了跳过生效。
        skills = write_case(root / "empty-fixed-root", {
            "skill/SKILL.md": "/<任意占位符>\n",
        })
        status, _ = capture_check(skills, fixture_artifacts, fixture_model)
        cases.append(("空固定根不形成正则前缀", status == 0))

        for text in ("取第四字段作为工作名", "再取第四个词", "取第 4 字段", "看第二列"):
            skills = write_case(root / f"positional-{len(cases)}", {
                "skill/SKILL.md": text + "\n",
            })
            status, output = capture_check(skills, fixture_artifacts, fixture_model)
            cases.append((f"按序号取值失败：{text}", status == 1 and
                          "skill/SKILL.md:1 规则三：按序号取值" in output))

        skills = write_case(root / "positional-allowed", {
            "skill/SKILL.md": "先跑 `mmw task state`。第一个词决定这棵树要不要你自己建。\n",
        })
        status, output = capture_check(skills, fixture_artifacts, fixture_model)
        cases.append(("state 的第一个词通过", status == 0))

        broken_model = copy.deepcopy(model)
        broken_key = workdir_defaults[0][0]
        del broken_model["paths"][broken_key]
        broken_model_path = root / "broken-mmw.default.json"
        write_json(broken_model_path, broken_model)
        skills = write_case(root / "broken-data", {"skill/SKILL.md": "安全文本\n"})
        status, output = capture_check(skills, fixture_artifacts, broken_model_path)
        cases.append(("工作目录根缺少默认值失败", status == 1 and
                      "模型档 paths 缺少工作目录根" in output))

    failed = [name for name, passed in cases if not passed]
    for name, passed in cases:
        print(f"  {'通过' if passed else '失败'}  内部用例：{name}")
    if failed:
        return 1
    print(f"内部用例通过 {len(cases)} 项")
    return 0


skills, artifacts, model = sys.argv[1:4]
if run_examples(artifacts, model):
    sys.exit(1)
sys.exit(check(skills, artifacts, model, sys.stdout))
PY
