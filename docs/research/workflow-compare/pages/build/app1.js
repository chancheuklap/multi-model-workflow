/* ---------- data aliases ---------- */
const A = D.arch, M = D.mig, PB = D.pb, PR = D.pr, O = D.ops;
const OTAG = { ps: 'ps', mp: 'mp', new: '新', fork: '分叉', merged: '合并', dd: 'dd' };
const KZH = { mode: 'mode', playbook: 'playbook', capability: '能力技能', reference: 'reference', principle: '原则', script: '脚本与 hook', config: '角色表与配置' };

/* ---------- header ---------- */
function header() {
  $('h-sub').textContent = A.head.subtitle;
  $('h-claims').innerHTML = A.head.claims.map((c, i) => `<b>${'①②③'[i]}</b> ${codeify(c.text)} <span class="srcnote">（${esc(c.src)}）</span>`).join(' ') + ' <span class="srcnote">图里的名字、命令、事件、数字都取自 R18（定稿，含第 16 节 #591 与第 17 节你定下的九项决定）、R14、R13；表的最后一列是出处；鼠标停在图里的盒子上（手机上点一下）看完整说明。</span>';
  $('h-nums').innerHTML = A.head.numbers.map(n => `<div class="num" title="${esc(n.detail + '（' + n.src + '）')}"><div class="v">${esc(n.value)} <span class="l">${esc(n.label)}</span></div><div class="d">${codeify(n.detail)}</div></div>`).join('');
  tbl('t1-nums', [{ h: '数字', f: r => r.value + ' ' + r.label }, { h: '完整说明', f: r => r.detail }, srcCol()], A.head.numbers, { fold: '页首四个数字的完整说明' });
  $('h-facts').innerHTML = A.head.now_facts.map(f => `<span class="fact" title="${esc(f.src)}">${esc(f.label)} <b>${esc(f.value)}</b> <span class="srcnote">${esc(f.note)} · ${esc(f.src)}</span></span>`).join('');
  const kinds = ['mode', 'playbook', 'capability', 'reference', 'principle', 'script', 'config'];
  let lg = kinds.map(k => `<span class="lg"><span class="sw ${kc(k)}"></span>${esc(KZH[k])}</span>`).join('');
  lg += `<span class="lg"><span class="sw k-pb ps"></span>虚线：pstack</span>`;
  lg += `<span class="lg"><span class="pill">mp</span>mattpocock</span>`;
  lg += `<span class="lg" title="每次由你点名要导入的组件（R18 §17 D6、D7）"><span class="pill">按需</span>pstack 的组件，你点名时才导入</span>`;
  lg += `<span class="lg"><span class="sw k-nt"></span>文档、状态、入口</span>`;
  $('h-legend').innerHTML = lg;
  $('h-rule').innerHTML = '判据：每段内容默认搬到它按类型该在的层；留在原处必须写明是下面 H1–H6 或 S 中的哪一条。这条判据同时写进 ADR 0032 与每张批次票的验收条件。<span class="srcnote">（R18 前言「判据」）</span>这条判据与此前的设计方向相反。<span class="srcnote">（设计方说明，R18 未写）</span>';
  tbl('t-constraints', [{ h: '编号', f: r => r.id }, { h: '硬约束（只有这些算约束）', f: r => r.text }], A.fig1.constraints, { fold: '七条硬约束 H1–H6 与 S' });
}

/* ---------- figure 1 ---------- */
function numMark(p, x, y, n) { // small circled number on a line
  const g = S('g', null, p);
  S('circle', { cx: x, cy: y, r: 8, style: 'fill:var(--surface);stroke:var(--ink2);stroke-width:1.2' }, g);
  T(g, x, y + 4, String(n), { size: 10.5, anchor: 'middle', cls: 'b' });
  return g;
}
function fig1() {
  const F = A.fig1, W = 1320, c = mkSvg('f1', W, 1150), L = c.L;
  const CX = 184, CW = 896, CR = CX + CW, RX = 1146, RW = W - RX - 2;
  const lanes = { run: 1096, config: 1112, wake: 1128 };
  let y = 4;
  const at = {};
  // --- entries
  const eW = (CW - 24) / 3; const eg = [];
  F.entries.forEach((e, i) => {
    const x = CX + i * (eW + 12);
    let items, sub = null;
    if (e.id === 'entry:script') { items = e.sessions.map(s => { const ps = e.prompt_shapes.find(p => p.role === s); return { text: s, kind: 'nt', tip: ps ? ps.text + srcOf(ps) : '' }; }); sub = e.rule + '；' + e.certainty; }
    else items = e.paths.map(p => ({ text: `${p.label}（${p.certainty}）`, kind: 'nt', mono: false, tip: p.detail + '\n确定性：' + p.certainty + srcOf(p) }));
    const gr = group(L.node, x, y, eW, e.label, items, { sub, tip: (e.note || '') + (e.data_file ? '\n数据文件：' + e.data_file : '') + srcOf(e) });
    eg.push(gr); at[e.id] = { x, y, w: eW };
  });
  const eh = Math.max(...eg.map(g => g.h)); eg.forEach(g => g.rect.setAttribute('height', eh));
  Object.values(at).forEach(a => a.h = eh);
  y += eh + 70;
  // --- mode box + roles box
  const mW = 660, mg = S('g', { class: 'k-mode' }, L.node);
  const mRect = R(mg, CX, y, mW, 10);
  T(mg, CX + 10, y + 21, 'mmw', { size: 16, mono: true, cls: 'b' });
  T(mg, CX + 62, y + 20, 'mode · ' + F.mode.path + ' · 模型可调用（H2）', { size: 11, cls: 't2' });
  T(mg, CX + 10, y + 37, '批次：' + F.mode.batch, { size: 10.5, cls: 'tm' });
  tip(mg, F.mode.frontmatter + '\n' + F.mode.section_count_note + srcOf(F.mode));
  const cols = 3, cw = (mW - 20 - 2 * 8) / cols; let cyy = y + 48; const cells = {};
  const ms = F.mode.sections.map(s => mChip(s.label, cw, { size: 11.5, mono: false, tags: s.origin === 'ps' ? ['ps', s.batch] : [] }));
  const rowHs = []; ms.forEach((m, i) => { const r = Math.floor(i / cols); rowHs[r] = Math.max(rowHs[r] || 30, m.h); });
  F.mode.sections.forEach((s, i) => {
    const r = Math.floor(i / cols); const cx = CX + 10 + (i % cols) * (cw + 8), cy = cyy + rowHs.slice(0, r).reduce((a, h) => a + h + 6, 0);
    const m = ms[i]; m.w = cw; m.h = rowHs[r];
    dChip(mg, cx, cy, m, { kind: 'mode', dash: s.origin === 'ps', tip: s.label + '\n' + s.note + (s.batch ? '\n批次：' + s.batch : '') + srcOf(s) });
    cells[s.id] = { x: cx, y: cy, w: cw, h: m.h };
  });
  let mH = 48 + rowHs.reduce((a, h) => a + h + 6, 0) + 4;
  const PRI = F.priority;
  T(mg, CX + 10, y + mH + 12, '优先级（## Autonomy 第一条）', { size: 11, cls: 'b' });
  let px = CX + 10, py = y + mH + 20;
  PRI.chain.forEach((lv, i) => {
    const m = mChip(lv, 420, { size: 10.5, mono: false });
    if (px + m.w > CX + mW - 10) { px = CX + 10; py += m.h + 6; }
    dChip(mg, px, py, m, { kind: ['nt', 'mode', 'playbook', 'principle'][i], tip: PRI.note + srcOf(PRI) });
    px += m.w + 4; if (i < PRI.chain.length - 1) { T(mg, px + 2, py + 13, '>', { size: 12, cls: 'b' }); px += 16; }
  });
  py += 26;
  TL(mg, CX + 10, py + 10, wrap('能力技能自带的人工闸门不在这条链里：人在场照闸门停，无人会话走本角色的无人出路。', mW - 20, 10.5, false), { size: 10.5, cls: 'tm', lh: 13 });
  py += 22;
  T(mg, CX + 10, py + 6, 'dispatch.sh where 的四种输出（被压缩的会话据此找回自己那一步）', { size: 11, cls: 'b' }); py += 12;
  A.fig1.where_outputs.forEach(o => { const m = mChip(o.form, mW - 20, { size: 10, mono: true }); dChip(mg, CX + 10, py, m, { kind: 'script', tip: o.form + '\n' + o.meaning }); py += m.h + 3; });
  mH = py - y + 6;
  // roles
  const rx = CX + mW + 14, rw = CR - rx; const rg = S('g', { class: 'k-cfg' }, L.node);
  const rRect = R(rg, rx, y, rw, 10);
  T(rg, rx + 8, y + 18, 'mmw/roles.json', { size: 12, mono: true, cls: 'b' });
  T(rg, rx + 8, y + 33, `${F.roles.length} 个角色 · 角色 → playbook`, { size: 10.5, cls: 'tm' });
  let ry = y + 40;
  F.roles.forEach(r => {
    const g = S('g', null, rg);
    T(g, rx + 8, ry + 12, r.role, { size: 11, mono: true, cls: 'b' });
    const pbl = r.playbook.startsWith('（例外）') ? '→ advisor/references/advising.md（例外）' : '→ ' + r.playbook;
    const ls = wrap(pbl, rw - 16, 10, true);
    TL(g, rx + 8, ry + 25, ls, { size: 10, mono: true, cls: 'tm', lh: 12 });
    tip(g, `${r.role}\nplaybook：${r.playbook}\nmodels.json 行：${r.models_row}\n启动：${r.started_by}\n唤醒：${jwakes(r.wakes)}${r.note ? '\n' + r.note : ''}${srcOf(r)}`);
    ry += 16 + ls.length * 12 + 2;
  });
  const rH = Math.max(mH, ry - y + 4);
  rRect.setAttribute('height', rH); mRect.setAttribute('height', rH);
  const rolesSt = F.state.find(s => s.id === 'cfg:roles.json');
  tip(rg, F.roles_notes.map(n => n.text).join('\n') + (rolesSt ? '\n' + rolesSt.note : ''));
  at.mode = { x: CX, y, w: mW, h: rH }; at.roles = { x: rx, y, w: rw, h: rH };
  // entry edges
  // three entry arrows, each label left-aligned right next to its own line; the wake line lands on the mode box above the Re-entry column
  const eBot = at['entry:human'].y + eh;
  const hx = at['entry:human'].x + eW / 2;
  edge(c, [[hx, eBot], [hx, y - 1]], 'route', {});
  labelAt(c, 'description / 提醒 / /mmw', hx + 6, eBot + 22);
  const sx = at['entry:script'].x + 26;
  edge(c, [[sx, eBot], [sx, y - 1]], 'call', {});
  labelAt(c, '启动提示词点名 mode 与步骤', sx + 6, eBot + 22);
  const re = cells['mode#Re-entry'], wx = at['entry:wake'].x + eW / 2, lxw = re.x + re.w - 22;
  edge(c, [[wx, eBot], [wx, eBot + 40], [lxw, eBot + 40], [lxw, y - 1]], 'wake', {});
  labelAt(c, '唤醒行带指针 → ## Re-entry', lxw + 6, eBot + 56);
  y += rH + 50;

  // --- generic band; a row entry may be a stack of groups sharing one column
  const bands = {};
  function band(id, title, sub, rows) {
    T(L.node, CX, y + 14, title, { size: 14, cls: 'hd' });
    if (sub) T(L.node, CX + tw(title, 14) + 12, y + 14, sub, { size: 11, cls: 'tm' });
    const top = y; y += 24; const gpos = {};
    for (const row of rows) {
      let x = CX; const made = [];
      const tot = row.reduce((a, g) => a + g.w, 0), gap = row.length > 1 ? (CW - tot) / (row.length - 1) : 0;
      for (const gdef of row) {
        if (gdef.stack) {
          let sy = y; const parts = [];
          gdef.stack.forEach((sd, k) => { const gr = group(L.node, x, sy, gdef.w, sd.title, sd.items, sd.o || {}); parts.push(gr); gpos[sd.id] = { x, y: sy, w: gdef.w, h: gr.h, gr }; sy += gr.h + 6; });
          made.push({ h: sy - 6 - y, rect: null, last: parts[parts.length - 1], stackTop: y });
        } else {
          const gr = group(L.node, x, y, gdef.w, gdef.title, gdef.items, gdef.o || {});
          made.push(gr); gpos[gdef.id] = { x, y, w: gdef.w, gr };
        }
        x += gdef.w + gap;
      }
      const h = Math.max(...made.map(m => m.h));
      made.forEach(m => { if (m.rect) m.rect.setAttribute('height', h); else { const l = m.last; l.rect.setAttribute('height', l.h + (h - m.h)); } });
      Object.values(gpos).forEach(p => { if (p.y === y && p.h == null) p.h = h; });
      y += h + 10;
    }
    bands[id] = { top, bottom: y - 10, g: gpos };
    return bands[id];
  }
  const pbItem = p => ({ text: p.slug, kind: 'playbook', mono: true, dash: p.origin === 'ps', tags: [OTAG[p.origin]], tip: `${p.name}${p.p ? '（' + p.p + '）' : ''}\n${p.note || ''}${p.steps && p.steps.length ? '\n步骤：' + p.steps.join(' → ') : ''}${p.owner ? '\n所有权：' + p.owner : ''}${p.merged_note ? '\n' + p.merged_note : ''}${p.from ? '\n来自：' + p.from : ''}${p.clusters ? '\n规则簇：' + p.clusters.join('、') : ''}${srcOf(p)}` });
  const PG = Object.fromEntries(F.playbook_groups.map(g => [g.id, g]));
  const odSub = '按需：你点名时才导入（D6）';
  const pgDef = (id, w) => { const g = PG[id]; return { id, w, title: g.label + (g.batch && g.batch !== '—' ? ' · ' + g.batch : ''), items: g.items.map(pbItem), o: { dash: g.on_demand, sub: g.on_demand ? odSub : (g.location || null), tip: g.src } }; };
  const pbBand = band('pb', 'playbook 层', 'mmw/playbooks/ · ' + F.playbook_counts.b2 + ' · ' + F.playbook_counts.all, [
    [pgDef('pbg:day', 380), pgDef('pbg:night', 200), pgDef('pbg:private', 230)],
    [pgDef('pbg:ps-b1', 160), pgDef('pbg:ps-b3', 320), pgDef('pbg:ps-b4', 150), pgDef('pbg:ps-b5', 250)]
  ]);
  const pc = cells['mode#Playbooks'];
  edge(c, [[pc.x + pc.w / 2, at.mode.y + rH], [pc.x + pc.w / 2, pbBand.top + 2]], 'route', { label: '路由表：每份 playbook 一行', cands: [[pc.x + pc.w / 2, at.mode.y + rH + 20]] });
  edge(c, [[rx + rw / 2, at.roles.y + rH], [rx + rw / 2, pbBand.top + 2]], 'route', { label: '角色 → playbook', cands: [[rx + rw / 2, at.roles.y + rH + 20]] });
  y += 34;
  // capability band
  const capItem = it => ({ text: it.label, kind: 'capability', mono: true, dash: it.origin === 'ps', dim: it.status === '不装' || it.status === '不导入', tags: [OTAG[it.origin]], tip: `${it.label}\n${it.note || ''}${it.note2 ? '\n' + it.note2 : ''}${it.status ? '\n状态：' + it.status : ''}${it.switch ? '\n调用开关：' + it.switch : ''}${it.batch ? '\n批次：' + it.batch : ''}${it.from ? '\n来自：' + it.from : ''}` });
  const CG = Object.fromEntries(F.capability_groups.map(g => [g.id, g]));
  const cgDef = (id, w) => { const g = CG[id]; return { id, w, title: g.label + (g.batch ? ' · ' + g.batch : ''), items: g.items.map(capItem), o: { dash: g.on_demand, sub: g.on_demand ? odSub : (g.location || null), tip: g.src } }; };
  const capBand = band('cap', '能力技能层', 'mmw-v2/skills/<name>/ 与三个上游子树 · B2 后 35 个 · 全部 52 个', [
    [cgDef('capg:self', 336), cgDef('capg:mp', 552)],
    [{ w: 250, stack: [cgDef('capg:mp-off', 250), cgDef('capg:dd', 250)] }, cgDef('capg:ps-b3', 360), cgDef('capg:ps-b5', 280)]
  ]);
  edge(c, [[CX + 170, pbBand.bottom], [CX + 170, capBand.top + 2]], 'call', { label: '步骤按名调用能力技能', cands: [[CX + 170, pbBand.bottom + 17]] });
  y += 34;
  // reference band
  const refItem = it => ({ text: it.label, kind: 'reference', mono: true, dash: it.origin === 'ps', tags: [OTAG[it.origin] || null, it.batch], tip: `${it.label}\n${it.note || ''}${it.from ? '\n来自：' + it.from : ''}` });
  const RG = Object.fromEntries(F.reference_groups.map(g => [g.id, g]));
  const rgDef = (id, w) => { const g = RG[id]; return { id, w, title: g.label, items: g.items.map(refItem), o: { dash: g.on_demand, sub: g.on_demand ? odSub : null, tip: g.src } }; };
  const refBand = band('ref', 'reference 层', '只在某一步才读的材料；交给子代理或另起会话的简报', [[rgDef('refg:mode', 400), rgDef('refg:mode-ps', 250), rgDef('refg:cap', 240)]]);
  edge(c, [[CX + 170, capBand.bottom], [CX + 170, refBand.top + 2]], 'read', { label: '点名它的那一步才读', cands: [[CX + 170, capBand.bottom + 17]] });
  y += 34;
  // script band
  const scItem = it => ({ text: (it.owner ? it.owner + '/' : '') + it.label, kind: it.kind_override || 'script', mono: true, dash: it.origin === 'ps', tags: [it.hook ? 'hook' : null, it.oracle ? 'oracle' : null, OTAG[it.origin], it.batch && it.batch.length < 4 ? it.batch : null], tip: `${it.label}\n${it.note || ''}${it.from ? '\n来自：' + it.from : ''}${it.batch ? '\n批次：' + it.batch : ''}${srcOf(it)}` });
  const SG = Object.fromEntries(F.script_groups.map(g => [g.id, g]));
  const sgDef = (id, w) => { const g = SG[id]; return { id, w, title: g.label, items: g.items.map(scItem), o: { dash: g.on_demand, sub: g.on_demand ? odSub + ' · ' + g.batch : (g.batch || null), tip: g.src } }; };
  const scBand = band('sc', '脚本与 hook 层', '每次结果都一样的状态读写、投递、检查；不做判断', [[sgDef('scg:mmw', 420), sgDef('scg:mmw-ps', 180), sgDef('scg:tools', 290)]]);
  // capability scripts: one small group per owning skill
  {
    const g0 = SG['scg:cap']; const gg = S('g', null, L.node); const fr = R(gg, CX, y, CW, 10, { cls: 'grp' });
    T(gg, CX + 7, y + 16, g0.label + '（' + g0.items.length + ' 个，按所属能力技能分组）', { size: 12, cls: 'b' }); tip(gg, g0.src);
    const owners = []; g0.items.forEach(it => { const o = it.owner || 'upstream-unlazy'; let e = owners.find(x => x.o === o); if (!e) owners.push(e = { o, items: [] }); e.items.push(it); });
    let ox = CX + 7, oy = y + 24, rowH = 0;
    owners.forEach(o => {
      const its = o.items.map(it => ({ ...scItem(it), text: it.owner ? it.label : it.label }));
      const nat = its.reduce((a, it) => a + mChip(it.text, 400, { size: 11, mono: true, tags: it.tags }).w + 5, 0) + 14;
      const w = Math.min(CW - 14, Math.max(tw(o.o + '/', 11.5, true) + 20, nat));
      if (ox > CX + 7 && ox + w > CX + CW - 7) { ox = CX + 7; oy += rowH + 6; rowH = 0; }
      const gr = group(gg, ox, oy, w, o.o + '/', its, { kind: 'capability' });
      rowH = Math.max(rowH, gr.h); ox += w + 6;
    });
    const h = oy + rowH + 8 - y; fr.setAttribute('height', h); y += h + 10;
    scBand.bottom = y - 10;
  }
  y += 34;
  // state band
  const stItem = it => ({ text: it.label, kind: it.kind === 'state' ? 'nt' : it.kind, mono: isMono(it.label), dash: false, tags: [OTAG[it.origin], it.batch && it.batch.length <= 3 ? it.batch : null], tip: `${it.label}\n${it.note || ''}${it.from ? '\n来自：' + it.from : ''}${it.batch ? '\n批次：' + it.batch : ''}${srcOf(it)}` });
  const st = F.state; const tracker = st[0];
  const local = st.filter(s => ['cfg:hosts.json', 'cfg:models.json', 'cfg:installed-root', 'cfg:hook-launcher', 'cfg:skills-copies', 'st:statedir', 'cfg:boards.json', 'cfg:shared.md'].includes(s.id));
  const cons = st.filter(s => ['cfg:target.json', 'cfg:consumer-playbooks', 'cfg:docs-agents'].includes(s.id));
  const stBand = band('st', '状态与配置', 'roles.json 见上方 mode 旁', [[
    { id: 'tracker', w: 430, title: tracker.label + ' · ' + tracker.events.length + ' 种', items: tracker.events.map(e => ({ text: e, kind: 'nt', mono: true, size: 10.5 })), o: { sub: tracker.note, tip: tracker.note + srcOf(tracker) } },
    { id: 'local', w: 262, title: '本机 ~/.mmw/ 与 mmw 配置', items: local.map(stItem) },
    { id: 'cons', w: 200, title: '消费仓库', items: cons.map(stItem) }]]);
  edge(c, [[CX + 170, scBand.bottom], [CX + 170, stBand.top + 2]], 'events', { label: '读写票上的事件', cands: [[CX + 170, scBand.bottom + 17]] });
  edge(c, [[CX + 620, scBand.bottom], [CX + 620, stBand.top + 2]], 'config', { label: '读 models.json、installed-root', cands: [[CX + 620, scBand.bottom + 17]] });
  // lanes on the right of the center: ① run ② config ③ wake
  const pbMid = pbBand.top + 60, scY = scBand.top + 34;
  edge(c, [[CR, pbMid], [lanes.run, pbMid], [lanes.run, scY], [CR + 1, scY]], 'run', {});
  const rolesMid = at.roles.y + 30;
  edge(c, [[CR, scY + 16], [lanes.config, scY + 16], [lanes.config, rolesMid], [CR + 1, rolesMid]], 'config', {});
  const wakeMid = at['entry:wake'].y + 30;
  edge(c, [[CR, scY + 32], [lanes.wake, scY + 32], [lanes.wake, wakeMid], [CR + 1, wakeMid]], 'wake', {});
  numMark(L.lab, lanes.run, (pbMid + scY) / 2, 1);
  numMark(L.lab, lanes.config, (rolesMid + scY) / 2 + 60, 2);
  numMark(L.lab, lanes.wake, (wakeMid + rolesMid) / 2, 3);
  // --- right rail: principles
  let ry2 = pbBand.top; const railG = S('g', null, L.node);
  T(railG, RX, ry2 + 14, '原则层', { size: 14, cls: 'hd' });
  T(railG, RX, ry2 + 30, 'mmw/principles/', { size: 10, mono: true, cls: 'tm' });
  T(railG, RX, ry2 + 43, 'B2 后 ' + F.principle_counts.b1_or_b2, { size: 10, cls: 'tm' });
  T(railG, RX, ry2 + 56, '全部 ' + F.principle_counts.all, { size: 10, cls: 'tm' });
  ry2 += 72;
  T(railG, RX, ry2, '← 虚线：按名点名', { size: 10.5, cls: 't2' }); ry2 += 10;
  for (const g of F.principle_groups) {
    const gg = S('g', { class: 'k-pr' }, railG);
    const n = g.items.length, per = 10, sq = 11, gapq = 3.5;
    const rows = Math.ceil(n / per);
    const h = 36 + rows * (sq + gapq) + 4;
    R(gg, RX, ry2, RW, h, { soft: true });
    T(gg, RX + 7, ry2 + 15, g.label.split(' · ')[0] + ' · ' + g.count, { size: 11.5, cls: 'b' });
    T(gg, RX + 7, ry2 + 29, g.origin === 'self' ? 'MMW 自有 · B1' : `pstack · B1 ${g.b1} + B3 ${g.b3}`, { size: 10, cls: 'tm' });
    g.items.forEach((it, i) => {
      const qx = RX + 7 + (i % per) * (sq + gapq), qy = ry2 + 36 + Math.floor(i / per) * (sq + gapq);
      const r = S('rect', { x: qx, y: qy, width: sq, height: sq, rx: 2, class: it.batch === 'B3' ? 'dotb' : 'dot' }, gg);
      tip(r, `${it.slug}\n${it.note || ''}${it.absorbs ? '\n吸收：' + it.absorbs : ''}\n批次：${it.batch}`);
    });
    tip(gg, g.label + '\n' + g.items.map(i => i.label + '（' + i.batch + '）').join('\n') + srcOf(g));
    ry2 += h + 8;
  }
  TL(railG, RX, ry2 + 10, ['实心 = B1', '虚线 = B3（按需）'], { size: 10, cls: 'tm', lh: 12 });
  ry2 += 34;
  TL(railG, RX, ry2 + 4, wrap(F.principle_rules[0].text, RW, 10, false).slice(0, 8), { size: 10, cls: 'tm', lh: 12 });
  edge(c, [[CR, pbBand.top + 110], [RX - 2, pbBand.top + 110]], 'cite', {});
  edge(c, [[CR, capBand.top + 60], [RX - 2, capBand.top + 60]], 'cite', {});
  // --- left rail: sources
  const SRC = Object.fromEntries(F.sources.map(s => [s.id, s]));
  const srcItem = s => ({ text: s.label, kind: s.kind === 'source' ? 'nt' : s.kind, mono: true, size: 10.5, dash: s.origin === 'ps' || s.id === 'src:upstream-pstack', tags: [OTAG[s.origin], s.batch], tip: `${s.label}\n${s.note}${srcOf(s)}` });
  const LW = 170;
  group(L.node, 0, pbBand.top + 24, LW, '导入 pstack →', ['src:upstream-pstack', 'src:import_component', 'src:imports.tsv'].map(k => srcItem(SRC[k])), { sub: '复制 playbook、原则、reference、脚本并登记' });
  edge(c, [[LW, pbBand.top + 50], [CX - 1, pbBand.top + 50]], 'install', {});
  group(L.node, 0, capBand.top + 24, LW, '安装技能 →', ['src:upstream', 'src:upstream-diagram-design', 'src:upstream-unlazy', 'src:skills.txt', 'src:merge-notes'].map(k => srcItem(SRC[k])), { sub: 'skills.txt → 软链或 +model-invoked 安装副本' });
  edge(c, [[LW, capBand.top + 50], [CX - 1, capBand.top + 50]], 'install', {});
  group(L.node, 0, stBand.top + 24, LW, '安装 →', [srcItem(SRC['src:install.sh'])], { sub: '安装副本、hook-launcher、installed-root；--check 核对连线' });
  { // D8: the task board reads MMW only through stable interfaces
    const BD = F.board;
    const bg = group(L.node, 0, scBand.top + 24, LW, '← 任务面板读', BD.reads.map(r => ({ text: r.iface, kind: r.iface === 'mmw/roles.json' ? 'config' : 'script', mono: true, size: 10.5, tip: `${r.iface}\n读：${r.what}\n今天：${r.today}\n出处：${BD.src}` })), { sub: 'mmw-v2/board/ 只经这些接口读 MMW，不写死文件位置（D8）', tip: BD.label + '\n' + BD.scope + '\n以后能显示：' + BD.shows_later.join('；') + '\n出处：' + BD.src });
    edge(c, [[CX - 1, scBand.top + 50], [LW + 1, scBand.top + 50]], 'config', { tip: '任务面板经 locations.py 取路径、经 dispatch.sh where 取票的当前步骤、读 roles.json（D8）' });
  }
  edge(c, [[LW, stBand.top + 50], [CX - 1, stBand.top + 50]], 'install', {});
  c.done(y + 6);
  htmlLegend('f1', [...F.edge_kinds.map(k => [k.kind, k.label + (k.line === 'dashed' ? '（虚线）' : k.line === 'dashdot' ? '（点划线）' : '')]),
    ...[['1', '步骤写出脚本命令'], ['2', '查角色表定出唤醒到哪一步'], ['3', '唤醒：一行带指针送回会话']].map(([n, t]) => ({ html: `<span class="nm">${n}</span>${esc(t)}（右侧竖线）` }))], { title: '线的含义' });
  const sw = $('f1').previousElementSibling; if (sw && sw.classList.contains('swipe')) sw.textContent = '← 左右滑动看全图 →　左栏是来源，主图在中间，右栏是原则';
}

function nodeNames() {
  const F = A.fig1, m = { 'board/': 'mmw-v2/board/', mode: 'mode mmw', principles: '原则层（mmw/principles/）' };
  F.entries.forEach(e => m[e.id] = '入口：' + e.label);
  F.mode.sections.forEach(s => m[s.id] = 'mode ## ' + s.label);
  F.roles.forEach(r => m['role:' + r.role] = '角色 ' + r.role + '（roles.json）');
  F.playbook_groups.forEach(g => { m[g.id] = 'playbook 组：' + g.label; g.items.forEach(p => m['pb:' + p.slug] = p.slug); });
  [['capability_groups', '能力技能组：'], ['reference_groups', 'reference 组：'], ['script_groups', '脚本组：']].forEach(([k, pre]) => F[k].forEach(g => { m[g.id] = pre + g.label; g.items.forEach(i => { if (i.id) m[i.id] = (i.owner ? i.owner + '/' : '') + i.label; }); }));
  F.state.forEach(s => m[s.id] = s.label); F.sources.forEach(s => m[s.id] = s.label);
  F.principle_groups.forEach(g => { if (g.id) m[g.id] = '原则组：' + g.label; g.items.forEach(p => { if (p.id) m[p.id] = p.slug; }); });
  return id => m[id] || id;
}
function citeRows() { // principle x citer, one source for figure 1's table, figure 5's catalog and figure 9's matrix
  const CM = PR.fig9_principles.citation_matrix; const cols = Object.fromEntries(CM.columns.map(c => [c.id, c]));
  const pbById = Object.fromEntries(PB.playbooks.map(p => [p.id, p.slug]));
  return CM.cells.map(cl => {
    const col = cols[cl.col]; let fromName;
    if (/^P\d+$/.test(cl.col)) fromName = cl.col + ' ' + pbById[cl.col];
    else if (cl.col === 'P17/P18') fromName = /P18/.test(cl.where) ? 'P17 session-pickup、P18 pause-safely（按需，D6）' : 'P17 session-pickup（按需，D6）';
    else if (cl.col === 'mode') fromName = 'mode mmw';
    else fromName = col.label;
    return { principle: cl.principle, col: cl.col, fromName, where: cl.where.replace(/^被谁点名/, 'R18「被谁点名」列'), src: cl.src };
  });
}
function sec1Tables() {
  tbl('t1-comp', [{ h: '组件', f: r => r.name }, { h: '回答什么问题', f: r => r.question }, { h: '放在哪里', f: r => r.where }, { h: '谁到达它', f: r => r.reached_by }, { h: 'B2 后', f: r => r.count_b2 }, { h: '全部批次后', f: r => r.count_all }, srcCol()], A.components, { title: '七种组件各管什么', open: true });
  tbl('t1-mode', [{ h: '小节', f: r => r.label }, { h: '写什么', f: r => r.note }, { h: '批次', f: r => r.batch || 'B1' }, srcCol()], A.fig1.mode.sections, { title: 'mode 的各节（mmw-v2/skills/mmw/SKILL.md）', intro: A.fig1.mode.frontmatter + '。' + A.fig1.mode.section_count_note });
  const V = A.fig1.dispatch_verbs;
  const BD = A.fig1.board;
  tbl('t1-board', [{ h: '接口', f: r => '`' + r.iface + '`' }, { h: '面板从它读什么', f: r => r.what }, { h: '今天怎样读', f: r => r.today }, { h: '出处', src: true, f: () => BD.src }], BD.reads, { title: '任务面板（mmw-v2/board/）读哪些接口', open: true, intro: '已定（R18 §17 D8）：面板只经这些稳定接口读 MMW，不写死技能目录里的文件位置；' + BD.scope + '。改造后面板可以显示的新信息：' + BD.shows_later.join('；') + '。' });
  tbl('t1-verbs', [{ h: '命令', f: r => r.verb }, { h: '变化', f: r => r.kind }, { h: '说明', f: r => r.note }, srcCol()],
    [...V.new.map(v => ({ ...v, kind: '新增 · ' + v.batch })), ...V.changed.map(v => ({ ...v, kind: '改变' })), { verb: V.existing.join('、'), kind: '沿用', note: '', src: V.src }], { title: 'dispatch.sh 的子命令' });
  list('t1-rules', [...A.fig1.capability_rules, ...A.fig1.principle_rules, ...A.fig1.roles_notes, { text: '新增机制九项：' + A.fig1.new_mechanisms.items.join('、'), src: A.fig1.new_mechanisms.src }], { title: '图中各层的规则' });
  const nn = nodeNames();
  const cite = citeRows();
  const keep = A.fig1.edges.filter(e => !(e.kind === 'cite' && /^(pb|cap):/.test(e.from) && /^pr:/.test(e.to)));
  const rows = keep.map(e => ({ from: nn(e.from), to: nn(e.to), kind: (A.fig1.edge_kinds.find(k => k.kind === e.kind) || {}).label || e.kind, label: e.label + (e.on_demand ? '（按需）' : '') + (e.transitional ? '（过渡）' : ''), src: e.src }))
    .concat(cite.map(r => ({ from: r.fromName, to: 'principle-' + r.principle, kind: '点名原则', label: '按名点名 · ' + r.where, src: r.src })));
  tbl('t1-edges', [{ h: '从', f: r => r.from }, { h: '到', f: r => r.to }, { h: '关系', f: r => r.kind }, { h: '标签', f: r => r.label }, srcCol()], rows, { fold: `全部 ${rows.length} 条连线（图 1 把它们合并成层间箭头；点名原则的 ${cite.length} 条与图 9 点阵同一来源）` });
}

/* ---------- figure 2 ---------- */
const LAYER_SHORT = { 'mode': 'mode', 'playbooks': 'playbooks', 'private-playbooks': '私有 playbook', 'principles': 'principles', 'capability': '纯能力技能', 'upstream': '回上游原文', 'references': 'references', 'scripts': 'mmw/scripts', 'roles': '角色表与配置', 'shared-md': 'shared.md', 'repo-docs': '仓库文档', 'deleted': '删' };
function fig2() {
  const W = 1200, c = mkSvg('f2', W, 1100), L = c.L;
  const layerById = Object.fromEntries(M.layers.map(l => [l.id, l]));
  const typeKind = t => (t === 'neutral' ? 'nt' : t);
  const srcById = Object.fromEntries(M.sources.map(s => [s.id, s]));
  const groupsN = []; M.sources.forEach(s => { if (!groupsN.includes(s.group)) groupsN.push(s.group); });
  const lays = M.layers.filter(l => M.flows.some(f => f.to === l.id));
  const cnt = {}; M.flows.forEach(f => { const k = srcById[f.from].group + '|' + f.to; (cnt[k] = cnt[k] || []).push(f); });
  let y = 4;
  // ---- ① summary matrix: source group x target layer, cell = number of moves
  T(L.node, 0, y + 15, '① 今天的哪一块去了哪一层', { size: 14, cls: 'hd' });
  T(L.node, 210, y + 15, `行是今天的容器（${groupsN.length} 组），列是升级后的层（${lays.length} 层）；格内数字是搬迁条数，格子颜色是目标层的组件类型；悬停看逐条`, { size: 10.5, cls: 'tm' });
  y += 28;
  const RLW = 196, TOTW = 60, CWd = (W - RLW - TOTW) / lays.length, RH = 30;
  let hh = 0; const heads = lays.map(l => wrap(LAYER_SHORT[l.id], CWd - 10, 10.5, isMono(LAYER_SHORT[l.id])));
  hh = Math.max(...heads.map(h => h.length)) * 13 + 12;
  lays.forEach((l, i) => {
    const x = RLW + i * CWd; const g = S('g', { class: kc(typeKind(l.type)) }, L.node);
    R(g, x + 2, y, CWd - 4, hh, { soft: true, r: 4 });
    TL(g, x + CWd / 2, y + 16, heads[i], { size: 10.5, cls: 'b', anchor: 'middle', mono: isMono(LAYER_SHORT[l.id]), lh: 13 });
    tip(g, `${l.label}\n${l.path}\n${l.parts.join('\n')}${srcOf(l)}`);
  });
  T(L.node, RLW + lays.length * CWd + TOTW / 2, y + hh / 2 + 4, '合计', { size: 11, cls: 'b', anchor: 'middle' });
  y += hh + 4;
  const colTot = {};
  groupsN.forEach((gn, ri) => {
    S('rect', { x: 0, y, width: W, height: RH, class: ri % 2 ? 'cellbg' : 'lbg' }, L.bg);
    T(L.node, 6, y + RH / 2 + 4, gn, { size: 11.5, cls: 'b', mono: isMono(gn) });
    let rt = 0;
    lays.forEach((l, i) => {
      const fl = cnt[gn + '|' + l.id]; if (!fl) return;
      rt += fl.length; colTot[l.id] = (colTot[l.id] || 0) + fl.length;
      const x = RLW + i * CWd; const g = S('g', { class: kc(typeKind(l.type)) }, L.node);
      R(g, x + 6, y + 4, CWd - 12, RH - 8, { r: 4 });
      T(g, x + CWd / 2, y + RH / 2 + 4.5, String(fl.length), { size: 12.5, cls: 'b', anchor: 'middle' });
      tip(g, `${gn} → ${l.label}：${fl.length} 条\n` + fl.map(f => `${f.action} · ${f.label}`).join('\n'));
    });
    T(L.node, RLW + lays.length * CWd + TOTW / 2, y + RH / 2 + 4.5, String(rt), { size: 12, cls: 'b', anchor: 'middle' });
    y += RH;
  });
  S('line', { x1: 0, x2: W, y1: y + 1, y2: y + 1, style: 'stroke:var(--ink2);stroke-width:1' }, L.bg);
  T(L.node, 6, y + 19, '合计', { size: 11.5, cls: 'b' });
  lays.forEach((l, i) => T(L.node, RLW + i * CWd + CWd / 2, y + 19, String(colTot[l.id] || 0), { size: 12, cls: 'b', anchor: 'middle' }));
  T(L.node, RLW + lays.length * CWd + TOTW / 2, y + 19, String(M.flows.length), { size: 12.5, cls: 'b', anchor: 'middle' });
  y += 36;
  // ---- ② the target layers, what each one holds
  T(L.node, 0, y + 15, '② 升级后的层：每一层装什么（矩阵的列）', { size: 14, cls: 'hd' }); y += 26;
  const per = 4, LCW = (W - (per - 1) * 10) / per;
  for (let i = 0; i < lays.length; i += per) {
    const row = lays.slice(i, i + per).map((l, j) => {
      const gr = group(L.node, j * (LCW + 10), y, LCW, `${l.label} · 流入 ${colTot[l.id] || 0} 条`, l.parts.map(p => ({ text: p, kind: typeKind(l.type), size: 10, mono: isMono(p) })), { kind: typeKind(l.type), sub: l.path, tip: `${l.label}\n${l.path}\n${l.parts.join('\n')}${srcOf(l)}` });
      return gr;
    });
    const h = Math.max(...row.map(r => r.h)); row.forEach(r => r.rect.setAttribute('height', h));
    y += h + 10;
  }
  y += 14;
  // ---- ③ every move, one row each
  T(L.node, 0, y + 15, `③ ${M.flows.length} 条搬迁逐条`, { size: 14, cls: 'hd' });
  T(L.node, 170, y + 15, '左：今天的文件或小节；中：动作 · 搬走的内容；右：去哪一层（颜色同上）', { size: 10.5, cls: 'tm' });
  y += 30;
  const rowH = 19, X0 = 0, SW = 300, CXc = 312, CWc = 716, TX = 1042, TW = W - TX - 2;
  const flowsBySrc = {}; M.flows.forEach(f => (flowsBySrc[f.from] = flowsBySrc[f.from] || []).push(f));
  let lastGroup = null;
  for (const s of M.sources) {
    const fl = flowsBySrc[s.id] || [];
    if (s.group !== lastGroup) {
      y += 6; T(L.node, X0, y + 13, s.group, { size: 11.5, cls: 'b' });
      S('line', { x1: X0, x2: W, y1: y + 17, y2: y + 17, class: 'sep' }, L.bg);
      y += rowH + 4; lastGroup = s.group;
    }
    const n = Math.max(1, fl.length);
    const sg = S('g', { class: s.owner === 'mattpocock 上游' ? 'k-cap' : s.owner === '脚本文字' || s.owner === '宿主配置' ? 'k-sc' : 'k-nt' }, L.node);
    R(sg, X0 + 6, y + 2, SW - 6, n * rowH - 4, { soft: true, r: 3 });
    const lab = s.label + (s.owner === 'mattpocock 上游' ? '  mp' : '');
    const ll = wrap(lab, SW - 20, 11, isMono(s.label));
    T(sg, X0 + 12, y + 14, ll.length > 1 && n === 1 ? ll[0] + '…' : ll[0], { size: 11, mono: isMono(s.label) });
    if (n > 1 && ll.length > 1) TL(sg, X0 + 12, y + 14 + rowH, ll.slice(1, n), { size: 11, mono: isMono(s.label), lh: rowH });
    tip(sg, `${s.label}\n${s.path}\n${s.owner}${s.lines ? ' · ' + s.lines + ' 行' : ''}${s.note ? '\n' + s.note : ''}${s.files ? '\n' + s.files.join('、') : ''}${srcOf(s)}`);
    fl.forEach((f, i) => {
      const ry = y + i * rowH + rowH / 2;
      const lay = layerById[f.to];
      const g = S('g', null, L.node);
      S('path', { d: `M${SW},${ry} L${CXc},${ry}`, class: 'e e-install' }, g);
      const m = mChip(`${f.action} · ${f.label}`, CWc, { size: 10.5, mono: false, tags: [f.batch] });
      m.h = rowH - 3;
      dChip(g, CXc, ry - m.h / 2, m, { kind: typeKind(lay.type), tip: `${f.action}：${f.label}\n从：${s.label} · ${f.from_part}\n到：${lay.label} · ${f.to_part}\nR14 记号：${f.cats ? f.cats.join('') : '（无）'}\n批次：${f.batch || 'R18 未给批次'}${f.note ? '\n' + f.note : ''}${srcOf(f)}` });
      S('path', { d: `M${CXc + m.w + 2},${ry} L${TX - 2},${ry}`, class: 'sep', style: 'stroke-dasharray:1 3' }, L.bg);
      const tg = S('g', { class: kc(typeKind(lay.type)) }, g);
      R(tg, TX, ry - 7, TW, 14, { r: 7 });
      T(tg, TX + 8, ry + 4, '→ ' + LAYER_SHORT[lay.id], { size: 10, cls: 'b', mono: false });
    });
    y += n * rowH;
  }
  c.done(y + 8);
}

function sec2Tables() {
  tbl('t2-cats', [{ h: '记号', f: r => r.mark }, { h: '内容种类', f: r => r.label }, { h: '是什么', f: r => r.what }, { h: '默认去处', f: r => r.default_to }, srcCol()], M.categories, { title: '七类内容与默认去处（R14 的混装记号）' });
  tbl('t2-skills', [{ h: '技能', w: '150px', f: r => r.name }, { h: '升级后只剩', w: '52%', f: r => r.after }, { h: '剥离的内容去了哪里', f: r => [...new Set((r.stripped || []).map(s => s.to))].join('；') || '—' }], M.skills, { open: true, minW: 760, intro: '每一段剥离了什么、各去哪一处，在下面的全列表里逐条写出。' });
  tbl('t2-skills', [{ h: '技能', w: '118px', f: r => r.name }, { h: '来源', w: '72px', f: r => r.origin + (r.installed_now ? '' : '（今天未安装）') }, { h: '混装', w: '52px', f: r => (r.mixes || []).join('') }, { h: '行数 今天 → 纯能力', w: '86px', f: r => r.lines_now == null ? '—' : `${r.lines_now} → ${r.lines_pure_est ? '约 ' : ''}${r.lines_pure}` }, { h: '升级后只剩', w: '210px', f: r => r.after }, { h: '剥离的内容 → 去处', w: '290px', lines: true, f: r => (r.stripped || []).map(s => s.what + ' → ' + s.to) }, { h: '调用开关', w: '76px', f: r => r.switch || '' }, { h: '批次', w: '52px', f: r => r.batch || 'R18 未给' }, { h: '说明', w: '150px', f: r => r.note || '' }, { h: '出处', src: true, f: r => r.after_src + '；' + r.mixes_src }], M.skills, { minW: 1100, title: '能力技能变纯：全部列（来源、混装、行数、调用开关、批次、说明、出处）', intro: '行数取自 R14 第 6 节，标「约」的是 R14 的推断，早于 R18 的改判。' });
  const U = M.upstream_rule;
  para('t2-upstream', `<h3>上游目录今后只允许两类改动</h3><ul class="tight">${U.allowed.map(a => `<li><b>${esc(a.kind)}</b>：${codeify(a.what)}（${esc(a.why)}）</li>`).join('')}<li>${esc(U.never)}。</li><li>${codeify(U.switch)}</li><li>核对：${codeify(U.checked_by)}</li></ul><p class="srcnote">${esc(U.src)}</p>`);
  tbl('t2-more', [{ h: '留下的内容', f: r => r.what }, { h: '留下的理由（硬约束）', f: r => r.why }, srcCol()], M.stays, { title: '按类型本该搬走、因硬约束留下的全部例外' });
  tbl('t2-more', [{ h: '编号', f: r => r.id }, { h: '天然整体', f: r => r.whole }, { h: '拆开会怎样', f: r => r.break_if_split }, { h: '处理', f: r => r.handling }, srcCol()], M.natural_wholes, { title: '天然整体 W1–W7（要一起搬、同一次提交里改）' });
  tbl('t2-more', [{ h: '编号', f: r => r.id }, { h: '规则', f: r => r.rule }, { h: '位置 / 文件 / 技能', f: r => r.count || '' }, { h: '去处', f: r => r.to }, srcCol()], M.scattered_rules, { title: '散落的跨任务规则 PC1–PC29 与去处' });
  tbl('t2-more', [{ h: 'mode 的节', f: r => r.section }, { h: '今天散在哪里', f: r => r.scattered_in }, { h: '处数', f: r => r.places }, srcCol()], M.mode_sources, { title: 'mode 常驻节的内容今天散在哪里' });
  tbl('t2-more', [{ h: '「下一步」句的位置', f: r => r.where }, { h: '去处', f: r => r.to }, srcCol()], M.next_step_sentences, { title: '17 句「下一步用 X」的去处' });
  tbl('t2-more', [{ h: '量', f: r => r.what }, { h: '数值', f: r => r.value }, srcCol()], M.counts, { title: '图 2 周边的数字' });
  tbl('t2-more', [{ h: 'R14 候选', f: r => r.r14 }, { h: 'R18 定稿', f: r => r.r18 }, srcCol()], M.r14_playbook_map, { fold: 'R14 的 playbook 候选编号与 R18 定稿的对照' });
  const srcName = Object.fromEntries(M.sources.map(x => [x.id, x.label])), layName = Object.fromEntries(M.layers.map(x => [x.id, x.label]));
  tbl('t2-more', [{ h: '从', f: r => srcName[r.from] + ' · ' + r.from_part }, { h: '到', f: r => layName[r.to] + ' · ' + r.to_part }, { h: '动作', f: r => r.action }, { h: '标签', f: r => r.label }, { h: '记号', f: r => (r.cats || []).join('') }, { h: '批次', f: r => r.batch || 'R18 未给' }, { h: '说明', f: r => r.note || '' }, srcCol()], M.flows, { fold: `图 2 的 ${M.flows.length} 条搬迁逐条` });
}
