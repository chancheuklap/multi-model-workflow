# The top bar: the four lamp counts, "needs you" as the one button, and when the data was read.
# Build: DC_FX=FIXTURES DC_FRAME=1440x52 python3 mk.py "src/Component · 顶栏.py"
NAME = "Component · 顶栏"
CSS = ["tokens.css", "board.css"]
EXTRA_CSS = "          .sc-host { height: 100%; }"   # an imported component's host fills the slot the page gives it
PROPS = {
  "scene": {"editor": "enum", "default": "morning", "tsType": "string",
            "options": ["morning", "twenty-tickets", "bad-data", "empty"]},
}
TEMPLATE = r'''      <header class="topbar board" data-screen-label="顶栏">
        <div class="brand"><span class="brand-mark">MMW</span><span class="brand-name">task board</span><span class="brand-repo">chancheuklap/multi-model-workflow</span></div>
        <div class="counters">
          <button type="button" class="{{ v.needCls }}" disabled="{{ v.noNeed }}" onClick="{{ jump }}" title="跳到下一张需要你的票"><span class="{{ v.needLightCls }}"></span>需要你<span class="{{ v.needNCls }}">{{ v.orangeN }}</span></button>
          <span class="counter"><span class="light green"></span>在跑<span class="counter-n">{{ v.greenN }}</span><sc-if value="{{ v.hasWaiting }}" hint-placeholder-val="{{ true }}"><span class="counter-sub">{{ v.waitingSub }}</span></sc-if></span>
          <span class="counter"><span class="light hollow"></span>待派<span class="counter-n">{{ v.hollowN }}</span></span>
          <span class="counter"><span class="light ink"></span>好了<span class="counter-n">{{ v.inkN }}</span></span>
        </div>
        <div class="{{ v.readCls }}">{{ v.readText }}</div>
      </header>'''
LOGIC = r'''        init(props) { return {}; }
        onReady() { this.forceUpdate(); }
        renderVals() {
          const B = window.MMWBoard;
          const v = B ? B.topbarView(this.props.scene || "morning")
            : { needCls: "counter", needNCls: "counter-n", needLightCls: "light hollow", orangeN: 0, greenN: 0, hollowN: 0, inkN: 0, waitingSub: "", readCls: "readstate", readText: "" };
          v.noNeed = !v.hot;
          v.hasWaiting = !!v.waitingSub;
          return {
            toast: this.state.toast, v,
            jump: () => this.emit("onJumpNeedYou", null, "→ 画布跳到下一张需要你的票，并在详情栏打开它"),
          };
        }'''
