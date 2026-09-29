# Corrections applied to the extracted data before it is embedded in the page.
# Each fix names the reader-visible problem it removes.

def _sub(d, key, old, new):
    v = d.get(key)
    if isinstance(v, str) and old in v:
        d[key] = v.replace(old, new)


def patch(data):
    A, M, PB, PR, O = data['arch'], data['mig'], data['pb'], data['pr'], data['ops']

    # Non-negotiables: R18 §2.2 trigger table has 20 rows.
    for s in A['fig1']['mode']['sections']:
        _sub(s, 'note', 'MMW 触发行 22 行', 'MMW 触发行 20 行（R18 §2.2 表）')
    A['fig1']['mode']['section_count_note'] = ('七节：Non-negotiables、Principles、Autonomy、Re-entry、Subagents、Writing the reply、Playbooks；'
                                              'Imported triggers 是 Non-negotiables 下的小节，Comments 在 B3 加入')

    # B0 location of roles.json / anchors.py.
    b0loc = 'B0 时的位置：R18 未写（§10 B0 行只写「只登记」；§16 写明 B0 时 dispatch.sh 仍在 dispatch/scripts/，B2 随整目录搬家）'
    for st in A['fig1']['state']:
        if st.get('id') == 'cfg:roles.json':
            st['note'] += '\n' + b0loc
    for g in A['fig1']['script_groups']:
        for it in g['items']:
            if it.get('id') == 'sc:anchors.py':
                it['note'] += '\n' + b0loc
            if it.get('id') == 'sc:gate-check':
                it['label'] = 'upstream-unlazy/gate-check.mjs（verify-ticket 调用）'
                it['owner'] = None

    def walk(n):
        if n.get('name') in ('roles.json', 'mode-hook.py anchors.py') and n.get('batch') in (None, 'B0') :
            n['note'] = (n.get('note') or '') + '。' + b0loc if n.get('note') else b0loc
        for ch in n.get('children', []): walk(ch)
    walk(A['fig3']['after']['mmw-v2'])
    # not_found wording: no reference to the data files or earlier pages.
    for n in A.get('not_found', []):
        for k in ('status', 'item'):
            _sub(n, k, '数据用 7，并在组件表注明', '本页按 7 个画，并在组件表注明')
            _sub(n, k, '（与上一版页面同法）', '')
            _sub(n, k, '数据用 §16 的 5 步', '本页按 §16 的 5 步画')
    _sub(M['categories'][6], 'src', '「态」是本数据给的简记', '「态」是设计方的简记，R18 未写')
    for f in M['flows']:
        _sub(f, 'note', '逐条去处见 scattered_rules', '逐条去处见本节『散落的跨任务规则 PC1–PC29 与去处』表')
        if f['id'] == 'f68':
            f['batch'] = None
            f['note'] = 'anchors.py 在 B0 建（R18 第 10 节）；标题登记的批次 R18 未给'
    nf = []
    for s in M.get('not_found', []):
        if isinstance(s, str):
            s = (s.replace('（对应流与技能的 batch 为 null）', '（对应的流与技能标「R18 未给批次」）')
                 .replace('lines_pure 用的是', '「纯能力」行数用的是')
                 .replace('这些流的 cats 为 null', '这些流不标记号'))
        nf.append(s)
    M['not_found'] = nf

    for w in PB['wake_line_shapes']:
        _sub(w, 'note', '四种形式见 where.forms', '四种形式见图 8 下『dispatch.sh where 的输出』表')
    for p in PB['playbooks']:
        if p.get('steps') == '见 work_a_ticket_matrix':
            p['steps'] = '见图 6 下『11 步逐条』表'
    ms = []
    for s in PB['missing']:
        if isinstance(s, str):
            s = (s.replace('本数据依据', '设计方依据').replace('设计规格要求按 7 个画', '本页按 7 个画')
                 .replace('Chinese names（name_zh）与图上的中文短标签', '图上的中文短名与中文标签'))
        ms.append(s)
    PB['missing'] = ms

    PR['roles']['count']['with_591'] = '7 个（加 researcher，R18 §16）'
    PR['gaps'] = [g.replace('分组与 gloss_zh 所据的', '分组与中文短释所据的')
                  .replace('两份都放进了 fixed_night_breakpoints', '两份名单都列在图 8 下『修掉的四处夜间断点』')
                  for g in PR['gaps']]
    for c in PR['fig9_principles']['citation_matrix']['columns']:
        if c['id'] == 'P17_18':
            c['id'] = 'P17/P18'
    for c in PR['fig9_principles']['citation_matrix']['cells']:
        if c['col'] == 'P17_18':
            c['col'] = 'P17/P18'

    DU = O['decisions_for_user']
    for cd in DU['cards']:
        for k in ('background_src', 'src'):
            _sub(cd, k, '；v3 页面「需要你决定的事」·范围', '')
        r = cd.get('recommendation_src', '')
        if r.startswith('编排方的建议'):
            cd['recommendation_src'] = '设计方建议，R18 未写；R18 §0.3 把 B3–B5 排为计划内'
        elif r.startswith('v3 页面建议「先回答 researcher 那一行」'):
            cd['recommendation_src'] = '设计方建议，R18 未写；理由句取自 R18 §16「#591 是正在发生的故障」'
        elif r.startswith('v3 页面建议'):
            cd['recommendation_src'] = '设计方建议，R18 未写'
    ED = O['engineering_decisions']
    _sub(ED['note'], 'text', '标 from_body 的 4 条取自正文各节', '后 4 条取自正文各节')
    for it in ED['items']:
        for k in ('rejected', 'reason'):
            v = it.get(k)
            if isinstance(v, str):
                it[k] = v.replace('上一版本文：', 'R18 上一版本文：').replace('上一版：', 'R18 上一版本文：').replace('上一版的 P9', 'R18 上一版本文的 P9').replace('上一版「', 'R18 上一版本文「')
    for r in O['risks']['items']:
        _sub(r, 'src', '；v3 页面「我的判断」', '')
    _sub(O['basis'], 'reports_src', '；v3 页面「依据」', '')
    O['closing_judgement']['src'] = '设计方的判断，R18 未写；自查表见 R18 §12'
    for d in O['source_discrepancies']:
        _sub(d, 'detail', '页面照抄原文即可，但两者不一致。', '两者不一致。')
        _sub(d, 'detail', '设计规格写「U-1…U-17 都在 B0 的隔离环境里做」；R18 只写', '「U-1…U-17 都在 B0 的隔离环境里做」这句 R18 没有写；R18 只写')
    _sub(O['import_pipeline']['playbook_import_a_component']['steps'][1], 'detail', '见 entry_questions', '见本节『第 2 步的六个入口问题』表')
    for lp in PR['fig7_arrival']['launch_prompts']:
        lp['role'] = {'human_hook': 'mode-hook 提醒（人起的会话）', 'subagent_hook': 'mode-hook（会话内子代理）', 'wake': '唤醒', 'resume': 'resume', 'open': 'open 输出'}.get(lp['role'], lp['role'])
    W = PR['fig8_reentry']['where']
    _sub(W, 'why_not_resume_at', '上一版「', 'R18 上一版本文「')
    for c in O['probes']['closed']:
        _sub(c, 'text', '上一版的 U-10', 'R18 上一版本文的 U-10')
    return data
