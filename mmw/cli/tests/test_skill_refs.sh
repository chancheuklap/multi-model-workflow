#!/usr/bin/env bash
# 技能之间的四类引用必须指得到东西。四类都是「删一节、加一节、改个名」时最容易
# 漏掉的，而漏掉之后没有任何运行时报错——读到那句话的 agent 只会去找一个不存在
# 的东西，然后自己编一个。
#
#   `/技能名`        那个技能目录真在
#   [x.md](x.md)     同目录那个文件真在
#   「第 N 步」       被指的那个技能真有第 N 步
#   `mmw a b`        点名的命令与子命令 CLI 里真有
#
# 第三类是这个脚本的由来：mmw-review 删掉一节之后步骤重编号，三处「第 8 步复审」
# 和一处指错节的「第 6 步」在仓库里躺了一轮才被发现。
#
# 第四类防的是承诺一条不存在的命令。指针节曾写着「标签清单用 mmw 的子命令查」，
# 而那条命令根本没有——agent 照做只会打出一条报错。真实命令表从 cli/mmw 的两层
# 分发里解析，不另手抄一份。
#
# 曾经还有第五类：散文里用反引号点名的 `x.md` 必须存在。它删掉了。机械上分不出
# 「技能目录里的文件」和「运行时才产生的文件名」——research 的 `test-plan.md`、
# `report.md` 都是后者，判成断链是错的。要留住它只能不断加豁免清单，而按 AGENTS.md，
# 靠豁免清单撑着的校验不算机械校验，越界就删掉，不加例外分支。
#
# 解析用内嵌 python：四类都是正则提取加路径判断，写成 sed 管道要跟分隔符转义
# 缠斗，BSD 与 GNU 的 sed 行为还不一样。
#
# mmw-setup 排除在外，理由同 test_labels_sync.sh：那个目录是上一版做法的背景
# 线索，不是技能。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 技能源目录现在叫 skills-src；skills-claude-code 等是物化产物，不在这里查。
SKILLS="$(cd "$HERE/../../skills-src" && pwd)"
CLI="$(cd "$HERE/.." && pwd)"

python3 - "$SKILLS" "$CLI" <<'PY'
import json, pathlib, re, sys

skills = pathlib.Path(sys.argv[1])
cli = pathlib.Path(sys.argv[2])
names = {d.name for d in skills.iterdir() if d.is_dir()}

# 真实命令表从 cli/mmw 的两层分发解析出来，不另抄一份——抄一份就会跟 CLI 走散。
cli_src = (cli / 'mmw').read_text()
TOP_CMDS = set(re.findall(r'^  ([a-z-]+)\) shift; ', cli_src, re.M))
SUB_CMDS = {}
for m in re.finditer(r'^cmd_(\w+)\(\) \{(.*?)^\}', cli_src, re.M | re.S):
    SUB_CMDS[m.group(1).replace('_', '-')] = set(
        re.findall(r'^    ([a-z-]+)\)', m.group(2), re.M))
if not TOP_CMDS:
    print("  失败  解析不出 cli/mmw 的顶层命令表，分发写法变了就改这里")
    sys.exit(1)

# `/名字` 里排除真实路径与别的宿主的东西：/wiki 是 GitHub 的 wiki 页，/tmp 是
# 目录，/install-wiki 是 Factory droid 的命令，/settings 与 /playwright-cli
# 属于别的宿主。
NOT_SKILLS = {'wiki', 'tmp', 'install-wiki', 'settings', 'playwright-cli'}

RE_SKILL = re.compile(r'`/([a-z0-9][a-z0-9-]*)`')
RE_LINK = re.compile(r'\]\((?!http)([^)]+\.md)\)')
RE_STEP = re.compile(r'`/([a-z0-9-]+)`[^|。，]{0,12}第 ([0-9]+) 步')
# 步骤两种写法都要认：标题式的 `## 3. 干什么`，和 `## 流程` 底下的有序列表 `3. 干什么`。
# 只认一种就是跟排版绑死：技能把步骤从标题改成列表，语义没动，测试却红。
RE_STEP_NUM = re.compile(r'^(?:#{2,3} )?([0-9]+)\. ', re.M)
RE_CMD = re.compile(r'`mmw ([a-z-]+)(?: ([a-z-]+))?')

ok = 0
bad = []

for p in sorted(skills.rglob('*.md')):
    if 'mmw-setup' in p.parts:
        continue
    rel = p.relative_to(skills)
    text = p.read_text()

    for i, line in enumerate(text.split('\n'), 1):
        for m in RE_SKILL.finditer(line):
            name = m.group(1)
            if name in NOT_SKILLS:
                continue
            if name in names:
                ok += 1
            else:
                bad.append(f"{rel}:{i} 引用了不存在的技能 /{name}")

        # CONTEXT-FORMAT.md 画的是目标仓库里的目录树示例，不是本仓库的路径。
        if p.name != 'CONTEXT-FORMAT.md':
            for m in RE_LINK.finditer(line):
                if (p.parent / m.group(1)).is_file():
                    ok += 1
                else:
                    bad.append(f"{rel}:{i} 链到不存在的文件 {m.group(1)}")

        for m in RE_CMD.finditer(line):
            top, sub = m.group(1), m.group(2)
            if top not in TOP_CMDS:
                bad.append(f"{rel}:{i} 点名的命令不存在 mmw {top}")
                continue
            # 收子命令的那几条，第二个词必须是真子命令；不收的（dispatch 的角色、
            # skill-path 的角色）第二个词是参数，不查。
            expected = SUB_CMDS.get(top, set())
            if expected and sub and sub not in expected:
                bad.append(f"{rel}:{i} mmw {top} 没有子命令 {sub}")
            else:
                ok += 1

        for m in RE_STEP.finditer(line):
            skill, step = m.group(1), m.group(2)
            target = skills / skill / 'SKILL.md'
            if not target.is_file():
                bad.append(f"{rel}:{i} 指向不存在的技能 /{skill}")
            elif step in RE_STEP_NUM.findall(target.read_text()):
                ok += 1
            else:
                bad.append(f"{rel}:{i} 说「/{skill} 第 {step} 步」，但那个技能里没有第 {step} 步")

# 第五类：派发时点名的方法论技能。roles.json 的 skill 字段非空时，派发会让那个
# agent 去调用它。技能名写错，或者技能没装进 headless Codex 的技能目录，agent
# 那边同样不会报错——它调不到，就自己按印象审。
roles = json.loads((cli.parent / 'agent-src' / 'roles.json').read_text())['roles']
wanted = re.search(r'^WANTED=\(([^)]*)\)',
                   (cli / 'lib' / 'install-agent-skills.sh').read_text(), re.M)
if not wanted:
    print("  失败  解析不出 install-agent-skills.sh 的 WANTED 列表，写法变了就改这里")
    sys.exit(1)
installed = set(wanted.group(1).split())
for role, meta in sorted(roles.items()):
    skill = (meta.get('skill') or '').strip()
    if not skill:
        continue
    if skill not in names:
        bad.append(f"agent-src/roles.json 角色 {role} 的 skill 指向不存在的技能 {skill}")
    elif skill not in installed:
        bad.append(
            f"agent-src/roles.json 角色 {role} 要 {skill}，"
            "但 install-agent-skills.sh 的 WANTED 里没有它")
    else:
        ok += 1

for b in bad:
    print(f"  失败  {b}")
print()
print(f"过 {ok}，失败 {len(bad)}")
sys.exit(1 if bad else 0)
PY
