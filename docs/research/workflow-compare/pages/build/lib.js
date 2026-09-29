/* ---------- core layout helpers ---------- */
const NS = 'http://www.w3.org/2000/svg';
function S(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  if (attrs) for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function esc(s) { return String(s == null ? '' : s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;'); }
function codeify(s) { // escape, then wrap `x` in <code>
  return esc(s).replace(/`([^`]+)`/g, '<code>$1</code>').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
}
function charW(c, mono) {
  const cp = c.codePointAt(0);
  if (cp >= 0x2E80 || (cp >= 0x2190 && cp <= 0x2BFF) || (cp >= 0x2018 && cp <= 0x201F) || cp === 0x2026 || cp === 0x00B7 && !mono) return 1.0;
  if (mono) return 0.61;
  if (/[A-Z]/.test(c)) return 0.66;
  if (/[mwMW]/.test(c)) return 0.85;
  if (/[il.,:;'|!()\[\] ]/.test(c)) return 0.34;
  return 0.57;
}
function tw(s, size, mono) { let w = 0; for (const c of String(s)) w += charW(c, mono); return w * size; }
const CLOSE_P = '、，。；：）」』》！？,.;:)]';
const OPEN_P = '（「『《([';
function tokens(s) { // strong break points: spaces, CJK characters, CJK punctuation, arrows, middle dots
  const out = []; let cur = '', pre = '';
  const flush = () => { if (cur) { out.push(pre + cur); cur = ''; pre = ''; } };
  for (const c of String(s)) {
    const cp = c.codePointAt(0);
    const wide = cp >= 0x2E80 || c === '→' || c === '·' || c === '…';
    if (OPEN_P.includes(c) && wide) { flush(); pre += c; continue; }
    if (CLOSE_P.includes(c) && wide) { if (cur) { cur += c; flush(); } else if (pre) { pre += c; } else if (out.length) out[out.length - 1] += c; else out.push(c); continue; }
    if (wide) { flush(); out.push(pre + c); pre = ''; continue; }
    if (c === ' ') { cur += c; flush(); continue; }
    cur += c;
  }
  flush(); if (pre) out.push(pre);
  return out;
}
function weakSplit(tk) { // soft break points inside one identifier: after / - _ . , :
  const parts = []; let cur = '';
  for (const c of tk) { cur += c; if ('/-_.,:'.includes(c)) { parts.push(cur); cur = ''; } }
  if (cur) parts.push(cur);
  const merged = [];
  for (const p of parts) { if (merged.length && (merged[merged.length - 1].length < 3 || p.trim().length <= 3)) merged[merged.length - 1] += p; else merged.push(p); }
  return merged;
}
window.__hard = []; window.__weak = [];
function wrap(s, maxW, size, mono) {
  s = String(s == null ? '' : s);
  const lines = []; let line = '';
  const fits = t => tw(t, size, mono) <= maxW;
  const push = () => { lines.push(line.trimEnd()); line = ''; };
  for (const tk of tokens(s)) {
    if (fits(line + tk)) { line += tk; continue; }
    if (line && fits(tk.trimStart())) { push(); line = tk.trimStart(); continue; }
    if (mono || /^[\x21-\x7E]+$/.test(tk.trim())) window.__weak.push(tk.trim() + ' @' + Math.round(maxW));
    for (const pc of weakSplit(tk)) {
      if (fits(line + pc)) { line += pc; continue; }
      if (line) push();
      let piece = pc.trimStart();
      if (!fits(piece)) {
        window.__hard.push(s);
        let part = '';
        for (const c of piece) { if (!fits(part + c) && part) { lines.push(part); part = ''; } part += c; }
        piece = part;
      }
      line = piece;
    }
  }
  if (line.trim()) push();
  for (let i = 1; i < lines.length; i++) { // no line starts with closing punctuation
    while (lines[i] && CLOSE_P.includes(lines[i][0])) { lines[i - 1] += lines[i][0]; lines[i] = lines[i].slice(1); }
  }
  const res = lines.filter(l => l !== '');
  return res.length ? res : [''];
}
const KIND = { mode: 'mode', playbook: 'pb', capability: 'cap', reference: 'ref', principle: 'pr', script: 'sc', config: 'cfg' };
function kc(kind) { return 'k-' + (KIND[kind] || (Object.values(KIND).includes(kind) ? kind : 'nt')); }
function isMono(s) { return /^[\x00-\x7F<>]+$/.test(String(s)) && /[a-z_.\/#-]/.test(String(s)); }

function T(p, x, y, s, o = {}) {
  const size = o.size || 12;
  const t = S('text', { x, y, 'font-size': size, 'text-anchor': o.anchor || null, class: [o.mono ? 'mono' : '', o.cls || ''].join(' ').trim() || null, 'dominant-baseline': o.baseline || null }, p);
  t.textContent = s; return t;
}
function TL(p, x, y, lines, o = {}) {
  const size = o.size || 12, lh = o.lh || Math.round(size * 1.35);
  lines.forEach((ln, i) => T(p, x, y + i * lh, ln, o));
  return lines.length * lh;
}
function tip(g, s) { if (s) g.setAttribute('data-tip', s); return g; }
function srcOf(o) { return o && o.src ? '\n出处：' + o.src : ''; }

/* rect box */
function R(p, x, y, w, h, o = {}) {
  return S('rect', { x, y, width: w, height: h, rx: o.r == null ? 5 : o.r, class: o.cls || ('bx ' + (o.soft ? 'soft ' : '') + (o.dash ? 'dash ' : '') + (o.dim ? 'dim' : '')) }, p);
}

/* chip: measure then draw */
function mChip(text, maxW, o = {}) {
  const size = o.size || 11, mono = o.mono != null ? o.mono : isMono(text);
  const tags = (o.tags || []).filter(Boolean);
  const tagW = tags.reduce((a, t) => a + tw(t, 9, false) + 9, 0);
  const pad = 7;
  const inner = maxW - 2 * pad - tagW;
  const lines = wrap(text, inner, size, mono);
  const textW = Math.max(...lines.map(l => tw(l, size, mono)));
  const lh = Math.round(size * 1.3);
  return { lines, w: Math.min(maxW, Math.ceil(textW + 2 * pad + tagW)), h: lines.length * lh + 8, lh, size, mono, tags, tagW };
}
function dChip(p, x, y, m, o = {}) {
  const g = S('g', { class: kc(o.kind) }, p);
  R(g, x, y, m.w, m.h, { dash: o.dash, soft: o.soft, dim: o.dim, r: 4 });
  m.lines.forEach((ln, i) => T(g, x + 7, y + 4 + m.size + i * m.lh - 1, ln, { size: m.size, mono: m.mono, cls: o.bold ? 'b' : '' }));
  let tx = x + m.w - 4;
  for (let i = m.tags.length - 1; i >= 0; i--) {
    const t = m.tags[i]; const w = tw(t, 9) + 7; tx -= w;
    R(g, tx, y + 3, w, 13, { cls: 'tagbg', r: 3 });
    T(g, tx + 3.5, y + 13, t, { size: 9, cls: 't2' });
    tx -= 2;
  }
  tip(g, o.tip);
  return g;
}
function chip(p, x, y, text, maxW, o = {}) { const m = mChip(text, maxW, o); dChip(p, x, y, m, o); return m; }

/* flow of chips inside width */
function flow(p, x, y, w, items, o = {}) {
  const gap = o.gap || 5; let cx = x, cy = y, rowH = 0;
  const pos = [];
  for (const it of items) {
    const m = mChip(it.text, it.maxW || w, { size: it.size || o.size, mono: it.mono, tags: it.tags });
    if (cx > x && cx + m.w > x + w) { cx = x; cy += rowH + gap; rowH = 0; }
    const g = dChip(p, cx, cy, m, it);
    pos.push({ it, x: cx, y: cy, w: m.w, h: m.h, g });
    cx += m.w + gap; rowH = Math.max(rowH, m.h);
  }
  return { h: items.length ? cy + rowH - y : 0, pos };
}

/* group container with title + chips */
function group(p, x, y, w, title, items, o = {}) {
  const g = S('g', { class: o.kind ? kc(o.kind) : null }, p);
  const rect = R(g, x, y, w, 10, { cls: o.kind ? ('bx soft' + (o.dash ? ' dash' : '')) : ('grp' + (o.dash ? ' dash' : '')) });
  let cy = y + 16;
  const tl = wrap(title, w - 14, 12, false);
  tl.forEach((ln, i) => T(g, x + 7, cy + i * 15, ln, { size: 12, cls: 'b' }));
  cy += (tl.length - 1) * 15 + 4;
  if (o.sub) { const sl = wrap(o.sub, w - 14, 10.5, false); sl.forEach((ln, i) => T(g, x + 7, cy + 12 + i * 13, ln, { size: 10.5, cls: 'tm' })); cy += sl.length * 13 + 2; }
  cy += 6;
  const f = flow(g, x + 7, cy, w - 14, items, o);
  const h = cy - y + f.h + 8;
  rect.setAttribute('height', h);
  tip(g, o.tip);
  return { h, rect, pos: f.pos, g };
}

/* svg scaffold */
const MARKER_KINDS = ['route', 'call', 'run', 'events', 'evt', 'deny', 'cite', 'install', 'wake', 'config', 'check', 'say', 'prompt', 'read', 'refusal', 'return', 'user'];
function addMarkers(defs, pre) {
  for (const k of MARKER_KINDS) {
    if (k === 'evt') { // events on the ticket: hollow circle at the receiving end
      const m = S('marker', { id: pre + k, viewBox: '0 0 12 12', refX: 10.5, refY: 6, markerWidth: 10, markerHeight: 10, markerUnits: 'userSpaceOnUse', orient: 'auto' }, defs);
      S('circle', { cx: 6, cy: 6, r: 4.2, class: 'mk-evt-o' }, m); continue;
    }
    const m = S('marker', { id: pre + k, viewBox: '0 0 10 10', refX: 9, refY: 5, markerWidth: 8, markerHeight: 8, markerUnits: 'userSpaceOnUse', orient: 'auto-start-reverse' }, defs);
    S('path', { d: 'M0,0 L10,5 L0,10 z', class: 'mk-' + k }, m);
  }
}
/* legend as an HTML row under a figure's diagram, so it wraps on a phone instead of being cut off with the scrolled svg */
let LGDEFS = false;
function htmlLegend(hostId, items, o = {}) {
  if (!LGDEFS) { const d = document.createElementNS(NS, 'svg'); d.setAttribute('width', 0); d.setAttribute('height', 0); d.setAttribute('aria-hidden', 'true'); d.style.position = 'absolute'; addMarkers(S('defs', null, d), 'lgm-'); document.body.appendChild(d); LGDEFS = true; }
  const html = items.map(it => {
    if (it.html) return `<span class="it">${it.html}</span>`;
    const [k0, lab, sty] = it; const k = ek(k0);
    let sw;
    if (k0 === 'self') sw = `<svg width="30" height="14" viewBox="0 0 30 14" aria-hidden="true"><path d="M4,3 L16,3 L16,11 L6,11" class="e e-return" marker-end="url(#lgm-return)"/></svg>`;
    else sw = `<svg width="38" height="12" viewBox="0 0 38 12" aria-hidden="true"><path d="M2,6 L${k === 'evt' ? 30 : 34},6" class="e e-${k}"${sty ? ` style="${sty}"` : ''} marker-end="url(#lgm-${k})"/></svg>`;
    return `<span class="it">${sw}${esc(lab)}</span>`;
  }).join('');
  const host = $(hostId);
  host.insertAdjacentHTML('afterend', `<div class="elegend">${o.title ? `<b>${esc(o.title)}</b>` : ''}${html}</div>`);
}
let SVGN = 0;
function mkSvg(hostId, W, minW) {
  const host = document.getElementById(hostId);
  if (!(host.previousElementSibling && host.previousElementSibling.classList.contains('swipe'))) host.insertAdjacentHTML('beforebegin', '<div class="swipe">← 左右滑动看全图 →</div>');
  const id = 'sv' + (++SVGN);
  const svg = S('svg', { id, role: 'img', xmlns: NS }, host);
  svg.style.minWidth = (minW || Math.min(W, 1100)) + 'px';
  const defs = S('defs', null, svg);
  addMarkers(defs, id + '-');
  const L = { bg: S('g', null, svg), edge: S('g', null, svg), node: S('g', null, svg), lab: S('g', null, svg) };
  const cap = host.closest('figure') && host.closest('figure').querySelector('figcaption');
  if (cap) svg.setAttribute('aria-label', cap.textContent.trim());
  return { svg, id, L, W, P: new Placer(), done(H) { svg.setAttribute('viewBox', `0 0 ${W} ${Math.ceil(H)}`); } };
}
const EKIND = { handoff: 'route', starts: 'run', tell_user: 'user', command: 'run', event: 'events', ev: 'events', note: 'return' };
function ek(k) { return EKIND[k] || k; }
function edge(ctx, pts, kind, o = {}) {
  kind = ek(kind);
  let d;
  if (o.curve && pts.length === 2) {
    const [a, b] = pts; const v = o.curve === 'v';
    const mx = (a[0] + b[0]) / 2, my = (a[1] + b[1]) / 2;
    d = v ? `M${a[0]},${a[1]} C${a[0]},${my} ${b[0]},${my} ${b[0]},${b[1]}` : `M${a[0]},${a[1]} C${mx},${a[1]} ${mx},${b[1]} ${b[0]},${b[1]}`;
  } else d = 'M' + pts.map(p => p.join(',')).join(' L');
  const g = S('g', { class: o.gcls || null }, o.layer || ctx.L.edge);
  S('path', { d, class: 'e e-' + kind, 'marker-end': o.noHead ? null : `url(#${ctx.id}-${kind})`, 'marker-start': o.both ? `url(#${ctx.id}-${kind})` : null }, g);
  tip(g, o.tip);
  if (o.label) {
    const cands = o.cands || [midOf(pts, o.curve)];
    label(ctx, o.label, cands, o);
  }
  return g;
}
function midOf(pts, curve) {
  if (pts.length === 2) return [(pts[0][0] + pts[1][0]) / 2, (pts[0][1] + pts[1][1]) / 2];
  // longest segment midpoint
  let best = 0, bi = 0;
  for (let i = 0; i < pts.length - 1; i++) { const l = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]); if (l > best) { best = l; bi = i; } }
  return [(pts[bi][0] + pts[bi + 1][0]) / 2, (pts[bi][1] + pts[bi + 1][1]) / 2];
}
class Placer {
  constructor() { this.obs = []; }
  add(x, y, w, h) { this.obs.push([x, y, w, h]); }
  free(x, y, w, h) { return !this.obs.some(r => x < r[0] + r[2] && x + w > r[0] && y < r[1] + r[3] && y + h > r[1]); }
  cost(x, y, w, h) { let a = 0; for (const r of this.obs) a += Math.max(0, Math.min(x + w, r[0] + r[2]) - Math.max(x, r[0])) * Math.max(0, Math.min(y + h, r[1] + r[3]) - Math.max(y, r[1])); return a; }
}
function label(ctx, text, cands, o = {}) {
  const size = o.lsize || 10.5, mono = o.lmono != null ? o.lmono : false;
  const lines = o.lmax ? wrap(text, o.lmax, size, mono) : [text];
  const w = Math.max(...lines.map(l => tw(l, size, mono))) + 8, lh = size + 3, h = lines.length * lh + 4;
  const offs = [[0, 0], [0, -h - 2], [0, h + 2], [-w / 2 - 6, 0], [w / 2 + 6, 0], [0, -2 * h], [0, 2 * h], [-w, -h], [w, h], [-w, h], [w, -h], [0, -3 * h], [0, 3 * h], [-w - 10, 0], [w + 10, 0]];
  let pick = null;
  outer: for (const of of offs) for (const c of cands) {
    const x = c[0] - w / 2 + of[0], y = c[1] - h / 2 + of[1];
    if (ctx.P.free(x, y, w, h) && x >= 0 && x + w <= ctx.W) { pick = [x, y]; break outer; }
  }
  if (!pick) {
    let best = 1e18;
    for (const of of offs.concat([[0, -4 * h], [0, 4 * h], [0, -5 * h], [0, 5 * h]])) for (const c of cands) {
      const x = c[0] - w / 2 + of[0], y = c[1] - h / 2 + of[1]; if (x < 0 || x + w > ctx.W) continue;
      const k = ctx.P.cost(x, y, w, h) + Math.hypot(of[0], of[1]) * 0.5; if (k < best) { best = k; pick = [x, y]; }
    }
    if (!pick) pick = [cands[0][0] - w / 2, cands[0][1] - h / 2];
  }
  const [x, y] = pick;
  ctx.P.add(x, y, w, h);
  const g = S('g', null, ctx.L.lab);
  S('rect', { x, y, width: w, height: h, rx: 3, class: 'lbg' }, g);
  lines.forEach((ln, i) => T(g, x + 4, y + 2 + size + i * lh - 1, ln, { size, mono, cls: o.lcls || 't2' }));
  return g;
}
function labelAt(ctx, text, x, yc, o = {}) { const w = tw(text, o.lsize || 10.5, o.lmono) + 8; return label(ctx, text, [[x + w / 2, yc]], o); }
function vlabel(ctx, x, y, text, o = {}) { // vertical label centered at (x,y)
  const size = o.size || 10.5; const h = tw(text, size) + 8, w = size + 6;
  const g = S('g', null, ctx.L.lab);
  S('rect', { x: x - w / 2, y: y - h / 2, width: w, height: h, rx: 3, class: 'lbg' }, g);
  const t = T(g, x, y - h / 2 + 4, text, { size, cls: 't2' });
  t.setAttribute('style', 'writing-mode:vertical-rl;text-orientation:upright');
  t.setAttribute('x', x); t.setAttribute('y', y - h / 2 + 4);
  return g;
}
function legendRow(ctx, x, y, kinds) {
  let cx = x;
  for (const [k, lab] of kinds) {
    edge(ctx, [[cx, y], [cx + 30, y]], k, { layer: ctx.L.node });
    T(ctx.L.node, cx + 36, y + 4, lab, { size: 11, cls: 't2' });
    cx += 46 + tw(lab, 11) + 16;
    if (cx > ctx.W - 150) { cx = x; y += 18; }
  }
  return y + 12;
}

/* ---------- HTML helpers ---------- */
function $(id) { return document.getElementById(id); }
function tbl(hostId, cols, rows, o = {}) {
  const host = typeof hostId === 'string' ? $(hostId) : hostId; if (!host) return;
  const foldT = o.fold || (!o.open && o.title ? `展开：${o.title}（${rows.length} 行）` : null);
  const introH = o.intro ? `<p class="sub">${codeify(o.intro)}</p>` : '';
  const h3 = o.title ? `<h3>${esc(o.title)}</h3>` : '';
  const fixed = cols.some(c => c.w);
  const tstyle = o.minW ? ` style="min-width:${o.minW}px"` : '';
  let t = `<div class="tw"><table class="${fixed ? 'fixed' : ''}"${tstyle}>`;
  if (fixed) t += `<colgroup>${cols.map(c => `<col style="width:${c.w || (c.src ? '140px' : 'auto')}">`).join('')}</colgroup>`;
  t += `<thead><tr>${cols.map(c => `<th class="${c.src ? 'src' : ''}">${esc(c.h)}</th>`).join('')}</tr></thead><tbody>`;
  for (const r of rows) t += `<tr>${cols.map(c => {
    let v = c.f(r);
    if (Array.isArray(v)) v = c.lines ? v.map(x => `<span class="ln">${c.raw ? x : codeify(x)}</span>`).join('') : (c.raw ? v.join('；') : codeify(v.join('；')));
    else v = c.raw ? (v == null ? '' : v) : codeify(v == null ? '' : v);
    return `<td class="${c.src ? 'src' : ''}">${v}</td>`; }).join('')}</tr>`;
  t += '</tbody></table></div>';
  let h;
  if (!foldT) h = h3 + introH + t;
  else if (o.fold) h = h3 + introH + `<details><summary>${esc(foldT)}</summary>${t}</details>`;
  else h = `<details><summary>${esc(foldT)}</summary>${introH}${t}</details>`;
  host.insertAdjacentHTML('beforeend', h);
}
function para(hostId, html) { $(hostId).insertAdjacentHTML('beforeend', html); }
function list(hostId, items, o = {}) {
  const foldT = o.fold || (!o.open && o.title ? `展开：${o.title}（${items.length} 条）` : null);
  let h = o.title && !foldT ? `<h3>${esc(o.title)}</h3>` : '';
  const body = `<ul class="tight">${items.map(i => `<li>${typeof i === 'string' ? codeify(i) : codeify(i.text) + (i.src ? ` <span class="srcnote">（${esc(i.src)}）</span>` : '')}</li>`).join('')}</ul>`;
  h += foldT ? `<details><summary>${esc(foldT)}</summary>${body}</details>` : body;
  $(hostId).insertAdjacentHTML('beforeend', h);
}
function srcCol() { return { h: '出处', src: true, f: r => r.src || '' }; }
function jwakes(w) { if (!w) return ''; if (Array.isArray(w)) return w.map(x => `${x.event} → ${x.step}`).join('；'); const k = Object.keys(w); return k.length ? k.map(e => `${e} → ${w[e]}`).join('；') : '{}（一次性会话）'; }

/* tooltip */
(function () {
  const tipEl = () => $('tip');
  let pinned = null;
  function show(el, x, y) {
    const t = tipEl(); t.textContent = el.getAttribute('data-tip'); t.hidden = false;
    const r = t.getBoundingClientRect();
    let px = x + 14, py = y + 14;
    if (px + r.width > innerWidth - 8) px = Math.max(8, x - r.width - 14);
    if (py + r.height > innerHeight - 8) py = Math.max(8, y - r.height - 14);
    t.style.left = px + 'px'; t.style.top = py + 'px';
  }
  document.addEventListener('mousemove', e => { if (pinned) return; const el = e.target.closest && e.target.closest('[data-tip]'); if (el) show(el, e.clientX, e.clientY); else tipEl().hidden = true; });
  document.addEventListener('click', e => { const el = e.target.closest && e.target.closest('[data-tip]'); if (el) { pinned = el; show(el, e.clientX, e.clientY); } else { pinned = null; tipEl().hidden = true; } });
  document.addEventListener('scroll', () => { if (pinned) { pinned = null; tipEl().hidden = true; } }, { passive: true });
})();
