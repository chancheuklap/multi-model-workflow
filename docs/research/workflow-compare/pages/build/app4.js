/* ---------- shared card helper: box with title + wrapped lines ---------- */
function unq(s) { return String(s == null ? '' : s).replace(/`/g, '').replace(/\*\*/g, ''); }
function card(p, x, y, w, o = {}) {
  const g = S('g', { class: kc(o.kind || 'nt') }, p);
  const rect = R(g, x, y, w, 10, { dash: o.dash, soft: o.soft, r: 5 });
  const tags = (o.tags || []).filter(Boolean);
  const tagW = tags.reduce((a, t) => a + tw(t, 9) + 9, 0);
  let cy = y + 6;
  if (o.title) {
    const ts = o.tsize || 12, tm = o.tmono != null ? o.tmono : isMono(o.title);
    const tl = wrap(o.title, w - 16 - tagW, ts, tm);
    tl.forEach((ln, i) => T(g, x + 8, cy + ts + i * (ts + 3), ln, { size: ts, mono: tm, cls: 'b' }));
    cy += tl.length * (ts + 3) + 3;
  }
  let tx = x + w - 4;
  for (let i = tags.length - 1; i >= 0; i--) { const t = tags[i]; const tw2 = tw(t, 9) + 7; tx -= tw2; R(g, tx, y + 4, tw2, 13, { cls: 'tagbg', r: 3 }); T(g, tx + 3.5, y + 14, t, { size: 9, cls: 't2' }); tx -= 2; }
  if (!o.title && tags.length) cy += 14;
  for (const ln of (o.lines || [])) {
    if (ln == null || ln === '') continue;
    const L0 = typeof ln === 'string' ? { t: ln } : ln;
    const sz = L0.size || 10.5, mono = L0.mono || false, lh = Math.round(sz * 1.3);
    const ls = wrap(unq(L0.t), w - 16 - (L0.indent || 0), sz, mono);
    ls.forEach((l, i) => T(g, x + 8 + (L0.indent || 0), cy + sz + i * lh, l, { size: sz, mono, cls: L0.cls || 't2' }));
    cy += ls.length * lh + (L0.gap || 2);
  }
  const h = Math.max(o.minH || 0, cy - y + 6);
  rect.setAttribute('height', h);
  tip(g, o.tip);
  return { x, y, w, h, g, rect };
}
function mCard(w, o) { // measure height without drawing
  const tmp = S('g', null, null); const r = card(tmp, 0, 0, w, o); return r.h;
}
const bb = (b, s, f = 0.5) => s === 'r' ? [b.x + b.w + 1, b.y + b.h * f] : s === 'l' ? [b.x - 1, b.y + b.h * f] : s === 't' ? [b.x + b.w * f, b.y - 1] : [b.x + b.w * f, b.y + b.h + 1];

/* ---------- figure 10: pstack import pipeline ---------- */
function fig10() {
  const IP = O.import_pipeline, W = 1200, c = mkSvg('f10', W, 1150), L = c.L;
  const ST = Object.fromEntries(IP.stages.map(s => [s.id, s]));
  T(L.node, 0, 15, '主张：' + IP.claim, { size: 12, cls: 't2' });
  const Y0 = 40;
  // A subtree
  const A0 = card(L.node, 0, Y0 + 20, 170, { kind: 'nt', dash: true, tags: ['ps'], title: 'upstream-pstack/', tmono: true,
    lines: [ST.subtree.sub, 'cursor/plugins 的 pstack/ 子目录', { t: '快照 pstack 0.15.4', cls: 'tm' }, { t: 'git subtree split → subtree add --squash（推断，U-13）', cls: 'tm', size: 10 }, { t: 'LICENSE（MIT）随子树保留', cls: 'tm', size: 10 }],
    tip: IP.source_and_install.map(s => s.label + '：' + unq(s.text)).join('\n') + '\n出处：' + ST.subtree.src });
  c.P.add(A0.x, A0.y, A0.w, A0.h);
  // B playbook with six steps
  const BX = 206, BWd = 318; const PIA = IP.playbook_import_a_component;
  const bg = S('g', { class: 'k-pb' }, L.node);
  const bRect = R(bg, BX, Y0, BWd, 10);
  T(bg, BX + 8, Y0 + 17, 'Import a component', { size: 13, cls: 'b' });
  T(bg, BX + 8, Y0 + 31, PIA.file, { size: 10, mono: true, cls: 'tm' });
  T(bg, BX + 8, Y0 + 45, PIA.note, { size: 10, cls: 'tm' });
  tip(bg, PIA.file + '\n' + PIA.note + '\n出处：' + ST.playbook.src);
  let by = Y0 + 54; const stepBox = {};
  PIA.steps.forEach(s => {
    const extra = s.n === 2 ? PIA.entry_questions.map(q => `${'①②③④⑤⑥'[q.n - 1]} ${q.label}`) : [];
    const sub = unq(s.detail);
    const r = card(bg, BX + 8, by, BWd - 16, { kind: 'playbook', soft: true, title: `${s.n}. ${s.title}  ${s.label}`, tsize: 11, tmono: false,
      lines: [{ t: sub, size: 10, cls: 'tm' }, ...extra.map(e => ({ t: e, size: 10, cls: 't2', indent: 6, gap: 0 }))],
      tip: `${s.n}. ${s.title}（${s.label}）\n${sub}${s.n === 2 ? '\n' + PIA.entry_questions.map(q => `${q.n}. ${q.label}：${unq(q.q)}（${q.src}）`).join('\n') : ''}\n出处：${s.src}` });
    stepBox[s.n] = r; by += r.h + 5;
  });
  bRect.setAttribute('height', by - Y0 + 4);
  const B0 = { x: BX, y: Y0, w: BWd, h: by - Y0 + 4 }; c.P.add(B0.x, B0.y, B0.w, B0.h);
  // C importer
  const CX0 = 566, CWd = 232; const IM = IP.importer;
  const cg = S('g', { class: 'k-sc' }, L.node);
  const cRect = R(cg, CX0, Y0, CWd, 10);
  T(cg, CX0 + 8, Y0 + 17, 'import_component.py', { size: 13, mono: true, cls: 'b' });
  TL(cg, CX0 + 8, Y0 + 31, wrap(ST.importer.path, CWd - 16, 10, false), { size: 10, cls: 'tm', lh: 12 });
  let cy = Y0 + 31 + wrap(ST.importer.path, CWd - 16, 10, false).length * 12 + 2;
  T(cg, CX0 + 8, cy + 8, '做（全部是机械改写）', { size: 10.5, cls: 'b' }); cy += 14;
  const f1 = flow(cg, CX0 + 8, cy, CWd - 16, IM.does.map(d => ({ text: d.label, kind: 'script', mono: /^-/.test(d.label), size: 10.5, tip: unq(d.text) + '\n出处：' + d.src })), { gap: 4 }); cy += f1.h + 10;
  T(cg, CX0 + 8, cy + 8, '冲突时拒绝并点名', { size: 10.5, cls: 'b' }); cy += 14;
  const f2 = flow(cg, CX0 + 8, cy, CWd - 16, IM.conflict_rules.map(r => ({ text: r.case, kind: 'nt', size: 10, tip: r.case + '：' + unq(r.rule) + '\n出处：' + r.src })), { gap: 4 }); cy += f2.h + 10;
  T(cg, CX0 + 8, cy + 8, `扫 ${IM.slot_keywords.length} 个槽位关键词`, { size: 10.5, cls: 'b' }); cy += 14;
  const f3 = flow(cg, CX0 + 8, cy, CWd - 16, IM.slot_keywords.map(k => ({ text: k, kind: 'nt', mono: true, size: 9.5, tip: '槽位关键词（' + IM.slot_keywords_src + '）' })), { gap: 3 }); cy += f3.h + 10;
  const dn = IM.does_not[0]; const dl = wrap('不做：' + dn.label + '。交给跑这份 playbook 的 agent：加一行 pstack-names.md，或做一处判断改动并记账', CWd - 16, 10, false);
  TL(cg, CX0 + 8, cy + 10, dl, { size: 10, cls: 't2', lh: 12.5 }); cy += dl.length * 12.5 + 8;
  cRect.setAttribute('height', cy - Y0 + 4);
  tip(cg, ST.importer.path + '\n' + unq(dn.text) + '\n出处：' + ST.importer.src);
  const C0 = { x: CX0, y: Y0, w: CWd, h: cy - Y0 + 4 }; c.P.add(C0.x, C0.y, C0.w, C0.h);
  // D eight types
  const DX = 846, DWd = W - DX - 2; let dy = Y0; const dBox = [];
  T(L.node, DX, Y0 - 8, '八种类型各自落位（复制 + 机械改写）', { size: 12.5, cls: 'hd' });
  IP.import_types.forEach(t => {
    const r = card(L.node, DX, dy, DWd, { kind: t.kind, dash: true, tags: ['ps'], title: `${t.label}  ·  ${t.type}`, tsize: 11.5, tmono: false,
      lines: [{ t: '→ ' + unq(t.lands_at), size: 10, mono: false, cls: '' }, { t: '登记：' + unq(t.registers), size: 10, cls: 'tm' }, { t: '改写：' + unq(t.mechanical_rewrite), size: 10, cls: 'tm' }],
      tip: `${t.label}（${t.type}）\n落位：${unq(t.lands_at)}\n登记：${unq(t.registers)}\n机械改写：${unq(t.mechanical_rewrite)}\n例：${unq(t.examples)}\n出处：${t.src}` });
    dBox.push(r); c.P.add(r.x, r.y, r.w, r.h); dy += r.h + 6;
  });
  // below B/C: ledger + check + slots
  let ly = Math.max(B0.y + B0.h, C0.y + C0.h) + 46;
  const LG = ST.ledger;
  const led = card(L.node, BX, ly, 300, { kind: 'config', title: 'imports.tsv', tmono: true, lines: [{ t: LG.path, size: 10, cls: 'tm' }, LG.sub, { t: '列：' + LG.columns.join(' · '), size: 10 }], tip: LG.path + '\n' + LG.sub + '\n列：' + LG.columns.join('、') + '\n出处：' + LG.src });
  c.P.add(led.x, led.y, led.w, led.h);
  const CK = ST.check;
  const chk = card(L.node, 0, ly, 170, { kind: 'script', title: 'check_wiring.py', tmono: true, lines: ['+ install.sh --check', { t: CK.sub, cls: 'tm' }], tip: CK.label + '\n' + CK.sub + '\n出处：' + CK.src });
  c.P.add(chk.x, chk.y, chk.w, chk.h);
  const JC = IP.judgement_changes;
  const jb = card(L.node, CX0, ly, CWd, { kind: 'nt', title: `需要判断的改动：全部 ${JC.total} 处`, tsize: 12,
    lines: [{ t: Object.entries(JC.by_batch).map(([k, v]) => `${k}：${v} 处`).join(' · '), cls: '' }, { t: '每处记入 imports.tsv「判断改动」列与 merge-notes/pstack.md', size: 10, cls: 'tm' }, { t: '逐条见下图', size: 10, cls: 'tm' }],
    tip: JC.note + '\n' + JC.items.map(j => `${j.id} ${unq(j.where)}：${unq(j.change)}（${j.batch}）`).join('\n') + '\n' + unq(JC.caveat) + '\n出处：' + JC.items[0].src });
  c.P.add(jb.x, jb.y, jb.w, jb.h);
  // pstack-names.md translation box
  const sy = Math.max(led.y + led.h, chk.y + chk.h, jb.y + jb.h) + 30;
  const SX = 0, SWd = 798; const sg = S('g', { class: 'k-ref' }, L.node); const sRect = R(sg, SX, sy, SWd, 10);
  T(sg, SX + 8, sy + 17, 'pstack-names.md：把 pstack 专有的说法读成 MMW 的对应物', { size: 12.5, cls: 'b' });
  T(sg, SX + 8, sy + 31, ST.slots.path + ` · 共 ${IP.slots.length} 行，这里是主要 ${IP.slots_main_labels.length} 行，全表在图下`, { size: 10, cls: 'tm' });
  const c1 = SX + 8, c2 = SX + 100, c3 = SX + 400, w1 = 88, w2 = 290, w3 = SWd - 400 - 10;
  let ry = sy + 44;
  T(sg, c1, ry + 10, '槽位', { size: 10.5, cls: 'b' }); T(sg, c2, ry + 10, 'pstack 原文里的说法', { size: 10.5, cls: 'b' }); T(sg, c3, ry + 10, 'MMW 读作', { size: 10.5, cls: 'b' }); ry += 16;
  const slotBy = Object.fromEntries(IP.slots.map(s => [s.label, s]));
  IP.slots_main_labels.forEach((lab, i) => {
    const s = slotBy[lab]; if (!s) return;
    const l1 = wrap(lab, w1, 10.5, false), l2 = wrap(unq(s.pstack), w2, 10, false), l3 = wrap(unq(s.mmw), w3, 10, false);
    const n = Math.max(l1.length, l2.length, l3.length), h = n * 12.5 + 8;
    S('rect', { x: SX + 4, y: ry, width: SWd - 8, height: h, class: i % 2 ? 'cellbg' : 'lbg' }, sg);
    const rg = S('g', null, sg);
    TL(rg, c1, ry + 13, l1, { size: 10.5, cls: 'b', lh: 12.5 }); TL(rg, c2, ry + 13, l2, { size: 10, cls: 't2', lh: 12.5 }); TL(rg, c3, ry + 13, l3, { size: 10, lh: 12.5 });
    S('path', { d: `M${c3 - 18},${ry + 9} L${c3 - 6},${ry + 9}`, class: 'e e-read', 'marker-end': `url(#${c.id}-read)` }, rg);
    tip(rg, `${lab}\npstack：${unq(s.pstack)}\nMMW：${unq(s.mmw)}\n依据：${unq(s.basis)}\n出处：${s.src}`);
    ry += h;
  });
  sRect.setAttribute('height', ry - sy + 8);
  const SL = { x: SX, y: sy, w: SWd, h: ry - sy + 8 }; c.P.add(SL.x, SL.y, SL.w, SL.h);
  // edges
  const s1 = stepBox[1], s3 = stepBox[3], s4 = stepBox[4], s5 = stepBox[5];
  edge(c, [[A0.x + A0.w + 1, s1.y + s1.h / 2], bb(s1, 'l', 0.5)], 'install', { label: '拉来源', cands: [[188, s1.y + s1.h / 2 - 11]] });
  edge(c, [bb(s3, 'r', 0.5), [CX0 - 1, s3.y + s3.h / 2]], 'run', { label: '第 3 步运行', cands: [[(BX + BWd + CX0) / 2 - 8, s3.y + s3.h / 2 - 12]] });
  dBox.forEach((d, i) => {
    edge(c, [[CX0 + CWd + 1, C0.y + 40 + i * 8], bb(d, 'l', 0.35)], 'install', { curve: 'h', noHead: false });
  });
  edge(c, [bb(s4, 'l', 0.5), [BX - 20, s4.y + s4.h / 2], [BX - 20, led.y + 20], [BX - 1, led.y + 20]], 'config', { label: '第 4 步登记', cands: [[BX + 36, ly - 20], [BX + 36, ly - 34]] });
  edge(c, [bb(C0, 'b', 0.3), [CX0 + CWd * 0.3, ly - 18], [BX + 280, ly - 18], [BX + 280, led.y - 1]], 'config', { label: '每个外来文件一行', cands: [[BX + 200, ly - 30]] });
  edge(c, [bb(s5, 'l', 0.5), [130, s5.y + s5.h * 0.5], [130, chk.y - 1]], 'check', { label: '第 5 步证明连线', cands: [[70, chk.y - 20], [70, chk.y - 36]] });
  edge(c, [bb(C0, 'b', 0.75), [CX0 + CWd * 0.75, jb.y - 1]], 'return', { label: '判断句不改，交给 agent', cands: [[CX0 + CWd * 0.75, jb.y - 16]] });
  edge(c, [bb(jb, 'b', 0.5), [jb.x + jb.w / 2, SL.y - 1]], 'read', { label: '或加一行 pstack-names.md', cands: [[jb.x + jb.w / 2, SL.y - 14]] });
  // namespace rule note + legend
  let yb = Math.max(SL.y + SL.h, dy) + 14;
  TL(L.node, 0, yb + 10, wrap('命名空间：' + IP.namespace_rule.text + '（' + IP.namespace_rule.src + '）', W - 10, 10.5, false), { size: 10.5, cls: 'tm', lh: 14 });
  yb += wrap('命名空间：' + IP.namespace_rule.text, W - 10, 10.5, false).length * 14 + 12;
  c.done(yb);
  htmlLegend('f10', [['install', '安装 / 导入（复制文件）'], ['run', '运行命令'], ['config', '登记'], ['check', '核对（虚线）'], ['read', '读作 / 查表'], ['return', '交回 agent']], { title: '线的含义' });
}

function fig10b() {
  const IP = O.import_pipeline, PI = IP.pstack_inventory, W = 1200, c = mkSvg('f10b', W, 1100), L = c.L;
  let y = 4;
  // --- part 1: 102 stacked bars
  T(L.node, 0, y + 14, `① pstack 全量 ${PI.total} 项：由什么组成、各去了哪里`, { size: 13, cls: 'hd' }); y += 26;
  const BX = 90, BW = W - BX - 250, unit = BW / PI.total, LGX = BX + BW + 18;
  const compKind = { '原则': 'principle', '其余能力技能': 'capability', 'mode 按节与触发行拆': 'mode', 'playbook': 'playbook', 'mode reference': 'reference', 'mode 脚本（组）': 'script', 'agent': 'reference', 'automation': 'nt' };
  function bar(label, segs, sub) {
    T(L.node, 0, y + 18, label, { size: 12, cls: 'b' });
    let x = BX;
    segs.forEach(s => {
      const w = s.n * unit, g = S('g', { class: kc(s.kind) }, L.node);
      R(g, x + 0.5, y, w - 1, 28, { dash: s.dash, soft: s.soft, r: 2 });
      if (w >= 24) T(g, x + w / 2, y + 18, String(s.n), { size: 11, anchor: 'middle', cls: 'b' });
      tip(g, s.tip); s.x = x; s.w = w; x += w;
    });
    y += 32;
    const small = segs.filter(s => s.w < 40);
    let ly2 = y - 32;
    small.forEach(s => { const g = S('g', { class: kc(s.kind) }, L.node); R(g, LGX, ly2 + 1, 16, 11, { dash: s.dash, soft: s.soft, r: 2 }); T(L.node, LGX + 22, ly2 + 10, s.short + ' ' + s.n, { size: 10, cls: 't2' }); tip(g, s.tip); ly2 += 15; });
    // labels under the bar for the wide segments, staggered to avoid overlap
    const rows = [];
    segs.filter(s => s.w >= 40).forEach(s => {
      const txt = s.short + ' ' + s.n; const tw0 = tw(txt, 10) + 4; let lx = Math.max(BX, Math.min(s.x + s.w / 2 - tw0 / 2, W - tw0));
      let r = 0; while (rows[r] != null && rows[r] > lx - 6) r++;
      rows[r] = lx + tw0;
      const ty = y + 12 + r * 14;
      S('line', { x1: s.x + s.w / 2, x2: s.x + s.w / 2, y1: y - 3, y2: ty - 9, class: 'sep' }, L.bg);
      T(L.node, lx, ty, txt, { size: 10, cls: 't2' });
    });
    y = Math.max(y + rows.length * 14 + 6, ly2 + 4);
    if (sub) { T(L.node, BX, y + 8, sub, { size: 10, cls: 'tm' }); y += 14; }
    y += 8;
  }
  bar('组成', PI.composition.map(s => ({ n: s.count, kind: compKind[s.group] || 'nt', short: s.group, tip: `${s.group}：${s.count}\n${s.path}\n出处：${PI.composition_src}` })), '来源：' + PI.where + '（' + PI.composition_src + '）');
  bar('去向', PI.outcomes.map(o => ({ n: o.count, kind: o.kind === 'other' ? 'nt' : o.kind, dash: o.outcome !== '不导入', soft: o.outcome === '不导入', short: o.outcome === '导入' ? o.what.split('（')[0] : o.outcome, tip: `${o.outcome}：${o.what} ${o.count}\n出处：${PI.outcomes_src}\n合计核对：${PI.outcomes_sum_check}` })), '合计核对：' + PI.outcomes_sum_check + '（' + PI.outcomes_src + '）');
  y += 6;
  // --- part 2: judgement changes by batch
  const JC = IP.judgement_changes;
  T(L.node, 0, y + 14, `② 需要判断的改动：全部批次共 ${JC.total} 处（机械改动不计）`, { size: 13, cls: 'hd' }); y += 26;
  const bats = ['B1', 'B3', 'B4', 'B5'], colW = (W - 3 * 12) / 4; let colH = 0; const top = y;
  bats.forEach((b, i) => {
    const x = i * (colW + 12); const items = JC.items.filter(j => j.batch === b);
    T(L.node, x, y + 13, `${b} · ${JC.by_batch[b]} 处${b !== 'B1' ? '（按需）' : ''}`, { size: 12, cls: 'b' });
    let cy = y + 20;
    if (!items.length) { T(L.node, x, cy + 14, '无', { size: 11, cls: 'tm' }); cy += 20; }
    items.forEach(j => { const r = card(L.node, x, cy, colW, { kind: 'nt', dash: b !== 'B1', title: `${j.id}  ${unq(j.where)}`, tsize: 11, tmono: false, lines: [{ t: unq(j.change), size: 10.5 }], tip: `${j.id} ${unq(j.where)}\n${unq(j.change)}\n批次：${j.batch}\n出处：${j.src}` }); cy += r.h + 6; });
    colH = Math.max(colH, cy - top);
  });
  y = top + colH + 4;
  TL(L.node, 0, y + 10, wrap(unq(JC.caveat) + '（' + JC.caveat_src + '）', W, 10.5, false), { size: 10.5, cls: 'tm', lh: 14 }); y += 34;
  // --- part 3: bug-fix merge example
  const BF = IP.bugfix_merge_example;
  T(L.node, 0, y + 14, '③ 同名 playbook 的合并：bug-fix = pstack 原文 + 插入一步 MMW', { size: 13, cls: 'hd' }); y += 24;
  const own = card(L.node, 250, y, 470, { kind: 'playbook', dash: true, tags: ['ps'], title: '所有权行（原文）', tsize: 11, lines: [{ t: unq(BF.ownership), size: 10.5, mono: false }], tip: unq(BF.ownership) + '\n出处：' + BF.ownership_src });
  y += own.h + 8; const stTop = y;
  // B1 column
  let by = y; T(L.node, 0, by + 12, 'B1–B2 的 MMW 版（5 步）', { size: 11.5, cls: 'b' }); by += 18;
  BF.b1_version_steps.forEach((s, i) => { const r = card(L.node, 0, by, 200, { kind: 'playbook', title: `${i + 1}. ${s}`, tsize: 10.5, tmono: true, tip: 'B1 版步骤（' + BF.b1_version_src + '）' }); by += r.h + 4; });
  edge(c, [[204, stTop + 40], [246, stTop + 40]], 'install', { label: 'B3 换成', cands: [[225, stTop + 24]] });
  TL(L.node, 0, by + 12, wrap('原文依赖 B3 才有：' + BF.depends_on.join('、'), 200, 10, false), { size: 10, cls: 'tm', lh: 12.5 });
  // ps column
  let py = y;
  BF.steps.forEach(s => {
    const ins = s.inserted;
    const r = card(L.node, ins ? 270 : 250, py, ins ? 450 : 470, { kind: 'playbook', dash: !ins, tags: [ins ? 'MMW 插入 · J4' : 'ps'], title: `${s.n}. ${s.label}`, tsize: 11.5, tmono: false, lines: [{ t: unq(s.text), size: 10, cls: 't2' }], tip: `${s.n}. ${s.label}\n${unq(s.text)}${s.reads_as ? '\n读作：' + unq(s.reads_as) : ''}\n出处：${s.src}` });
    if (ins) { S('rect', { x: 250, y: py - 3, width: 472, height: r.h + 6, rx: 6, class: 'hl' }, L.bg); }
    if (s.reads_as) {
      const rl = wrap('读作：' + unq(s.reads_as), 460, 10, false);
      TL(L.node, 740, py + 14, rl, { size: 10, cls: 'tm', lh: 12.5 });
      edge(c, [[722, py + 10], [736, py + 10]], 'read', {});
    }
    py += Math.max(r.h, s.reads_as ? wrap('读作：' + unq(s.reads_as), 460, 10, false).length * 12.5 + 8 : 0) + 6;
  });
  const rp = card(L.node, 250, py, 470, { kind: 'playbook', dash: true, tags: ['ps'], title: 'Reply（原文）', tsize: 11, lines: [{ t: unq(BF.reply), size: 10 }], tip: unq(BF.reply) + '\n出处：' + BF.reply_src });
  py += rp.h;
  y = Math.max(py, by + 40) + 20;
  // --- part 4: on-demand import lists
  const BI = IP.batch_imports;
  T(L.node, 0, y + 14, '④ 按需导入的组件（虚线框：你点名时才导入，R18 §17 D6、D7）', { size: 13, cls: 'hd' }); y += 24;
  const cols = [
    { b: 'B3', w: 520, groups: [['能力技能 ' + BI.B3.skills.length, BI.B3.skills, 'capability'], ['原则 ' + BI.B3.principles.length, BI.B3.principles, 'principle'], ['playbook ' + BI.B3.playbooks.length, BI.B3.playbooks.map(p => p.name), 'playbook'], ['mode', BI.B3.mode.map(unq), 'mode'], ['直接能力行 ' + BI.B3.direct_capability_rows.length, BI.B3.direct_capability_rows, 'mode'], ['agent 简报', [BI.B3.agent], 'reference'], ['脚本与配置（随需要它的组件，D7）', BI.B3.scripts.map(t => t.replace(/（.*）$/, '')), 'script'], ['未定批次（D6 从 B1 推迟）', BI.on_demand_unbatched.playbooks, 'playbook']] },
    { b: 'B4', w: 330, groups: [['playbook ' + BI.B4.playbooks.length, BI.B4.playbooks.map(p => p.name), 'playbook'], ['mode reference', BI.B4.mode_reference ? [BI.B4.mode_reference] : [], 'reference'], ['mode 脚本', BI.B4.mode_scripts, 'script'], ['mode 触发行', BI.B4.mode_triggers ? [BI.B4.mode_triggers] : [], 'mode'], ['其他', BI.B4.other ? [unq(BI.B4.other)] : [], 'nt']].filter(g => g[1].length) },
    { b: 'B5', w: W - 520 - 330 - 24, groups: [['playbook ' + BI.B5.playbooks.length, BI.B5.playbooks.map(p => p.name), 'playbook'], ['能力技能 ' + BI.B5.skills.length, BI.B5.skills, 'capability'], ['其他', [BI.B5.other], 'reference']] }
  ];
  let x = 0, maxH = 0;
  cols.forEach(col => {
    const gg = S('g', null, L.node); const fr = R(gg, x, y, col.w, 10, { cls: 'grp dash' });
    T(gg, x + 8, y + 17, col.b + ' · 按需，你点名时才导入', { size: 12.5, cls: 'b' });
    let cy = y + 26;
    col.groups.forEach(([t, items, kind]) => {
      T(gg, x + 8, cy + 11, t, { size: 10.5, cls: 'tm' }); cy += 15;
      const f = flow(gg, x + 8, cy, col.w - 16, items.map(it => ({ text: unq(it), kind, dash: true, size: 10, mono: isMono(unq(it)) })), { gap: 3 }); cy += f.h + 6;
    });
    fr.setAttribute('height', cy - y + 4); maxH = Math.max(maxH, cy - y + 4);
    x += col.w + 12;
  });
  y += maxH + 10;
  TL(L.node, 0, y + 10, wrap(BI.count_note + '（' + BI.count_note_src + '）', W, 10.5, false), { size: 10.5, cls: 'tm', lh: 14 });
  c.done(y + 36);
}

function sec10Tables() {
  const IP = O.import_pipeline;
  para('t10-more', `<p class="sub">决定：${codeify(IP.decision)} 理由：${codeify(IP.reason)} <span class="srcnote">（${esc(IP.src)}）</span></p>`);
  tbl('t10-more', [{ h: '步骤', f: r => r.label }, { h: '做法', f: r => r.text }, { h: '状态', f: r => r.status || '' }, srcCol()], IP.source_and_install, { title: '子树怎样进来、怎样安装' });
  tbl('t10-more', [{ h: '类型', f: r => r.label + '（' + r.type + '）' }, { h: '落到哪里', f: r => r.lands_at }, { h: '登记', f: r => r.registers }, { h: '机械改写', f: r => r.mechanical_rewrite }, { h: '例子', f: r => r.examples }, srcCol()], IP.import_types, { title: '八种导入类型', intro: IP.namespace_rule.text });
  const PIA = IP.playbook_import_a_component;
  tbl('t10-more', [{ h: '#', f: r => r.n }, { h: '步骤', f: r => r.title + '（' + r.label + '）' }, { h: '做法', f: r => r.detail }, srcCol()], PIA.steps, { title: '私有 playbook Import a component 的六步', intro: PIA.file + '：' + PIA.note });
  tbl('t10-more', [{ h: '#', f: r => r.n }, { h: '入口问题', f: r => r.label }, { h: '原句', f: r => r.q }, srcCol()], PIA.entry_questions, { title: '第 2 步的六个入口问题' });
  const IM = IP.importer;
  tbl('t10-more', [{ h: '做什么', f: r => r.label }, { h: '说明', f: r => r.text }, srcCol()], [...IM.does, ...IM.does_not.map(d => ({ ...d, label: '不做：' + d.label }))], { title: IM.path + ' 做与不做', intro: '槽位关键词：' + IM.slot_keywords.map(k => '`' + k + '`').join('、') + '（' + IM.slot_keywords_src + '）' });
  tbl('t10-more', [{ h: '情形', f: r => r.case }, { h: '处理', f: r => r.rule }, srcCol()], IM.conflict_rules, { title: '冲突规则' });
  tbl('t10-more', [{ h: '槽位', f: r => r.label }, { h: 'pstack 原文', f: r => r.pstack }, { h: 'MMW 读作', f: r => r.mmw }, { h: '依据', f: r => r.basis }, srcCol()], IP.slots, { title: `pstack-names.md 全部 ${IP.slots.length} 行` });
  const JC = IP.judgement_changes;
  tbl('t10-more', [{ h: '编号', f: r => r.id }, { h: '位置', f: r => r.where }, { h: '改动', f: r => r.change }, { h: '批次', f: r => r.batch }, srcCol()], JC.items, { title: '需要判断的改动 J1–J10', intro: JC.note + ' 各批：' + Object.entries(JC.by_batch).map(([k, v]) => k + ' ' + v).join('、') + '（' + JC.by_batch_src + '）。' });
  const BF = IP.bugfix_merge_example;
  tbl('t10-more', [{ h: '#', f: r => String(r.n) }, { h: '来源', f: r => r.origin === 'ps' ? 'pstack 原文' : 'MMW 插入' }, { h: '步骤', f: r => r.label }, { h: '原文', f: r => r.text }, { h: '读作', f: r => r.reads_as || '' }, srcCol()], BF.steps, { title: BF.file + ' 合并后的步骤', intro: BF.summary + '（' + BF.src + '）' });
  tbl('t10-more', [{ h: '类型', f: r => r.type }, { h: '数量', f: r => r.count }, { h: '要改的文件', f: r => r.files }, srcCol()], IP.b3_file_changes, { title: 'B3 实际要改的文件' });
  const PI = IP.pstack_inventory;
  tbl('t10-more', [{ h: '能力技能', f: r => r.name }, { h: '批次', f: r => r.batch || '—' }, { h: '去向', f: r => r.outcome }, { h: '+model-invoked', f: r => r.plus_model ? '是' : '' }, { h: '说明', f: r => r.note || '' }, srcCol()], PI.skills, { fold: `pstack 能力技能 ${PI.skills.length} 个逐项` });
  tbl('t10-more', [{ h: 'playbook', f: r => r.name }, { h: '批次', f: r => r.batch || '—' }, { h: '去向', f: r => r.outcome }, srcCol()], PI.playbooks, { fold: `pstack playbook ${PI.playbooks.length} 份逐项` });
  tbl('t10-more', [{ h: 'mode 项', f: r => r.item }, { h: '去向', f: r => r.outcome }, { h: '批次', f: r => r.batch || '—' }, srcCol()], PI.mode_items, { fold: 'pstack mode 各项逐项' });
  tbl('t10-more', [{ h: '其他项', f: r => r.item }, { h: '去向', f: r => r.outcome }, { h: '批次', f: r => r.batch || '—' }], PI.other_items, { fold: 'pstack 其余项（reference、脚本、agent、automation）' });
  list('t10-more', [...PI.not_imported_detail.map(n => `不导入 · ${n.group}：${n.item}`), PI.not_a_component, { text: PI.principle_mechanical, src: PI.principle_mechanical_src }], { title: '不导入的 16 项与其他（' + PI.not_imported_src + '）' });
  tbl('t10-more', [{ h: '场合', f: r => r.case }, { h: 'pstack', f: r => r.pstack }, { h: 'MMW', f: r => r.mmw }, srcCol()], IP.pr_mapping, { title: '交付方式的对应（R18 §17 D2 不用 PR 的依据）' });
  tbl('t10-more', [{ h: 'pstack shipping.md 的一步', f: r => r[0] }, { h: 'MMW 现行交付里的对应物', f: r => r[1] }], IP.shipping_correspondence.pairs, { title: 'shipping 九步在 MMW 现行交付里的对应', intro: IP.shipping_correspondence.text + '（' + IP.shipping_correspondence.src + '）' });
  list('t10-more', [{ text: '多模型面板 `' + IP.panel.command + '`：' + IP.panel.text, src: IP.panel.src }, ...IP.deviations_from_pstack.items.map(d => ({ text: '偏离 pstack：' + d, src: IP.deviations_from_pstack.src }))], { title: '导入接口的其余部分' });
}

/* ---------- figure 11: #591 before / after ---------- */
function seqPanel(c, x0, w, y0, lanes, msgs, o = {}) {
  const L = c.L, n = lanes.length, lw = w / n, lx = i => x0 + lw * i + lw / 2;
  let hh = 0;
  lanes.forEach((l, i) => {
    const bw = lw - 10, bx = lx(i) - bw / 2; const g = S('g', { class: kc(o.laneKinds ? o.laneKinds[i] : 'nt') }, L.node);
    const ls = Array.isArray(l) ? l : wrap(l, bw - 10, 11, isMono(l)); const h = 10 + ls.length * 14;
    R(g, bx, y0, bw, h); TL(g, lx(i), y0 + 16, ls, { size: 11, anchor: 'middle', cls: 'b', mono: !Array.isArray(l) && isMono(l), lh: 14 });
    hh = Math.max(hh, h);
  });
  let y = y0 + hh + 14; const top = y;
  msgs.forEach(m => {
    const a = lx(m.from), b = lx(m.to), self = m.from === m.to, k = { call: 'call', command: 'run', return: 'return', refusal: 'refusal', read: 'read', note: 'return' }[m.kind] || 'call';
    const start = self ? a + 16 : Math.min(a, b) + 6;
    const avail = x0 + w - start - 4;
    const g = S('g', null, L.node);
    const lab = wrap(m.label, self ? avail : Math.max(Math.abs(b - a) - 12, 120), 11.5, isMono(m.label));
    TL(g, start, y + 12, lab, { size: 11.5, cls: (k === 'refusal' ? 'b risk' : 'b') + ' lbl', mono: isMono(m.label), lh: 14 });
    let ay = y + 12 + (lab.length - 1) * 14 + 8;
    if (self) { S('path', { d: `M${a},${ay - 4} L${a + 12},${ay - 4} L${a + 12},${ay + 6} L${a + 2},${ay + 6}`, class: 'e e-' + k, 'marker-end': `url(#${c.id}-${k})` }, g); ay += 4; }
    else { S('path', { d: `M${a},${ay} L${b + (b > a ? -2 : 2)},${ay}`, class: 'e e-' + k, 'marker-end': `url(#${c.id}-${k})` }, g); S('circle', { cx: a, cy: ay, r: 2.5, class: 'mk-' + k }, g); }
    let yy = ay + 4;
    if (m.detail) { const dl = wrap(unq(m.detail), avail, 9.5, false).slice(0, 3); TL(g, start, yy + 10, dl, { size: 9.5, cls: 'tm lbl', lh: 12 }); yy += dl.length * 12; }
    tip(g, m.label + (m.detail ? '\n' + unq(m.detail) : '') + (m.src ? '\n出处：' + m.src : ''));
    y = yy + 10;
  });
  lanes.forEach((l, i) => S('line', { x1: lx(i), x2: lx(i), y1: top - 10, y2: y, class: 'lane' }, L.bg));
  return y;
}
function fig11() {
  const I = O.issue_591, W = 1200, c = mkSvg('f11', W, 1100), L = c.L;
  const LW = 560, RX = 600, RW = W - RX;
  S('line', { x1: 580, x2: 580, y1: 0, y2: 2000, class: 'sep' }, L.bg);
  T(L.node, 0, 16, '今天：调研子代理写不了报告', { size: 14, cls: 'hd' });
  T(L.node, RX, 16, '升级后：researcher 另起一个会话', { size: 14, cls: 'hd' });
  const B = I.before_sequence, A = I.after_sequence;
  const yl = seqPanel(c, 0, LW, 30, B.lanes.map(l => ({ '画地图的会话（wayfinder）': ['画地图的会话', '（wayfinder）'] })[l] || l), B.messages.map(m => ({ ...m, src: B.src })), { laneKinds: ['capability', 'nt', 'nt', 'nt'] });
  const LN = { 'map-a-large-effort 会话': ['map-a-large-effort', '会话'], '仓库 research/<n>': ['仓库', 'research/<n>'], '画地图的会话（wayfinder）': ['画地图的会话', '（wayfinder）'] };
  const yr = seqPanel(c, RX, RW, 30, A.lanes.map(l => LN[l] || l), A.messages, { laneKinds: ['playbook', 'script', 'playbook', 'nt', 'nt'] });
  // under-left: side note + three mixings
  let y1 = yl + 6;
  const sn = card(L.node, 0, y1, LW, { kind: 'nt', title: '附注', tsize: 11, lines: [{ t: B.side_note, size: 10.5 }, { t: '拒绝原文：' + I.problem.refusal_text, size: 10, mono: false, cls: 'tm' }], tip: unq(I.problem.text) + '\n出处：' + I.problem.src });
  y1 += sn.h + 8;
  const mx = card(L.node, 0, y1, LW, { kind: 'nt', title: '混在一起的三件事', tsize: 11.5, lines: I.three_mixings.map((m, i) => ({ t: `${i + 1}. ${m.label}：${m.text}`, size: 10.5 })), tip: I.three_mixings.map(m => m.text + '（' + m.src + '）').join('\n') });
  y1 += mx.h;
  // under-right: session facts
  const SF = A.session_facts; let y2 = yr + 6;
  const sf = card(L.node, RX, y2, RW, { kind: 'config', title: 'researcher 会话', tsize: 12, lines: [
    { t: '宿主 · 模型 · 推理强度：' + SF.host_model_effort.join(' · '), mono: false, cls: '' },
    { t: '工作树 ' + SF.worktree + ' · 分支 ' + SF.branch, cls: '' },
    { t: '唤醒：' + SF.wakes, cls: 't2' },
    { t: '为什么不用 issue-<n>：' + SF.why_not_issue_n, size: 10, cls: 'tm' },
    { t: I.role_count_effect, size: 10, cls: 'tm' }], tip: '出处：' + SF.src });
  y2 += sf.h;
  let y = Math.max(y1, y2) + 14;
  T(L.node, 0, y + 6, '主张：' + I.claim, { size: 11.5, cls: 't2' }); y += 16;
  c.done(y + 8);
  htmlLegend('f11', [['call', '调用 / 写'], ['run', '运行命令'], ['refusal', '被拒绝'], ['return', '交回'], ['read', '下次读到']], { title: '线的含义' });
}
function sec11Tables() {
  const I = O.issue_591;
  para('t11-more', `<p class="sub"><b>问题：</b>${codeify(I.problem.text)} <span class="srcnote">（${esc(I.problem.src)}）</span></p>`);
  tbl('t11-more', [{ h: '层', f: r => r.layer + (r.origin === 'mp' ? '（mp）' : '') }, { h: '改动', f: r => r.change }, { h: '依据', f: r => r.basis }, { h: '批次', f: r => r.batch }, srcCol()], I.by_layer, { title: '#591 按层的改动', open: true });
  tbl('t11-more', [{ h: '批次', f: r => r.batch }, { h: '做什么', f: r => r.text }, srcCol()], I.batches, { title: '放进哪一批', intro: I.why_not_wait + '（' + I.why_not_wait_src + '）' });
  list('t11-more', [...I.verification.commands.map(cmd => '`' + cmd + '`'), { text: I.verification.walkthrough, src: I.verification.src }, { text: '你要做的：' + I.user_action.text, src: I.user_action.src }, { text: I.role_count_effect, src: I.role_count_effect_src }], { title: '验证与你要做的' });
}

/* ---------- figure 12: six batches timeline ---------- */
function fig12() {
  const BT = O.batches, W = 1320, c = mkSvg('f12', W, 1150), L = c.L;
  const GX = 82, gap = 8, n = BT.list.length, colW = (W - GX - gap * (n - 1)) / n, cx = i => GX + i * (colW + gap);
  let y = 4;
  // axis
  S('path', { d: `M${GX},${y + 12} L${W - 4},${y + 12}`, class: 'e e-route', 'marker-end': `url(#${c.id}-route)` }, L.node);
  T(L.node, 0, y + 16, '时间 →', { size: 11, cls: 'tm' });
  y += 24;
  const colTop = y;
  // header row
  let hH = 0; const heads = [];
  BT.list.forEach((b, i) => { const lines = [b.on_demand ? '按需：你点名要导入的组件时才做（D6、D7）' : '核心批次', b.note ? b.note : null].filter(Boolean); heads.push(lines); hH = Math.max(hH, 26 + lines.reduce((a, l) => a + wrap(l, colW - 16, 10, false).length * 12.5, 0)); });
  BT.list.forEach((b, i) => {
    const x = cx(i); T(L.node, x + 8, y + 18, b.id + '  ' + b.name, { size: 14, cls: 'hd' });
    let hy = y + 32; heads[i].forEach(l => { const ls = wrap(l, colW - 16, 10, false); TL(L.node, x + 8, hy, ls, { size: 10, cls: b.on_demand ? 'b' : 'tm', lh: 12.5 }); hy += ls.length * 12.5; });
  });
  y += hH + 6;
  // row: items. One colour block per component type; inside it one line per item, naming only the component or file.
  // Every short name below is copied from the item's own text; the full text is in the tooltip and in the table under the figure.
  const SHORT12 = {
    'B0:0': 'hook-launcher 启动器', 'B0:1': 'locations.py（只登记）', 'B0:2': 'check_wiring.py 第 1、8、10 类', 'B0:3': 'dispatch.sh where', 'B0:4': 'dispatch.sh check 只报告',
    'B0:5': 'dispatch.sh research <n>', 'B0:6': 'roles.json（只登记）', 'B0:7': '四处断点 V6–V9', 'B0:8': 'wayfinder 第 5 步', 'B0:9': 'ADR 0032', 'B0:10': '任务板、测试、CONTEXT.md', 'B0:11': 'U-1、U-2、U-3、U-9、U-17 探针', 'B0:12': { h: '文字检查（五张票，D9）', p: ['check_verbatim_moves.py', 'check_component_structure.py', 'tests/skill-text'] },
    'B1:0': 'SKILL.md（B1 版）', 'B1:1': '26 条（MMW 12 + pstack 14）', 'B1:2': 'pstack 14 条（MMW 点名的）', 'B1:4': 'state-list-format.md', 'B1:5': 'mode-hook.py', 'B1:6': 'import_component.py',
    'B1:7': 'retro 的 DESTINATIONS', 'B1:8': '白天 11 份（P1–P11）', 'B1:9': 'session-pickup、pause-safely 推迟到按需（D6）', 'B1:10': '私有 .mmw/playbooks/ 三份', 'B1:12': 'to-spec、to-tickets 分叉',
    'B1:13': 'retro 的四条分拣规则', 'B1:14': 'research、wayfinder（#591）', 'B1:15': 'skills.txt +model-invoked', 'B1:16': 'upstream-pstack/ 子树（按需导入的前提）', 'B1:17': '根 AGENTS.md 改指针',
    'B2:1': 'orchestrator-wakes.md 等', 'B2:2': 'memory-records、setup-mmw', 'B2:3': 'implement 等 4 个回原文', 'B2:4': '5 个技能剥离流程句', 'B2:5': '启动提示词、唤醒指针',
    'B2:6': 'where 成为唯一', 'B2:7': 'dispatch/ → mmw/scripts/', 'B2:8': 'dispatch 解散', 'B2:9': 'mode（B2 版）', 'B2:10': 'downstream-note',
    'B3:0': { h: '15 个能力技能' }, 'B3:1': 'comment-sicko.md、pstack-names.md', 'B3:2': { h: '9 条原则' }, 'B3:3': { h: '6 份 + bug-fix 合并', p: ['feature', 'investigation', 'refactoring', 'perf-issue', 'autonomous-run', 'eval'] },
    'B3:4': 'Imported triggers、Comments', 'B3:5': 'panel（随需要它的组件，D7）等', 'B3:6': 'models.json 面板角色（D7）',
    'B4:0': 'worktree-cleanup', 'B4:1': 'worktree-audit.sh',
    'B5:0': { h: '4 份', p: ['runtime-forensics', 'trace-forensics', 'hillclimb', 'visual-parity'] }, 'B5:1': 'create-verification-skill、maintain-verification-skill', 'B5:2': 'pstack-names.md 的 control 行'
  };
  function rowLabel(t, yy) { TL(L.node, 0, yy + 12, wrap(t, GX - 8, 11, false), { size: 11, cls: 'b', lh: 14 }); }
  rowLabel('落地内容', y);
  let rH = 0;
  BT.list.forEach((b, bi) => {
    let cy = y; const x = cx(bi) + 5, w = colW - 10;
    const byKind = []; b.items.forEach((it, k) => { const kind = it.kind === 'other' ? 'nt' : it.kind; let e = byKind.find(z => z.kind === kind); if (!e) byKind.push(e = { kind, items: [] }); e.items.push({ it, k }); });
    byKind.forEach(grp => {
      const g = S('g', { class: kc(grp.kind) }, L.node);
      const allPs = grp.items.every(z => z.it.origin === 'ps');
      const rect = R(g, x, cy, w, 10, { dash: b.on_demand || allPs, soft: true, r: 5 });
      T(g, x + 7, cy + 14, (KZH[grp.kind] || '其他') + ' · ' + grp.items.length, { size: 10.5, cls: 'b' });
      let iy = cy + 20;
      grp.items.forEach(({ it, k }) => {
        const txt = unq(it.text); const sh = SHORT12[b.id + ':' + k];
        const tags = [it.origin === 'ps' ? 'ps' : it.origin === 'mp' ? 'mp' : null, it.ticket ? '票 ' + it.ticket : null, it.deferred ? '推迟' : null].filter(Boolean);
        const tipT = `${txt}\n类型：${KZH[it.kind] || '其他'}${it.ticket ? '\nB2 票 ' + it.ticket : ''}\n出处：${it.src}`;
        let head = typeof sh === 'string' ? sh : null, parts = null;
        if (!sh || typeof sh === 'object') { // a list item: head plus one small pill per name
          const ci = txt.indexOf('：'); const tail = ci > 0 ? txt.slice(ci + 1).split('；')[0] : '';
          parts = (sh && sh.p) || tail.split('、').map(t => t.trim()).filter(Boolean);
          head = (sh && sh.h) || (txt.slice(0, ci) + '（' + parts.length + '）');
        }
        const m = mChip(head, w - 12, { size: 10, mono: isMono(head), tags });
        m.w = w - 12; dChip(g, x + 6, iy, m, { kind: grp.kind, dash: b.on_demand || it.origin === 'ps', tip: tipT }); iy += m.h + 3;
        if (parts && parts.length) { const f = flow(g, x + 12, iy, w - 18, parts.map(t => ({ text: t, kind: grp.kind, soft: true, size: 9.5, mono: isMono(t), dash: b.on_demand, tip: tipT })), { gap: 3 }); iy += f.h + 4; }
      });
      rect.setAttribute('height', iy - cy + 3); tip(g, grp.items.map(z => unq(z.it.text)).join('\n'));
      cy = iy + 3 + 6;
    });
    rH = Math.max(rH, cy - y);
  });
  y += rH + 14;
  S('line', { x1: 0, x2: W, y1: y - 7, y2: y - 7, class: 'sep' }, L.bg);
  // row: why pipeline runs
  function textRow(label, get, o = {}) {
    rowLabel(label, y); let h = 0;
    BT.list.forEach((b, i) => {
      const arr = [].concat(get(b) || []); let yy = y;
      if (!arr.length) { T(L.node, cx(i) + 8, yy + 12, '—', { size: 10.5, cls: 'tm' }); h = Math.max(h, 16); return; }
      const g = S('g', null, L.node);
      arr.forEach(t => { const ls = wrap((o.bullet ? '· ' : '') + unq(t), colW - 16, 10.5, false); TL(g, cx(i) + 8, yy + 12, ls, { size: 10.5, cls: o.cls || 't2', lh: 13.5 }); yy += ls.length * 13.5 + 2; });
      tip(g, arr.map(unq).join('\n') + (o.src ? '\n出处：' + o.src(b) : ''));
      h = Math.max(h, yy - y);
    });
    y += h + 12; S('line', { x1: 0, x2: W, y1: y - 6, y2: y - 6, class: 'sep' }, L.bg);
  }
  textRow('为什么这时流水线还能跑', b => b.why_pipeline_runs, { src: b => b.src });
  textRow('你要做的', b => b.you_do, { bullet: true, cls: '', src: b => b.you_do_src });
  // row: wiring classes turning to failure
  rowLabel('这一批转为失败的连线检查', y); let wH = 0;
  BT.list.forEach((b, i) => {
    if (!b.wiring_fail_from.length) { T(L.node, cx(i) + 8, y + 12, '—', { size: 10.5, cls: 'tm' }); wH = Math.max(wH, 16); return; }
    const f = flow(L.node, cx(i) + 6, y, colW - 12, b.wiring_fail_from.map(t => ({ text: t, kind: 'script', size: 10, maxW: colW - 12, tip: 'check_wiring.py 第 ' + t + '\n出处：' + b.src })), { gap: 3 });
    wH = Math.max(wH, f.h);
  });
  y += wH + 10;
  // column frames
  BT.list.forEach((b, i) => { S('rect', { x: cx(i), y: colTop, width: colW, height: y - colTop, rx: 6, class: b.on_demand ? 'grp dash' : 'grp' }, L.bg); });
  y += 14;
  { const b = BT.list.find(x => x.full_suite_reason); if (b) {
    const r = card(L.node, 0, y, W, { kind: 'nt', title: '完整套件：只有 ' + b.id + ' 跑', tsize: 11.5, lines: [{ t: b.full_suite_reason, size: 10.5, cls: '' }], tip: b.full_suite_reason + '\n出处：' + b.full_suite_reason_src });
    y += r.h + 12; } }
  // bottom: rollback + acceptance + common
  const half = (W - 12) / 2;
  const rb = card(L.node, 0, y, half, { kind: 'nt', title: '回退办法', lines: [{ t: BT.rollback.text, size: 11, cls: '' }, ...BT.common.map(cm => ({ t: '· ' + cm.text, size: 10.5 }))], tip: '出处：' + BT.rollback.src + '；' + BT.common.map(x => x.src).join('；') });
  const ac = card(L.node, half + 12, y, half, { kind: 'nt', title: '每张批次票的验收条件', lines: [...BT.acceptance.items.map((t, i) => ({ t: `${i + 1}. ${t}`, size: 10.5, cls: '' })), { t: BT.acceptance.basis, size: 10, cls: 'tm' }], tip: '出处：' + BT.acceptance.src });
  y += Math.max(rb.h, ac.h) + 12;
  c.done(y);
  htmlLegend('f12', [['route', '批次先后'], { html: '<span class="sw k-sc" style="width:18px;height:12px"></span>每个色块是一类组件，块内一格一项（名字只写组件或文件名；完整说明在悬停提示与图下「六批逐项」表）' }, { html: '<span class="sw k-nt ps" style="width:18px;height:12px"></span>虚线框：按需，你点名时才导入（R18 §17 D6、D7）；ps / mp：来自 pstack / mattpocock 上游；票 a / 票 b：B2 的两张票；推迟：D6 从这一批移出' }], { title: '图例' });
}
function sec12Tables() {
  const BT = O.batches;
  para('t12-more', `<p class="sub">${codeify(BT.claim)} <span class="srcnote">（${esc(BT.claim_src)}）</span></p>`);
  tbl('t12-more', [{ h: '批次', f: r => r.id + ' ' + r.name + (r.on_demand ? '（按需）' : '') }, { h: '落地内容', f: r => r.items.map(i => `[${KZH[i.kind] || '其他'}${i.origin ? ' · ' + i.origin : ''}${i.ticket ? ' · 票 ' + i.ticket : ''}] ${i.text}`) }, { h: '为什么还能跑', f: r => r.why_pipeline_runs }, { h: '你要做的', f: r => r.you_do }, { h: '转为失败的连线检查', f: r => r.wiring_fail_from.length ? r.wiring_fail_from : '—' }, srcCol()], BT.list, { title: '六批逐项' });
  tbl('t12-more', [{ h: '批次', f: r => r.batch }, { h: '## Re-entry', f: r => r.reentry }, { h: '触发行', f: r => r.triggers }, { h: '路由', f: r => r.routes }, srcCol()], BT.mode_per_batch, { title: '各批的 mode', intro: BT.mode_per_batch_rule + ' 篇幅：' + BT.mode_length + '（' + BT.mode_length_src + '）' });
  tbl('t12-more', [{ h: '组件', f: r => r.what }, { h: 'B2 后', f: r => r.after_b2 }, { h: '全部批次后', f: r => r.after_all }], BT.counts_after, { title: '各批之后的数量（' + BT.counts_after_src + '）', intro: '量级：' + BT.magnitude.text + '（' + BT.magnitude.status + '，' + BT.magnitude.src + '）' });
}

/* ---------- sections 13-15 ---------- */
function sec13() {
  const DD = O.decided;
  $('d-boundary').innerHTML = codeify(DD.boundary.text) + ` <span class="srcnote">（${esc(DD.boundary.src)}）</span>`;
  $('d-cards').innerHTML = DD.items.map(d => `<div class="card"><span class="pill">已定 ${esc(d.id)}</span><h4>${codeify(d.q)}</h4><p><b>决定：</b>${codeify(d.decision)}</p><p><b>影响：</b>${codeify(d.effect)}</p><p class="srcnote"><b>本页改了什么：</b>${codeify(d.page)}（${esc(d.src)}）</p></div>`).join('');
  const RN = O.renames;
  tbl('d-renames', [{ h: '类别', f: r => r.kind }, { h: '今天的名字', f: r => '`' + r.old + '`' }, { h: '改为', f: r => '`' + r.new + '`' }, { h: '批次', f: r => r.batch }, srcCol()], RN.rows, { title: RN.title, open: true, intro: RN.intro + '（' + RN.src + '）' });
  const ED = O.engineering_decisions;
  tbl('d-eng', [{ h: '决定', f: r => r.decision }, { h: '理由', f: r => r.reason + (r.cost ? '。代价：' + r.cost : '') }, { h: '放弃的备选', f: r => r.rejected || '' }, srcCol()], ED.items, { intro: ED.note.text + '（' + ED.note.src + '）' });
}
function sec14() {
  const RK = O.risks; const main = RK.items.filter(r => RK.main_ids.includes(r.id)), rest = RK.items.filter(r => !RK.main_ids.includes(r.id));
  const cardH = r => `<div class="card ${r.status === 'pending' ? 'pending' : 'risk'}"><span class="pill ${r.status === 'pending' ? 'warn' : 'risk'}">${r.status === 'pending' ? '待实测' : '风险'}</span><h4>${codeify(r.title)}</h4><p>${codeify(r.risk)}</p><p><b>缓解：</b>${codeify(r.mitigation)}</p><div class="srcnote">${esc(r.src)}</div></div>`;
  $('r-cards').innerHTML = main.map(cardH).join('') + rest.map(cardH).join('');
  const NM = O.new_mechanisms;
  tbl('r-mech', [{ h: '机制', f: r => '`' + r.name + '`（' + r.label + '）' }, { h: '类型', f: r => KZH[r.kind] || r.kind }, { h: '是什么', f: r => r.what }, { h: '为什么要（它修的断点或满足的需求）', f: r => r.why }, srcCol()], NM.items, { intro: NM.note.text + '（' + NM.note.src + '）' });
  const PB2 = O.probes;
  $('r-where').innerHTML = codeify(PB2.where.text) + ` <span class="srcnote">（${esc(PB2.where.src)}）</span>`;
  tbl('r-probes', [{ h: '编号', f: r => r.id }, { h: '问题', f: r => r.label + '：' + r.question }, { h: '为什么重要', f: r => r.why }, { h: '怎么测', f: r => r.how }, { h: '时点', f: r => r.when || '来源未写' }, srcCol()], PB2.items, {});
  list('r-probes', [...PB2.closed.map(x => ({ text: x.text, src: x.src })), ...O.source_discrepancies.map(d => ({ text: '来源前后不一 · ' + d.topic + '：' + d.detail, src: d.src }))], { title: '已关闭的探针与来源里的前后不一' });
}
function sec15() {
  const CJ = O.closing_judgement;
  $('j-par').innerHTML = CJ.paragraphs.map(p => `<p>${codeify(p)}</p>`).join('') + `<p class="srcnote">${esc(CJ.src)}</p>`;
  const BS = O.basis;
  tbl('b-basis', [{ h: '报告', f: r => r.id }, { h: '内容', f: r => r.what }, { h: '路径', f: r => '`' + r.path + '`' }], BS.reports, { title: '报告文件', open: true, intro: '出处：' + BS.reports_src });
  list('b-basis', [{ text: '读过全文或相关行（MMW）：' + BS.read_verified.mmw, src: BS.read_verified.src }, { text: '读过（pstack）：' + BS.read_verified.pstack, src: BS.read_verified.src }, { text: '没读：' + BS.not_read.text, src: BS.not_read.src }], { title: '读了什么、没读什么' });
  list('b-basis', BS.unverified.map(u => ({ text: u.text, src: u.src })), { title: '未实测、标为推断的事项', open: true });
  list('b-basis', [{ text: BS.not_committed.text + '（' + BS.not_committed.checked + '）', src: BS.not_committed.src }, ...A.not_found.map(n => ({ text: '数据核对 · ' + n.item + '：' + n.status })), ...(M.not_found || []).map(n => typeof n === 'string' ? n : ({ text: '数据核对 · ' + (n.item || n.what || '') + '：' + (n.status || n.note || '') }))], { title: '报告状态与数据核对' });
}

/* ---------- boot ---------- */
function main() {
  const steps = [header, fig1, sec1Tables, fig2, sec2Tables, fig3, fig4, sec4Tables, fig5, sec5Tables, fig6, sec6Tables, fig7, sec7Tables, fig8, sec8Tables, fig9, sec9Tables, fig10, fig10b, sec10Tables, fig11, sec11Tables, fig12, sec12Tables, sec13, sec14, sec15];
  window.__errs = [];
  for (const f of steps) { try { f(); } catch (e) { console.error(f.name, e); window.__errs.push(f.name + ': ' + e.message + ' @ ' + (e.stack || '').split('\n')[1]); } }
}
main();
