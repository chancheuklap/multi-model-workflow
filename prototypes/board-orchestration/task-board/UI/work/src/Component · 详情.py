# The right column: everything about the selected card — a ticket, a spec, the map, or a decision ticket.
# Build: DC_FX=FIXTURES DC_FRAME=340x848 python3 mk.py "src/Component · 详情.py"
NAME = "Component · 详情"
CSS = ["tokens.css", "board.css"]
EXTRA_CSS = "          .sc-host { height: 100%; }"   # an imported component's host fills the slot the page gives it
PROPS = {
  "scene": {"editor": "enum", "default": "morning", "tsType": "string",
            "options": ["morning", "twenty-tickets", "bad-data", "empty", "ticket-returned", "ticket-bounced", "ticket-closeout",
                        "ticket-waiting", "ticket-review", "ticket-queued", "ticket-landed", "ticket-fault",
                        "ticket-missing-blocker", "spec", "map", "decision", "nothing-selected"]},
}
TEMPLATE = r'''      <aside class="detail board" data-screen-label="详情" aria-label="详情">
        <sc-if value="{{ d.isEmpty }}" hint-placeholder-val="{{ false }}">
          <div class="dp-empty"><p class="dp-empty-title">{{ emptyTitle }}</p>{{ emptyText }}</div>
        </sc-if>

        <sc-if value="{{ d.isTicket }}" hint-placeholder-val="{{ true }}">
          <div class="pv">
            <div class="pv-head"><span class="pv-eyebrow">{{ d.eyebrow }}</span><button type="button" class="pv-gh" onClick="{{ gh }}">GitHub ↗</button><button type="button" class="pv-close" aria-label="关闭详情" onClick="{{ close }}">×</button></div>
            <h2 class="pv-title">{{ d.title }}</h2>
            <div class="pv-links"><span>{{ d.num }}</span><sc-for list="{{ links }}" as="l" hint-placeholder-count="2"><span>·</span><button type="button" class="pv-link" onClick="{{ l.go }}">{{ l.label }}</button></sc-for></div>
            <div class="va-status"><span class="{{ d.lampCls }}"></span><span class="{{ d.wordCls }}">{{ d.statusWord }}</span><span class="{{ d.pillCls }}">{{ d.phase }}</span><span class="va-elapsed">{{ d.elapsed }}</span></div>
            <sc-if value="{{ d.hasRun }}" hint-placeholder-val="{{ true }}">
              <div class="pv-run">
                <div class="pv-run-who"><span class="pv-run-grade">{{ d.runGrade }}</span><span class="pv-run-model">{{ d.runModel }}</span></div>
                <div class="pv-run-where"><sc-for list="{{ d.runRows }}" as="r" hint-placeholder-count="4"><span class="pv-run-k">{{ r.k }}</span><span class="pv-run-v">{{ r.v }}</span></sc-for></div>
              </div>
            </sc-if>
            <sc-if value="{{ d.noRun }}" hint-placeholder-val="{{ false }}"><p class="pv-none">{{ d.noRunText }}</p></sc-if>
            <sc-if value="{{ d.hasWhy }}" hint-placeholder-val="{{ false }}">
              <div class="pv-why"><span class="pv-why-t">Needs you</span><sc-for list="{{ d.why }}" as="w" hint-placeholder-count="1"><span><b>{{ w.head }}</b> {{ w.body }}</span></sc-for></div>
            </sc-if>
            <sc-if value="{{ d.hasBlockedBy }}" hint-placeholder-val="{{ true }}">
              <section class="pv-sec">
                <div class="pv-sec-title"><span>Blocked by</span><span>{{ d.blockedByCount }}</span></div>
                <sc-for list="{{ blockedBy }}" as="r" hint-placeholder-count="1">
                  <button type="button" class="{{ r.cls }}" onClick="{{ r.go }}"><span class="{{ r.lampCls }}"></span><span class="pv-rel-n">{{ r.num }}</span><span class="pv-rel-t">{{ r.title }}</span><sc-if value="{{ r.showHold }}" hint-placeholder-val="{{ false }}"><span class="pv-rel-hold">held</span></sc-if><sc-if value="{{ r.showPill }}" hint-placeholder-val="{{ true }}"><span class="{{ r.pillCls }}">{{ r.phase }}</span></sc-if><sc-if value="{{ r.showState }}" hint-placeholder-val="{{ false }}"><span class="pv-rel-s">{{ r.state }}</span></sc-if></button>
                </sc-for>
              </section>
            </sc-if>
            <sc-if value="{{ d.hasBlocking }}" hint-placeholder-val="{{ true }}">
              <section class="pv-sec">
                <div class="pv-sec-title"><span>Blocking</span><span>{{ d.blockingCount }}</span></div>
                <sc-for list="{{ blocking }}" as="r" hint-placeholder-count="1">
                  <button type="button" class="{{ r.cls }}" onClick="{{ r.go }}"><span class="{{ r.lampCls }}"></span><span class="pv-rel-n">{{ r.num }}</span><span class="pv-rel-t">{{ r.title }}</span><sc-if value="{{ r.showHold }}" hint-placeholder-val="{{ false }}"><span class="pv-rel-hold">held</span></sc-if><sc-if value="{{ r.showPill }}" hint-placeholder-val="{{ true }}"><span class="{{ r.pillCls }}">{{ r.phase }}</span></sc-if><sc-if value="{{ r.showState }}" hint-placeholder-val="{{ false }}"><span class="pv-rel-s">{{ r.state }}</span></sc-if></button>
                </sc-for>
              </section>
            </sc-if>
            <section class="pv-sec">
              <div class="pv-sec-title"><span>Events</span><span>{{ d.eventCount }}</span></div>
              <sc-if value="{{ d.noEvents }}" hint-placeholder-val="{{ false }}"><p class="pv-none">no events yet</p></sc-if>
              <sc-for list="{{ phaseBlocks }}" as="b" hint-placeholder-count="3">
                <div class="{{ b.cls }}">
                  <button type="button" class="va-bhead" onClick="{{ b.toggle }}"><span class="va-chev">{{ b.chev }}</span><span class="{{ b.pillCls }}">{{ b.phase }}</span><span class="va-bsum">{{ b.summary }}</span><span class="va-btime">{{ b.time }}</span></button>
                  <sc-if value="{{ b.open }}" hint-placeholder-val="{{ true }}">
                    <div class="va-body">
                      <sc-for list="{{ b.items }}" as="e" hint-placeholder-count="2">
                        <button type="button" class="va-ev" onClick="{{ e.toggle }}"><span class="va-t">{{ e.time }}</span><span class="{{ e.nameCls }}">{{ e.name }}</span><sc-if value="{{ e.hasText }}" hint-placeholder-val="{{ true }}"><span class="va-x">{{ e.text }}</span></sc-if><sc-if value="{{ e.open }}" hint-placeholder-val="{{ false }}"><span class="va-x"><span class="pv-detail"><sc-for list="{{ e.detail }}" as="f" hint-placeholder-count="3"><span class="pv-detail-k">{{ f.k }}</span><span class="pv-detail-v">{{ f.v }}</span></sc-for></span></span></sc-if></button>
                      </sc-for>
                    </div>
                  </sc-if>
                </div>
              </sc-for>
            </section>
            <sc-if value="{{ d.hasKids }}" hint-placeholder-val="{{ true }}">
              <section class="pv-sec">
                <div class="pv-sec-title"><span>Sub-issues</span><span>{{ d.kidCount }}</span></div>
                <sc-for list="{{ d.kids }}" as="k" hint-placeholder-count="2">
                  <div class="pv-rel"><span class="{{ k.lampCls }}"></span><span class="pv-rel-n">{{ k.num }}</span><span class="pv-rel-t">{{ k.title }}</span><span class="{{ k.kindCls }}">{{ k.kind }}</span></div>
                </sc-for>
              </section>
            </sc-if>
          </div>
        </sc-if>

        <sc-if value="{{ d.isCardNotTicket }}" hint-placeholder-val="{{ false }}">
          <div class="dp">
            <div class="dp-head"><span class="dp-eyebrow">{{ d.eyebrow }}</span><button type="button" class="dp-close" aria-label="关闭详情" onClick="{{ close }}">×</button></div>
            <div class="dp-origin"><span>{{ d.num }}</span><sc-for list="{{ links }}" as="l" hint-placeholder-count="2"><span>·</span><button type="button" class="dp-link" onClick="{{ l.go }}">{{ l.label }}</button></sc-for></div>
            <h2 class="dp-title">{{ d.title }}</h2>
            <div class="dp-status"><span class="{{ d.lampCls }}"></span><span class="{{ d.statusCls }}">{{ d.statusWord }}</span><span class="dp-elapsed">{{ d.elapsed }}</span></div>

            <sc-if value="{{ d.isContainer }}" hint-placeholder-val="{{ false }}">
              <section class="dp-section">
                <div class="dp-section-title"><span>{{ d.listTitle }}</span><span>{{ d.listCount }}</span></div>
                <div class="lamps-count"><sc-for list="{{ d.lamps }}" as="lc" hint-placeholder-count="3"><span class="lc-item"><span class="{{ lc.cls }}"></span>{{ lc.word }}<span class="lc-n">{{ lc.n }}</span></span></sc-for></div>
                <div class="phases-count"><sc-for list="{{ d.phases }}" as="st" hint-placeholder-count="3"><span class="{{ st.cls }}">{{ st.label }}</span></sc-for></div>
              </section>
              <sc-if value="{{ d.isSpec }}" hint-placeholder-val="{{ true }}">
                <section class="dp-section">
                  <div class="dp-section-title"><span>By number</span></div>
                  <sc-for list="{{ ticketRows }}" as="r" hint-placeholder-count="4"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lampCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.pillCls }}">{{ r.phase }}</span></button></sc-for>
                </section>
              </sc-if>
              <sc-if value="{{ d.isMap }}" hint-placeholder-val="{{ false }}">
                <section class="dp-section">
                  <div class="dp-section-title"><span>spec</span><span>{{ d.specCount }}</span></div>
                  <sc-for list="{{ specRows }}" as="r" hint-placeholder-count="3"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lampCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                </section>
                <sc-if value="{{ d.hasDecisions }}" hint-placeholder-val="{{ true }}">
                  <section class="dp-section">
                    <div class="dp-section-title"><span>Decision tickets</span><span>{{ d.decisionCount }}</span></div>
                    <sc-for list="{{ decisionRows }}" as="r" hint-placeholder-count="3"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lampCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                  </section>
                </sc-if>
              </sc-if>
            </sc-if>

            <sc-if value="{{ d.isDecision }}" hint-placeholder-val="{{ false }}">
              <section class="dp-section">
                <div class="dp-section-title"><span>Blocked by</span><span>{{ d.blockerCount }}</span></div>
                <sc-for list="{{ blockers }}" as="r" hint-placeholder-count="1"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lampCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                <sc-if value="{{ d.noBlockers }}" hint-placeholder-val="{{ false }}"><p class="rel-none">none</p></sc-if>
              </section>
              <section class="dp-section">
                <div class="dp-section-title"><span>Blocking</span><span>{{ d.blocksCount }}</span></div>
                <sc-for list="{{ blocks }}" as="r" hint-placeholder-count="1"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lampCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                <sc-if value="{{ d.noBlocks }}" hint-placeholder-val="{{ false }}"><p class="rel-none">none</p></sc-if>
              </section>
            </sc-if>

            <button type="button" class="dp-gh" onClick="{{ gh }}">{{ d.ghLabel }}</button>
          </div>
        </sc-if>
      </aside>'''
LOGIC = r'''        dataKey() {
          const B = window.MMWBoard;
          return ((B && B.DETAIL_SCENES[this.props.scene]) || { data: "morning" }).data;
        }
        init(props) {
          const B = window.MMWBoard;
          if (!B) return { sel: null, toggled: {}, opened: {} };
          const ds = B.DETAIL_SCENES[props.scene] || B.DETAIL_SCENES.morning;
          const sel = props.sel !== undefined ? props.sel : ("node" in ds ? ds.node : (B.scene(ds.data).select.node ?? null));
          return { sel, toggled: {}, opened: {} };
        }
        onReady() { this.setState(this.init(this.props)); }
        afterUpdate(prev) {
          if (this.props.sel !== undefined && this.props.sel !== prev.sel && this.props.sel !== this.state.sel) this.setState({ sel: this.props.sel });
        }
        goTo(n) {
          if (n == null) return;
          this.setState({ sel: n });
          this.emit("onGoto", n, "→ 画布跳到 #" + n + " 并选中它");
        }
        // A phase block's header opens or shuts it against its default; an event opens its backend fields.
        flip(which, k) {
          const next = Object.assign({}, this.state[which] || {});
          next[k] = !next[k];
          this.setState({ [which]: next });
        }
        renderVals() {
          const B = window.MMWBoard;
          const key = this.dataKey();
          const d = B ? B.detailView(key, this.state.sel) : { isEmpty: true, hasTasks: true };
          d.isCardNotTicket = !d.isEmpty && !d.isTicket;
          const rawEvents = d.rawEvents || [];
          delete d.rawEvents;
          const toggled = this.state.toggled || {}, opened = this.state.opened || {};
          const withGo = rows => (rows || []).map(r => Object.assign({}, r, { unknown: r.known === false, go: () => this.goTo(r.n) }));
          const phaseBlocks = (d.phaseBlocks || []).map((b, i) => {
            const bk = d.gh + ":b" + i;
            const open = toggled[bk] ? !b.openByDefault : b.openByDefault;
            return Object.assign({}, b, {
              open, chev: open ? "▾" : "▸", summary: open ? "" : b.summary, time: open ? b.span : b.from,
              toggle: () => this.flip("toggled", bk),
              items: b.items.map((e, j) => {
                const ek = bk + ":" + j;
                return Object.assign({}, e, { open: !!opened[ek], toggle: () => this.flip("opened", ek) });
              }),
            });
          });
          return {
            toast: this.state.toast, d, rawEvents, phaseBlocks,
            emptyTitle: d.hasTasks === false ? "这里是详情" : "点一张卡",
            emptyText: d.hasTasks === false ? "The Night 开起来之后，点画布上的卡，它的细节显示在这一栏。" : "画布上任意一张卡——map、spec、ticket 或 decision ticket——点一下，它的全部细节就在这一栏。",
            links: (d.links || []).map(l => Object.assign({}, l, { go: () => this.goTo(l.n) })),
            blockedBy: withGo(d.blockedBy), blocking: withGo(d.blocking),
            blockers: withGo(d.blockers), blocks: withGo(d.blocks),
            ticketRows: withGo(d.ticketRows), specRows: withGo(d.specRows), decisionRows: withGo(d.decisionRows),
            close: () => { this.setState({ sel: null }); this.emit("onClose", null, "→ 详情栏关上，画布取消选中"); },
            gh: () => this.toast("示例数据：真的 board 在这里用新标签页打开 GitHub 上的 #" + d.gh + "。board 自己不写 ticket。"),
          };
        }'''
