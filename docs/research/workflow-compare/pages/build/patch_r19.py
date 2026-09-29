# The naming table R19-naming-table.md (§4, §8) and R18 §17 D10, applied to the extracted data after patch_d17.py.
# Two kinds of change, as R19 §8 counts them:
#   PLANNED: 26 names R18 planned and no file in the repository carries yet ("新" in R19 §4). They are replaced
#            everywhere, since nothing on the page describes them as they are today.
#   EXISTING: 18 names that exist today (8 reference files, 7 dispatch.sh subcommands, 3 flags). They are replaced
#            only where the page describes the upgraded state; where it describes today (the "now" tree, migration
#            sources, today's line citations, anything at B0 before the move) they stay.
# Every record whose EXISTING name changes carries "R19 §4.x" in its source.
import re

S = 'R19 §4'

# Order matters: longer forms first.
PLANNED = [
    (r'(?<![\w-])ticket\.py (<n>) --check(?![\w-])', r'ticket_state.py \1 --run-and-record-criteria'),
    (r'(?<![\w-])ticket\.py', 'ticket_state.py'),
    (r'anchors\.py', 'locations.py'),
    (r'(?<![\w-])mmw-hook', 'hook-launcher'),
    (r'shared-experience', 'memory-records'),
    (r'slots\.md', 'pstack-names.md'),
    (r'orchestrator-events', 'orchestrator-wakes'),
    (r'(?<![\w-])writing-code\.md', 'code-writing-rules.md'),
    (r'tracker-additions\.md', 'issue-tracker-pipeline-sections.md'),
    (r'review-axes/\{standards,spec,tests,ui\}\.md', '{standards,spec,tests,ui}-reviewer.md'),
    (r'review-axes/(standards|spec|tests|ui)\.md', r'\1-reviewer.md'),
    (r'review-axes/<axis>\.md', '<axis>-reviewer.md'),
    (r'review-axes/（四个 axis）', '<axis>-reviewer.md（四个 axis）'),
    (r'references/review-axes/', 'references/<axis>-reviewer.md'),
    (r'(?<![\w.-])ps/', 'pstack/'),
    (r'pstack\.map', 'pstack-rewrites.tsv'),
    (r'\+model(?![\w-])', '+model-invoked'),
    (r'\.mmw/skills/', '.mmw/skill-copies/'),
    (r'self-picked-worker', 'adopting-worker'),
    (r'(?<![\w-])ticket-orchestrator', 'one-ticket-orchestrator'),
    (r'define-a-change', 'write-a-spec-and-tickets'),
    (r'Define a change', 'Write a spec and tickets'),
    (r'design-an-interface', 'design-a-ui'),
    (r'Design an interface', 'Design a UI'),
    (r'direct-change', 'make-a-small-change'),
    (r'Direct change', 'Make a small change'),
    (r'run-one-ticket', 'land-one-ticket'),
    (r'Run one ticket', 'Land one ticket'),
    (r'After the closeout, picked up yourself', 'After the closeout of an adopted ticket'),
    (r'Picked up yourself', 'Adopted ticket'),
    (r'the-tracker-is-the-state', 'resume-from-durable-state'),
    (r'(?<![\w-])woken-not-polled', 'agents-are-woken-not-polled'),
    (r'route-faults-dont-bypass', 'report-faults-through-the-pipeline'),
    (r'no-secrets-in-artifacts', 'no-secrets-or-personal-data-in-artifacts'),
    (r'tests/wiring', 'tests/skill-text'),
    (r'kind: adopt(?![\w-])', 'kind: adopted-ticket'),
    (r'adopt → adopt(?![\w-])', 'adopt → adopted-ticket'),
]
_PLANNED = [(re.compile(a), b) for a, b in PLANNED]


def rename_planned(s):
    for rx, new in _PLANNED:
        s = rx.sub(new, s)
    return s


def _walk(o):
    if isinstance(o, dict):
        items = [(rename_planned(k), _walk(v)) for k, v in o.items()]
        o.clear()
        o.update(items)
        return o
    if isinstance(o, list):
        for i, v in enumerate(o):
            o[i] = _walk(v)
        return o
    if isinstance(o, str):
        return rename_planned(o)
    return o


def _at(data, path):
    o = data
    for key, idx in re.findall(r'\.([^.\[]+)|\[(\d+)\]', path):
        o = o[int(idx)] if idx else o[key]
    return o


def _rep(data, path, key, old, new, sec):
    """Replace old with new in one field; fail loudly if the text is not there, so a changed extraction is noticed."""
    d = _at(data, path)
    v = d[key]
    if isinstance(v, list):
        hit = [i for i, x in enumerate(v) if old in x]
        if not hit:
            raise KeyError((path, key, old))
        for i in hit:
            v[i] = v[i].replace(old, new)
    else:
        if old not in v:
            raise KeyError((path, key, old))
        d[key] = v.replace(old, new)
    if 'src' in d and isinstance(d['src'], str) and 'R19' not in d['src']:
        d['src'] += '；R19 ' + sec


# EXISTING names, where the page describes the upgraded state: (path, field, old, new, R19 section)
AFTER = [
    # dispatch.sh subcommands (R19 §4.7)
    ('.arch.fig1.entries[0]', 'note', 'dispatch.sh open、open-ticket 打印', 'dispatch.sh open-night、open-ticket-watch 打印', '§4.7'),
    ('.arch.fig1.roles[3]', 'started_by', 'dispatch.sh open <spec>', 'dispatch.sh open-night <spec>', '§4.7'),
    ('.arch.fig1.roles[4]', 'started_by', 'dispatch.sh open-ticket <n>', 'dispatch.sh open-ticket-watch <n>', '§4.7'),
    ('.arch.fig1.roles_notes[1]', 'text', 'open → night，open-ticket → ticket', 'open-night → night，open-ticket-watch → ticket', '§4.7'),
    ('.arch.fig1.edges[128]', 'label', 'check、open、advance、status、findings、route、memory-list、reverify、summary、where',
     'check、open-night、advance、status、findings、resolve-child、prepare-memory-decisions、reverify、close-night、where', '§4.7'),
    ('.arch.fig1.edges[131]', 'label', 'route、finish', 'resolve-child、finish', '§4.7'),
    ('.arch.fig1.edges[132]', 'label', 'open-ticket、start worker、land', 'open-ticket-watch、start worker、land', '§4.7'),
    ('.pb.wake_line_shapes[3]', 'sender', 'dispatch.sh open', 'dispatch.sh open-night', '§4.7'),
    ('.pb.wake_line_shapes[3]', 'note', 'open、open-ticket 打印', 'open-night、open-ticket-watch 打印', '§4.7'),
    ('.pb.night_sequence[2]', 'text', 'dispatch.sh open <spec>', 'dispatch.sh open-night <spec>', '§4.7'),
    ('.pb.night_sequence[3]', 'note', '由 open 写入', '由 open-night 写入', '§4.7'),
    ('.pb.night_sequence[47]', 'text', 'dispatch.sh route', 'dispatch.sh resolve-child', '§4.7'),
    ('.pb.night_sequence[47]', 'certainty_note', 'findings、route', 'findings、resolve-child', '§4.7'),
    ('.pb.night_sequence[48]', 'text', 'dispatch.sh memory-list <spec>', 'dispatch.sh prepare-memory-decisions <spec>', '§4.7'),
    ('.pb.night_sequence[50]', 'text', 'dispatch.sh summary <spec>', 'dispatch.sh close-night <spec>', '§4.7'),
    ('.pb.night_sequence[56]', 'note', 'dispatch.sh route', 'dispatch.sh resolve-child', '§4.7'),
    ('.pb.where.table[14]', 'out', '（memory-list 可重跑）', '（prepare-memory-decisions 可重跑）', '§4.7'),
    ('.pr.fig8_reentry.where.table[14]', 'output', '（memory-list 可重跑）', '（prepare-memory-decisions 可重跑）', '§4.7'),
    ('.pb.roles[3]', 'started_by', 'dispatch.sh open <spec>', 'dispatch.sh open-night <spec>', '§4.7'),
    ('.pb.roles[4]', 'started_by', 'dispatch.sh open-ticket <n>', 'dispatch.sh open-ticket-watch <n>', '§4.7'),
    ('.pr.roles.items[3]', 'started_by', 'dispatch.sh open <spec>', 'dispatch.sh open-night <spec>', '§4.7'),
    ('.pr.roles.items[3]', 'discipline_from', 'open 打印的指针', 'open-night 打印的指针', '§4.7'),
    ('.pr.roles.items[4]', 'started_by', 'dispatch.sh open-ticket <n>', 'dispatch.sh open-ticket-watch <n>', '§4.7'),
    ('.pr.roles.recipient_rule', 'items', 'open → night，open-ticket → ticket', 'open-night → night，open-ticket-watch → ticket', '§4.7'),
    ('.pb.playbooks[2].rule_clusters[2]', 'text', 'dispatch.sh route', 'dispatch.sh resolve-child', '§4.7'),
    ('.pb.playbooks[11].steps[0].components[1]', 'name', 'dispatch.sh open <spec>', 'dispatch.sh open-night <spec>', '§4.7'),
    ('.pb.playbooks[11].steps[4].components[1]', 'name', 'dispatch.sh route', 'dispatch.sh resolve-child', '§4.7'),
    ('.pb.playbooks[11].steps[5].components[0]', 'name', 'dispatch.sh memory-list <spec>', 'dispatch.sh prepare-memory-decisions <spec>', '§4.7'),
    ('.pb.playbooks[11].steps[6].components[1]', 'name', 'dispatch.sh summary <spec>', 'dispatch.sh close-night <spec>', '§4.7'),
    ('.pb.playbooks[12].steps[1].components[3]', 'name', 'dispatch.sh route', 'dispatch.sh resolve-child', '§4.7'),
    ('.pb.playbooks[12].steps[1]', 'text', 'dispatch.sh route', 'dispatch.sh resolve-child', '§4.7'),
    ('.pb.playbooks[13].steps[0].components[0]', 'name', 'dispatch.sh open-ticket <n>', 'dispatch.sh open-ticket-watch <n>', '§4.7'),
    ('.pr.fig7_arrival.columns[7]', 'detail', 'dispatch.sh open、open-ticket 打印', 'dispatch.sh open-night、open-ticket-watch 打印', '§4.7'),
    ('.pr.fig7_arrival.rows[7].cells.open_pointer', 'note', 'dispatch.sh open、open-ticket 打印', 'dispatch.sh open-night、open-ticket-watch 打印', '§4.7'),
    ('.pr.fig7_arrival.launch_prompts[6]', 'text', 'dispatch.sh open 打印的行末尾接 · mmw run-a-night#Handle each wake（open-ticket 为',
     'dispatch.sh open-night 打印的行末尾接 · mmw run-a-night#Handle each wake（open-ticket-watch 为', '§4.7'),
    ('.pr.fig9_principles.priority_ladder', 'attended_just_do', '（advance、route、resume）', '（advance、resolve-child、resume）', '§4.7'),
    ('.ops.import_pipeline.pr_mapping[1]', 'mmw', '`summary`', '`close-night`', '§4.7'),
    # flags that move to ticket_state.py (R19 §4.8)
    ('.arch.fig1.script_groups[0].items[13]', 'note', '--preflight、--check、--decisions、--review、--touched、--draft、--closeout、--sub-issue',
     '--claim、--run-and-record-criteria、--decisions、--review、--touched、--closing-draft、--closeout、--open-child', '§4.8'),
    ('.arch.fig1.edges[134]', 'label', '--preflight、--check、--decisions、--touched、--draft、--closeout、--sub-issue',
     '--claim、--run-and-record-criteria、--decisions、--touched、--closing-draft、--closeout、--open-child', '§4.8'),
    ('.pb.night_sequence[11]', 'text', '--preflight', '--claim', '§4.8'),
    ('.pb.night_sequence[32]', 'text', '--sub-issue', '--open-child', '§4.8'),
    ('.pb.night_sequence[38]', 'text', '--draft', '--closing-draft', '§4.8'),
    ('.pb.work_a_ticket_matrix.rows[0]', 'text', '--preflight', '--claim', '§4.8'),
    ('.pb.work_a_ticket_matrix.rows[0]', 'scripts', '--preflight', '--claim', '§4.8'),
    ('.pb.work_a_ticket_matrix.rows[5]', 'text', '--sub-issue', '--open-child', '§4.8'),
    ('.pb.work_a_ticket_matrix.rows[5]', 'scripts', '--sub-issue', '--open-child', '§4.8'),
    ('.pb.work_a_ticket_matrix.rows[9]', 'text', '--draft', '--closing-draft', '§4.8'),
    ('.pb.work_a_ticket_matrix.rows[9]', 'scripts', '--draft', '--closing-draft', '§4.8'),
    # reference files (R19 §4.5)
    ('.arch.fig1.capability_groups[0].items[5]', 'note', '接收 writing-interface-code.md', '接收 writing-ui-code.md', '§4.5'),
    ('.arch.fig1.capability_groups[0].items[10]', 'note', 'key.md、new-product.md、driving.md', 'release-manifest.md、new-product.md、release-loop.md', '§4.5'),
    ('.arch.fig1.reference_groups[0].items[6]', 'id', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.arch.fig1.reference_groups[0].items[6]', 'label', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.arch.fig1.edges[125]', 'to', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.arch.fig1.reference_groups[2].items[0]', 'id', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.arch.fig1.reference_groups[2].items[0]', 'label', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.arch.fig1.edges[123]', 'to', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.arch.fig3.after.mmw-v2.children[4].children[0].children[6].children[6]', 'name', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.arch.fig3.after.mmw-v2.children[4].children[5]', 'note', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.arch.fig3.moves[14]', 'to', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.mig.layers[6]', 'parts', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.mig.layers[6]', 'parts', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.mig.flows[41]', 'to_part', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.mig.flows[74]', 'to_part', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.mig.skills[1]', 'after', '（sub-issues.md 第', '（今天 sub-issues.md 第', '§4.5'),
    ('.mig.skills[1]', 'after', '行）。跑判据', '行，改名 child-issues.md）。跑判据', '§4.5'),
    ('.mig.skills[2]', 'after', '接收 writing-interface-code.md', '接收 writing-ui-code.md', '§4.5'),
    ('.mig.skills[7]', 'after', 'key.md、new-product.md、driving.md', 'release-manifest.md、new-product.md、release-loop.md', '§4.5'),
    ('.pb.playbooks[1].steps[1].components[1]', 'name', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
    ('.pb.playbooks[2].steps[0].components[0]', 'note', 'edit-pages.md', 'set-up-and-sign-off.md', '§4.5'),
    ('.pb.work_a_ticket_matrix.rows[1]', 'text', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.pb.work_a_ticket_matrix.rows[1]', 'skills', 'writing-interface-code.md', 'writing-ui-code.md', '§4.5'),
    ('.pb.five_jumps_today.jumps[3]', 'goes_to', '搬进 ui-acceptance 自己的 references/', '搬进 ui-acceptance 自己的 references/，改名 writing-ui-code.md', '§4.5'),
    ('.ops.batches.list[1].items[3]', 'text', 'interface-and-remake.md', 'ui-and-remake-tickets.md', '§4.5'),
]

# The 18 existing names R19 §8 changes, for the table under the decision cards.
EXISTING = [
    ('reference', 'design-pages/references/edit-pages.md', 'set-up-and-sign-off.md', 'B1'),
    ('reference', 'exe-release/references/driving.md', 'release-loop.md', 'B1'),
    ('reference', 'exe-release/references/key.md', 'release-manifest.md', 'B1'),
    ('reference', 'verify-ticket/references/sub-issues.md', 'child-issues.md', 'B2'),
    ('reference', 'to-tickets/references/cutting-interface-tickets.md', 'screen-contract-tickets.md', 'B1'),
    ('reference', 'to-spec/references/several-specs.md', 'spec-division.md', 'B1'),
    ('reference', 'wayfinder/references/interface-and-remake.md', 'mmw/references/ui-and-remake-tickets.md', 'B1'),
    ('reference', 'implement/references/writing-interface-code.md', 'ui-acceptance/references/writing-ui-code.md', 'B2'),
    ('dispatch.sh 子命令', 'open <spec>', 'open-night <spec>', 'B2'),
    ('dispatch.sh 子命令', 'open-ticket <n>', 'open-ticket-watch <n>', 'B2'),
    ('dispatch.sh 子命令', 'summary <spec>', 'close-night <spec>', 'B2'),
    ('dispatch.sh 子命令', 'wait <n> worker|reviewer', 'result <n> worker|reviewer', 'B2'),
    ('dispatch.sh 子命令', 'integrated <n>', 'landed-since <n>', 'B2'),
    ('dispatch.sh 子命令', 'memory-list <spec>', 'prepare-memory-decisions <spec>', 'B2'),
    ('dispatch.sh 子命令', 'route <ticket> <child> …', 'resolve-child <ticket> <child> …', 'B2'),
    ('开关（verify-ticket.py → ticket_state.py）', '--preflight', '--claim', 'B2'),
    ('开关（verify-ticket.py → ticket_state.py）', '--draft', '--closing-draft', 'B2'),
    ('开关（verify-ticket.py → ticket_state.py）', '--sub-issue', '--open-child', 'B2'),
]
RENAMED_VERBS = {'open': 'open-night', 'open-ticket': 'open-ticket-watch', 'summary': 'close-night', 'wait': 'result',
                 'integrated': 'landed-since', 'memory-list': 'prepare-memory-decisions', 'route': 'resolve-child'}


def patch_r19(data):
    _walk(data)
    for path, key, old, new, sec in AFTER:
        _rep(data, path, key, old, new, sec)
    A, PB, O = data['arch'], data['pb'], data['ops']

    R = next(r for r in data['pr']['roles']['items'] if r.get('watch_kind') == 'adopt')
    R['watch_kind'] = 'adopted-ticket'  # R19 §4.9: the planned watch kind value
    for s in PB['night_sequence']:
        if s.get('phase') == 'reverify 与 summary':
            s['phase'] = 'reverify 与 close-night'
    for slug, zh in (('write-a-spec-and-tickets', '写 spec 与切票'), ('make-a-small-change', '小改动'), ('land-one-ticket', '落地一张票')):
        next(p for p in PB['playbooks'] if p['slug'] == slug)['name_zh'] = zh

    V = A['fig1']['dispatch_verbs']
    V['existing'] = [v for v in V['existing'] if v not in RENAMED_VERBS]
    V['changed'] += [{'verb': old + ' → ' + new, 'note': '改名，B2 随 dispatch.sh 搬进 mode 时改；旧名留一版，只打印一行拒绝并点名新命令',
                      'src': 'R19 §4.7'} for old, new in RENAMED_VERBS.items()]

    A['head']['subtitle'] = 'multi-model-workflow · 架构升级 · 定稿 R18（含 #591 与 §17 的十项决定）· 名字按 R19 改名表'

    DD = O['decided']
    DD['boundary'] = {'text': ('下面十项写在 R18 §17，优先于 R18 前文各节：D1 至 D9 由你在 2026-09-29 定下，D10 由 Claude 按你当夜的授权代定，'
                               '待你复核。本页各图与表已按它们改写，名字按 R19 改名表。「本页改了什么」一行写每一项落在页面的哪些地方。'),
                      'src': 'R18 §17 首句与 D10；R19 §8'}
    d9 = next(i for i in DD['items'] if i['id'] == 'D9')
    d9['page'] = ('本页名字已按 R19 改名表：R18 预定、还没建的 26 个名字在各图各表直接写新名字；仓库里已有、要改的 18 个名字只在描述升级后的地方写新名字，'
                  '描述今天的地方（今天的目录树、图 2 的来源一侧、今天文件的行号、B0 时的状态）仍写今天的名字，对照见下面「改名表（R19）」；'
                  '图 12 B0 加了两道文字检查')
    d9['src'] = 'R18 §17 D9；R19 §8；R21 §0'
    DD['items'].append({
        'id': 'D10', 'q': 'mode 技能的名字（Claude 代定，待你复核）',
        'decision': '`mmw`。你在 2026-09-29 夜间授权 Claude 完成剩余决定，这一项由 Claude 代定，等你复核',
        'effect': ('目录 `skills/mmw/`，测试套件 `tests/mmw`，唤醒行的指针前缀 `mmw <slug>#<Step title>`，你输入 `/mmw`。'
                   '放弃的备选是 `mmw-mode`；复核时若改用它，要改的就是这三处，命令随之变成 `/mmw-mode`。'),
        'page': '本页一直写 mode `mmw`，名字不用改；本节加了这张卡片与下面的「改名表（R19）」',
        'src': 'R18 §17 D10；R19「用户过目」'})

    O['renames'] = {
        'title': '改名表（R19）',
        'intro': ('R19 §8 共改 44 个名字。下表是仓库里已有、要改的 18 个：在搬家的同一张票里改，旧的子命令与开关留一版，只打印一行拒绝并点名新名字。'
                  '另 26 个是 R18 预定、还没建的名字（如 `locations.py`、`ticket_state.py`、`hook-launcher`、`pstack-names.md`、`memory-records`、'
                  '**Write a spec and tickets**），本页各处已直接写新名字。'),
        'rows': [{'kind': k, 'old': o, 'new': n, 'batch': b, 'src': 'R19 §4.5' if k == 'reference' else ('R19 §4.7' if k.startswith('dispatch') else 'R19 §4.8')}
                 for k, o, n, b in EXISTING],
        'src': 'R19-naming-table.md §4、§7、§8',
    }

    b0 = next(b for b in O['batches']['list'] if b['id'] == 'B0')
    b0['items'].append({'kind': 'script',
                        'text': ('文字检查：`check_verbatim_moves.py`（逐字搬运检查）、`check_component_structure.py`（结构 lint）、共用套件 `tests/skill-text`；'
                                 '分五张票（共用检查入口与套件、逐字比较、票上的清单与未动文字、切票时的清单检查、结构 lint）'),
                        'src': 'R21 §0 第 1、9 条；R18 §17 D9'})
    return data
