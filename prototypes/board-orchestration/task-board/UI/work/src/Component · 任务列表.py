# The left column: every task (one map ticket each), its lamp and how much of it has landed.
# Build: DC_FX=FIXTURES DC_FRAME=236x848 python3 mk.py "src/Component · 任务列表.py"
NAME = "Component · 任务列表"
CSS = ["tokens.css", "board.css"]
EXTRA_CSS = "          .sc-host { height: 100%; }"   # an imported component's host fills the slot the page gives it
PROPS = {
  "scene": {"editor": "enum", "default": "morning", "tsType": "string",
            "options": ["morning", "twenty-tickets", "bad-data", "empty"]},
}
TEMPLATE = r'''      <nav class="tasks board" data-screen-label="任务" aria-label="任务">
        <div class="col-eyebrow"><span>任务</span><span>{{ v.count }}</span></div>
        <sc-if value="{{ v.empty }}" hint-placeholder-val="{{ false }}"><p class="tasks-empty">没有带 mmw:map label 的票。</p></sc-if>
        <sc-for list="{{ rows }}" as="r" hint-placeholder-count="3">
          <button type="button" class="{{ r.cls }}" onClick="{{ r.pick }}">
            <span class="{{ r.lightCls }}" title="{{ r.lightWord }}"></span><span class="task-meta">{{ r.meta }}</span>
            <span class="{{ r.titleCls }}">{{ r.title }}</span>
            <span class="task-progress"><span class="bar"><span class="bar-fill" style="{{ r.barStyle }}"></span></span><span class="task-count">{{ r.count }}</span></span>
          </button>
        </sc-for>
      </nav>'''
LOGIC = r'''        init(props) {
          const B = window.MMWBoard;
          if (!B) return { task: null };
          const sc = B.scene(props.scene || "morning");
          return { task: sc.select.task != null ? sc.select.task : ((sc.tasks[0] || {}).n ?? null) };
        }
        onReady() { this.setState(this.init(this.props)); }
        afterUpdate(prev) {
          if (this.props.task !== undefined && this.props.task !== prev.task && this.props.task !== this.state.task) this.setState({ task: this.props.task });
        }
        renderVals() {
          const B = window.MMWBoard;
          const task = this.props.task !== undefined ? this.props.task : this.state.task;
          const v = B ? B.taskListView(this.props.scene || "morning", task) : { count: 0, empty: false, rows: [] };
          return {
            toast: this.state.toast, v,
            rows: v.rows.map(r => Object.assign({}, r, {
              pick: () => { this.setState({ task: r.n }); this.emit("onSelectTask", r.n, "→ 画布换成任务 #" + r.n); },
            })),
          };
        }'''
