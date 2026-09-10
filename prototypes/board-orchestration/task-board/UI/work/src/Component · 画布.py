# The centre: one task's tree on a pan-and-zoom canvas. Cards are template markup; the lines
# (trunk, expand, blocking curves and their beams) are one SVG drawn after each render,
# since they are computed geometry and nobody polishes them from the editor.
# Build: DC_FX=FIXTURES DC_FRAME=864x848 python3 mk.py "src/Component · 画布.py"
NAME = "Component · 画布"
CSS = ["tokens.css", "board.css"]
EXTRA_CSS = "          .sc-host { height: 100%; }"   # an imported component's host fills the slot the page gives it
PROPS = {
  "scene": {"editor": "enum", "default": "morning", "tsType": "string",
            "options": ["morning", "twenty-tickets", "bad-data", "empty", "nothing-selected"]},
}
TEMPLATE = r'''      <main class="canvas board" data-screen-label="画布" aria-label="画布：拖动平移，按住 ⌘ 或双指捏合缩放" ref="{{ rf.canvas }}" onPointerDown="{{ down }}">
        <sc-if value="{{ v.hasTask }}" hint-placeholder-val="{{ true }}">
          <div class="world" ref="{{ rf.world }}" style="{{ v.worldSize }}">
            <div class="edges-host" ref="{{ rf.edges }}"></div>
            <sc-for list="{{ v.labels }}" as="lb" hint-placeholder-count="2">
              <div class="{{ lb.cls }}" style="{{ lb.pos }}">{{ lb.text }}</div>
            </sc-for>
            <sc-for list="{{ containers }}" as="c" hint-placeholder-count="3">
              <div class="{{ c.cls }}" style="{{ c.pos }}" onClick="{{ c.pick }}">
                <div class="card-top"><span class="{{ c.lightCls }}" title="{{ c.lightWord }}"></span><span class="card-num">{{ c.num }}</span>
                  <span class="card-right"><span class="card-count">{{ c.count }}</span><sc-if value="{{ c.canExpand }}" hint-placeholder-val="{{ true }}"><button type="button" class="chev" onClick="{{ c.toggle }}" aria-label="{{ c.toggleLabel }}">{{ c.chev }}</button></sc-if></span></div>
                <div class="{{ c.titleCls }}">{{ c.title }}</div>
                <div class="card-bar"><div class="card-bar-fill" style="{{ c.barStyle }}"></div></div>
              </div>
            </sc-for>
            <sc-for list="{{ decisions }}" as="d" hint-placeholder-count="3">
              <div class="{{ d.cls }}" style="{{ d.pos }}" onClick="{{ d.pick }}" title="{{ d.title }}">
                <div class="card-top"><span class="{{ d.lightCls }}"></span><span class="card-num">{{ d.num }}</span><span class="card-right"><span class="card-kind">{{ d.kind }}</span></span></div>
                <div class="card-title decision">{{ d.title }}</div>
              </div>
            </sc-for>
            <sc-for list="{{ tickets }}" as="t" hint-placeholder-count="5">
              <div class="{{ t.cls }}" style="{{ t.pos }}" onClick="{{ t.pick }}" title="{{ t.title }}">
                <div class="card-top"><span class="{{ t.lightCls }}" title="{{ t.lightWord }}"></span><span class="card-num">{{ t.num }}</span><span class="card-right"><span class="{{ t.pillCls }}">{{ t.step }}</span></span></div>
                <div class="card-title">{{ t.title }}</div>
                <div class="{{ t.runCls }}">{{ t.run }}</div>
              </div>
            </sc-for>
          </div>
          <div class="legend">
            <span class="legend-item"><span class="legend-line"></span>展开 · 走过</span>
            <span class="legend-item"><span class="legend-line flow"></span>在走</span>
            <span class="legend-item"><span class="legend-line blocked"></span>被挡</span>
            <span class="legend-item"><span class="legend-bar"></span>收口新开</span>
          </div>
          <div class="zoom">
            <button type="button" class="zoom-btn" aria-label="缩小" onClick="{{ zoomOut }}">−</button>
            <span class="zoom-level" ref="{{ rf.zoom }}">100%</span>
            <button type="button" class="zoom-btn" aria-label="放大" onClick="{{ zoomIn }}">+</button>
            <span class="zoom-sep"></span>
            <button type="button" class="zoom-btn text" onClick="{{ fit }}">适配</button>
          </div>
        </sc-if>
        <sc-if value="{{ v.noTask }}" hint-placeholder-val="{{ false }}">
          <div class="canvas-empty"><div>
            <p class="canvas-empty-title">还没有任务</p>
            <p class="canvas-empty-text">一个任务就是一次讨论开出的那张票。给它打上 <span class="code">mmw:map</span> label，下一次读取时它和它下面的 spec、ticket 就会出现在这里。</p>
          </div></div>
        </sc-if>
      </main>'''
LOGIC = r'''        dataKey() {
          const B = window.MMWBoard;
          return ((B && B.CANVAS_SCENES[this.props.scene]) || { data: "morning" }).data;
        }
        init(props) {
          this.view = this.view || { x: 20, y: 12, k: 1 };
          this.rf = this.rf || {
            canvas: el => { this.canvasEl = el; if (el) this.bind(); },
            world: el => { this.worldEl = el; },
            edges: el => { this.edgesEl = el; if (el) el.__svg = null; },
            zoom: el => { this.zoomEl = el; },
          };
          const B = window.MMWBoard;
          if (!B) return { task: null, sel: null, expanded: [] };
          const cs = B.CANVAS_SCENES[props.scene] || B.CANVAS_SCENES.morning;
          const data = B.scene(cs.data);
          const task = props.task !== undefined ? props.task : (data.select.task != null ? data.select.task : ((data.tasks[0] || {}).n ?? null));
          const sel = props.sel !== undefined ? props.sel : ("node" in cs ? cs.node : (data.select.node ?? null));
          const t = data.tasks.find(x => x.n === task);
          const expanded = t ? B.defaultExpanded(t) : [];
          const c = sel != null ? B.containerOf(cs.data, sel) : null;
          if (c != null && !expanded.includes(c)) expanded.push(c);
          this._resetView = true;
          return { task, sel, expanded };
        }
        onReady() { this.setState(this.init(this.props)); }
        bind() {
          if (this._bound || !this.canvasEl) return;
          this._bound = true;
          this._wheel = e => {
            if (!this.lastView || !this.lastView.layout) return;
            e.preventDefault();
            const r = this.canvasEl.getBoundingClientRect();
            if (e.ctrlKey || e.metaKey) this.zoomAt(this.view.k * Math.exp(-e.deltaY * 0.01), e.clientX - r.left, e.clientY - r.top);
            else { this.view.x -= e.deltaX; this.view.y -= e.deltaY; this.applyView(); }
          };
          this._move = e => {
            const d = this.drag;
            if (!d || e.pointerId !== d.id) return;
            const dx = e.clientX - d.x, dy = e.clientY - d.y;
            if (!d.moved && Math.hypot(dx, dy) > 4) { d.moved = true; this.canvasEl.classList.add("dragging"); }
            if (d.moved) { this.view.x = d.vx + dx; this.view.y = d.vy + dy; this.applyView(); }
          };
          this._up = e => {
            const d = this.drag;
            if (!d || e.pointerId !== d.id) return;
            this.drag = null;
            this.canvasEl.classList.remove("dragging");
            if (d.moved) { this.suppress = true; setTimeout(() => { this.suppress = false; }, 0); }
          };
          this._key = e => {
            if (e.target.closest && e.target.closest("input, textarea, [contenteditable]")) return;
            if (e.key === "f" && !e.metaKey && !e.ctrlKey) this.fitView();
          };
          this.canvasEl.addEventListener("wheel", this._wheel, { passive: false });
          window.addEventListener("pointermove", this._move);
          window.addEventListener("pointerup", this._up);
          window.addEventListener("keydown", this._key);
        }
        cleanup() {
          if (this.canvasEl && this._wheel) this.canvasEl.removeEventListener("wheel", this._wheel);
          window.removeEventListener("pointermove", this._move);
          window.removeEventListener("pointerup", this._up);
          window.removeEventListener("keydown", this._key);
        }
        afterUpdate(prev) {
          const B = window.MMWBoard;
          if (B && this.props.task !== undefined && this.props.task !== prev.task && this.props.task !== this.state.task) {
            const data = B.scene(this.dataKey());
            const t = data.tasks.find(x => x.n === this.props.task);
            const expanded = t ? B.defaultExpanded(t) : [];
            const sel = this.props.sel !== undefined ? this.props.sel : null;
            const c = sel != null ? B.containerOf(this.dataKey(), sel) : null;
            if (c != null && !expanded.includes(c)) expanded.push(c);
            this._resetView = true;
            this._reveal = sel;
            this.setState({ task: this.props.task, sel, expanded });
            return;
          }
          if (B && this.props.sel !== undefined && this.props.sel !== prev.sel && this.props.sel !== this.state.sel) {
            const c = this.props.sel != null ? B.containerOf(this.dataKey(), this.props.sel) : null;
            const expanded = c != null && !this.state.expanded.includes(c) ? this.state.expanded.concat([c]) : this.state.expanded;
            this._reveal = this.props.sel;
            this.setState({ sel: this.props.sel, expanded });
            return;
          }
          this.paint();
        }
        paint() {
          if (!this.lastView || !this.lastView.layout || !this.worldEl) return;
          if (this.edgesEl && this.edgesEl.__svg !== this.lastView.svg) { this.edgesEl.innerHTML = this.lastView.svg; this.edgesEl.__svg = this.lastView.svg; }
          if (this._resetView) { this._resetView = false; this.initialView(); }
          if (this._reveal != null) { const n = this._reveal; this._reveal = null; this.ensureVisible(n); }
          this.applyView();
        }
        applyView() {
          const v = this.view;
          if (this.worldEl) this.worldEl.style.transform = "translate(" + v.x + "px, " + v.y + "px) scale(" + v.k + ")";
          if (this.zoomEl) this.zoomEl.textContent = Math.round(v.k * 100) + "%";
        }
        clampK(k) { return Math.min(1.6, Math.max(0.3, k)); }
        zoomAt(k2, cx, cy) {
          const v = this.view; k2 = this.clampK(k2);
          v.x = cx - (cx - v.x) * (k2 / v.k);
          v.y = cy - (cy - v.y) * (k2 / v.k);
          v.k = k2; this.applyView();
        }
        box(n) { return this.lastView && this.lastView.layout ? this.lastView.layout.nodes.find(x => x.id === n) : null; }
        size() { return { width: this.canvasEl.offsetWidth, height: this.canvasEl.offsetHeight }; }   // layout size, unaffected by a scaled frame
        initialView() {
          const L = this.lastView.layout, r = this.size();
          const kFit = Math.min((r.width - 40) / L.W, (r.height - 70) / L.H);
          const v = this.view = { k: this.clampK(Math.max(0.9, Math.min(1, kFit))), x: 20, y: 12 };
          const b = this.state.sel != null ? this.box(this.state.sel) : null;
          if (b) {
            if ((b.y + b.h) * v.k + v.y > r.height - 70) v.y = Math.min(12, r.height * 0.45 - (b.y + b.h / 2) * v.k);
            if ((b.x + b.w) * v.k + v.x > r.width - 24) v.x = Math.min(20, r.width - 24 - (b.x + b.w) * v.k);
          }
        }
        fitView() {
          const L = this.lastView && this.lastView.layout;
          if (!L || !this.canvasEl) return;
          const r = this.size();
          const k = this.clampK(Math.min(1, (r.width - 40) / L.W, (r.height - 70) / L.H));
          this.view = { k, x: Math.max(12, (r.width - L.W * k) / 2), y: 12 };
          this.applyView();
        }
        ensureVisible(n) {
          const b = this.box(n);
          if (!b || !this.canvasEl) return;
          const r = this.size(), v = this.view;
          const x1 = b.x * v.k + v.x, x2 = (b.x + b.w) * v.k + v.x, y1 = b.y * v.k + v.y, y2 = (b.y + b.h) * v.k + v.y;
          if (x1 < 0 || y1 < 0 || x2 > r.width || y2 > r.height - 56) {
            v.x = r.width / 2 - (b.x + b.w / 2) * v.k;
            v.y = r.height / 2 - (b.y + b.h / 2) * v.k;
          }
        }
        choose(n) {
          if (this.suppress) return;
          this.setState({ sel: n });
          this.emit("onSelectNode", n, "→ 详情栏打开 #" + n);
        }
        toggleOpen(e, n) {
          e.stopPropagation();
          const ex = this.state.expanded;
          this.setState({ expanded: ex.includes(n) ? ex.filter(x => x !== n) : ex.concat([n]) });
        }
        renderVals() {
          const B = window.MMWBoard;
          const reduced = !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
          const v = B ? B.canvasView(this.dataKey(), this.state.task, this.state.sel, this.state.expanded || [], reduced)
            : { hasTask: false, noTask: false, containers: [], decisions: [], tickets: [], labels: [], worldSize: {}, svg: "", layout: null };
          this.lastView = v;
          const center = () => { const r = this.canvasEl ? this.size() : { width: 0, height: 0 }; return [r.width / 2, r.height / 2]; };
          return {
            toast: this.state.toast, v, rf: this.rf,
            containers: v.containers.map(c => Object.assign({}, c, { pick: () => this.choose(c.n), toggle: e => this.toggleOpen(e, c.n) })),
            decisions: v.decisions.map(d => Object.assign({}, d, { pick: () => this.choose(d.n) })),
            tickets: v.tickets.map(t => Object.assign({}, t, { pick: () => this.choose(t.n) })),
            down: e => {
              if (e.button !== 0 || (e.target.closest && e.target.closest(".zoom, .legend, .chev"))) return;
              this.drag = { x: e.clientX, y: e.clientY, vx: this.view.x, vy: this.view.y, moved: false, id: e.pointerId };
            },
            zoomIn: () => { const [cx, cy] = center(); this.zoomAt(this.view.k * 1.2, cx, cy); },
            zoomOut: () => { const [cx, cy] = center(); this.zoomAt(this.view.k / 1.2, cx, cy); },
            fit: () => this.fitView(),
          };
        }'''
