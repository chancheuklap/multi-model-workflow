# The right column: everything about the selected card — a ticket, a spec, the map, or a decision ticket.
# Build: DC_FX=FIXTURES DC_FRAME=340x848 python3 mk.py "src/Component · 详情.py"
NAME = "Component · 详情"
CSS = ["tokens.css", "board.css"]
EXTRA_CSS = "          .sc-host { height: 100%; }"   # an imported component's host fills the slot the page gives it
PROPS = {
  "scene": {"editor": "enum", "default": "morning", "tsType": "string",
            "options": ["morning", "twenty-tickets", "bad-data", "empty", "ticket-returned", "ticket-closeout",
                        "ticket-waiting", "ticket-review", "ticket-queued", "ticket-landed", "ticket-fault",
                        "ticket-missing-blocker", "spec", "map", "decision", "nothing-selected"]},
}
TEMPLATE = r'''      <aside class="detail board" data-screen-label="详情" aria-label="详情">
        <sc-if value="{{ d.isEmpty }}" hint-placeholder-val="{{ false }}">
          <div class="dp-empty"><p class="dp-empty-title">{{ emptyTitle }}</p>{{ emptyText }}</div>
        </sc-if>
        <sc-if value="{{ d.hasCard }}" hint-placeholder-val="{{ true }}">
          <div class="dp">
            <div class="dp-head"><span class="dp-eyebrow">{{ d.eyebrow }}</span><button type="button" class="dp-close" aria-label="关闭详情" onClick="{{ close }}">×</button></div>
            <div class="dp-origin"><span>{{ d.num }}</span><sc-for list="{{ links }}" as="l" hint-placeholder-count="2"><span>·</span><button type="button" class="dp-link" onClick="{{ l.go }}">{{ l.label }}</button></sc-for></div>
            <sc-if value="{{ d.closeout }}" hint-placeholder-val="{{ false }}">
              <div class="dp-closeout"><span class="dp-closeout-bar"></span>收口那一轮新开 · 出自<button type="button" class="dp-link" onClick="{{ goCloseout }}">{{ d.closeoutFromLabel }}</button>{{ d.closeoutChild }}</div>
            </sc-if>
            <h2 class="dp-title">{{ d.title }}</h2>
            <div class="dp-status"><span class="{{ d.lightCls }}"></span><span class="{{ d.statusCls }}">{{ d.statusWord }}</span><span class="dp-elapsed">{{ d.elapsed }}</span></div>

            <sc-if value="{{ d.isTicket }}" hint-placeholder-val="{{ true }}">
              <div class="dp-step"><span class="{{ d.pillCls }}">{{ d.step }}</span><span class="dp-hint">{{ d.hint }}</span></div>
              <div class="path"><sc-for list="{{ d.path }}" as="p" hint-placeholder-count="6"><span class="{{ p.cls }}">{{ p.name }}</span><sc-if value="{{ p.sep }}" hint-placeholder-val="{{ true }}"><span class="path-sep">›</span></sc-if></sc-for></div>
              <sc-if value="{{ d.hasWhy }}" hint-placeholder-val="{{ true }}">
                <div class="why"><span class="why-title">为什么是橙的</span><sc-for list="{{ d.why }}" as="w" hint-placeholder-count="1"><span><b class="why-child">{{ w.head }}</b> {{ w.body }}</span></sc-for></div>
              </sc-if>
              <section class="dp-section">
                <div class="dp-section-title"><span>运行时</span><span>{{ runtimeNote }}</span></div>
                <sc-if value="{{ d.hasWorker }}" hint-placeholder-val="{{ true }}">
                  <div class="facts"><sc-for list="{{ d.facts }}" as="f" hint-placeholder-count="5"><span class="fact-key">{{ f.k }}</span><span class="fact-val">{{ f.v }}</span></sc-for></div>
                  <sc-if value="{{ d.manySessions }}" hint-placeholder-val="{{ false }}">
                    <sc-for list="{{ d.sessions }}" as="s" hint-placeholder-count="2"><div class="session"><span class="session-kind">{{ s.kind }}</span><span class="session-what">{{ s.what }}</span><span class="{{ s.stateCls }}">{{ s.state }}</span></div></sc-for>
                  </sc-if>
                </sc-if>
                <sc-if value="{{ noWorker }}" hint-placeholder-val="{{ false }}"><p class="rel-none">尚未派发。frontier 选中它之后，这里会出现它跑在哪个 host、哪个 runner。</p></sc-if>
              </section>
              <section class="dp-section">
                <div class="dp-section-title"><span>阻塞</span></div>
                <div class="rel-label">阻塞它的</div>
                <sc-for list="{{ blockers }}" as="r" hint-placeholder-count="1">
                  <sc-if value="{{ r.known }}" hint-placeholder-val="{{ true }}"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }} <span class="rel-where">{{ r.where }}</span></span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-if>
                  <sc-if value="{{ r.unknown }}" hint-placeholder-val="{{ false }}"><div class="rel-static"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></div></sc-if>
                </sc-for>
                <sc-if value="{{ d.noBlockers }}" hint-placeholder-val="{{ false }}"><p class="rel-none">无，一开始就能动</p></sc-if>
                <div class="rel-label">它阻塞的</div>
                <sc-for list="{{ blocks }}" as="r" hint-placeholder-count="1">
                  <button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }} <span class="rel-where">{{ r.where }}</span></span><span class="{{ r.stateCls }}">{{ r.state }}</span></button>
                </sc-for>
                <sc-if value="{{ d.noBlocks }}" hint-placeholder-val="{{ false }}"><p class="rel-none">无</p></sc-if>
              </section>
              <section class="dp-section">
                <div class="dp-section-title"><span>子 issue</span><span>{{ d.kidCount }}</span></div>
                <sc-for list="{{ kids }}" as="k" hint-placeholder-count="2">
                  <div class="kid"><span class="{{ k.lightCls }}"></span><span class="kid-num">{{ k.num }}</span><span class="kid-kind">{{ k.kind }}</span>
                    <sc-if value="{{ k.hasGoto }}" hint-placeholder-val="{{ false }}"><button type="button" class="dp-link kid-to" onClick="{{ k.go }}">{{ k.to }}</button></sc-if>
                    <sc-if value="{{ k.noGoto }}" hint-placeholder-val="{{ true }}"><span class="{{ k.toCls }}">{{ k.to }}</span></sc-if>
                    <span class="kid-title">{{ k.title }}</span></div>
                </sc-for>
                <sc-if value="{{ d.noKids }}" hint-placeholder-val="{{ false }}"><p class="rel-none">没有开出子 issue</p></sc-if>
              </section>
              <section class="dp-section">
                <div class="dp-section-title"><span>事件</span><span>{{ d.eventCount }}</span></div>
                <sc-if value="{{ d.noEvents }}" hint-placeholder-val="{{ false }}"><p class="rel-none">还没有事件。第一条会是 worker.started。</p></sc-if>
                <div class="events"><sc-for list="{{ d.events }}" as="e" hint-placeholder-count="4">
                  <div class="ev"><span class="{{ e.dotCls }}"></span>
                    <div class="ev-head"><span class="ev-time">{{ e.time }}</span><span class="{{ e.nameCls }}">{{ e.name }}</span><span class="ev-field">{{ e.field }}</span></div>
                    <div class="ev-line">{{ e.line }}</div></div>
                </sc-for></div>
              </section>
            </sc-if>

            <sc-if value="{{ d.isContainer }}" hint-placeholder-val="{{ false }}">
              <section class="dp-section">
                <div class="dp-section-title"><span>{{ d.listTitle }}</span><span>{{ d.listCount }}</span></div>
                <div class="lights-count"><sc-for list="{{ d.lights }}" as="lc" hint-placeholder-count="3"><span class="lc-item"><span class="{{ lc.cls }}"></span>{{ lc.word }}<span class="lc-n">{{ lc.n }}</span></span></sc-for></div>
                <div class="steps-count"><sc-for list="{{ d.steps }}" as="st" hint-placeholder-count="3"><span class="{{ st.cls }}">{{ st.label }}</span></sc-for></div>
              </section>
              <sc-if value="{{ d.isSpec }}" hint-placeholder-val="{{ true }}">
                <section class="dp-section">
                  <div class="dp-section-title"><span>按票号</span></div>
                  <sc-for list="{{ ticketRows }}" as="r" hint-placeholder-count="4"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.pillCls }}">{{ r.step }}</span></button></sc-for>
                </section>
              </sc-if>
              <sc-if value="{{ d.isMap }}" hint-placeholder-val="{{ false }}">
                <section class="dp-section">
                  <div class="dp-section-title"><span>spec</span><span>{{ d.specCount }}</span></div>
                  <sc-for list="{{ specRows }}" as="r" hint-placeholder-count="3"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                </section>
                <sc-if value="{{ d.hasDecisions }}" hint-placeholder-val="{{ true }}">
                  <section class="dp-section">
                    <div class="dp-section-title"><span>决策票</span><span>{{ d.decisionCount }}</span></div>
                    <sc-for list="{{ decisionRows }}" as="r" hint-placeholder-count="3"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                  </section>
                </sc-if>
              </sc-if>
            </sc-if>

            <sc-if value="{{ d.isDecision }}" hint-placeholder-val="{{ false }}">
              <section class="dp-section">
                <div class="dp-section-title"><span>阻塞</span></div>
                <div class="rel-label">阻塞它的</div>
                <sc-for list="{{ blockers }}" as="r" hint-placeholder-count="1"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                <sc-if value="{{ d.noBlockers }}" hint-placeholder-val="{{ false }}"><p class="rel-none">无</p></sc-if>
                <div class="rel-label">它阻塞的</div>
                <sc-for list="{{ blocks }}" as="r" hint-placeholder-count="1"><button type="button" class="rel" onClick="{{ r.go }}"><span class="{{ r.lightCls }}"></span><span class="rel-num">{{ r.num }}</span><span class="rel-title">{{ r.title }}</span><span class="{{ r.stateCls }}">{{ r.state }}</span></button></sc-for>
                <sc-if value="{{ d.noBlocks }}" hint-placeholder-val="{{ false }}"><p class="rel-none">无</p></sc-if>
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
          if (!B) return { sel: null };
          const ds = B.DETAIL_SCENES[props.scene] || B.DETAIL_SCENES.morning;
          const sel = props.sel !== undefined ? props.sel : ("node" in ds ? ds.node : (B.scene(ds.data).select.node ?? null));
          return { sel };
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
        renderVals() {
          const B = window.MMWBoard;
          const key = this.dataKey();
          const d = B ? B.detailView(key, this.state.sel) : { isEmpty: true, hasTasks: true };
          d.hasCard = !d.isEmpty;
          const withGo = rows => (rows || []).map(r => Object.assign({}, r, { unknown: r.known === false, go: () => this.goTo(r.n) }));
          return {
            toast: this.state.toast, d,
            emptyTitle: d.hasTasks === false ? "这里是详情" : "点一张卡",
            emptyText: d.hasTasks === false ? "有了任务之后，点画布上的卡，它的细节显示在这一栏。" : "画布上任意一张卡——map、spec、ticket 或决策票——点一下，它的全部细节就在这一栏。",
            runtimeNote: d.hasWorker ? "取自 worker.started" : "",
            noWorker: !!d.isTicket && !d.hasWorker,
            links: (d.links || []).map(l => Object.assign({}, l, { go: () => this.goTo(l.n) })),
            blockers: withGo(d.blockers), blocks: withGo(d.blocks),
            ticketRows: withGo(d.ticketRows), specRows: withGo(d.specRows), decisionRows: withGo(d.decisionRows),
            kids: (d.kids || []).map(k => Object.assign({}, k, { noGoto: !k.hasGoto, go: () => this.goTo(k.goto) })),
            goCloseout: () => this.goTo(d.closeoutFrom),
            close: () => { this.setState({ sel: null }); this.emit("onClose", null, "→ 详情栏关上，画布取消选中"); },
            gh: () => this.toast("示例数据：真的 board 在这里用新标签页打开 GitHub 上的 #" + d.gh + "。board 自己不写票。"),
          };
        }'''
