#!/usr/bin/env bash
# 技能之间的三类引用必须指得到东西。三类都是「删一节、加一节、改个名」时最容易
# 漏掉的，而漏掉之后没有任何运行时报错——读到那句话的 agent 只会去找一个不存在
# 的东西，然后自己编一个。
#
#   `/技能名`        那个技能目录真在
#   [x.md](x.md)     同目录那个文件真在
#   「第 N 步」       被指的那个技能真有第 N 步
#   `x/y.md`         散文里点名的文件真在（跨技能引用大多长这样，不是 markdown 链接）
#   `mmw a b`        点名的命令与子命令 CLI 里真有
#
# 第三类是这个脚本的由来：mmw-review 删掉一节之后步骤重编号，三处「第 8 步复审」
# 和一处指错节的「第 6 步」在仓库里躺了一轮才被发现。第四类补的是同一个洞的另一半：
# 跨技能引用几乎都写成散文（「`/mmw-review` 目录里的 `self-review.md`」），第二类
# 那条只认 markdown 链接语法，管不到它们。
#
# 第五类防的是承诺一条不存在的命令。指针节曾写着「标签清单用 mmw 的子命令查」，
# 而那条命令根本没有——agent 照做只会打出一条报错。真实命令表从 cli/mmw 的两层
# 分发里解析，不另手抄一份。
#
# 解析用内嵌 python：三类都是正则提取加路径判断，写成 sed 管道要跟分隔符转义
# 缠斗，BSD 与 GNU 的 sed 行为还不一样。
#
# mmw-setup 排除在外，理由同 test_labels_sync.sh：那个目录是上一版做法的背景
# 线索，不是技能。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$(cd "$HERE/../../skills" && pwd)"
SKILLS_PI="$(cd "$HERE/../../skills-pi" && pwd)"
SKILLS_CLAUDE="$(cd "$HERE/../../skills-claude-code" && pwd)"
SKILLS_CODEX="$(cd "$HERE/../../skills-codex" && pwd)"
CLI="$(cd "$HERE/.." && pwd)"

# 引用扫描扫发布面；源目录只参与占位符与存在性
python3 - "$SKILLS_SRC" "$SKILLS_PI" "$SKILLS_CLAUDE" "$SKILLS_CODEX" "$CLI" <<'PY'
import pathlib, re, sys

skills_src = pathlib.Path(sys.argv[1])
skills_roots = [pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4])]
cli = pathlib.Path(sys.argv[5])
names = set()
for root in [skills_src, *skills_roots]:
    if root.is_dir():
        names |= {d.name for d in root.iterdir() if d.is_dir() and d.name != 'mmw-setup'}

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
RE_CODEX_SKILL = re.compile(r'`\$mmw:(mmw-[a-z0-9-]+)`')
RE_LINK = re.compile(r'\]\((?!http)([^)]+\.md)\)')
RE_STEP = re.compile(r'`/([a-z0-9-]+)`[^|。，]{0,12}第 ([0-9]+) 步')
RE_HEADING = re.compile(r'^#{2,3} ([0-9]+)\.', re.M)
RE_FILE = re.compile(r'`([A-Za-z0-9_][A-Za-z0-9._/-]*\.md)`')
RE_CMD = re.compile(r'`mmw ([a-z-]+)(?: ([a-z-]+))?')

# 目标仓库里的文件，不在插件里，查不到是正常的。
HOST_REPO_FILES = {
    'AGENTS.md', 'CLAUDE.md', 'CONTEXT.md', 'CONTEXT-MAP.md', 'TESTING.md',
    'README.md', 'CODING_STANDARDS.md', 'CONTRIBUTING.md', 'Home.md', '_Sidebar.md',
}
# 讲命名规则时举的例子，不是真文件。
NAMING_EXAMPLES = {
    'dark-mode.md', 'plugin-system.md', 'graphql-api.md', '0001-slug.md', '0002-slug.md',
}

ok = 0
bad = []

def skill_file(skill_name: str, filename: str = 'SKILL.md') -> pathlib.Path:
    for root in skills_roots:
        candidate = root / skill_name / filename
        if candidate.is_file():
            return candidate
    return None

def any_skill_file(ref: str) -> bool:
    for root in skills_roots:
        if (root / ref).is_file():
            return True
        if '/' not in ref and any(root.rglob(ref)):
            return True
    return False

for skills in skills_roots:
    if not skills.is_dir():
        continue
    for p in sorted(skills.rglob('*.md')):
        if 'mmw-setup' in p.parts:
            continue
        rel = f"{skills.name}/{p.relative_to(skills)}"
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

            for m in RE_CODEX_SKILL.finditer(line):
                name = m.group(1)
                if name in names:
                    ok += 1
                else:
                    bad.append(f"{rel}:{i} 引用了不存在的 Codex 技能 $mmw:{name}")

            # CONTEXT-FORMAT.md 画的是目标仓库里的目录树示例，不是本仓库的路径。
            if p.name != 'CONTEXT-FORMAT.md':
                for m in RE_LINK.finditer(line):
                    if (p.parent / m.group(1)).is_file():
                        ok += 1
                    else:
                        bad.append(f"{rel}:{i} 链到不存在的文件 {m.group(1)}")

            for m in RE_FILE.finditer(line):
                ref = m.group(1)
                # 模板占位（含 <> 或 *）、点开头的产出目录、docs/ 下的产出物都不是插件内的文件。
                if ref in HOST_REPO_FILES or ref in NAMING_EXAMPLES:
                    continue
                if ref.startswith('.') or ref.startswith('docs/'):
                    continue
                if '/' in ref:
                    # 带技能名前缀的写法（`mmw-tdd/quality-bar.md`）从各 skills 根解析。
                    found = any_skill_file(ref)
                else:
                    # 裸文件名：同目录优先，其次全树同名——跨技能引用常写成
                    # 「`/mmw-prototype` 的 `EVIDENCE.md`」，不带路径。
                    found = (p.parent / ref).is_file() or any_skill_file(ref)
                if found:
                    ok += 1
                else:
                    bad.append(f"{rel}:{i} 点名的文件不存在 {ref}")

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
                target = skill_file(skill)
                if target is None:
                    bad.append(f"{rel}:{i} 指向不存在的技能 /{skill}")
                elif step in RE_HEADING.findall(target.read_text()):
                    ok += 1
                else:
                    bad.append(f"{rel}:{i} 说「/{skill} 第 {step} 步」，但那个技能里没有第 {step} 步")

# 已废除中转派发技能；源用占位符，发布面写死启动句
for root in skills_roots:
    banned = root / 'mmw-dispatching-agents'
    if banned.exists():
        bad.append(f'发布面不应再有 {banned}')
    else:
        ok += 1

src_impl = skills_src / 'mmw-implement' / 'SKILL.md'
if not src_impl.is_file():
    bad.append('缺少 skills/mmw-implement/SKILL.md 源')
else:
    st = src_impl.read_text()
    if '[[mmw-launch:worker:worktree]]' not in st:
        bad.append('skills 源 implement 缺 [[mmw-launch:worker:worktree]]')
    elif 'mmw-dispatching-agents' in st:
        bad.append('skills 源 implement 仍引用派发中转技能')
    else:
        ok += 1

pi_impl = skills_roots[0] / 'mmw-implement' / 'SKILL.md'
cc_impl = skills_roots[1] / 'mmw-implement' / 'SKILL.md'
codex_impl = skills_roots[2] / 'mmw-implement' / 'SKILL.md'
if pi_impl.is_file():
    t = pi_impl.read_text()
    if 'mmw-worker' not in t or 'task' not in t:
        bad.append('skills-pi/mmw-implement 缺 worker agent 或 task 字段合同')
    else:
        ok += 1
    if 'mmw dispatch' in t:
        bad.append('skills-pi/mmw-implement 不得含 mmw dispatch')
    if '[[mmw-launch:' in t:
        bad.append('skills-pi 仍残留 launch 占位符')
else:
    bad.append('缺少 skills-pi/mmw-implement/SKILL.md（先 mmw skills materialize --host pi）')

if cc_impl.is_file():
    t = cc_impl.read_text()
    if 'mmw dispatch' not in t or '--task' not in t or 'worker' not in t:
        bad.append('skills-claude-code/mmw-implement 缺 dispatch worker --task 合同')
    else:
        ok += 1
    if '[[mmw-launch:' in t:
        bad.append('skills-claude-code 仍残留 launch 占位符')
else:
    bad.append('缺少 skills-claude-code/mmw-implement/SKILL.md')

if codex_impl.is_file():
    t = codex_impl.read_text()
    if '`create_thread`' not in t or '`wait_threads`' not in t or 'gpt-5.6-sol' not in t:
        bad.append('Codex mmw-implement 缺后台 Worktree 任务调用合同')
    else:
        ok += 1
    if 'mmw dispatch' in t or 'codex exec' in t or '[[mmw-launch:' in t:
        bad.append('Codex mmw-implement 仍残留旧派发合同')
else:
    bad.append('缺少 skills-codex/mmw-implement/SKILL.md')

plugin = cli.parent / '.claude-plugin' / 'plugin.json'
if plugin.is_file():
    pj = plugin.read_text()
    if './skills-claude-code/mmw-implement' in pj:
        ok += 1
    else:
        bad.append('Claude plugin.json 未指向 skills-claude-code/mmw-implement')
    if 'mmw-dispatching-agents' in pj:
        bad.append('Claude plugin.json 仍列出 mmw-dispatching-agents')
    if './skills/mmw-' in pj:
        bad.append('Claude plugin.json 仍直接指向 skills/ 源（应指向 skills-claude-code）')

pkg = cli.parent / 'package.json'
if pkg.is_file():
    pt = pkg.read_text()
    if './skills-pi' in pt:
        ok += 1
    else:
        bad.append('Pi package.json 未指向 ./skills-pi')

for rel, needle in [
    ('skills/mmw-implement/SKILL.md', '[[mmw-launch:worker:worktree]]'),
    ('skills/mmw-to-plan/SKILL.md', '[[mmw-launch:planner:worktree]]'),
    ('skills/mmw-research/SKILL.md', '[[mmw-launch:investigator:none]]'),
    ('skills/mmw-review/SKILL.md', '[[mmw-launch-group:reviewers:none]]'),
]:
    fp = cli.parent / rel
    if not fp.is_file():
        bad.append(f'缺少 {rel}')
    elif needle not in fp.read_text():
        bad.append(f'{rel} 缺占位符 {needle}')
    else:
        ok += 1

for b in bad:
    print(f"  失败  {b}")
print()
print(f"过 {ok}，失败 {len(bad)}")
sys.exit(1 if bad else 0)
PY
