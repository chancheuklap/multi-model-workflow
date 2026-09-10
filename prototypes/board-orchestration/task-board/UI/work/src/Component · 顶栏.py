# The top bar: the four lamp counts, "needs you" as the one button, when the data was read, and
# the refresh button and the gear that opens the settings sheet.
# Build: DC_FX=FIXTURES DC_FRAME=1440x52 python3 mk.py "src/Component · 顶栏.py"
NAME = "Component · 顶栏"
CSS = ["tokens.css", "board.css", "settings.css"]
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
        <button type="button" class="gear" aria-label="立刻重读 GitHub" title="立刻重读 GitHub（页面开着时每分钟自动读一次）" onClick="{{ refresh }}"><svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"></path><path d="M21 3v5h-5"></path></svg></button>
        <button type="button" class="{{ gearCls }}" aria-label="本机配置" title="本机配置：每个角色跑在哪个 host、model、effort" onClick="{{ openSettings }}"><svg class="gear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"></path><circle cx="12" cy="12" r="3"></circle></svg></button>
      </header>'''
LOGIC = r'''        init(props) { return { refreshed: false }; }
        onReady() { this.forceUpdate(); }
        renderVals() {
          const B = window.MMWBoard;
          const v = B ? B.topbarView(this.props.scene || "morning", this.state.refreshed)
            : { needCls: "counter", needNCls: "counter-n", needLightCls: "light hollow", orangeN: 0, greenN: 0, hollowN: 0, inkN: 0, waitingSub: "", readCls: "readstate", readText: "" };
          v.noNeed = !v.hot;
          v.hasWaiting = !!v.waitingSub;
          return {
            toast: this.state.toast, v,
            jump: () => this.emit("onJumpNeedYou", null, "→ 画布跳到下一张需要你的票，并在详情栏打开它"),
            gearCls: this.props.settingsOpen ? "gear on" : "gear",
            refresh: () => {
              const failed = B && B.scene(this.props.scene || "morning").readFailed;
              if (!failed) this.setState({ refreshed: true });
              this.toast(failed ? "示例：重读仍然失败，下面还是旧数据。" : "示例：真的 board 在这里立刻重读一次 GitHub；页面开着时它每分钟自己读一次。");
            },
            openSettings: () => this.emit("onOpenSettings", null, "→ 打开本机配置"),
          };
        }'''
