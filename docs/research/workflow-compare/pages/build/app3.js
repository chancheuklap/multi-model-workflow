/* ---------- figure 7: arrival matrix ---------- */
function statusMark(p, x, y, st, note) {
  const g = S('g', null, p);
  if (st === 'certain') S('circle', { cx: x, cy: y, r: 7, style: 'fill:var(--ink)' }, g);
  else if (st === 'probe') { S('circle', { cx: x, cy: y, r: 7, style: 'fill:none;stroke:var(--warn);stroke-width:1.6' }, g); S('path', { d: `M${x},${y - 7} A7,7 0 0,0 ${x},${y + 7} Z`, class: 'warn' }, g); }
  else if (st === 'partial') { S('circle', { cx: x, cy: y, r: 7, style: 'fill:none;stroke:var(--warn);stroke-width:1.6' }, g); S('circle', { cx: x, cy: y, r: 2.8, class: 'warn' }, g); }
  else if (st === 'decide') S('path', { d: `M${x},${y - 8} L${x + 8},${y} L${x},${y + 8} L${x - 8},${y} Z`, style: 'fill:none;stroke:var(--c-mode);stroke-width:1.8' }, g);
  const u = (note || '').match(/U-\d+/);
  const word = { certain: '确定', probe: '待实测' + (u ? ' ' + u[0] : ''), partial: '部分已观察', decide: '待你决定' }[st];
  T(g, x, y + 21, word, { size: 10, anchor: 'middle', cls: st === 'certain' ? 't2' : 'tm' });
  return g;
}
function fig7() {
  const F = PR.fig7_arrival; const cols = F.columns, rows = F.rows;
  const RLW = 250, CWd = 100, W = RLW + cols.length * CWd + 6, c = mkSvg('f7', W, 1100), L = c.L;
  let hh = 0;
  cols.forEach((col, i) => {
    const x = RLW + i * CWd; const g = S('g', null, L.node);
    const sp = col.label.match(/^([\x21-\x7E]+) (.+)$/); const ls = sp && tw(col.label, 11.5) > CWd - 10 ? [sp[1], sp[2]] : wrap(col.label, CWd - 10, 11.5, isMono(col.label));
    TL(g, x + CWd / 2, 16, ls, { size: 11.5, cls: 'b', anchor: 'middle', mono: isMono(col.label), lh: 14 });
    if (col.extra) T(g, x + CWd / 2, 16 + ls.length * 14, '（补充）', { size: 10, cls: 'tm', anchor: 'middle' });
    tip(g, col.label + '\n' + col.detail + srcOf(col)); hh = Math.max(hh, ls.length * 14 + (col.extra ? 14 : 0));
  });
  let y = hh + 20; let lastG = null;
  rows.forEach((r, ri) => {
    const grp = ri === rows.length - 1 && /orchestrator/.test(r.label) ? 'orchestrator' : r.group;
    if (grp !== lastG) { S('line', { x1: 0, x2: W, y1: y, y2: y, class: 'sep' }, L.bg); T(L.node, 0, y + 14, grp, { size: 10.5, cls: 'tm' }); y += 18; lastG = grp; }
    const ls = wrap(r.label, RLW - 16, 12, false); const h = Math.max(46, ls.length * 15 + 16);
    S('rect', { x: 0, y, width: W, height: h, class: ri % 2 ? 'cellbg' : 'lbg' }, L.bg);
    const g = S('g', null, L.node); TL(g, 4, y + 18, ls, { size: 12, cls: 'b', lh: 15 }); tip(g, r.label + (r.note ? '\n' + r.note : '') + srcOf(r));
    cols.forEach((col, i) => {
      const cell = r.cells[col.id]; if (!cell) return;
      const m = statusMark(L.node, RLW + i * CWd + CWd / 2, y + 16, cell.status, (cell.note || '') + ' ' + (cell.src || ''));
      tip(m, `${r.label} × ${col.label}\n${cell.note}${srcOf(cell)}`);
    });
    y += h;
  });
  y += 16;
  const lg = [['certain', '确定'], ['probe', '待实测（U 编号见第 14 节）'], ['partial', '部分宿主已观察到，其余待测']];
  let lx = 8; lg.forEach(([s, t]) => { statusMark(L.node, lx + 8, y, s, '').lastChild.remove(); T(L.node, lx + 22, y + 4, t, { size: 11, cls: 't2' }); lx += 40 + tw(t, 11); });
  y += 18; T(L.node, 4, y + 8, F.fallback_statement + '（' + F.fallback_src + '）', { size: 11, cls: 'tm' });
  c.done(y + 16);
}
function sec7Tables() {
  const RI = PR.roles;
  tbl('t7-roles', [{ h: '角色', f: r => r.role }, { h: 'playbook', f: r => r.playbook || ('能力技能 ' + r.skill + ' 的 ' + r.brief + '（例外）') }, { h: 'models.json 行', f: r => r.models_row ? r.models_row.join(' / ') + (r.models_default ? `（默认 ${r.models_default.host}、${r.models_default.model}、${r.models_default.effort}）` : '') : '（人起的会话）' }, { h: '谁启动', f: r => r.started_by }, { h: 'watch kind', f: r => r.watch_kind || '' }, { h: '被哪些事件叫醒到哪一步', f: r => jwakes(r.wakes) }, { h: '常驻纪律从哪来', f: r => r.discipline_from }, { h: '说明', f: r => [r.note, r.worktree].filter(Boolean).join('；') }, srcCol()], RI.items, { title: 'mmw/roles.json：7 个角色（含 #591 的 researcher；现役宿主按 R18 §17 D3）', open: true, intro: '角色数：' + RI.count.B2 + '；' + RI.count.with_591 + '。' });
  list('t7-roles', [RI.star_expansion.label + '：' + RI.star_expansion.items.join('；'), ...RI.recipient_rule.items.map(i => '收件角色：' + i), '读 roles.json 的：' + RI.readers.items.join('、') + '。' + RI.readers.rule, ...RI.not_in_roles_json.map(n => `不是角色：${n.role}，${n.file}，${n.model}，${n.started_by}，${n.discipline}`)], { title: 'roles.json 的其余规则（* 展开、收件角色、谁读它、哪些不是角色）' });
  const F = PR.fig7_arrival;
  tbl('t7-more', [{ h: '角色', f: r => r.role }, { h: '送进会话的一行', f: r => r.text }, srcCol()], F.launch_prompts, { title: '各类会话收到的那一行' });
  list('t7-more', ['数据文件 `' + F.data_file.path + '`：' + F.data_file.contains.join('；'), F.data_file.why, '今天：' + F.data_file.today, ...F.mode_hook_scope.events.map(e => `mode-hook.py · ${e.event}：${e.does}`), ...F.mode_hook_scope.scope_rules.map(s => 'mode-hook.py 范围：' + s), `到达机制：改造前 ${F.arrival_count.before}；改造后 ${F.arrival_count.after}`], { title: '启动数据文件与 mode-hook.py' });
  const cells = []; F.rows.forEach(r => F.columns.forEach(col => { const cl = r.cells[col.id]; if (cl) cells.push({ row: r.label, col: col.label, ...cl }); }));
  tbl('t7-more', [{ h: '会话', f: r => r.row }, { h: '路径', f: r => r.col }, { h: '状态', f: r => ({ certain: '确定', probe: '待实测', partial: '部分已观察', decide: '待你决定' })[r.status] }, { h: '依据', f: r => r.note }, srcCol()], cells, { fold: '矩阵每一格的依据' });
}

/* ---------- figure 8: re-entry ---------- */
function fig8() {
  const F = PR.fig8_reentry, W = 1250, c = mkSvg('f8', W, 1100), L = c.L;
  const nd = Object.fromEntries(F.nodes.map(n => [n.id, n]));
  const kindOf = { state: 'nt', script: 'script', config: 'config', text: 'nt', session: 'nt', mode: 'mode', playbook: 'playbook', output: 'script', test: 'script', reference: 'reference' };
  const P = { event: [10, 30, 160], sender: [205, 30, 210], roles: [455, 30, 205], wakeline: [760, 30, 230], session: [1040, 30, 200],
    anchors: [10, 185, 190], orchevents: [455, 185, 220], reentry: [1015, 175, 225], compact: [10, 350, 160], modehook: [205, 350, 210], where: [455, 350, 220], step: [1015, 420, 225],
    status: [455, 500, 220], out_at: [250, 620, 170], out_between: [440, 620, 190], out_fresh: [650, 620, 170], out_unknown: [840, 620, 190], wiring: [205, 790, 420] };
  const outs = Object.fromEntries(F.where.outputs.map(o => [o.form.split(' ')[0], o]));
  const box = {};
  const ctags = {}; // checks drawn as tags on the checked box instead of long dashed lines
  F.edges.filter(e => e.kind === 'check').forEach(e => {
    const m = (e.label || '').match(/第 \d+ 类/);
    const t = e.from === 'wiring' ? 'check_wiring ' + (m ? m[0] : '核对') : e.from === 'anchors' ? 'locations.py 登记' : e.from;
    (ctags[e.to] = ctags[e.to] || []).push({ t, tip: (e.from === 'wiring' ? 'check_wiring.py：' : 'locations.py：') + e.label + srcOf(e) });
  });
  for (const id in P) {
    const n = nd[id]; const [x, y, w] = P[id]; const g = S('g', { class: kc(kindOf[n.type]) }, L.node);
    let lines = [];
    if (id === 'reentry') lines = F.reentry_steps.flatMap(s => wrap(`${'①②③④'[s.n - 1]} ${s.label}：${s.text}`, w - 16, 10, false));
    else if (id.startsWith('out_')) { const o = outs[n.label]; lines = wrap(o.label + '：' + o.meaning, w - 16, 10, false); }
    else if (n.detail) lines = wrap(n.detail, w - 16, 10, false);
    const tl = wrap(n.label, w - 16, 12, isMono(n.label));
    const h = 24 + (tl.length - 1) * 15 + lines.length * 12.5 + 6 + (ctags[id] ? 18 : 0);
    R(g, x, y, w, h, { soft: n.type === 'session' || n.type === 'text' });
    if (ctags[id]) { let tx = x + w - 5; ctags[id].forEach(ct => { const tw2 = tw(ct.t, 9.5, false) + 10; tx -= tw2; const tg = S('g', { class: ct.t.startsWith('anchors') ? 'k-sc' : 'k-sc' }, g); R(tg, tx, y + h - 17, tw2, 14, { r: 7, dash: true, soft: true }); T(tg, tx + 5, y + h - 6.5, ct.t, { size: 9.5, cls: 't2' }); tip(tg, ct.tip); tx -= 4; }); }
    TL(g, x + 8, y + 16, tl, { size: 12, cls: 'b', mono: isMono(n.label), lh: 15 });
    TL(g, x + 8, y + 31 + (tl.length - 1) * 15, lines, { size: 10, cls: 't2', lh: 12.5 });
    let t = n.label + (n.detail ? '\n' + n.detail : '') + srcOf(n);
    if (id === 'reentry') t = 'mode ## Re-entry\n' + F.reentry_steps.map(s => `${s.n}. ${s.label}：${s.text}${s.principle ? '（principle-' + s.principle + '）' : ''}`).join('\n') + '\n' + F.reentry_notes.map(r => r.text).join('\n');
    if (id.startsWith('out_')) { const o = outs[n.label]; t = o.form + '\n' + o.meaning; }
    if (id === 'anchors') t += '\n登记：' + F.anchors_and_wiring.anchors_py.registers.map(r => r.what).join('；') + '\n' + F.anchors_and_wiring.anchors_py.rule;
    if (id === 'wiring') t += '\n' + F.anchors_and_wiring.check_wiring_classes.map(k => `${k.n} ${k.name}：${k.checks}`).join('\n');
    tip(g, t);
    box[id] = { x, y, w, h }; c.P.add(x, y, w, h);
  }
  const side = (b, s, f = 0.5) => s === 'r' ? [b.x + b.w + 1, b.y + b.h * f] : s === 'l' ? [b.x - 1, b.y + b.h * f] : s === 't' ? [b.x + b.w * f, b.y - 1] : [b.x + b.w * f, b.y + b.h + 1];
  const route = {
    'event>sender': ['r', 'l', 'h'], 'sender>roles': ['r', 'l', 'h'], 'roles>wakeline': ['r', 'l', 'h'], 'wakeline>session': ['r', 'l', 'h'], 'session>reentry': ['b', 't', 'v'],
    'reentry>step': ['b', 't', 'v'], 'reentry>where': ['l', 'r', 'h'], 'compact>modehook': ['r', 'l', 'h'], 'modehook>where': ['r', 'l', 'h'], 'where>status': ['b', 't', 'v'],
    'status>out_at': ['b', 't', 'v'], 'status>out_between': ['b', 't', 'v'], 'status>out_fresh': ['b', 't', 'v'], 'status>out_unknown': ['b', 't', 'v'], 'out_at>step': ['r', 'b', 'h'],
    'roles>orchevents': ['b', 't', 'v'], 'wiring>anchors': ['l', 'b', 'h'], 'wiring>roles': ['t', 'b', 'v'], 'wiring>step': ['r', 'b', 'h'], 'wiring>wakeline': ['r', 'b', 'h'], 'anchors>where': ['r', 'l', 'h'], 'anchors>sender': ['t', 'b', 'v']
  };
  const frac = { 'wiring>roles': [0.3, 0.2], 'wiring>step': [0.5, 0.7], 'wiring>wakeline': [0.35, 0.5], 'reentry>where': [0.75, 0.3], 'anchors>where': [0.7, 0.7], 'out_at>step': [0.5, 0.3], 'status>out_at': [0.2, 0.5], 'status>out_unknown': [0.8, 0.5], 'status>out_between': [0.4, 0.5], 'status>out_fresh': [0.6, 0.5], 'roles>orchevents': [0.5, 0.5], 'anchors>sender': [0.8, 0.3], 'wiring>anchors': [0.5, 0.5] };
  F.edges.filter(e => e.kind !== 'check').forEach(e => {
    const k = e.from + '>' + e.to;
    if (k === 'out_at>step') { // around the bottom of the output row, up the right side
      const a = box.out_at, b = box.step, yb = Math.max(box.out_at.y + box.out_at.h, box.out_between.y + box.out_between.h, box.out_fresh.y + box.out_fresh.h, box.out_unknown.y + box.out_unknown.h) + 18, xr = box.out_unknown.x + box.out_unknown.w + 40;
      edge(c, [[a.x + a.w / 2, a.y + a.h + 1], [a.x + a.w / 2, yb], [xr, yb], [xr, b.y + b.h + 1]], 'call', { label: e.label, cands: [[(a.x + xr) / 2, yb]], tip: e.label + srcOf(e) });
      return;
    } const r = route[k] || ['r', 'l', 'h']; const fr = frac[k] || [0.5, 0.5];
    const a = side(box[e.from], r[0], fr[0]), b = side(box[e.to], r[1], fr[1]);
    const kind = e.kind === 'event' ? 'wake' : e.kind;
    const mid = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    if (k === 'roles>wakeline') { // a wide gap so the arrow shows; its label sits just above the line
      edge(c, [a, b], kind, { curve: r[2], tip: e.label + srcOf(e) });
      if (e.label) labelAt(c, e.label, mid[0] - (tw(e.label, 10.5) + 8) / 2, mid[1] - 13);
      return;
    }
    edge(c, [a, b], kind, { curve: r[2], label: e.label || null, cands: [mid, cub(a, r[2] === 'v' ? [a[0], mid[1]] : [mid[0], a[1]], r[2] === 'v' ? [b[0], mid[1]] : [mid[0], b[1]], b, 0.35), cub(a, r[2] === 'v' ? [a[0], mid[1]] : [mid[0], a[1]], r[2] === 'v' ? [b[0], mid[1]] : [mid[0], b[1]], b, 0.65)], lmax: 190, tip: e.label + srcOf(e) });
  });
  const y = Math.max(...Object.values(box).map(b => b.y + b.h)) + 12;
  c.done(y);
  htmlLegend('f8', [['call', '实线：调用或运行命令'], ['wake', '点划线：事件唤醒'], { html: '<span class="tagx">check_wiring 第 N 类</span>这个盒子被 check_wiring.py 的第 N 类核对；「locations.py 登记」：它登记在 locations.py；locations.py 与 check_wiring.py 两个盒子是这两个脚本本身' }], { title: '线与标签' });
}
function sec8Tables() {
  const F = PR.fig8_reentry;
  const bp = F.fixed_night_breakpoints;
  let h = '<h3>修掉的四处夜间断点与两处静默失效</h3><div class="cards">';
  bp.list_0_2.forEach(b => h += `<div class="card"><span class="pill">${esc(b.id)}</span><h4>${codeify(b.problem)}</h4><p>修法：${codeify(b.fix)}</p><div class="srcnote">${esc(b.src)}</div></div>`);
  F.fixed_silent_failures.forEach(b => h += `<div class="card risk"><span class="pill risk">静默失效</span><h4>${codeify(b.problem)}</h4><p>修法：${codeify(b.fix)}</p><div class="srcnote">${esc(b.src)}</div></div>`);
  h += '</div>';
  h += `<p class="sub">R18 §10 B0 行的名单：${bp.list_B0.items.map(i => esc(i.id + ' ' + i.label) + (i.fix_hint ? '（' + codeify(i.fix_hint) + '）' : '')).join('；')}。${esc(bp.discrepancy)} ${esc(bp.where_fixed)}</p>`;
  para('t8-fix', h);
  const WH = F.where;
  tbl('t8-more', [{ h: '角色', f: r => r.role }, { h: '票上最新的记录', f: r => r.record }, { h: 'where 输出', f: r => r.output }], WH.table, { title: 'dispatch.sh where：事件 → 步骤全表（' + WH.table_src + '）', intro: WH.how + '。' + WH.why_not_resume_at + '。' + WH.no_new_events + '。' + WH.script_rule + '。实测：' + WH.test + '。' });
  tbl('t8-more', [{ h: '形式', f: r => r.form }, { h: '含义', f: r => r.label + '：' + r.meaning }, srcCol()], WH.outputs, { title: 'dispatch.sh where 的输出' });
  const AW = F.anchors_and_wiring;
  tbl('t8-more', [{ h: '登记什么', f: r => r.what }, { h: '例子', f: r => r.example }], AW.anchors_py.registers, { title: AW.anchors_py.path + '：文字锚点与跨目录路径的唯一登记处', intro: AW.anchors_py.rule });
  tbl('t8-more', [{ h: '类', f: r => r.n }, { h: '名称', f: r => r.name }, { h: '核对什么', f: r => r.checks }, { h: '防什么', f: r => r.guards }, { h: '从哪一批起失败', f: r => r.fail_from }, { h: '与重入相关', f: r => r.reentry ? '是' : '' }], AW.check_wiring_classes, { title: 'check_wiring.py 的 12 类核对', intro: AW.install_check + '。' + AW.counter_examples + '。' });
  const HL = F.hook_launcher;
  tbl('t8-more', [{ h: 'hook', f: r => r.hook }, { h: '事件', f: r => r.event }, { h: '找不到目标时', f: r => r.does }, { h: '为什么', f: r => r.why }], HL.on_missing, { title: 'hook 启动器 ' + HL.path, intro: '命令：`' + HL.command + '`。查找：' + HL.lookup + '。要修的问题：' + HL.problem + '。效果：' + HL.effect + '。验收：' + HL.acceptance });
  tbl('t8-more', [{ h: '批次', f: r => r.batch }, { h: '重入相关的变化', f: r => r.items }, srcCol()], F.batches, { title: '各批次里重入相关的变化' });
  tbl('t8-more', [{ h: '探针', f: r => r.id }, { h: '问题', f: r => r.q }, srcCol()], F.probes, { title: '相关实测', intro: F.adr + '（' + F.adr_src + '）' });
  tbl('t8-more', [{ h: '事件来源', f: r => r.source }, { h: '事件', f: r => r.events }, srcCol()], F.event_sources, { title: '唤醒来自哪里' });
}

/* ---------- figure 9 ---------- */
function fig9() {
  const F = PR.fig9_principles, W = 1200, c = mkSvg('f9', W, 1100), L = c.L;
  const LW = 578, RX0 = 606, BW = 284;
  function pmeasure(p, w, o) {
    const title = wrap(p.slug, w - 16 - (o.tag ? tw(o.tag, 9) + 10 : 0), 11, true);
    const body = wrap(o.text, w - 16, 11, false);
    const foot = o.foot ? wrap(o.foot, w - 16, 10, false) : [];
    return { title, body, foot, h: 10 + title.length * 14 + body.length * 14 + foot.length * 12.5 + 8 };
  }
  function pbox(p, x, y, w, o, hh) {
    const m = pmeasure(p, w, o); const g = S('g', { class: 'k-pr' }, L.node);
    R(g, x, y, w, hh || m.h, { dash: o.dash });
    TL(g, x + 8, y + 16, m.title, { size: 11, mono: true, cls: 'b', lh: 14 });
    if (o.tag) { const tw2 = tw(o.tag, 9) + 7; R(g, x + w - tw2 - 4, y + 4, tw2, 13, { cls: 'tagbg', r: 3 }); T(g, x + w - tw2 + -0.5, y + 14, o.tag, { size: 9, cls: 't2' }); }
    TL(g, x + 8, y + 16 + m.title.length * 14, m.body, { size: 11, lh: 14 });
    TL(g, x + 8, y + 16 + m.title.length * 14 + m.body.length * 14, m.foot, { size: 10, cls: 'tm', lh: 12.5 });
    tip(g, o.tip);
  }
  function pairRows(list, x0, y, optsOf) { // two boxes per row, one height per row
    for (let i = 0; i < list.length; i += 2) {
      const pair = [list[i], list[i + 1]].filter(Boolean).map(p => ({ p, o: optsOf(p) }));
      const hh = Math.max(...pair.map(q => pmeasure(q.p, BW, q.o).h));
      pair.forEach((q, j) => pbox(q.p, x0 + j * (BW + 10), y, BW, q.o, hh));
      y += hh + 8;
    }
    return y;
  }
  T(L.node, 0, 18, 'MMW 自有 12 条 · 索引组 Pipeline · B1', { size: 14, cls: 'hd' });
  T(L.node, RX0, 18, 'pstack 23 条 · 五组 · B1 14 条 + 按需 9 条（B3）', { size: 14, cls: 'hd' });
  let y = pairRows(F.mmw_principles, 0, 30, p => ({ text: p.rule_zh, foot: '吸收 ' + p.absorbs.join('、') + ' · 被点名 ' + p.named_by.length + ' 处', tip: `principle-${p.slug}\n${p.rule_zh}\n理由出处：${p.why_src}\n被谁点名：${p.named_by.join('、')}\n吸收：${p.absorbs.join('、')}${p.distinct_from ? '\n' + p.distinct_from : ''}${p.boundaries ? '\n' + p.boundaries : ''}${p.note ? '\n' + p.note : ''}${srcOf(p)}` }));
  let ry = 30;
  const bySlug = Object.fromEntries(F.pstack_principles.map(p => [p.slug, p]));
  for (const gdef of F.pstack_groups.filter(g => g.group !== 'Pipeline')) {
    T(L.node, RX0, ry + 14, `${gdef.group} · ${gdef.count}`, { size: 12, cls: 'b' }); ry += 22;
    ry = pairRows(gdef.members.map(m => bySlug[m]).filter(Boolean), RX0, ry, p => { const catches = (p.catches || []).concat((p.catches_partial || []).map(x => x + '（部分）')); return { text: p.gloss_zh, dash: p.batch === 'B3', tag: p.batch, foot: (catches.length ? '接住 ' + catches.join('、') : '不对应 MMW 已有规则'), tip: `principle-${p.slug}（${p.group} · ${p.batch}）\n${p.gloss_zh}\n接住：${catches.join('、') || '—'}\n点名它的：${(p.named_by || []).join('、')}${p.extra_named_by ? '；' + p.extra_named_by.join('、') : ''}${p.local_note ? '\n本地限定：' + p.local_note : ''}${p.conflict ? '\n冲突：' + p.conflict : ''}${p.mechanical ? '\n机械改动：' + p.mechanical : ''}${p.note ? '\n' + p.note : ''}${srcOf(p)}` }; });
    ry += 4;
  }
  // priority ladder in the left column
  y += 18; const PL = F.priority_ladder;
  T(L.node, 0, y + 14, '冲突时谁赢：四级优先级（## Autonomy 第一条）', { size: 14, cls: 'hd' }); y += 26;
  const kinds = ['nt', 'mode', 'playbook', 'principle'], STEP = 26, LVW = LW - 3 * STEP;
  PL.levels.forEach((lv, i) => {
    const x = i * STEP; const g = S('g', { class: kc(kinds[i]) }, L.node);
    const nl = wrap(lv.note, LVW - 20, 10.5, false); const h = 26 + nl.length * 13 + 6;
    R(g, x, y, LVW, h);
    T(g, x + 10, y + 18, `${lv.rank}　${lv.layer}`, { size: 12.5, cls: 'b' });
    TL(g, x + 10, y + 34, nl, { size: 10.5, cls: 't2', lh: 13 });
    tip(g, lv.layer + '\n' + lv.note + srcOf(PL));
    if (i < PL.levels.length - 1) {
      const vx = x + 12, ny = y + h + 22;
      edge(c, [[vx, y + h + 1], [vx, ny + 12], [x + STEP - 1, ny + 12]], 'route', {});
      T(L.node, vx + 12, y + h + 15, '高于下一层', { size: 10, cls: 'tm lbl' });
    }
    y += h + 22;
  });
  y -= 8;
  const CG = PL.capability_gates; const gg = S('g', { class: 'k-cap' }, L.node);
  const gl = [CG.rule, '人在场：' + CG.attended, '无人会话：' + CG.unattended, '例：' + CG.example, '宿主闸门：' + CG.host_gate_example, CG.how_vs_order].map(t => wrap(t, LW - 20, 10.5, false));
  const gh = 30 + gl.reduce((a, l) => a + l.length * 13 + 4, 0);
  R(gg, 0, y, LW, gh, { dash: true });
  T(gg, 10, y + 18, '能力技能自带的人工闸门（不在这条链里）', { size: 12, cls: 'b' });
  let gy = y + 36; gl.forEach(l => { TL(gg, 10, gy, l, { size: 10.5, cls: 't2', lh: 13 }); gy += l.length * 13 + 4; });
  y += gh + 8;
  const ol = wrap('上层赢。' + PL.origin, LW, 10.5, false); TL(L.node, 0, y + 12, ol, { size: 10.5, cls: 'tm', lh: 14 }); y += ol.length * 14 + 8;
  c.done(Math.max(y, ry) + 6);
  // 9b matrix: short column names; full names in the note under the header and in tooltips
  const CM = F.citation_matrix; const RLW = 290, CW2 = 34; const W2 = RLW + CM.columns.length * CW2 + 80;
  const SHORT = { 'P17/P18': 'P17/P18', import: 'Import a component', b3_imports: 'B3–B5 导入', writing_code: 'writing-code 等', design_contract: 'design-pages 等', coding_standards: 'CODING_STANDARDS.md' };
  const c2 = mkSvg("f9b", W2, 1100), L2 = c2.L; const HH = 214;
  T(L2.node, 0, 16, '列头上方色条 = 组件类型（颜色见页首图例；虚线 = pstack）', { size: 10.5, cls: 'tm' });
  CM.columns.forEach((col, i) => {
    const x = RLW + i * CW2 + CW2 / 2; const g = S('g', { class: kc(col.type === 'repo-doc' ? 'nt' : col.type) }, L2.node);
    R(g, x - CW2 / 2 + 2, HH - 8, CW2 - 4, 6, { r: 2, dash: col.pstack });
    const lab = col.id === 'P17/P18' ? 'P17/P18' : (SHORT[col.id] || ((/^P\d/.test(col.id) ? col.id + ' ' : '') + col.label));
    const t = T(g, x + 3, HH - 14, lab, { size: 10.5, mono: isMono(lab) });
    t.setAttribute('transform', `rotate(-60 ${x + 3} ${HH - 14})`);
    tip(g, (/^P\d/.test(col.id) ? col.id + ' ' : '') + col.label);
  });
  let y2 = HH + 4;
  const cellMap = {}; CM.cells.forEach(cl => (cellMap[cl.principle + '|' + cl.col] = cellMap[cl.principle + '|' + cl.col] || []).push(cl));
  CM.rows_order.forEach((slug, ri) => {
    if (ri === 0 || ri === 12) {
      if (ri === 12) { S('line', { x1: 0, x2: W2, y1: y2 + 3, y2: y2 + 3, style: 'stroke:var(--ink2);stroke-width:1.2' }, L2.bg); y2 += 6; }
      T(L2.node, 4, y2 + 13, ri === 0 ? 'MMW 自有 12' : 'pstack 23', { size: 11, cls: 'b' }); y2 += 18;
    }
    S('rect', { x: 0, y: y2, width: W2, height: 18, class: ri % 2 ? 'cellbg' : 'lbg' }, L2.bg);
    const isB3 = bySlug[slug] && bySlug[slug].batch === 'B3';
    T(L2.node, RLW - 8, y2 + 13, slug + (isB3 ? ' ·B3' : ''), { size: 10.5, mono: true, anchor: 'end', cls: isB3 ? 'tm' : '' });
    CM.columns.forEach((col, i) => {
      const cl = cellMap[slug + '|' + col.id]; if (!cl) return;
      const g = S('g', { class: 'k-pr' }, L2.node);
      S('circle', { cx: RLW + i * CW2 + CW2 / 2, cy: y2 + 9, r: 5.2, class: 'dot' }, g);
      tip(g, `${slug} ← ${col.label}\n在：${cl.map(x => x.where).join('；')}\n出处：${cl.map(x => x.src).join('；')}`);
    });
    y2 += 18;
  });
  y2 += 10;
  const notes = CM.columns.filter(col => SHORT[col.id] && SHORT[col.id] !== col.label).map(col => col.id === 'P17/P18' ? { ...col, label: 'P17 session-pickup / P18 pause-safely（按需，D6）' } : col).map(col => `${SHORT[col.id]} = ${col.label}`);
  const nl = wrap('列名全称：' + notes.join('；'), W2 - 4, 10.5, false); TL(L2.node, 0, y2 + 10, nl, { size: 10.5, cls: 'tm', lh: 14 });
  c2.done(y2 + nl.length * 14 + 12);
}
function sec9Tables() {
  const F = PR.fig9_principles;
  tbl('t9-more', [{ h: '原则', f: r => 'principle-' + r.slug }, { h: '规则', f: r => r.rule_zh + (r.boundaries ? '\n' + r.boundaries : '') }, { h: '理由出处', f: r => r.why_src }, { h: '被谁点名', f: r => r.named_by }, { h: '吸收', f: r => r.absorbs }, { h: '说明', f: r => [r.distinct_from, r.note].filter(Boolean).join('；') }, srcCol()], F.mmw_principles, { title: 'MMW 自有 12 条', intro: F.mmw_principles_notes.map(n => n.text).join(' ') });
  tbl('t9-more', [{ h: '原则', f: r => r.slug }, { h: '组 · 批次', f: r => r.group + ' · ' + r.batch }, { h: '中文短释', f: r => r.gloss_zh }, { h: '接住的 MMW 规则', f: r => (r.catches || []).concat((r.catches_partial || []).map(x => x + '（部分）')) }, { h: '点名它的', f: r => (r.named_by || []).concat(r.extra_named_by || []) }, { h: '说明', f: r => [r.local_note, r.conflict, r.mechanical, r.note].filter(Boolean).join('；') }, srcCol()], F.pstack_principles, { title: 'pstack 23 条', intro: F.pstack_batches.mechanical + '。' + F.pstack_batches.why_file_not_skill + '。覆盖：' + F.pc_coverage.direct + '；' + F.pc_coverage.partial + '；' + F.pc_coverage.total_pc + '。' });
  tbl('t9-more', [{ h: '编号', f: r => r.pc }, { h: '规则', f: r => r.rule }, { h: '去处', f: r => r.to }], F.not_principles.items, { title: '不建成原则的候选', intro: F.not_principles.src });
  tbl('t9-more', [{ h: '#', f: r => r.n }, { h: '情形', f: r => r.name }, { h: '处理', f: r => r.rule }, { h: '例', f: r => r.example || '' }], F.overlap_rules.items, { title: '与 MMW 已有规则重合时的五条处理', intro: F.overlap_rules.src });
  const FM = F.format;
  list('t9-more', ['位置：' + FM.location, 'frontmatter：' + FM.frontmatter, '正文：' + FM.body, '怎么读：' + FM.reading, '方向：' + FM.direction, '调用方：' + FM.callers, '引用：' + FM.citation, '接受的写法：' + FM.parse_forms.join('、'), '索引行：' + FM.index_line, '索引分组：' + FM.index_groups, '索引首句：' + FM.index_first_line, 'Non-negotiables 首句：' + FM.non_negotiables_first, '门槛：' + FM.threshold, ...FM.unattended_trace.map(u => `无人会话的痕迹 · ${u.role}：${u.where}`)], { title: '原则文件的格式与引用（' + FM.src + '）' });
  const PL = F.priority_ladder;
  list('t9-more', [...PL.unattended_outlets.map(u => `无人出路 · ${u.role}：${u.outlet}`), '无人触发：' + PL.unattended_trigger, '人在场总是先问：' + PL.attended_always_ask.join('；'), '人在场直接做：' + PL.attended_just_do, '与 shared.md 规则 11 的划界：' + PL.rule11_boundary, '冲突例：' + PL.conflict_example, PL.replaces_constant], { title: 'mode ## Autonomy 与优先级（' + PL.src + '）' });
  const SM = F.shared_md;
  list('t9-more', [SM.what, ...SM.division.map(d => d.layer + '：' + d.owns), SM.citation, SM.writing_the_reply, SM.priority, SM.only_copy, SM.pstack_autonomy_conflict, ...SM.r14_segments.map(s => `shared.md ${s.segment}：${s.kind} → ${s.maps_to}`)], { title: '与你的全局规则 shared.md 的关系（' + SM.src + '）' });
  list('t9-more', [{ text: F.risk.text, src: F.risk.src }, { text: F.citation_matrix.note }, { text: '导入组件点名原则的条数（只有条数）：' + F.citation_matrix.imported_counts.items.map(i => i.component + ' ' + i.principles).join('、'), src: F.citation_matrix.imported_counts.src }, ...PR.gaps.map(g => '来源缺口：' + g)], { title: '其余' });
}
