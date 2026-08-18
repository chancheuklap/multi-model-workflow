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

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 技能源目录是 skills-src。五个宿主装的都是它，没有第二份可查。
SKILLS="$(cd "$HERE/../../skills-src" && pwd)"
CLI="$(cd "$HERE/.." && pwd)"

python3 - "$SKILLS" "$CLI" <<'PY'
import json, pathlib, re, sys

skills = pathlib.Path(sys.argv[1])
cli = pathlib.Path(sys.argv[2])
names = {d.name for d in skills.iterdir() if d.is_dir()}

# MMW 装进各宿主的外部技能也算数。名字取自 ui-qa/deps.json 里 kind 为 skill
# 的那几条的 installName——那份声明就是安装脚本照着装的那一份，不是另抄的清单。
# 声明里没有的名字照样判不存在。
ui_qa_deps = cli.parent / 'ui-qa' / 'deps.json'
if ui_qa_deps.is_file():
    try:
        declared = json.loads(ui_qa_deps.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  失败  读不出 ui-qa/deps.json：{exc}")
        sys.exit(1)
    for entry in declared.get('packages', []):
        if entry.get('kind') == 'skill':
            install_name = entry.get('installName')
            if not install_name:
                print("  失败  ui-qa/deps.json 里 kind 为 skill 的条目缺 installName")
                sys.exit(1)
            names.add(install_name)

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

try:
    artifacts = json.loads((cli / 'artifacts.json').read_text())
except (OSError, json.JSONDecodeError) as exc:
    print(f"  失败  读不出 artifacts.json：{exc}")
    sys.exit(1)
if not isinstance(artifacts, dict):
    print("  失败  artifacts.json 顶层必须是对象")
    sys.exit(1)
ARTIFACT_CATEGORIES = set(artifacts)

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

# 同一个技能目录里，一份 reference 指主文件或另一份 reference 的第 N 步。上面那条
# RE_STEP 只认跨技能的 `/技能名` 加中文「第 N 步」，这一类它一条都抓不到——
# mmw-ui-qa 全英文，指的又都是同目录 sibling，14 处引用里错了一处（scope 写成第 6 步，
# 实际在第 7 步）在仓库里躺着，正是这条测试当初要防的那种错。
# 三种写法，都要有明确的目标文件，才判得出「第 N 步」指的是哪一份的第 N 步：
#   [SKILL.md](SKILL.md) step 4        文件在前
#   Step 3 of [SKILL.md](SKILL.md)     步骤在前
#   main-file step 4                   指同目录 SKILL.md
# 不认没有目标文件的裸 `step 3`：技能里的「第 3 步」和路径包里的「第 3 步」机械上
# 分不开（SEMANTIC.md 的 `Step 1 writes ...` 说的是走查路径的第一步），
# 硬认就只能靠豁免清单撑着，那按 AGENTS.md 就不算机械校验了。
STEP_WORD = r'(?:step|Step|第\s*)'
RE_FILE_THEN_STEP = re.compile(
    r'\[[^\]]+\.md\]\((?!http)([^)]+\.md)\)[^|。，]{0,40}?' + STEP_WORD + r'\s*([0-9]+)')
RE_STEP_THEN_FILE = re.compile(
    STEP_WORD + r'\s*([0-9]+)[^|。，]{0,20}?of \[[^\]]+\.md\]\((?!http)([^)]+\.md)\)')
RE_MAINFILE_STEP = re.compile(r'main-file ' + STEP_WORD + r'\s*([0-9]+)')
RE_CMD = re.compile(r'`mmw ([a-z-]+)(?: ([a-z-]+))?')

RE_ARTIFACT_PATH = re.compile(r'`mmw artifact path ([a-z0-9][a-z0-9-]*)')

ok = 0
bad = []

for p in sorted(skills.rglob('*.md')):
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

        for m in RE_ARTIFACT_PATH.finditer(line):
            category = m.group(1)
            if category in ARTIFACT_CATEGORIES:
                ok += 1
            else:
                bad.append(
                    f"{rel}:{i} mmw artifact path 的类别不存在 {category}")

        for m in RE_STEP.finditer(line):
            skill, step = m.group(1), m.group(2)
            target = skills / skill / 'SKILL.md'
            if not target.is_file():
                bad.append(f"{rel}:{i} 指向不存在的技能 /{skill}")
            elif step in RE_STEP_NUM.findall(target.read_text()):
                ok += 1
            else:
                bad.append(f"{rel}:{i} 说「/{skill} 第 {step} 步」，但那个技能里没有第 {step} 步")

        sibling_refs = [(m.group(1), m.group(2)) for m in RE_FILE_THEN_STEP.finditer(line)]
        sibling_refs += [(m.group(2), m.group(1)) for m in RE_STEP_THEN_FILE.finditer(line)]
        sibling_refs += [('SKILL.md', m.group(1)) for m in RE_MAINFILE_STEP.finditer(line)]
        for name, step in sibling_refs:
            target = p.parent / name
            if not target.is_file():
                bad.append(f"{rel}:{i} 指向不存在的文件 {name}")
            elif step in RE_STEP_NUM.findall(target.read_text()):
                ok += 1
            else:
                bad.append(f"{rel}:{i} 说 {name} 的第 {step} 步，但那份文件里没有第 {step} 步")

# MMW 的技能面全部可被模型触发：一个技能只有用户点名才进得去时，需要它的那一跳
# 只能靠用户记得它存在。frontmatter 里出现 disable-model-invocation 就是把它关掉。
for p in sorted(skills.glob('*/SKILL.md')):
    head = p.read_text().split('\n---', 1)[0]
    if re.search(r'(?m)^disable-model-invocation:\s*true\s*$', head):
        bad.append(f"{p.relative_to(skills)} 声明了 disable-model-invocation")
    else:
        ok += 1

# 第五类：派发时点名的方法论技能。roles.json 的 skill 字段非空时，派发会让那个
# agent 去调用它。技能名写错，agent 那边不会报错——它调不到，就自己按印象审。
# 装没装不在这里判：install-skills.sh 把 skills-src 全套装进五个宿主，没有子集。
roles = json.loads((cli.parent / 'agent-src' / 'roles.json').read_text())['roles']
for role, meta in sorted(roles.items()):
    skill = (meta.get('skill') or '').strip()
    if not skill:
        continue
    if skill not in names:
        bad.append(f"agent-src/roles.json 角色 {role} 的 skill 指向不存在的技能 {skill}")
    else:
        ok += 1

# 第六类：派发占位符。派发动作曾经在构建期展开，正文里写 [[mmw-…]] 占位符；现在
# 派发由 mmw launch 在运行期回答，技能直接装给宿主，没有哪一层会再展开它。留下
# 的占位符对模型就是一句看不懂的话，那一跳会静悄悄地没人做。
for p in sorted(skills.rglob('*.md')):
    text = p.read_text()
    if '[[mmw-' in text:
        for i, line in enumerate(text.split('\n'), 1):
            if '[[mmw-' in line:
                bad.append(
                    f"{p.relative_to(skills)}:{i} 还在用 [[mmw-…]] 占位符；"
                    "派发写 `mmw launch`，见 cli/host-actions.json")
    else:
        ok += 1

# 上面那三条规则得真能抓到东西，不然全绿也说明不了什么。反例同样要测：裸的
# `step 3` 没有目标文件，判不出指的是哪一份，抓到它才是错的。
probes = [
    (RE_FILE_THEN_STEP, 'the map is in [SKILL.md](SKILL.md) step 4', True),
    (RE_STEP_THEN_FILE, 'Step 3 of [SKILL.md](SKILL.md) sends you here', True),
    (RE_MAINFILE_STEP, 'goes in the coverage report (main-file step 4)', True),
    (RE_FILE_THEN_STEP, 'go back to step 3 and continue', False),
    (RE_STEP_THEN_FILE, 'old step 3 is now 4', False),
]
for rx, sample, want in probes:
    if bool(rx.search(sample)) != want:
        verb = "抓不到" if want else "误抓了"
        print(f"  失败  sibling 步骤引用的正则{verb}：{sample}")
        sys.exit(1)
    ok += 1

for b in bad:
    print(f"  失败  {b}")
print()
print(f"过 {ok}，失败 {len(bad)}")
sys.exit(1 if bad else 0)
PY
