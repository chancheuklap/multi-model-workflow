# The owner's decisions of 2026-09-29 (R18 §17 D1-D9), applied to the extracted data after patch.py.
# R18 §17 says these decisions take precedence over the earlier sections; every record this file
# rewrites carries "§17 D<n>" in its source so a reader can see which decision changed it.

S = 'R18 §17'


def _sub(d, key, old, new):
    v = d.get(key)
    if isinstance(v, str) and old in v:
        d[key] = v.replace(old, new)
        return True
    return False


def _src(d, add, key='src'):
    v = d.get(key)
    d[key] = (v + '；' + add) if v else add


def _rm(lst, pred):
    lst[:] = [x for x in lst if not pred(x)]


def _one(lst, **kw):
    for x in lst:
        if all(x.get(k) == v for k, v in kw.items()):
            return x
    raise KeyError(kw)


PR_PB = ('opening-a-pr', 'babysit', 'shipping')
D2_WHY = 'D2：不用 PR 交付；MMW 现行交付（closeout → advance 合进 project branch → 你验收 → finish）已覆盖 shipping.md 九步的意图（R18 §8.4 对照）'
HOSTS3 = 'Claude Code、Codex、Grok'


def patch_d17(data):
    A, M, PB, PR, O = data['arch'], data['mig'], data['pb'], data['pr'], data['ops']
    arch(A)
    mig(M)
    playbooks(PB)
    principles(PR)
    ops(O)
    return data


# ---------------------------------------------------------------- arch
def arch(A):
    A['head']['subtitle'] = 'multi-model-workflow · 架构升级 · 定稿 R18（含 #591 与 §17 的九项决定）'
    A['about']['batch_values'] = 'B0–B5 = R18 §10 的六批；核心批次只到 B0–B2，B3–B5 按需：每次由你点名要导入的组件（R18 §17 D6、D7）。'
    n = _one(A['head']['numbers'], id='n-playbooks')
    n['value'] = '0 → 16 / 29'
    n['detail'] = ('第 2 批后 16 份（全是 MMW 自写），另有本仓库私有 3 份；pstack 的 13 份都按需：'
                   'session-pickup、pause-safely（D6 从 B1 推迟）、B3 6 份、B4 1 份、B5 4 份，全部导入后 29 份')
    n['src'] = 'R18 §0.1、§3、§17 D2、D6（16 与 29 是本页按 §17 重算）'
    n = _one(A['head']['numbers'], id='n-principles')
    n['detail'] = ('第 2 批后 26 条（MMW 12、pstack 14）；D6 只导入 MMW 点名的 pstack 原则，'
                   'R18 §5.3 B1 的 14 行「MMW 调用方」一列都非空，所以仍是 14 条；全部按需导入后 35 条')
    n['src'] = 'R18 §0.1、§5.3、§17 D6（14 条是本页按 §5.3 表逐行核对）'

    C = {c['kind']: c for c in A['components']}
    C['mode']['reached_by'] = '脚本起的会话：启动提示词点名；人起的会话：mode-hook 提醒、mode description、/mmw（D4：不往消费仓库 AGENTS.md 加行）'
    _src(C['mode'], '§17 D4')
    C['playbook']['count_b2'] = '16 份（MMW 自写）+ 本仓库私有 3 份'
    C['playbook']['count_all'] = '29 份（pstack 按需再进 13 份）+ 私有 3 份'
    _src(C['playbook'], '§17 D2、D6')
    C['capability']['count_all'] = '52 个（pstack 17 个，全部按需）'
    _src(C['capability'], '§17 D6、D7')
    C['reference']['count_all'] = '加按需导入的 reference（如 ps/agents/comment-sicko.md）'
    _src(C['reference'], '§17 D2')
    C['script']['count_all'] = '同左，加按需的 ps/worktree-audit.sh'
    _src(C['script'], '§17 D2')
    C['config']['count_all'] = '同左；面板角色随第一个需要它的组件按需进 models.json'
    _src(C['config'], '§17 D7')

    F = A['fig1']
    F['constraints'][0]['text'] = ('宿主不换：现役宿主是 ' + HOSTS3 + '，runner 是 Orca（R18 §17 D3）；'
                                   '这些宿主没有 pstack 依赖的 mode: true / reminder 常驻机制')
    hum = _one(F['entries'], id='entry:human')
    _rm(hum['paths'], lambda p: p['label'] == 'AGENTS.md 一行')
    _src(hum, '§17 D4')
    for s in F['mode']['sections']:
        if s['id'] == 'mode#Autonomy':
            _sub(s, 'note', '；产品事项清单抄一次', '；产品事项只点名 shared.md 规则 1，不抄清单（D3）')
            _src(s, '§17 D3')
        if s['id'] == 'mode#Imported-triggers':
            s['note'] = 'pstack mode 触发行原文：B3 11 行，按需（D6）'
            s['batch'] = 'B3'
            _src(s, '§17 D2、D6')
    roles = {r['role']: r for r in F['roles']}
    roles['worker']['note'] = '现役宿主：junior-worker 为 Grok，senior-worker 为 Codex（D3）'
    roles['reviewer']['note'] = '一次性会话；现役宿主 Claude Code（D3）'
    roles['advisor']['note'] = '现役宿主 Claude Code（D3）'
    roles['researcher']['note'] += '；B0 发布步骤里给本机 models.json 加这一行（D1）'
    for r in ('worker', 'reviewer', 'advisor', 'researcher'):
        _src(roles[r], '§17 D1' if r == 'researcher' else '§17 D3')

    G = {g['id']: g for g in F['playbook_groups']}
    g = G['pbg:ps-b1']
    g.update(label='pstack · 2 份（D6 从 B1 推迟）', batch='按需', on_demand=True)
    _src(g, '§17 D6', 'src')
    for it in g['items']:
        it['note'] = ((it.get('note') or '') + '；D6 从 B1 推迟到按需').lstrip('；')
    g = G['pbg:ps-b4']
    g.update(label='pstack · 工作树清理 · 1 份', on_demand=True)
    _rm(g['items'], lambda i: i['slug'] in PR_PB)
    g['src'] = (g.get('src') or 'R18 §10 B4') + '；§17 D2'
    for it in G['pbg:day']['items']:
        if it['slug'] == 'deliver-a-change':
            it['note'] = '按 .mmw/target.json 的 delivery 交出改动：commit 或私有 playbook；别名 Opening a PR（D2）'
    F['playbook_counts'] = {'b2': '16 = 白天 11 + 夜间 5；另私有 3',
                            'all': '按需再进 13 份：session-pickup、pause-safely、B3 6、B4 1、B5 4',
                            'src': 'R18 §3、§13.1、§17 D2、D6'}

    for g in F['capability_groups']:
        for it in g['items']:
            if _sub(it, 'note', '→ dispatch.sh panel', '→ dispatch.sh panel（随它按需加入，D7）') or \
               _sub(it, 'note', '→ panel', '→ panel（随它按需加入，D7）'):
                pass
    SG = {g['id']: g for g in F['script_groups']}
    _rm(SG['scg:mmw-ps']['items'], lambda i: i['label'] != 'worktree-audit.sh')
    SG['scg:mmw-ps']['src'] = (SG['scg:mmw-ps'].get('src') or '') + '；§17 D2'
    RG = {g['id']: g for g in F['reference_groups']}
    _rm(RG['refg:mode-ps']['items'], lambda i: 'bugbot' in i['label'])
    for it in RG['refg:mode-ps']['items']:
        it['batch'] = 'B3'
    V = F['dispatch_verbs']['new']
    for v in V:
        if v['verb'].startswith('panel'):
            v['batch'] = '按需'
            v['note'] += '；随第一个需要它的组件加入（D7）'
            _src(v, '§17 D7')
    F['new_mechanisms']['items'] = [x if x != 'panel' else 'panel（按需，D7）' for x in F['new_mechanisms']['items']]
    for s in F['sources']:
        _sub(s, 'note', '、副本过期、bun', '、副本过期')
    ST = {s['id']: s for s in F['state']}
    ST['cfg:models.json']['note'] = '角色 → host、model、effort；runner；面板角色随第一个需要它的组件按需加入（D7）；B0 发布步骤里加 researcher 一行（D1）'
    _src(ST['cfg:models.json'], '§17 D1、D7')
    ST['cfg:target.json']['note'] = '新增可选键 delivery（commit | playbook:<slug>，缺省 commit；没有 pr，D2）与 control（界面 → 技能）'
    _src(ST['cfg:target.json'], '§17 D2')
    ST['st:statedir']['note'] = 'watches.json（新增 kind）、relay.lock、watchdog.lock；新增 prompts/；panels/ 随 panel 按需（D7）'
    ST['cfg:boards.json']['note'] = '任务板的端口登记；任务板只经 anchors.py、dispatch.sh where、roles.json 读 MMW（D8）'
    _src(ST['cfg:boards.json'], '§17 D8')

    E = F['edges']
    _rm(E, lambda e: e.get('to') in ('pb:opening-a-pr', 'pb:babysit', 'pb:shipping'))
    for e in E:
        if e.get('to') == 'pbg:ps-b4' and e.get('from') == 'mode#Playbooks':
            e['label'] = 'B4 按需加 1 行（worktree-cleanup）'
            _src(e, '§17 D2')
        if e.get('to') == 'pbg:ps-b1' and e.get('from') == 'mode#Playbooks':
            e['label'] = '路由表（按需导入后加行）'
            e['on_demand'] = True
            _src(e, '§17 D6')
        if e.get('to') == 'ref:slots.md' and e.get('label') == 'Cursor / pstack 专有名字':
            e['label'] = 'pstack 专有名字'
        if e.get('to') == 'pb:pause-safely':
            e['label'] += '（pause-safely 按需，D6）'

    # figure 3
    F3 = A['fig3']['after']
    mv = F3['mmw-v2']
    _sub(mv['children'][1], 'note', '、开着的 watch、bun', '、开着的 watch')
    mmw = mv['children'][4]['children'][0]
    for c in mmw['children']:
        if c['name'] == 'playbooks/':
            c['note'] = c['note'].replace('18 份：', '16 份：').replace(' session-pickup(ps) pause-safely(ps)', '').replace('；B3–B5 再进 14 份', '；按需再进 13 份（含从 B1 推迟的 session-pickup、pause-safely，D6）')
            _src(c, '§17 D6')
        if c['name'] == 'references/':
            for ch in c.get('children', []):
                if ch['name'] == 'ps/':
                    ch['batch'] = 'B3'
        if c['name'] == 'scripts/':
            for ch in c.get('children', []):
                if ch['name'] == 'ps/':
                    ch['note'] = '导入的 pstack 脚本（按需，worktree-audit.sh）'
    _sub(F3['repo_root']['children'][0], 'note', '；## Package Manager 加 bun 一行', '')
    for c in F3['consumer_repo']['children']:
        if c['name'] == 'AGENTS.md':
            c['note'] = '不加 mmw 一行（D4）；人起的会话用 /mmw 或 mode description'
            c['origin'] = 'unchanged'
            _src(c, '§17 D4')
        if c['name'] == '.mmw/target.json':
            c['note'] = '新增可选键 delivery（commit | playbook:<slug>，缺省 commit；D2）与 control（界面 → 技能）'
            _src(c, '§17 D2')
    for c in F3['home_mmw']['children']:
        if c['name'] == 'models.json':
            c['note'] = '角色 → host、model、effort；runner；面板角色按需（D7）；B0 发布步骤里加 researcher 一行（D1）'
        if c['name'].startswith('state/'):
            c['note'] = 'watches.json（新增 kind 字段）、relay.lock、watchdog.lock；新增 prompts/；panels/ 随 panel 按需（D7）'
            for ch in c.get('children', []):
                if ch['name'].startswith('panels/'):
                    ch['batch'] = '按需'
                    ch['note'] = '面板成员的答案（panel 按需，D7）'
    for g in F['script_groups']:
        for it in g['items']:
            _sub(it, 'note', 'bash，不需要 bun；', 'bash；')
    # D8: the board and the interfaces it reads
    F['board'] = {
        'label': 'mmw-v2/board/ 任务板',
        'reads': [
            {'iface': 'anchors.py', 'what': '跨目录的路径（events.py、issue_tree.py、ghlist.py、models.py、statedir.py 的位置）', 'today': 'board_data.py、codeversion.py、settings_api.py、supervisor.py 写死 skills/dispatch/scripts 与 skills/verify-ticket/scripts（R18 §7.6 第 998 行一格；本轮读 board/AGENTS.md 与四个文件核实）'},
            {'iface': 'dispatch.sh where <n>', 'what': '一张票现在在 playbook 的哪一步：AT / BETWEEN / FRESH / UNKNOWN', 'today': '没有；任务板今天只从 GitHub 读票与事件'},
            {'iface': 'mmw/roles.json', 'what': '角色、每个角色读哪份 playbook、用 models.json 哪一行', 'today': '设置页的角色名单写在 page/local-config.mjs 的 agents 列表里（R18 §16 要在这里加 researcher）'},
            {'iface': 'models.py config show', 'what': '每个角色的 host、model、effort 与 runner（今天已有的读写路径）', 'today': 'settings_api.py 导入 models；B2 后模块位置改从 anchors.py 取'},
        ],
        'shows_later': ['每个角色与它的模型（roles.json + models.json）', '每张票当前在 playbook 的哪一步（dispatch.sh where）', '原则索引（mode ## Principles 与 mmw/principles/）', '导入登记（mmw/imports.tsv）'],
        'scope': '改路径随 B2 第 7.6 节的 board/ 四处一起做；新信息的显示不在本次范围，另开 spec',
        'src': 'R18 §17 D8、§7.2、§7.6',
    }


# ---------------------------------------------------------------- migration
def mig(M):
    for f in M['flows']:
        if f['id'] == 'f126':
            f['note'] = '留（S）；mode 只点名 shared.md 规则号，不抄产品事项清单（D3）'
            _src(f, '§17 D3')
    _rm(M['stays'], lambda s: s['what'] == 'mode ## Autonomy 抄一次产品事项清单')
    for l in M['layers']:
        if l['id'] == 'scripts':
            l['parts'] = [p if p != 'ps/（B4）' else 'ps/（B4，按需）' for p in l['parts']]


# ---------------------------------------------------------------- playbooks
def playbooks(PB):
    P = {p['slug']: p for p in PB['playbooks']}
    s2 = P['onboard-a-repository']['steps'][1]
    s2['text'] = '不写 mmw 那一行（D4）'
    _src(s2, '§17 D4')
    d = P['deliver-a-change']
    d['entry'] = '其他 playbook 的最后一步；别名 Opening a PR（D2）'
    d['task_type'] = '按本仓库收改动的方式交出一个完成的改动'
    st = d['steps'][0]
    st['text'] = ('在票的工作树里：交付就是 closeout，本 playbook 不适用。其余按 delivery：commit 或缺省 → 提交到当前分支并告诉用户；'
                  'playbook:<slug> → 该仓库私有 playbook <slug>（D2：没有 pr 这一取值）')
    _src(st, '§17 D2')
    _rm(d['steps'][1]['components'], lambda c: c['name'] == 'opening-a-pr')
    _src(d, '§17 D2')
    bf = P['bug-fix']
    if bf.get('b3_merge'):
        bf['b3_merge']['text'] += '；原文第 6 步「Run Opening a PR」经 slots.md 读作 Deliver a change（D2）'
    for slug in ('session-pickup', 'pause-safely'):
        p = P[slug]
        p['batch'] = '按需（D6）'
        p['origin'] = 'pstack 原文（按需导入）'
        p['entry'] = p['entry'].replace('路由', '路由（导入后加行）', 1)
        p['status'] = '按需：你点名时导入（D6 从 B1 推迟）'
        _src(p, '§17 D6')
    for p in PB['playbooks']:
        if p.get('status') == '按需：每批开工前你点头':
            p['status'] = '按需：你点名时导入（D6）'
    _rm(PB['playbooks'], lambda p: p['slug'] in PR_PB)
    for slug, name in (('opening-a-pr', 'Opening a PR'), ('babysit', 'Babysit'), ('shipping', 'Shipping')):
        PB['not_imported_playbooks'].append({'slug': slug, 'why': D2_WHY, 'src': 'R18 §17 D2、§8.4', 'd2': True})
    ia = P['import-a-component']['steps'][1]
    ia['text'] = ia['text'].replace('③依赖 PR 吗？是就只路由给 delivery: pr 的仓库', '③依赖 PR 吗？是就不导入（D2）') \
                           .replace('④依赖跨厂商面板吗？panel 在就用，否则在路由行写明降级', '④依赖跨厂商面板吗？是就随它一起加入 dispatch.sh panel（D7）')
    _src(ia, '§17 D2、D7（本页按这两条改写第 ③④ 问）')
    for g in PB['playbook_groups']:
        if g['id'] == 'pstack_b1':
            g.update(label='pstack 原文（按需，D6 从 B1 推迟）', batch='按需')
        if g['id'] == 'import':
            g['members'] = [m for m in g['members'] if m not in PR_PB]
            g['count'] = len(g['members'])
    PB['playbook_totals'] = {'after_B2': '16 份（MMW 自写）＋本仓私有 3 份',
                             'after_all': '29 份（pstack 按需再进 13 份）＋私有 3 份',
                             'src': 'R18 §0.1、§3、§17 D2、D6（本页重算）'}
    rn = PB['route_table_notes']
    rn['aliases'][0] = '**Opening a PR** means **Deliver a change**（D2：不导入 Opening a PR）'
    rn['rows_by_batch']['B4'] = '按需加 1 行（worktree-cleanup）'
    rn['rows_by_batch']['按需（D6）'] = 'session-pickup、pause-safely 导入时各加 1 行'
    rn['src'] += '；§17 D2、D6'
    H = PB['handoff_edges']
    _rm(H, lambda e: e['to'] in PR_PB)
    for e in H:
        if 'session-pickup' in (e['from'], e['to']) or 'pause-safely' in (e['from'], e['to']):
            e['batch'] = '按需'
            _src(e, '§17 D6')
    PB['missing'] = [s.replace('B3–B5 导入的 14 份', 'B3–B5 按需导入的 11 份').replace('opening-a-pr、babysit、shipping、', '')
                     for s in PB['missing']]


# ---------------------------------------------------------------- principles
def principles(PR):
    R = {r['role']: r for r in PR['roles']['items']}
    R['worker']['note'] = ((R['worker'].get('note') or '') + '；现役宿主：junior-worker 为 Grok，senior-worker 为 Codex（D3）').lstrip('；')
    R['reviewer']['note'] = ((R['reviewer'].get('note') or '') + '；现役宿主 Claude Code（D3）').lstrip('；')
    R['advisor']['note'] = ((R['advisor'].get('note') or '') + '；现役宿主 Claude Code（D3）').lstrip('；')
    R['researcher']['note'] = ((R['researcher'].get('note') or '') + '；B0 发布步骤里执行 `models.py config set researcher codex "gpt 6 sol" high`（D1）').lstrip('；')
    for r in ('worker', 'reviewer', 'advisor', 'researcher'):
        _src(R[r], '§17 D1' if r == 'researcher' else '§17 D3')

    F = PR['fig7_arrival']
    _rm(F['columns'], lambda c: c['id'] == 'agents_md')
    for r in F['rows']:
        r['cells'].pop('agents_md', None)
        for k, c in r['cells'].items():
            _sub(c, 'note', 'U-1 实测五个宿主', 'U-1 实测三个宿主（' + HOSTS3 + '，D3）')
    F['arrival_count']['after'] = '四条到达路径（R18 §2.3）：启动提示词；唤醒指针；hook；人起会话的 description、/mmw（D4 删去 AGENTS.md 一行）'
    _src(F['arrival_count'], '§17 D4')
    _rm(F['mode_hook_scope']['scope_rules'], lambda s: 'Cursor' in s)
    PR['about']['status_legend'] = '矩阵格子的状态：certain = ● 确定；probe = ◐ 待实测（带 U 编号）；partial = 部分宿主已观察到、其余待实测；空 = 这条路径不服务这类会话。'
    _rm(PR['gaps'], lambda g: g.startswith('人起会话的四条路径里，AGENTS.md 一行'))

    R8 = PR['fig8_reentry']
    for p in R8['probes']:
        _sub(p, 'q', '五个宿主', '三个宿主（' + HOSTS3 + '，D3）')
        if p['id'] == 'U-9':
            p['q'] += '（现役 runner 是 Orca，D3）'

    for k in R8['anchors_and_wiring']['check_wiring_classes']:
        _sub(k, 'checks', '（opening-a-pr.md 例外）', '')
    F9 = PR['fig9_principles']
    SM = F9['shared_md']
    SM['what'] = 'mmw-v2/prompt/shared.md 是用户写给所有项目的全局规则，经 install.sh 发给各宿主；现役宿主 ' + HOSTS3 + ' 都收到（D3）。MMW 不改写它（S）'
    SM['only_copy'] = 'mode 不复述 shared.md：## Autonomy 只点名规则 1 与它的适用时机（D3 删去为 Cursor 抄一次产品事项清单的一条）'
    SM.pop('cursor_decision', None)
    SM['src'] += '；§17 D3'
    for c in F9['citation_matrix']['columns']:
        if c['id'] in ('P17/P18', 'P17_18'):
            c['label'] = 'session-pickup / pause-safely（按需，D6）'
    for p in F9['mmw_principles'] + F9['pstack_principles']:
        if p.get('named_by'):
            p['named_by'] = [x + '（按需，D6）' if x in ('P17', 'P18') else x for x in p['named_by']]


# ---------------------------------------------------------------- ops
def ops(O):
    IP = O['import_pipeline']
    IP['decision'] = ('pstack 以 squash subtree 引入 mmw-v2/upstream-pstack/，原文不改；子树、import_component.py、slots.md 在 B1 照建，'
                      '它们是按需导入的前提（D6）。组件按八种类型落位，每个外来文件登记在 imports.tsv；pstack 专有的说法、forge、control、模型角色由 '
                      'mmw/references/slots.md 解析，「Opening a PR」读作 Deliver a change（D2）；跨厂商面板 dispatch.sh panel 随第一个需要它的组件按需加入（D7）。')
    IP['src'] += '；§17 D2、D6、D7'
    for t in IP['import_types']:
        _sub(t, 'examples', 'feature、investigation、babysit、visual-parity …', 'feature、investigation、worktree-cleanup、visual-parity …')
        _sub(t, 'examples', '；第 31–33 行（B4）', '')
        if t.get('examples') == 'bugbot-triage.md（B4）':
            t['examples'] = '本次清单里没有：pstack 唯一的 mode reference 随 D2 不导入；类型保留给以后'
            _src(t, '§17 D2')
        if isinstance(t.get('examples'), str) and 'watch-pr' in t['examples']:
            t['examples'] = 'worktree-audit.sh（B4，按需）'
            _src(t, '§17 D2')
    _sub(IP['namespace_rule'], 'text', '不混入 bun 的 package.json、bun.lock', '不混入外来脚本')
    Q = IP['playbook_import_a_component']['entry_questions']
    Q[2]['q'] = '依赖 PR 吗？是就不导入。'
    Q[2]['src'] += '；§17 D2（本页按它改写）'
    Q[3]['q'] = '依赖跨厂商面板吗？是就随它一起加入 dispatch.sh panel。'
    Q[3]['src'] += '；§17 D7（本页按它改写）'
    SL = {s['label']: s for s in IP['slots']}
    SL['delivery 槽位']['mmw'] = '**Deliver a change**（P10）；slots.md 这一行写「Opening a PR → **Deliver a change**」'
    _src(SL['delivery 槽位'], '§17 D2')
    SL['个人 mode']['mmw'] = '按需时再定对应物'
    _src(SL['个人 mode'], '§17 D7')
    SL['多模型面板']['mmw'] = '`dispatch.sh panel <label> <brief>`，列表取自 models.json 该面板角色；随第一个需要它的组件按需加入'
    _src(SL['多模型面板'], '§17 D7')
    st = IP['bugfix_merge_example']['steps'][6]
    st['reads_as'] = 'delivery 槽位 → **Deliver a change**（D2）'
    _src(st, '§17 D2')

    BI = IP['batch_imports']
    _rm(BI['B1']['playbooks'], lambda p: p['name'] in ('session-pickup', 'pause-safely'))
    BI['B1']['also'] = 'upstream-pstack/ 子树、import_component.py、slots.md 在 B1 建，它们是按需导入的前提（R18 §10 B1、§17 D6）'
    BI['on_demand_unbatched'] = {'playbooks': ['session-pickup', 'pause-safely'], 'note': 'D6 从 B1 推迟到按需，R18 没有指定批次', 'src': 'R18 §17 D6'}
    BI['B3']['scripts'] = ['dispatch.sh panel、panel-wait（随第一个需要它的组件，D7）', 'models.json 面板角色（同上）']
    BI['B3']['scripts_src'] += '；§17 D7'
    B4 = BI['B4']
    _rm(B4['playbooks'], lambda p: p['name'] in PR_PB)
    B4['mode_reference'] = None
    B4['mode_scripts'] = ['worktree-audit.sh']
    B4['mode_triggers'] = None
    B4['other'] = None
    B4['src'] += '；§17 D2'
    BI['count_note'] = ('按需导入的 pstack playbook 共 13 份（session-pickup、pause-safely 2，B3 6，B4 1，B5 4；另有 bug-fix 在 B3 合并）、'
                        '能力技能 17 个（B3 15、B5 2）、原则 9 条（B3）。')
    BI['count_note_src'] = 'R18 §10、§13.1、§17 D2、D6（本页重算）'
    for f in IP['b3_file_changes']:
        _sub(f, 'files', 'dispatch.sh 的 panel、panel-wait；models.json 面板角色', 'dispatch.sh 的 panel、panel-wait 与 models.json 面板角色只在导入的组件需要时加（D7）')

    PI = IP['pstack_inventory']
    PI['outcomes'] = [
        {'outcome': '导入', 'what': '能力技能（按需）', 'count': 17, 'kind': 'capability'},
        {'outcome': '导入', 'what': '原则（B1 14 + 按需 9）', 'count': 23, 'kind': 'principle'},
        {'outcome': '导入', 'what': 'playbook 文件（按需；bug-fix 以合并方式进入）', 'count': 14, 'kind': 'playbook'},
        {'outcome': '并入 MMW 版', 'what': '同名 playbook（authoring-a-skill、prototype）', 'count': 2, 'kind': 'playbook'},
        {'outcome': '导入', 'what': 'mode 触发行原文（按需）', 'count': 11, 'kind': 'mode'},
        {'outcome': '导入', 'what': 'mode 小节（## Comments，按需）', 'count': 1, 'kind': 'mode'},
        {'outcome': '导入', 'what': 'mode 脚本（worktree-audit.sh，按需）', 'count': 1, 'kind': 'script'},
        {'outcome': '导入', 'what': 'agent 简报（comment-sicko，按需）', 'count': 1, 'kind': 'reference'},
        {'outcome': '映射', 'what': '映射到 MMW 对应小节的 mode 项', 'count': 8, 'kind': 'mode'},
        {'outcome': '不导入', 'what': '能力技能 6、playbook 7、触发行 5、mode reference 1、mode 脚本 3、agent 1、automation 1', 'count': 24, 'kind': 'other'},
    ]
    PI['outcomes_sum_check'] = '17+23+14+2+11+1+1+1+8+24 = 102'
    PI['outcomes_src'] = 'R18 §13.1 合计，按 §17 D2 把 PR 组 8 项移到「不导入」后重算'
    for p in PI['playbooks']:
        if p['name'] in PR_PB:
            p['batch'] = None
            p['outcome'] = '不导入：' + D2_WHY
            p['src'] += '；§17 D2'
        if p['name'] in ('session-pickup', 'pause-safely'):
            p['batch'] = '按需（D6）'
            p['src'] += '；§17 D6'
    for it in PI['mode_items']:
        if it['item'].startswith('第 31、32、33 行'):
            it['outcome'] = '不导入（D2）'
            it['batch'] = None
            it['src'] += '；§17 D2'
    for it in PI['other_items']:
        if 'bugbot' in it['item'] or 'watch-pr' in it['item']:
            it['outcome'] = '不导入（D2）'
            it['batch'] = None
        if it['item'] == 'scripts/worktree-audit.sh':
            it['batch'] = 'B4（按需）'
    ND = {n['group']: n for n in PI['not_imported_detail']}
    ND['playbook 4']['item'] += '；opening-a-pr、babysit、shipping（D2）'
    ND['playbook 4']['group'] = 'playbook 7'
    ND['触发行 2']['item'] += '；第 31、32、33 行（Babysit、Shipping、Bugbot，D2）'
    ND['触发行 2']['group'] = '触发行 5'
    ND['mode 脚本 2']['item'] += '；scripts/watch-pr/ 一组（D2）'
    ND['mode 脚本 2']['group'] = 'mode 脚本 3'
    PI['not_imported_detail'].insert(4, {'item': 'references/bugbot-triage.md（只服务 PR 看护，D2）', 'group': 'mode reference 1'})
    PI['not_imported_src'] = 'R18 §13.1、§17 D2'

    IP['pr_mapping'] = [r for r in IP['pr_mapping'] if r['case'] != '白天在用 PR 的仓库']
    for r in IP['pr_mapping']:
        if r['case'] == '一夜的结果':
            r['pstack'] = '一个 stack 经 PR 看护与合并落地；或 Autopilot、Orchestrate'
    IP['pr_mapping'].append({'case': '用 PR 交付的仓库', 'pstack': 'PR 组三份 playbook', 'mmw': '没有这种仓库（D2）', 'src': 'R18 §17 D2'})
    IP['shipping_correspondence']['text'] = 'pstack shipping.md 九步在 MMW 现行交付里逐条都有对应物，这是 D2 不用 PR 的依据。'
    IP['shipping_correspondence']['src'] += '；§17 D2'
    IP['shipping_correspondence']['pairs'] = [pr if pr[0] != 'watch-pr 与 /loop' else ['PR 看护脚本与 /loop', pr[1]] for pr in IP['shipping_correspondence']['pairs']]
    IP.pop('bun', None)
    IP['panel']['text'] = IP['panel']['text'].replace('arena、architect、interrogate、reflect、eval 与它同批（B3），价值来自模型多样性，不以降级方式导入。',
                                                      '它随第一个需要它的组件按需加入（D7），不进核心批次 B0–B2。')
    IP['panel']['src'] += '；§17 D7'

    I = O['issue_591']
    I['user_action'] = {'text': '已定（D1）：B0 发布步骤里执行 `models.py config set researcher codex "gpt 6 sol" high`，给本机 ~/.mmw/models.json 加 researcher 一行。', 'src': 'R18 §16、§17 D1'}

    BT = O['batches']
    BT['claim'] = '六批，每批是本仓库的一张票，由当时已安装的冻结版本跑；每批完成后流水线照常能跑。核心批次只到 B0–B2；B3–B5 按需：每次由你点名要导入的组件。'
    BT['claim_src'] = 'R18 §0.3、§10、§17 D6、D7'
    L = {b['id']: b for b in BT['list']}
    b0 = L['B0']
    _sub(b0['items'][0], 'text', '与五个宿主的 hook 改登记', '与三个宿主（' + HOSTS3 + '）的 hook 改登记')
    _src(b0['items'][0], '§17 D3')
    b0['you_do'] = [x if 'researcher' not in x else '无需另批：发布步骤里执行 `models.py config set researcher codex "gpt 6 sol" high`（D1）' for x in b0['you_do']]
    b0['you_do_src'] += '；§17 D1'
    b1 = L['B1']
    for it in b1['items']:
        if it['text'] == '导入 session-pickup、pause-safely（pstack 原文）':
            it['text'] = 'session-pickup、pause-safely 推迟到按需（D6）'
            it['kind'] = 'other'
            it['src'] = 'R18 §17 D6'
            it['deferred'] = True
        if it['text'] == 'pstack 14 条（prove-it-works 等）':
            it['text'] = 'pstack 14 条（prove-it-works 等）：只导入 MMW 点名的，§5.3 B1 的 14 行都有调用方（D6）'
            it['src'] += '；§17 D6'
        if it['text'] == 'upstream-pstack/ 子树':
            it['text'] = 'upstream-pstack/ 子树（按需导入的前提，D6）'
            it['src'] += '；§17 D6'
    b2 = L['B2']
    b2['you_do'] = ['在没有 watch 开着时授权「移动 checkout + install.sh」（它会重载 com.mmw.board）',
                    '开新会话（dispatch、implement 的 description 消失，code-review 的 description 改回上游）',
                    '不用挑 spec：发布后你照常跑的下一个 spec 就是验收夜（D5）',
                    '读 downstream-note']
    b2['you_do_src'] += '；§17 D5'
    b3 = L['B3']
    b3['name'] = 'pstack 核心'
    for it in b3['items']:
        if it['text'].startswith('dispatch.sh panel、panel-wait'):
            it['text'] = 'dispatch.sh panel、panel-wait 随第一个需要它的组件加入（D7）；启动器删旧路径候选；closeout 步骤核对转为拒绝'
            it['src'] += '；§17 D7'
        if it['text'].startswith('models.json 面板角色'):
            it['text'] = 'models.json 面板角色（同上，D7）'
            it['src'] += '；§17 D7'
    b3['you_do'] = ['点名要导入的组件', '授权 install.sh（skills.txt 与启动器变了）', '开新会话']
    b3['you_do_src'] += '；§17 D6'
    b4 = L['B4']
    b4['name'] = '工作树清理'
    b4['items'] = [
        {'kind': 'playbook', 'text': 'worktree-cleanup', 'src': 'R18 §10、§17 D2', 'origin': 'ps'},
        {'kind': 'script', 'text': 'mode 脚本 worktree-audit.sh', 'src': 'R18 §10、§17 D2', 'origin': 'ps'},
    ]
    b4['why_pipeline_runs'] = '只加。'
    b4['you_do'] = ['点名要导入时授权 install.sh', '开新会话']
    b4['you_do_src'] = 'R18 §10、§17 D2、D6'
    b4['src'] = 'R18 §10、§17 D2'
    L['B5']['you_do'] = ['点名要导入的组件'] + L['B5']['you_do']
    L['B5']['you_do_src'] += '；§17 D6'
    for m in BT['mode_per_batch']:
        if m['batch'] == 'B4、B5':
            m['triggers'] = 'B4、B5 不加触发行'
            m['routes'] = 'B4 按需加 1 行（worktree-cleanup），B5 按需加 4 行'
            m['src'] += '；§17 D2'
    BT['mode_length'] = 'B2 后约 170 行，B4 后约 200 行（推断；pstack mode 143 行）。200 行按含 PR 组估，D2 后会少一些（推断）。'
    BT['mode_length_src'] += '；§17 D2'
    CA = {c['what']: c for c in BT['counts_after']}
    CA['playbook']['after_b2'] = '16 份（MMW 自写）＋本仓库私有 3 份'
    CA['playbook']['after_all'] = '29 份（pstack 按需 13 份）＋私有 3'
    CA['能力技能']['after_all'] = '52 个（加按需的 pstack 17）'
    CA['原则']['after_all'] = '35 条（加按需的 pstack 9 条）'
    CA['脚本']['after_all'] = '加按需的 ps/worktree-audit.sh'
    BT['counts_after_src'] = 'R18 §0.1、§0A.2、§17 D2、D6（本页重算）'
    for c in BT['common']:
        pass

    # Section 13: decided, not pending
    O['decided'] = {
        'boundary': {'text': '下面九项由你在 2026-09-29 定下，写在 R18 §17，优先于 R18 前文各节；本页各图与表已按它们改写。「本页改了什么」一行写每一项落在页面的哪些地方。',
                     'src': 'R18 §17 首句'},
        'items': [
            {'id': 'D1', 'q': 'B0 发布后给 ~/.mmw/models.json 加 researcher 一行', 'decision': '加',
             'effect': '发布步骤里执行 `models.py config set researcher codex "gpt 6 sol" high`，不再单独问你。',
             'page': '图 11 下「验证与你要做的」、图 12 B0「你要做的」、图 1 角色表 researcher 行、~/.mmw/models.json 盒子'},
            {'id': 'D2', 'q': '是否有仓库改用 PR 交付', 'decision': '不用。MMW 现行交付（closeout → advance 合进 project branch → 你验收 → finish）已覆盖 pstack shipping.md 九步的意图，单人、无 CI 的仓库用 PR 只多一层',
             'effect': '删去 delivery: pr 取值与 PR 组三份导入、它们的 reference、脚本组与 bun；deliver-a-change 只保留 commit 与 playbook:<slug>；slots.md 的 delivery 行写「Opening a PR → Deliver a change」；worktree-cleanup 改为按需导入。',
             'page': '图 1 playbook 层与脚本层、图 3、图 5 出口一排、图 10 导入类型与入口问题、图 10 下 102 项核算（PR 组 8 项改记「不导入」）、图 12 B4、「PR 与交付的对应」表改为 D2 的依据'},
            {'id': 'D3', 'q': 'Cursor', 'decision': '不考虑。现役宿主以 ~/.mmw/models.json 为准：Claude Code（reviewer、advisor）、Codex（senior-worker）、Grok（junior-worker），runner 是 Orca',
             'effect': 'H1 的宿主清单收窄为这三个；mode ## Autonomy 不再为 Cursor 抄产品事项清单，只点名 shared.md 规则号；mode-hook.py 的「判断是不是 Cursor」一句删去；探针 U-1–U-4 只测这三个宿主。',
             'page': '硬约束 H1、图 1 mode 的 Autonomy、角色表各行的现役宿主、图 2 shared.md 一行、图 7 下 mode-hook.py 范围、图 9 下 shared.md 关系、探针 U-1–U-4'},
            {'id': 'D4', 'q': '消费仓库 AGENTS.md 是否加一行指向 mmw', 'decision': '不加。人起的会话用 /mmw，或由 mmw 的 description 被加载',
             'effect': '删去人起会话的「AGENTS.md 一行」这条到达路径、消费仓库 AGENTS.md 那一行、dispatch.sh check 的缺行提示；onboard-a-repository 第 2 步不写这一行。',
             'page': '图 1 入口、图 3 消费仓库、图 7 的一整列（它是矩阵里唯一的「待你决定」列）、P9 第 2 步'},
            {'id': 'D5', 'q': 'B2 的发布时机与验收', 'decision': '不需要你选择',
             'effect': 'B2 只在没有 watch 开着时发布；发布前在隔离 home 用假 tracker 跑一整夜；发布后你照常跑的下一个 spec 就是验收夜。',
             'page': '图 12 B2「你要做的」、风险「上游 code-review 可能抢触发」'},
            {'id': 'D6', 'q': 'pstack 导入', 'decision': '按需，先不要让 pstack 的东西过多进入',
             'effect': 'B3–B5 全部按需，每次由你点名要导入的组件，走私有 playbook Import a component；B1 只导入被 MMW 自写 playbook 或能力技能点名的 pstack 原则（§5.3 B1 的 14 行都有调用方，仍是 14 条）；session-pickup、pause-safely 推迟到按需；upstream-pstack/ 子树、import_component.py、slots.md 照建。',
             'page': '页首数字、图 1 playbook 层、图 5 两张 pstack 卡片、图 9 P17/P18 列、图 10 下按需清单、图 12 B1 与 B3–B5 表头'},
            {'id': 'D7', 'q': 'pstack 扩展工具箱（reflect、eval、figure-it-out、automate-me、show-me-your-work、create-verification-skill、maintain-verification-skill）与多模型面板 dispatch.sh panel 是否提进核心批次', 'decision': '不提，全部保持按需',
             'effect': '核心批次只到 B0–B2；dispatch.sh panel、panel-wait 与 models.json 面板角色随第一个需要它的组件按需加入；slots.md 的 automate-me 一行是「按需时再定对应物」。',
             'page': 'dispatch.sh 子命令表、新增机制表 panel 一行、slots.md 表、图 12 B3、工程决定表（原「panel 与 B3 同批」一条移除）'},
            {'id': 'D8', 'q': '任务面板（mmw-v2/board/）怎样读 MMW', 'decision': '只经稳定接口读：跨目录的路径从 anchors.py 取，「一张票现在在哪一步」从 dispatch.sh where 取，角色从 roles.json 取；不写死技能目录里的文件位置',
             'effect': 'B2 改 board/ 四处路径时按此写。面板以后可以显示的新信息（角色与模型、每张票当前在 playbook 的哪一步、原则索引、imports.tsv）不在本次范围，另开 spec。',
             'page': '图 1 左栏「任务面板」盒子与图 1 下「任务面板读哪些接口」表'},
            {'id': 'D9', 'q': '技能文本的写作与命名', 'decision': '技能文本同时遵守 pstack 的文本结构与 mattpocock 的写作方式；搬运的句子逐字保留；MMW 自有的技能、reference、脚本趁这次系统改名，上游 mattpocock 与 pstack 的名字不改',
             'effect': '写作规范 R20-writing-style-guide.md 与范本 docs/research/workflow-compare/exemplars/ 作票的基准；逐字搬运检查与结构 lint（R21-text-integrity-checks.md）进 B0；改名按你过目的 R19-naming-table.md，在搬家的同一张票里做。',
             'page': '本页没有改名：页面上的名字仍是 R18 定稿的名字。R19、R20、R21 与 exemplars/ 在本页生成时还不存在（已用 ls 核实），改名表定稿后本页要随之更新'},
        ],
    }
    for it in O['decided']['items']:
        it['src'] = 'R18 §17 ' + it['id']
    O.pop('decisions_for_user', None)

    ED = O['engineering_decisions']
    _rm(ED['items'], lambda e: e['decision'].startswith('引入 bun') or e['decision'].startswith('多模型面板 panel'))
    ED['note'] = {'text': '前 8 条是 R18 §0.5「我已自行做出的工程决定」（原第 5 条「引入 bun」随 §17 D2 删去）；后 3 条取自正文各节（原「panel 与 B3 同批」一条被 §17 D7 取代）。',
                  'src': 'R18 §0.5、§17 D2、D7'}

    RK = {r['id']: r for r in O['risks']['items']}
    _sub(RK['code-review-trigger'], 'mitigation', 'B2 验收夜会看到', 'B2 发布后你照常跑的下一个 spec（验收夜，D5）会看到')
    _src(RK['code-review-trigger'], '§17 D5')
    RK['nine-mechanisms']['title'] = '新增九项机制（panel 按需）'
    _sub(RK['nine-mechanisms'], 'mitigation', 'import_component.py、panel）', 'import_component.py、panel；panel 随第一个需要它的组件按需加入，D7）')
    _src(RK['nine-mechanisms'], '§17 D7')
    _sub(RK['mode-reach'], 'risk', '各宿主能否注入一行要实测（U-2）', '三个宿主（' + HOSTS3 + '，D3）能否注入一行要实测（U-2）')

    PBS = O['probes']
    _sub(PBS['where'], 'text', 'U-11 在 B2 验收夜看到', 'U-11 在 B2 发布后的第一个真实夜（D5）看到')
    for p in PBS['items']:
        for k in ('question', 'how'):
            _sub(p, k, '五个宿主', '三个宿主（' + HOSTS3 + '，D3）')
        if p['id'] in ('U-2', 'U-3'):
            p['question'] += '（只测 ' + HOSTS3 + '，D3）'
        if p['id'] in ('U-1', 'U-2', 'U-3', 'U-4'):
            _src(p, '§17 D3')
        if p['id'] == 'U-9':
            p['why'] += '；现役 runner 是 Orca（D3）'
        if p['id'] == 'U-6':
            p['when'] = '随 panel 按需加入时（D7）'
        _sub(p, 'when', 'B2 验收夜会看到（§0.4）', 'B2 发布后的第一个真实夜（§0.4、§17 D5）')
    NM = O['new_mechanisms']
    for it in NM['items']:
        if it['name'] == 'dispatch.sh panel':
            it['what'] += '；随第一个需要它的组件按需加入（D7）'
            _src(it, '§17 D7')
        _sub(it, 'why', 'H1：这些宿主没有 Cursor 的 mode: true / reminder 常驻机制', 'H1：' + HOSTS3 + ' 没有 pstack 依赖的 mode: true / reminder 常驻机制')
    _sub(O['basis']['unverified'][0], 'text', '五个宿主的加载与 hook 注入', '三个宿主（' + HOSTS3 + '，D3）的加载与 hook 注入')
    CJ = O['closing_judgement']
    CJ['paragraphs'][3] = '需要你知道的风险有四个：B2 面最大；mode 在部分宿主上能否被自动读到还要实测；worker 每张票要多读 mode（约 170–200 行）；新增了九项机制（其中 panel 按 D7 按需加入）。'
    CJ['paragraphs'].append('你 2026-09-29 定下的九项（R18 §17）把这次改造收在 B0–B2：pstack 只在你点名时导入，不用 PR，不考虑 Cursor，消费仓库的 AGENTS.md 不动，任务面板只经稳定接口读 MMW。')
    CJ['src'] += '；R18 §17'
    O['about']['batches'] = O['about']['batches'].replace('页面画虚线框并标「按需：每批开工前你点头」', '页面画虚线框并标「按需：你点名要导入的组件时才做」（R18 §17 D6、D7）')
