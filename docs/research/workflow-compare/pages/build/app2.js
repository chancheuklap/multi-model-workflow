/* ---------- figure 3: directory trees ---------- */
function ell(s, maxW, size, mono) { s = String(s); if (tw(s, size, mono) <= maxW) return s; let o = ''; for (const ch of s) { if (tw(o + ch + '…', size, mono) > maxW) break; o += ch; } return o + '…'; }
function fig3() {
  const groups = [['mmw-v2', 'f3', 'mmw-v2/（技能、脚本、子树）'], ['repo_root', 'f3b', '本仓库根'], ['home_mmw', 'f3c', '~/.mmw/（本机状态与配置）'], ['consumer_repo', 'f3d', '消费仓库']];
  const allRows = [];
  groups.forEach(([k, host, title], gi) => {
    const W = 1200, c = mkSvg(host, W, 1100), L = c.L;
    const NX = 0, NW = 440, AX = 560, AW = W - AX - 2;
    const reg = { now: [], after: [] };
    function row(p, n, x, y, w, side, path) {
      const full = path + n.name;
      allRows.push({ side: side === 'now' ? '现在' : '升级后', path: full, kind: KZH[n.kind] || (n.kind === 'source' ? '子树' : n.kind === 'doc' ? '文档' : n.kind === 'state' ? '状态' : n.kind === 'test' ? '测试' : '其他'), note: n.note || '', move: side === 'now' ? (n.goes_to ? '→ ' + n.goes_to : '') : (n.from ? '← ' + n.from : ''), batch: n.batch || '', origin: n.origin || '', src: n.src || '' });
      if (n.type === 'note') { const ls = wrap(n.name + (n.note ? '：' + n.note : ''), w, 11, false); TL(p, x, y + 12, ls, { size: 11, cls: 'tm', lh: 14 }); return ls.length * 14 + 4; }
      const g = S('g', { class: kc(n.kind) }, p);
      const rect = R(g, x, y, w, 10, { soft: n.type === 'dir', dash: n.origin === 'ps', r: 4 });
      const tags = [OTAG[n.origin], n.origin === 'moved' ? '搬' : null, n.batch].filter(Boolean);
      const tagsW = tags.reduce((a, t) => a + tw(t, 9) + 9, 0);
      let tx = x + w - 5;
      for (let i = tags.length - 1; i >= 0; i--) { const t = tags[i], tw2 = tw(t, 9) + 7; tx -= tw2; R(g, tx, y + 4, tw2, 13, { cls: 'tagbg', r: 3 }); T(g, tx + 3.5, y + 14, t, { size: 9, cls: 't2' }); tx -= 2; }
      const mono = isMono(n.name), avail = w - 16 - tagsW;
      const one = side === 'now' ? (n.goes_to ? '→ ' + n.goes_to : (n.note || '')) : (n.note || (n.from ? '← ' + n.from : ''));
      const pills = side === 'after' && n.name === 'playbooks/' && n.note ? n.note.split('：')[1].split('；')[0].split(/\s+/).filter(Boolean) : null;
      let cy = y + 4;
      const nw = tw(n.name, 11.5, mono);
      const two = (t, w0) => { const ls = wrap(t, w0, 10.5, false); return ls.length <= 2 ? ls : [ls[0], ell(t.slice(ls[0].length).trimStart(), w0, 10.5, false)]; };
      if (one && !pills && nw <= avail * 0.62 && tw(one, 10.5, false) <= avail - nw - 10) { // name and the whole note on one row
        T(g, x + 8, cy + 12, n.name, { size: 11.5, mono, cls: 'b' });
        T(g, x + 16 + nw, cy + 12, one, { size: 10.5, cls: side === 'now' && n.goes_to ? 't2' : 'tm' });
        cy += 17;
      } else {
        const nl = wrap(n.name, avail, 11.5, mono); TL(g, x + 8, cy + 12, nl, { size: 11.5, mono, cls: 'b', lh: 15 }); cy += nl.length * 15 + 2;
        if (pills) {
          const f = flow(g, x + 8, cy, w - 16, pills.map(t => { const ps = /\(ps\)$/.test(t); return { text: t.replace('(ps)', ''), kind: 'playbook', mono: true, size: 10, dash: ps, tags: ps ? ['ps'] : [] }; }), { gap: 3 }); cy += f.h + 4;
          const extra = n.note.split('；').slice(1).join('；') + (n.from ? '　← ' + n.from : '');
          const el = two(extra, w - 16); TL(g, x + 8, cy + 10, el, { size: 10.5, cls: 'tm', lh: 14 }); cy += el.length * 14 + 1;
        } else if (one) { const ol = two(one, w - 16); TL(g, x + 8, cy + 10, ol, { size: 10.5, cls: side === 'now' && n.goes_to ? 't2' : 'tm', lh: 14 }); cy += ol.length * 14 + 1; }
      }
      cy += 3;
      tip(g, `${full}${n.note ? '\n' + n.note : ''}${n.goes_to ? '\n去向：' + n.goes_to : ''}${n.from ? '\n来自：' + n.from : ''}${n.batch ? '\n批次：' + n.batch : ''}${srcOf(n)}`);
      reg[side].push({ n, x, y, w, h: 0, rect, path: full, get h2() { return +rect.getAttribute('height'); } });
      if (n.children && n.children.length) { for (const ch of n.children) cy += row(g, ch, x + 10, cy, w - 20, side, n.type === 'dir' ? full : path) + 4; cy += 3; }
      rect.setAttribute('height', cy - y);
      return cy - y;
    }
    T(L.node, NX, 16, '现在', { size: 15, cls: 'hd' });
    T(L.node, AX, 16, '升级后（第 2 批完成时）', { size: 15, cls: 'hd' });
    if (gi === 0) T(L.node, AX + 190, 16, A.fig3.scope_note, { size: 10.5, cls: 'tm' });
    const y0 = 30;
    const h1 = row(L.node, A.fig3.now[k], NX, y0, NW, 'now', '');
    const h2 = row(L.node, A.fig3.after[k], AX, y0, AW, 'after', '');
    edge(c, [[NX + NW + 2, y0 + 12], [AX - 2, y0 + 12]], 'install', { label: '升级', cands: [[(NX + NW + AX) / 2, y0 + 2]] });
    // connectors: where each part of dispatch/ and verify-ticket/ goes
    const keyOf = r => r.n.name.split(/[\s、]+/).map(t => t.replace(/\/$/, '')).filter(t => t.length > 3);
    const targets = reg.after.filter(r => r.n.type !== 'note');
    const plNames = (A.fig3.after['mmw-v2'].children.find(x => x.name === 'skills/') ? 1 : 0);
    const pbNode = targets.find(r => r.n.name === 'playbooks/');
    reg.now.filter(r => /skills\/(dispatch|verify-ticket)\/./.test(r.path) && r.n.goes_to).forEach(r => {
      const gt = r.n.goes_to; const hits = new Set();
      targets.forEach(t => { if (t.n.name === 'playbooks/') return; for (const key of keyOf(t)) { if (gt.includes(key) && !(key === 'mmw' )) { hits.add(t); break; } } });
      if (pbNode && /run-a-night|land-one-ticket|work-a-ticket|accept-the-night/.test(gt)) hits.add(pbNode);
      if (/mode ## Re-entry/.test(gt)) { const sk = targets.find(t => t.path.endsWith('skills/mmw/SKILL.md')); if (sk) hits.add(sk); }
      if (/mmw\/scripts\/（整目录平移）/.test(gt)) { const sc = targets.find(t => t.path.endsWith('mmw/scripts/')); if (sc) { hits.clear(); hits.add(sc); } }
      [...hits].forEach(t => {
        const a = [NX + NW + 1, r.y + 11], b = [AX - 1, t.y + 11], mx = (a[0] + b[0]) / 2;
        const kind = { playbook: 'wake', reference: 'read', script: 'run', config: 'config', capability: 'call', mode: 'route' }[t.n.kind] || 'install';
        const g = S('g', null, L.edge);
        S('path', { d: `M${a[0]},${a[1]} C${mx},${a[1]} ${mx},${b[1]} ${b[0]},${b[1]}`, class: 'e e-' + kind, style: 'stroke-width:1.1;stroke-dasharray:none;opacity:.75', 'marker-end': `url(#${c.id}-${kind})` }, g);
        S('circle', { cx: a[0] + 2, cy: a[1], r: 2.4, class: 'mk-' + kind }, g);
        tip(g, `${r.path} → ${t.path}\n${r.n.goes_to}`);
      });
    });
    let yb = y0 + Math.max(h1, h2) + 10;
    c.done(yb + 4);
    if (gi === 0) htmlLegend(host, [...[['wake', '→ playbook'], ['read', '→ reference'], ['run', '→ 脚本'], ['config', '→ 配置'], ['call', '→ 能力技能'], ['route', '→ mode']].map(([k, t]) => [k, t, 'stroke-dasharray:none']), { html: '<span class="hint">细线只画 dispatch/ 与 verify-ticket/ 的各部分去了哪里，线色是目标的类型；其余盒子的去向写在盒子里的「→」后</span>' }], { title: '细线' });
    const cap = $(host).previousElementSibling && $(host).previousElementSibling.classList.contains('swipe') ? $(host).previousElementSibling : $(host);
    cap.insertAdjacentHTML('beforebegin', `<div class="subfig">${gi + 1}/4　${esc(title)}</div>`);
  });
  tbl('t3-moves', [{ h: '从', f: r => r.from }, { h: '到', f: r => r.to }, { h: '怎么搬', f: r => r.label }, srcCol()], A.fig3.moves, { title: '20 处搬迁' });
  tbl('t3-moves', [{ h: '', f: r => r.side }, { h: '路径', f: r => r.path }, { h: '类型', f: r => r.kind }, { h: '说明', f: r => r.note }, { h: '去向 / 来处', f: r => r.move }, { h: '批次', f: r => r.batch }, srcCol()], allRows, { fold: '目录逐项（图里每个盒子的完整说明）' });
  list('t3-moves', A.not_found.map(n => n.item + '：' + n.status), { fold: '图 1、图 3 的数据在来源里找不到或对不上的项' });
}

/* ---------- generic sequence diagram ---------- */
function seq(hostId, lanes, rows, o = {}) {
  const W = o.W || 1200, c = mkSvg(hostId, W, o.minW || 1100), L = c.L;
  const PX = o.phaseW == null ? 104 : o.phaseW, n = lanes.length, lw = (W - PX - 6) / n;
  const lx = i => PX + lw * i + lw / 2;
  const idx = {}; lanes.forEach((l, i) => idx[l.id] = i);
  let y = 4, hh = 0;
  lanes.forEach((l, i) => {
    const w = lw - 14, x = lx(i) - w / 2; const g = S('g', { class: kc(l.kind) }, L.node);
    const ls = wrap(l.label, w - 12, 12, isMono(l.label)); const ws = l.who ? wrap(l.who, w - 12, 10, false) : [];
    const h = 10 + ls.length * 15 + ws.length * 12 + 4;
    R(g, x, y, w, h); TL(g, lx(i), y + 17, ls, { size: 12, cls: 'b', anchor: 'middle', mono: isMono(l.label), lh: 15 });
    TL(g, lx(i), y + 17 + ls.length * 15 - 2, ws, { size: 10, cls: 'tm', anchor: 'middle', lh: 12 });
    tip(g, l.tip || ''); hh = Math.max(hh, h);
  });
  y += hh + 16; const top = y;
  let lastPhase = null;
  for (const r of rows) {
    if (r.type === 'hdr') {
      y += 8; S('line', { x1: 0, x2: W, y1: y, y2: y, class: 'sep' }, L.bg);
      T(L.node, 4, y + 17, r.text, { size: 12.5, cls: 'hd' });
      if (r.sub) T(L.node, 8 + tw(r.text, 12.5) + 10, y + 17, r.sub, { size: 10.5, cls: 'tm' });
      y += 28; continue;
    }
    if (o.phases && r.phase !== lastPhase) {
      S('line', { x1: 0, x2: W, y1: y - 2, y2: y - 2, class: 'sep' }, L.bg);
      TL(L.node, 2, y + 12, wrap(r.phase, PX - 10, 11, false), { size: 11, cls: 'b', lh: 13 });
      lastPhase = r.phase; y += 4;
    }
    const a = lx(idx[r.from]), b = lx(idx[r.to]);
    const self = r.from === r.to;
    const start = self ? a + 18 : Math.min(a, b) + 8;
    const avail = W - 6 - start;
    const size = r.mono ? 10.5 : 11;
    const txt = (r.cert ? '（推断）' : '') + r.text;
    const ls = wrap(txt, self ? Math.min(avail, 2 * lw) : Math.min(avail, Math.max(Math.abs(b - a) - 16, 2 * lw - 16)), size, r.mono);
    const g = S('g', null, L.node);
    const textY = y + 11;
    ls.forEach((ln, i) => T(g, start, textY + i * 13.5, ln, { size, mono: r.mono && !/[一-鿿]/.test(ln) ? true : false, cls: 'lbl' }));
    let ay = textY + (ls.length - 1) * 13.5 + 8;
    const k = ek(r.kind);
    if (r.n != null) { // circled message number in the gutter left of the first lane, same numbering as the table under the figure
      const ng = S('g', null, L.node); const nx = PX + 12;
      S('circle', { cx: nx, cy: ay, r: 9, style: 'fill:var(--surface);stroke:var(--ink2);stroke-width:1.1' }, ng);
      T(ng, nx, ay + 3.8, String(r.n), { size: r.n > 9 ? 9.5 : 10.5, anchor: 'middle', cls: 'b' });
    }
    if (self) {
      ay += 2;
      S('path', { d: `M${a},${ay - 4} L${a + 12},${ay - 4} L${a + 12},${ay + 5} L${a + 2},${ay + 5}`, class: 'e e-' + k, 'marker-end': `url(#${c.id}-${k})` }, g);
    } else {
      S('path', { d: `M${a},${ay} L${b + (b > a ? -2 : 2)},${ay}`, class: 'e e-' + k, 'marker-end': `url(#${c.id}-${k})` }, g);
      S('circle', { cx: a, cy: ay, r: 2.5, class: 'mk-' + k }, g);
    }
    let yy = ay + 4;
    if (r.step) { T(g, start, yy + 10, r.step, { size: 9.5, mono: true, cls: 'tm lbl' }); yy += 12; }
    tip(g, [r.text, r.step ? '步骤：' + r.step : '', r.note, r.cert ? '确定性：推断' + (r.certNote ? '（' + r.certNote + '）' : '') : '', r.src ? '出处：' + r.src : ''].filter(Boolean).join('\n'));
    y = yy + 8;
  }
  lanes.forEach((l, i) => S('line', { x1: lx(i), x2: lx(i), y1: top - 12, y2: y, class: 'lane' }, L.bg));
  c.done(y + 6);
  if (o.legend) htmlLegend(hostId, o.legend, { title: '线的含义' });
  return c;
}
const SEQKIND = { say: 'say', command: 'run', event: 'evt', wake: 'wake', prompt: 'prompt', read: 'read', self: 'return', call: 'call', refusal: 'refusal', return: 'return', note: 'return' };
function fig4() {
  const laneKind = { you: 'nt', orch: 'playbook', scripts: 'script', worker: 'playbook', reviewer: 'playbook', tracker: 'nt' };
  const lanes = PB.lanes.map(l => ({ id: l.id, label: l.label, who: l.playbook ? l.playbook : (l.id === 'tracker' ? '票上的事件' : l.id === 'scripts' ? 'dispatch.sh · relay · watchdog · ticket_state.py · hook' : '人'), kind: laneKind[l.id], tip: l.who + (l.note ? '\n' + l.note : '') + srcOf(l) }));
  const seqTxt = t => String(t).replace(/seq (\d+)/g, '第 $1 条');
  const rows = PB.night_sequence.map(m => ({ n: m.seq, from: m.from, to: m.to, kind: SEQKIND[m.kind], text: seqTxt(m.text), step: m.step, note: m.note, cert: m.certainty === '推断', certNote: m.certainty_note, src: m.src, phase: m.phase, mono: /^[\x00-\x7F]/.test(m.text) && m.kind !== 'say' }));
  const leg = [['say', '人话（粗实线）'], ['run', '运行命令'], ['prompt', '启动提示词'], ['evt', '写 / 读票上的事件（空心圆头）'], ['wake', '唤醒（点划线，一行带指针）'], ['read', '读文件'], ['self', '本泳道内的动作（折回小钩）'], { html: '<span class="nm">1</span>消息编号，与图下「一夜的 63 条消息逐条」的 # 列相同' }];
  seq('f4', lanes, rows, { phases: true, legend: leg, phaseW: 132 });
  const seqStep = Object.fromEntries(PB.night_sequence.map(m => [m.seq, m.step]));
  const joinTxt = j => { const m = String(j).match(/^seq (\d+)(（(.*)）)?$/); if (!m) return j; return (m[3] || seqStep[+m[1]] || '') + '（图 4 第 ' + m[1] + ' 条）'; };
  const brows = [];
  PB.night_branches.forEach(b => { brows.push({ type: 'hdr', text: b.label, sub: '回到：' + joinTxt(b.joins) }); b.steps.forEach(s => brows.push({ from: s.from, to: s.to, kind: /^(REFUSAL|NO_QUESTION)/.test(s.text) ? 'deny' : SEQKIND[s.kind], text: s.text, note: s.note, cert: s.certainty === '推断', src: s.src, mono: /^[\x00-\x7F]/.test(s.text) })); });
  seq('f4b', lanes, brows, { phaseW: 132, legend: [...leg.slice(0, 7), ['deny', 'hook 拒绝并给出路（紫色短虚线，REFUSAL / NO_QUESTION 开头的一行）']] });
}
function sec4Tables() {
  const sp = PB.start_prompts;
  tbl('t4-more', [{ h: '角色', f: r => r.role }, { h: '今天', f: r => r.today || '' }, { h: '升级后（一行）', f: r => r.text }, { h: '说明', f: r => r.note || '' }, srcCol()],
    [{ role: 'worker', today: sp.today.worker, ...sp.worker }, { role: 'reviewer', today: sp.today.reviewer, ...sp.reviewer, note: '（推断）' + sp.reviewer.note }, { role: 'researcher', ...sp.researcher }, { role: 'advisor', today: sp.today.advisor, ...sp.advisor }, { role: 'axis 子代理', ...sp.axis_subagent }],
    { title: '启动提示词：今天与升级后', intro: sp.today.note + ' 数据文件 `' + sp.data_file.path + '`：' + sp.data_file.contents.join('、') + '。' + sp.data_file.why });
  tbl('t4-more', [{ h: '发出方', f: r => r.sender }, { h: '一行的形状', f: r => r.text }, { h: '规则与说明', f: r => (r.certainty ? '（' + r.certainty + '）' : '') + (r.rule || r.note || '') }, srcCol()], PB.wake_line_shapes, { title: '送进会话的那一行', open: true });
  const oe = PB.orchestrator_events_reference;
  list('t4-more', [...oe.contents.map(x => ({ text: x.part + (x.fixes ? '（修 ' + x.fixes + '）' : ''), src: x.src })), { text: '「*」：' + oe.orchestrator_wakes_star, src: oe.src_star }], { title: oe.file + '（' + oe.shared_by.join('、') + ' 共用的唤醒表）' });
  tbl('t4-more', [{ h: '#', f: r => r.seq }, { h: '阶段', f: r => r.phase }, { h: '从 → 到', f: r => { const ln = Object.fromEntries(PB.lanes.map(l => [l.id, l.label])); return ln[r.from] + ' → ' + ln[r.to]; } }, { h: '类型', f: r => ({ command: '运行命令', event: '写 / 读事件', prompt: '启动提示词', read: '读文件', say: '人话', self: '本泳道内的动作', wake: '唤醒' })[r.kind] || r.kind }, { h: '内容', f: r => String(r.text).replace(/seq (\d+)/g, '第 $1 条') }, { h: '步骤', f: r => r.step || '' }, { h: '说明', f: r => [r.certainty ? '（' + r.certainty + '）' : '', r.note || '', r.certainty_note || ''].join(' ') }, srcCol()], PB.night_sequence, { fold: '一夜的 63 条消息逐条' });
}

/* ---------- figure 5: day playbooks ---------- */
function fig5() {
  const W = 1360, c = mkSvg('f5', W, 1150), L = c.L;
  const pbs = Object.fromEntries(PB.playbooks.map(p => [p.slug, p]));
  let y = 4;
  const mg = S('g', { class: 'k-mode' }, L.node);
  R(mg, 0, y, W, 40);
  T(mg, 10, y + 17, 'mode mmw · ## Playbooks 路由表：每张卡片都是路由表的一行', { size: 13, cls: 'b' });
  T(mg, 10, y + 33, '行格式：' + unq(PB.route_table_notes.row_format) + '　没有匹配：B1–B2 先列步骤，B3 起交给 figure-it-out', { size: 10.5, cls: 't2' });
  tip(mg, PB.route_table_notes.execution_protocol_first_paragraph + '\n\n没有匹配（B1–B2）：' + PB.route_table_notes.no_match_B1_B2 + '\n没有匹配（B3）：' + PB.route_table_notes.no_match_B3 + '\n\n别名：\n' + PB.route_table_notes.aliases.join('\n') + '\n\n' + PB.route_table_notes.private_line);
  y += 48;
  const dc = group(L.node, 0, y, W, '直接能力行：路由表直接指向能力技能，不经 playbook（' + PB.route_direct_capability.length + ' 行）', PB.route_direct_capability.map(r => ({ text: r.trigger + ' → ' + r.target, kind: 'capability', mono: false, size: 10.5, dash: r.batch === 'B3', tags: [r.batch.length <= 3 ? r.batch : r.batch.slice(0, 2)], tip: `${r.trigger} → ${r.target}${r.distinct_from ? '\nDistinct from：' + r.distinct_from : ''}${r.then ? '\n之后：' + r.then : ''}\n批次：${r.batch}${srcOf(r)}` })), { kind: 'mode' });
  c.P.add(0, y, W, dc.h);
  y += dc.h + 8;
  // three rows: from an idea to something doable; making the change; exits
  const grid = {
    'triage-an-issue': [0, 0], 'research-a-question': [1, 0], 'map-a-large-effort': [2, 0], 'design-a-ui': [3, 0], 'prototype': [4, 0], 'pause-safely': [5, 0], 'session-pickup': [6, 0], 'onboard-a-repository': [7, 0],
    'write-a-spec-and-tickets': [2, 1], 'make-a-small-change': [3, 1], 'bug-fix': [4, 1], '/improve-codebase-architecture': [5, 1], 'authoring-a-skill': [6, 1], 'import-a-component': [7, 1],
    'accept-the-night': [0, 2], 'run-a-night': [1, 2], 'land-one-ticket': [2, 2], 'deliver-a-change': [3, 2], 'promote-a-change': [4, 2], 'eval': [6, 2], 'pull-an-upstream': [7, 2]
  };
  const NW = 156, PITCH = 170, colX = i => 5 + i * PITCH + (PITCH - NW) / 2;
  const calls = {}; PB.handoff_edges.filter(e => e.kind === 'calls').forEach(e => (calls[e.from] = calls[e.from] || []).push(e));
  const nodes = {};
  for (const slug in grid) {
    const p = pbs[slug]; const g = S('g', null, L.node);
    let h;
    if (!p) {
      const gg = S('g', { class: 'k-nt' }, g); const ls = wrap(slug, NW - 16, 11, true); const sl = wrap('用户触发的技能，告诉用户运行', NW - 16, 10, false);
      const hh = 10 + ls.length * 14 + sl.length * 12 + 6; R(gg, 0, 0, NW, hh, { dash: true, soft: true });
      TL(gg, 8, 15, ls, { size: 11, mono: true, cls: 'b', lh: 14 }); TL(gg, 8, 12 + ls.length * 14 + 4, sl, { size: 10, cls: 'tm', lh: 12 });
      h = hh; tip(gg, 'bug-fix 的 Choose the route：没有能锁住 bug 的 seam 时，告诉用户运行它');
    } else {
      const dash = /pstack 原文（按需导入）/.test(p.origin) || /pstack 原文，不改/.test(p.origin) || ['B3', 'B4', 'B5'].includes(p.batch) || /^按需/.test(p.batch);
      const gg = S('g', { class: 'k-pb' }, g); const rect = R(gg, 0, 0, NW, 10, { dash });
      const sl = wrap(p.slug, NW - 16, 11, true), dy = (sl.length - 1) * 13;
      TL(gg, 8, 16, sl, { size: 11, mono: true, cls: 'b', lh: 13 });
      T(gg, 8, 30 + dy, `${p.name_zh} · ${p.id} · ${p.batch.split('（')[0]}`, { size: 10, cls: 'tm' });
      let cy = 38 + dy;
      const cl = (calls[slug] || []).map(e => ({ text: e.to, kind: 'capability', mono: true, size: 9.5, tip: `${e.label}（${e.at_step}）${e.note ? '\n' + e.note : ''}${srcOf(e)}` }));
      if (cl.length) { const f = flow(gg, 8, cy, NW - 16, cl, { gap: 3 }); cy += f.h + 6; }
      rect.setAttribute('height', cy + 2); h = cy + 2;
      tip(gg, `${p.name}（${p.name_zh}）\n任务：${p.task_type}\n入口：${p.entry}\n${p.distinct_from && p.distinct_from.length ? 'Distinct from：' + p.distinct_from.join('；') + '\n' : ''}${Array.isArray(p.steps) && p.steps.length ? '步骤：' + p.steps.map(s => s.title).join(' → ') + '\n' : ''}${p.ownership ? '所有权：' + p.ownership + '\n' : ''}交付：${p.deliverable}${srcOf(p)}`);
    }
    nodes[slug] = { g, h, col: grid[slug][0], row: grid[slug][1] };
  }
  const rowH = [0, 1, 2].map(r => Math.max(...Object.values(nodes).filter(n => n.row === r).map(n => n.h)));
  const TOPCH = 76, TMCH = 132, MBCH = 124;
  const rowY = [y + TOPCH, 0, 0]; rowY[1] = rowY[0] + rowH[0] + TMCH; rowY[2] = rowY[1] + rowH[1] + MBCH;
  for (const s in nodes) { const n = nodes[s]; n.x = colX(n.col); n.y = rowY[n.row]; n.w = NW; n.g.setAttribute('transform', `translate(${n.x},${n.y})`); c.P.add(n.x, n.y, NW, n.h); }
  // row bands behind the cards
  const rowName = ['从想法到可做', '动手改', '出口：交给夜、单票、交付'];
  const N = s => nodes[s];
  const P = (s, side, off = 0) => { const n = N(s); return side === 't' ? [n.x + NW / 2 + off, n.y - 1] : side === 'b' ? [n.x + NW / 2 + off, n.y + n.h + 1] : side === 'l' ? [n.x - 1, n.y + off] : [n.x + NW + 1, n.y + off]; };
  const Tb = rowY[0] + rowH[0], Mb = rowY[1] + rowH[1], Bb = rowY[2] + rowH[2];
  const TOP = k => rowY[0] - 14 - k * 20, TM = k => Tb + 16 + k * 20, MB = k => Mb + 16 + k * 20, BOT = k => Bb + 16 + k * 20;
  const via = (p0, ly, p1) => [p0, [p0[0], ly], [p1[0], ly], p1];
  const straight = (p0, p1) => [p0, [p0[0], p1[1]]];
  const EK = { handoff: 'route', starts: 'run', tell_user: 'user' };
  const ed = {}; PB.handoff_edges.forEach(e => ed[e.from + '>' + e.to] = e);
  function draw(from, to, pts, o = {}) {
    const e = ed[from + '>' + to]; const kind = EK[e.kind] || 'route';
    const g = S('g', null, L.edge);
    S('path', { d: 'M' + pts.map(p => p.join(',')).join(' L'), class: 'halo' }, g);
    const d = 'M' + pts.map(p => p.join(',')).join(' L');
    S('path', { d, class: 'e e-' + kind + (['B3', 'B4', '按需'].includes(e.batch) ? ' later' : ''), 'marker-end': o.noHead ? null : `url(#${c.id}-${kind})` }, g);
    tip(g, `${e.from} → ${e.to}：${e.label}\n在：${e.at_step || ''}${e.note ? '\n' + e.note : ''}\n批次：${e.batch}${srcOf(e)}`);
    if (o.nolabel) return;
    let best = null, bl = -1; // label on the longest horizontal segment, else the longest segment
    for (let i = 0; i < pts.length - 1; i++) { const hz = pts[i][1] === pts[i + 1][1]; const l = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) * (hz ? 3 : 1); if (l > bl) { bl = l; best = i; } }
    const a = pts[best], b = pts[best + 1]; const hz = a[1] === b[1];
    const txt = e.label + (['B3', 'B4'].includes(e.batch) ? '（' + e.batch + '）' : '');
    const cands = hz ? [0.5, 0.35, 0.65, 0.2, 0.8].map(t => [a[0] + (b[0] - a[0]) * t, a[1]]) : [0.5, 0.3, 0.7].map(t => { const w0 = tw(txt, 10.5) + 8; return [a[0] + w0 / 2 + 6, a[1] + (b[1] - a[1]) * t]; });
    label(c, txt, o.cands || cands, { lmax: 170 });
  }
  // top channel
  draw('map-a-large-effort', 'research-a-question', via(P('map-a-large-effort', 't', -45), TOP(0), P('research-a-question', 't', 45)));
  draw('map-a-large-effort', 'design-a-ui', via(P('map-a-large-effort', 't', 45), TOP(0), P('design-a-ui', 't', -45)));
  draw('prototype', 'design-a-ui', via(P('prototype', 't', -45), TOP(0), P('design-a-ui', 't', 45)));
  draw('map-a-large-effort', 'prototype', via(P('map-a-large-effort', 't', 15), TOP(2), P('prototype', 't', -15)));
  draw('design-a-ui', 'pause-safely', via(P('design-a-ui', 't', 15), TOP(1), P('pause-safely', 't', -15)));
  { const p0 = P('session-pickup', 't', 0); const e = ed['session-pickup>mode']; const g = S('g', null, L.edge); S('path', { d: `M${p0[0]},${p0[1]} L${p0[0]},${TOP(2) - 6}`, class: 'e e-route later', 'marker-end': `url(#${c.id}-route)` }, g); tip(g, e.label + '（' + e.at_step + '）' + srcOf(e)); label(c, '剩余工作按路由表 → mode（按需）', [[p0[0] + 70, TOP(1)], [p0[0], TOP(1)]]); }
  // T-M channel
  draw('research-a-question', 'map-a-large-effort', via(P('research-a-question', 'b', 45), TM(0), P('map-a-large-effort', 'b', -55)));
  draw('design-a-ui', 'map-a-large-effort', via(P('design-a-ui', 'b', -55), TM(0), P('map-a-large-effort', 'b', 55)));
  draw('map-a-large-effort', 'write-a-spec-and-tickets', straight(P('map-a-large-effort', 'b', 0), P('write-a-spec-and-tickets', 't', 0)));
  draw('design-a-ui', 'write-a-spec-and-tickets', via(P('design-a-ui', 'b', -20), TM(1), P('write-a-spec-and-tickets', 't', 20)));
  draw('prototype', 'write-a-spec-and-tickets', via(P('prototype', 'b', -40), TM(2), P('write-a-spec-and-tickets', 't', 45)));
  draw('write-a-spec-and-tickets', 'prototype', via(P('write-a-spec-and-tickets', 't', 60), TM(2) + 9, P('prototype', 'b', -25)), { cands: [[P('write-a-spec-and-tickets', 't', 60)[0] + 100, TM(2) + 22]] });
  draw('triage-an-issue', 'write-a-spec-and-tickets', via(P('triage-an-issue', 'b', 30), TM(3), P('write-a-spec-and-tickets', 't', -40)));
  draw('prototype', 'make-a-small-change', via(P('prototype', 'b', 20), TM(4), P('make-a-small-change', 't', 40)));
  draw('triage-an-issue', 'accept-the-night', straight(P('triage-an-issue', 'b', -30), P('accept-the-night', 't', -30)));
  // M-B channel
  draw('write-a-spec-and-tickets', 'make-a-small-change', via(P('write-a-spec-and-tickets', 'b', 65), MB(0), P('make-a-small-change', 'b', -40)));
  draw('bug-fix', '/improve-codebase-architecture', via(P('bug-fix', 'b', 40), MB(0), P('/improve-codebase-architecture', 'b', -40)));
  draw('import-a-component', 'authoring-a-skill', via(P('import-a-component', 'b', -40), MB(0), P('authoring-a-skill', 'b', 40)));
  draw('bug-fix', 'write-a-spec-and-tickets', via(P('bug-fix', 'b', -40), MB(1), P('write-a-spec-and-tickets', 'b', 40)));
  draw('write-a-spec-and-tickets', 'land-one-ticket', straight(P('write-a-spec-and-tickets', 'b', 0), P('land-one-ticket', 't', 0)));
  draw('write-a-spec-and-tickets', 'run-a-night', via(P('write-a-spec-and-tickets', 'b', -40), MB(2), P('run-a-night', 't', 0)));
  draw('authoring-a-skill', 'eval', straight(P('authoring-a-skill', 'b', 20), P('eval', 't', 20)), { cands: [[P('eval', 't', 20)[0] + 60, P('eval', 't', 20)[1] - 16]] });
  draw('import-a-component', 'pull-an-upstream', straight(P('import-a-component', 'b', 45), P('pull-an-upstream', 't', 45)), { cands: [[P('pull-an-upstream', 't', 45)[0] - 40, MB(4)]] });
  // one bus for the five "交付" hand-offs into deliver-a-change
  {
    const yb = MB(3), dx = P('deliver-a-change', 't', 30)[0];
    const srcs = [['make-a-small-change', P('make-a-small-change', 'b', 30), 'b'], ['bug-fix', P('bug-fix', 'b', 0), 'b'], ['authoring-a-skill', P('authoring-a-skill', 'b', -20), 'b'], ['import-a-component', P('import-a-component', 'b', 0), 'b'], ['pull-an-upstream', P('pull-an-upstream', 't', -20), 't']];
    const xmax = Math.max(...srcs.map(s => s[1][0]));
    const g = S('g', null, L.edge);
    const segs = [`M${dx},${yb} L${xmax},${yb}`, ...srcs.map(([s, p]) => `M${p[0]},${p[1]} L${p[0]},${yb}`)];
    segs.forEach(d => { S('path', { d, class: 'halo' }, g); });
    segs.forEach(d => { S('path', { d, class: 'e e-route' }, g); });
    S('path', { d: `M${dx},${yb} L${dx},${N('deliver-a-change').y - 1}`, class: 'e e-route', 'marker-end': `url(#${c.id}-route)` }, g);
    srcs.forEach(([s, p]) => S('circle', { cx: p[0], cy: yb, r: 2.6, class: 'mk-route' }, g));
    tip(g, '交付（5 条）：' + srcs.map(s => s[0] + '「' + ed[s[0] + '>deliver-a-change'].at_step + '」').join('、') + '\n出处：' + [...new Set(srcs.map(s => ed[s[0] + '>deliver-a-change'].src))].join('；'));
    label(c, '交付（五份 playbook 在黑点处汇合）', [[(dx + xmax) / 2 + 40, yb], [(dx + xmax) / 2 + 120, yb]], { lmax: 420 });
  }
  // bottom channel
  draw('run-a-night', 'accept-the-night', via(P('run-a-night', 'b', -40), BOT(0), P('accept-the-night', 'b', 40)));
  draw('deliver-a-change', 'promote-a-change', via(P('deliver-a-change', 'b', 40), BOT(0), P('promote-a-change', 'b', -40)), { cands: [[P('promote-a-change', 'b', 0)[0], BOT(0)], [P('promote-a-change', 'b', 60)[0], BOT(0)]] });
  { // approved retro proposals: a short stub with the two targets named
    const p0 = P('accept-the-night', 'b', -40); const e1 = ed['accept-the-night>write-a-spec-and-tickets'];
    const g = S('g', null, L.edge); S('path', { d: `M${p0[0]},${p0[1]} L${p0[0]},${BOT(2)}`, class: 'e e-route', 'marker-end': `url(#${c.id}-route)` }, g);
    tip(g, `批准的 retro 提议 → write-a-spec-and-tickets、authoring-a-skill\n在：${e1.at_step}\n批次：${e1.batch}${srcOf(e1)}`);
    label(c, '批准的 retro 提议 → write-a-spec-and-tickets / authoring-a-skill', [[p0[0] + 150, BOT(2) + 10]], { lmax: 320 });
  }
  y = BOT(3) + 6;
  // imported group + not imported
  const imp = PB.playbooks.filter(p => p.group === 'import');
  const gi = group(L.node, 0, y, 960, 'B3–B5 按需导入的 pstack playbook（路由表各批加行）', imp.map(p => ({ text: p.slug, kind: 'playbook', mono: true, dash: true, tags: [p.batch], tip: `${p.name}（${p.name_zh}）\n任务：${p.task_type}\nDistinct from：${(p.distinct_from || []).join('；')}\n依赖：${(p.deps || []).join('、')}\n冲突与处理：${p.conflict}${srcOf(p)}` })), { dash: true, sub: '按需：你点名时才导入（R18 §17 D6）；eval 也画在上面的图里；从 B1 推迟的 session-pickup、pause-safely 画在上面第一排' });
  const gn = group(L.node, 976, y, W - 976, 'pstack 不导入', PB.not_imported_playbooks.filter(p => !p.d2).map(p => ({ text: p.slug, kind: 'nt', mono: true, dim: true, tip: p.why + srcOf(p) })), { sub: '理由见表；表里另有随 D2 不导入的三份' });
  y += Math.max(gi.h, gn.h) + 16;
  c.done(y);
  htmlLegend('f5', [['route', '交接给另一份 playbook'], ['run', '另起一个会话'], ['user', '告诉用户运行'], { html: '<span class="sw k-cap" style="width:18px;height:12px"></span>卡片内小块 = 按名调用的能力技能' }, { html: '<span class="sw k-pb ps" style="width:18px;height:12px"></span>虚线卡片与虚线：pstack 按需导入后才有（线上标 B3 的是那一批）' }, { html: '<span class="dotx" style="background:var(--c-mode);width:7px;height:7px"></span>黑点汇合处：多份 playbook 交给同一处' }], { title: '线的含义' });
}
function cub(a, b, c2, d, t) { const u = 1 - t; return [u * u * u * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c2[0] + t * t * t * d[0], u * u * u * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c2[1] + t * t * t * d[1]]; }
function pbPrinciples(r) { // same source as figure 9's matrix and figure 1's table
  if (!/^P\d+$/.test(r.id)) return r.principles_named || r.deps || [];
  const col = (r.id === 'P17' || r.id === 'P18') ? null : r.id;
  const set = [...(r.principles_named || [])];
  if (col) citeRows().filter(x => x.col === col).forEach(x => { if (!set.includes(x.principle)) set.push(x.principle); });
  return set.map(p => p === 'redesign-from-first-principles' ? p + '（与 attack-the-premise 合写，R18 §5.3）' : p);
}
function sec5Tables() {
  tbl('t5-cat', [{ h: '编号', w: '48px', f: r => r.id }, { h: 'playbook', w: '150px', f: r => r.slug }, { h: '中文', w: '76px', f: r => r.name_zh }, { h: '批次', w: '70px', f: r => r.batch }, { h: '来源', w: '96px', f: r => r.origin }, { h: '任务类型', w: '170px', f: r => r.task_type }, { h: '入口', w: '176px', f: r => r.entry }, { h: 'Distinct from', w: '190px', f: r => r.distinct_from || [] }, { h: '所有权行', w: '170px', f: r => r.ownership || '（' + (r.ownership_src ? (/^不写/.test(r.ownership_src) ? r.ownership_src : '不写：' + r.ownership_src) + (r.id === 'P8' ? '，R18 §3.3 P8' : '') : '不写：来源未给出') + '）' }, { h: '出处', w: '100px', src: true, f: r => r.src || '' }], PB.playbooks, { title: `playbook 总目录（${PB.playbooks.length} 份记录：MMW 16 + 私有 3 + pstack 按需 13）`, open: true, minW: 1100, intro: 'B2 后：' + PB.playbook_totals.after_B2 + '；全部批次后：' + PB.playbook_totals.after_all + '。每份的步骤、点名的原则与交付物在下一张折叠表。' });
  const stL = p => Array.isArray(p.steps) ? (p.steps.length ? p.steps.map(s => `${s.n}. ${s.title}`) : (p.known_steps ? p.known_steps.map(k => '已知：' + k.n + ' ' + k.text) : ['来源未给出'])) : [p.steps];
  tbl('t5-cat', [{ h: '编号', w: '64px', f: r => r.id }, { h: 'playbook', w: '200px', f: r => r.slug }, { h: '步骤', lines: true, f: stL }, { h: '点名的原则', w: '26%', lines: true, f: r => pbPrinciples(r) }, { h: '交付物', w: '18%', f: r => r.deliverable || '' }, srcCol()], PB.playbooks, { title: 'playbook × 步骤、点名的原则与交付物', minW: 900 });
  tbl('t5-more', [{ h: 'pstack playbook', f: r => r.slug }, { h: '不导入的理由', f: r => r.why }, srcCol()], PB.not_imported_playbooks, { title: `pstack 里不导入的 ${PB.not_imported_playbooks.length} 份（后 3 份随 R18 §17 D2）` });
  tbl('t5-more', [{ h: '用户说', f: r => r.trigger }, { h: '直接交给', f: r => r.target }, { h: 'Distinct from', f: r => r.distinct_from || '' }, { h: '批次', f: r => r.batch }, srcCol()], PB.route_direct_capability, { title: '路由表的直接能力行' });
  const rn = PB.route_table_notes;
  list('t5-more', ['行格式：`' + rn.row_format + '`', '执行协议首段：' + rn.execution_protocol_first_paragraph, '没有匹配（B1–B2）：' + rn.no_match_B1_B2, '没有匹配（B3 起）：' + rn.no_match_B3, ...rn.aliases.map(a => '别名：' + a), rn.private_line, ...Object.entries(rn.rows_by_batch).map(([k, v]) => k + '：' + v)], { title: '路由表的写法（' + rn.src + '）' });
  tbl('t5-more', [{ h: '从', f: r => r.from }, { h: '到', f: r => r.to }, { h: '类型', f: r => ({ handoff: '交接', calls: '按名调用', starts: '另起会话', tell_user: '告诉用户运行', route: '路由' })[r.kind] || r.kind }, { h: '标签', f: r => r.label }, { h: '在哪一步', f: r => r.at_step || '' }, { h: '批次', f: r => r.batch }, { h: '说明', f: r => r.note || '' }, srcCol()], PB.handoff_edges, { fold: `图 5 的 ${PB.handoff_edges.length} 条边逐条（含路由行与夜间内部的交接）` });
  list('t5-more', PB.missing, { fold: 'playbook 数据在来源里缺的项' });
}

/* ---------- figure 6: work-a-ticket ---------- */
function fig6() {
  const W = 1400, c = mkSvg('f6', W, 1228), L = c.L;
  const SK = PB.playbook_skeleton; const LW = 360;
  // file frame
  const fg = S('g', { class: 'k-pb' }, L.node);
  const fr = R(fg, 0, 4, LW, 10, { soft: true });
  T(fg, 10, 22, 'mmw/playbooks/work-a-ticket.md', { size: 12, mono: true, cls: 'b' });
  let y = 32;
  for (const b of SK.blocks) {
    const g = S('g', { class: 'k-pb' }, fg);
    const bl = wrap(b.block.replace(/\n/g, ' '), LW - 36, 10, true);
    const pl = wrap(b.purpose, LW - 36, 10.5, false);
    const el = wrap('work-a-ticket：' + b.example_work_a_ticket, LW - 36, 10, false);
    const h = 18 + bl.length * 12 + pl.length * 13 + el.length * 12 + 12;
    R(g, 10, y, LW - 20, h, { dash: !b.required });
    T(g, 18, y + 15, b.label + (b.required ? ' · 必需' : ' · 可选') + (b.mmw_only ? ' · MMW 多出' : ''), { size: 11.5, cls: 'b' });
    let cy = y + 28;
    TL(g, 18, cy, bl, { size: 10, mono: true, cls: 't2', lh: 12 }); cy += bl.length * 12;
    TL(g, 18, cy + 2, pl, { size: 10.5, lh: 13 }); cy += pl.length * 13 + 2;
    TL(g, 18, cy + 2, el, { size: 10, cls: 'tm', lh: 12 });
    tip(g, `${b.block}\n${b.purpose}\n例：${b.example_work_a_ticket}${b.checked_by ? '\n核对：' + b.checked_by : ''}${srcOf(b)}`);
    y += h + 6;
  }
  fr.setAttribute('height', y - 4 + 4);
  const leftH = y + 4;
  // matrix
  const MX = LW + 24; const cols = [['step', '步骤', 200], ['skills', '能力技能', 180], ['scripts', '脚本命令', 230], ['principles', '点名的原则', 252], ['events', '留下的事件', 150]];
  let x = MX; const cx = {}; cols.forEach(([k, lab, w]) => { cx[k] = [x, w]; T(L.node, x + 6, 20, lab, { size: 12, cls: 'b' }); x += w; });
  let ry = 30;
  const kindOf = { skills: 'capability', scripts: 'script', principles: 'principle', events: 'nt' };
  PB.work_a_ticket_matrix.rows.forEach((r, i) => {
    const g = S('g', null, L.node); const hs = [];
    // step cell
    const sl = wrap(`${r.n}. ${r.title}`, cx.step[1] - 12, 11.5, true);
    TL(g, cx.step[0] + 6, ry + 16, sl, { size: 11.5, mono: true, cls: 'b', lh: 14 }); let sh = 8 + sl.length * 14;
    if (r.wakes_here) { const wl = wrap('唤醒到这里：' + r.wakes_here.join('、'), cx.step[1] - 12, 10, false); TL(g, cx.step[0] + 6, ry + 10 + sh + 4, wl, { size: 10, cls: 'tm', lh: 12 }); sh += wl.length * 12 + 4; }
    hs.push(sh + 8);
    for (const k of ['skills', 'scripts', 'principles', 'events']) {
      const [x0, w] = cx[k]; const vals = r[k] || [];
      if (!vals.length) {
        if (k === 'events') { const tl = wrap(r.trace ? '不留事件 · 痕迹：' + r.trace : '—', w - 12, 10, false); TL(g, x0 + 6, ry + 16, tl, { size: 10, cls: 'tm', lh: 12 }); hs.push(tl.length * 12 + 12); }
        continue;
      }
      let vy = ry + 6; // one chip per line; a parenthesised note goes on a second, smaller line
      vals.forEach(v => {
        const mm = v.match(/^(.*?)\s*（(.*)）$/); const main = mm ? mm[1] : v, note = mm ? mm[2] : null;
        const mono = isMono(main);
        const ml = wrap(main, w - 26, 10, mono), nl = note ? wrap(note, w - 26, 9.5, false) : [];
        const hh = 6 + ml.length * 13 + nl.length * 12 + 2;
        const cg = S('g', { class: kc(kindOf[k]) }, g); R(cg, x0 + 6, vy, w - 12, hh, { r: 4 });
        TL(cg, x0 + 13, vy + 13, ml, { size: 10, mono, lh: 13 });
        if (nl.length) TL(cg, x0 + 13, vy + 13 + ml.length * 13 - 1, nl, { size: 9.5, cls: 'tm', lh: 12 });
        vy += hh + 3;
      });
      hs.push(vy - ry + 4);
    }
    const h = Math.max(...hs, 30);
    const bg = S('rect', { x: MX, y: ry, width: x - MX, height: h, class: i % 2 ? 'cellbg' : 'lbg' }, L.bg);
    tip(g, `${r.n}. ${r.title}\n${r.text}\nwhere 在这一步：${r.where_line}${r.closeout_check ? '\n' + r.closeout_check : ''}${srcOf(r)}`);
    ry += h;
  });
  T(L.node, MX, ry + 16, PB.work_a_ticket_matrix.note, { size: 10.5, cls: 'tm' });
  c.done(Math.max(leftH, ry + 26));
  // 6b five jumps
  const c2 = mkSvg('f6b', 1100, 1000), L2 = c2.L; const FJ = PB.five_jumps_today;
  const pos = { implement: [240, 200], dispatch: [20, 30], 'verify-ticket': [460, 30], 'ui-acceptance': [20, 370], 'code-review': [460, 370] };
  const BW = 210, box = {};
  FJ.jumps.forEach(j => {
    const [x0, y0] = pos[j.skill]; const g = S('g', { class: 'k-cap' }, L2.node);
    const hl = wrap(j.what_it_holds, BW - 16, 10, false).slice(0, 3);
    const bl = wrap('故障：' + j.breakage, BW - 16, 10, false).slice(0, 3);
    const h = 26 + hl.length * 12 + bl.length * 12 + 10;
    R(g, x0, y0, BW, h);
    T(g, x0 + 8, y0 + 17, j.skill, { size: 12.5, mono: true, cls: 'b' });
    TL(g, x0 + 8, y0 + 32, hl, { size: 10, cls: 't2', lh: 12 });
    TL(g, x0 + 8, y0 + 32 + hl.length * 12 + 2, bl, { size: 10, cls: 'risk', lh: 12 });
    tip(g, `${j.skill}\n装着：${j.what_it_holds}\n跳转：${j.jump}\n故障：${j.breakage}\n升级后：${j.goes_to}${srcOf(j)}`);
    box[j.skill] = { x: x0, y: y0, w: BW, h }; c2.P.add(x0, y0, BW, h);
  });
  const ctr = b => [b.x + b.w / 2, b.y + b.h / 2];
  const clipTo = (b, from) => { const [cx0, cy0] = ctr(b); const dx = from[0] - cx0, dy = from[1] - cy0; const s = Math.min((b.w / 2 + 3) / Math.abs(dx || 1e-6), (b.h / 2 + 3) / Math.abs(dy || 1e-6)); return [cx0 + dx * s, cy0 + dy * s]; };
  FJ.cycle_edges.forEach(e => {
    const a = box[e.from], b = box[e.to]; const pa = ctr(a), pb = ctr(b);
    const back = FJ.cycle_edges.some(x => x.from === e.to && x.to === e.from);
    const nx = -(pb[1] - pa[1]), ny = pb[0] - pa[0]; const nl = Math.hypot(nx, ny) || 1; const off = back ? 22 : 0;
    const A0 = clipTo(a, [pb[0] + nx / nl * off, pb[1] + ny / nl * off]), B0 = clipTo(b, [pa[0] + nx / nl * off, pa[1] + ny / nl * off]);
    const s = [A0[0] + nx / nl * off, A0[1] + ny / nl * off], t = [B0[0] + nx / nl * off, B0[1] + ny / nl * off];
    edge(c2, [s, t], 'refusal', { label: e.label, cands: [[(s[0] + t[0]) / 2, (s[1] + t[1]) / 2]], lmax: 150 });
  });
  T(L2.node, 20, 16, FJ.title, { size: 13, cls: 'hd' });
  // after
  const ax = 760, ay = 60, aw = 320; const ag = S('g', { class: 'k-pb' }, L2.node);
  const steps = PB.work_a_ticket_matrix.rows.map(r => `${r.n}. ${r.title}`);
  R(ag, ax, ay, aw, 40 + steps.length * 17 + 10);
  T(ag, ax + 10, ay + 20, 'mmw/playbooks/work-a-ticket.md', { size: 12, mono: true, cls: 'b' });
  steps.forEach((s, i) => T(ag, ax + 14, ay + 42 + i * 17, s, { size: 11, mono: true }));
  TL(L2.node, ax, ay - 26, wrap('升级后：' + FJ.after.replace('升级后：', ''), aw, 12, false), { size: 12, cls: 'hd', lh: 15 });
  edge(c2, [[680, 250], [ax - 4, 250]], 'route', { label: '升级后', cands: [[720, 236]] });
  c2.done(Math.max(...Object.values(box).map(b => b.y + b.h), ay + 40 + steps.length * 17 + 10) + 12);
}
function sec6Tables() {
  tbl('t6-more', [{ h: '规则簇', f: r => r.name }, { h: '内容', f: r => r.text }, { h: '点名的原则', f: r => r.principles || [] }, { h: '唤醒', f: r => r.wake || '' }, srcCol()], PB.work_a_ticket_rule_clusters, { title: 'work-a-ticket 的规则簇（常设规则，不进待办）' });
  tbl('t6-more', [{ h: '#', f: r => r.n }, { h: '步骤', f: r => r.title }, { h: '做什么', f: r => r.text }, { h: 'where 在这一步印什么', f: r => r.where_line }, { h: '没有事件时的痕迹', f: r => r.trace || '' }, srcCol()], PB.work_a_ticket_matrix.rows, { title: '11 步逐条' });
  tbl('t6-more', [{ h: '写法规则', f: r => r.rule }, { h: '依据', f: r => r.origin || r.checked_by || '' }, srcCol()], PB.playbook_skeleton.writing_rules, { title: 'playbook 的写法规则' });
  const ep = PB.playbook_skeleton.execution_protocol;
  list('t6-more', ['人在场：' + ep.attended, ...ep.unattended.map(u => `无人 · ${u.role}：${u.where}`), { text: 'pstack 的骨架：' + PB.playbook_skeleton.pstack_origin, src: PB.playbook_skeleton.pstack_origin_src }], { title: '执行协议（' + ep.src + '）' });
  tbl('t6-more', [{ h: '#', f: r => r.n }, { h: '技能', f: r => r.skill }, { h: '装着 worker 的哪一段', f: r => r.what_it_holds }, { h: '跳到哪里', f: r => r.jump }, { h: '已核实的故障', f: r => r.breakage }, { h: '升级后去处', f: r => r.goes_to }, srcCol()], PB.five_jumps_today.jumps, { title: '今天的五个跳点', intro: PB.five_jumps_today.cycle_edges_note });
}
