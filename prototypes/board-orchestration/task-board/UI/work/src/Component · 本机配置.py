# The settings sheet (#335): which host, model and effort each agent runs on, and the runner,
# chosen on this machine from what its hosts answered — asked of Paseo when the runner is paseo,
# of each host's own CLI otherwise, as `start` does. Opened from the gear in the top bar.
# Build: DC_FX=FIXTURES DC_FRAME=1440x900 python3 mk.py "src/Component · 本机配置.py"
NAME = "Component · 本机配置"
CSS = ["tokens.css", "board.css", "settings.css"]
EXTRA_CSS = "          .sc-host { height: 100%; }"   # an imported component's host fills the slot the page gives it
PROPS = {
  "scene": {"editor": "enum", "default": "mine", "tsType": "string",
            "options": ["mine", "fresh", "retired", "paseo-off", "changed", "edited", "incomplete", "scanning", "saved", "refused"]},
}
OPTION = '<option value="{{ o.value }}" disabled="{{ o.disabled }}" label="{{ o.text }}">{{ o.text }}</option>'
TEMPLATE = r'''      <div class="scrim board" data-screen-label="本机配置" onClick="{{ backdrop }}">
        <div class="sheet" role="dialog" aria-modal="true" aria-label="本机配置">
          <div class="sheet-head">
            <div class="sheet-head-text">
              <span class="dp-eyebrow">本机配置</span>
              <h2 class="sheet-title">这台机器上，每个角色跑在哪</h2>
              <p class="sheet-sub">下拉菜单里的选项，是 MMW 刚问过这台机器上的 host 得到的，问的地方和 <span class="sheet-code">start</span> 起会话时问的是同一处。这里就是 MMW 管这件事的唯一地方，保存在本机的 <span class="sheet-code">{{ v.store }}</span>；这一页不写 GitHub。</p>
            </div>
            <button type="button" class="dp-close" aria-label="关闭本机配置" onClick="{{ close }}">×</button>
          </div>
          <div class="sheet-body">
            <sc-if value="{{ v.refused }}" hint-placeholder-val="{{ false }}">
              <div class="refused" role="alert"><p class="refused-text"><b>没有保存。</b>{{ v.refusedText }}</p><button type="button" class="btn" onClick="{{ reread }}">重新读取</button></div>
            </sc-if>
            <section class="set-block">
              <div class="set-block-head"><span class="dp-section-title">本机的 host</span>
                <span class="scan">
                  <sc-if value="{{ v.scanning }}" hint-placeholder-val="{{ false }}"><span class="spin"></span>{{ v.scanningText }}</sc-if>
                  <sc-if value="{{ v.notScanning }}" hint-placeholder-val="{{ true }}">{{ v.scannedText }}<button type="button" class="linkbtn" onClick="{{ rescan }}">重新扫描</button></sc-if>
                </span>
              </div>
              <div class="hostscan">
                <sc-for list="{{ v.chips }}" as="c" hint-placeholder-count="5"><span class="{{ c.cls }}"><span class="hs-name">{{ c.host }}</span>{{ c.what }}</span></sc-for>
              </div>
            </section>
            <section class="set-block ruled">
              <div class="runner-row">
                <div class="role-name"><span class="role-agent">runner</span><span class="role-what">用什么起会话</span></div>
                <select class="{{ v.runnerCls }}" value="{{ v.runner }}" disabled="{{ v.runnerOff }}" onChange="{{ onRunner }}" aria-label="runner">
                  <sc-for list="{{ v.runnerOpts }}" as="o" hint-placeholder-count="4">@@OPTION@@</sc-for>
                </select>
                <sc-if value="{{ v.runnerHasBad }}" hint-placeholder-val="{{ false }}"><div class="role-foot"><sc-for list="{{ v.runnerBads }}" as="b" hint-placeholder-count="1"><div class="role-bad"><span class="hatch"></span>{{ b.text }}</div></sc-for></div></sc-if>
              </div>
              <p class="set-note">环境变量 <span class="sheet-code">MMW_RUNNER</span> 设了时，它优先于这一格。「按所在环境判断」让 <span class="sheet-code">start</span> 看自己跑在哪个 runner 里，判断不出时用 orca。runner 是 paseo 时，<span class="sheet-code">start</span> 向 Paseo 要 model，所以换到 paseo 或从 paseo 换走，选项会重新扫描。</p>
            </section>
            <section class="set-block ruled">
              <div class="set-block-head"><span class="dp-section-title">一个角色一行</span></div>
              <div class="roles">
                <div class="roles-head"><span>agent</span><span>host</span><span>model</span><span>effort</span></div>
                <sc-for list="{{ rows }}" as="r" hint-placeholder-count="5">
                  <div class="role">
                    <div class="role-name"><span class="role-agent">{{ r.agent }}</span><span class="role-what">{{ r.what }}</span></div>
                    <select class="{{ r.hostCls }}" value="{{ r.host }}" disabled="{{ r.hostOff }}" onChange="{{ r.onHost }}" aria-label="{{ r.hostLabel }}">
                      <sc-for list="{{ r.hostOpts }}" as="o" hint-placeholder-count="5">@@OPTION@@</sc-for>
                    </select>
                    <select class="{{ r.modelCls }}" value="{{ r.model }}" disabled="{{ r.modelOff }}" onChange="{{ r.onModel }}" aria-label="{{ r.modelLabel }}">
                      <sc-for list="{{ r.modelOpts }}" as="o" hint-placeholder-count="4">@@OPTION@@</sc-for>
                    </select>
                    <select class="{{ r.effortCls }}" value="{{ r.effort }}" disabled="{{ r.effortOff }}" onChange="{{ r.onEffort }}" aria-label="{{ r.effortLabel }}">
                      <sc-for list="{{ r.effortOpts }}" as="o" hint-placeholder-count="4">@@OPTION@@</sc-for>
                    </select>
                    <sc-if value="{{ r.hasBad }}" hint-placeholder-val="{{ false }}"><div class="role-foot"><sc-for list="{{ r.bads }}" as="b" hint-placeholder-count="1"><div class="role-bad"><span class="hatch"></span>{{ b.text }}</div></sc-for></div></sc-if>
                  </div>
                </sc-for>
              </div>
              <p class="set-note">一台新机器第一次安装时，这里填的是 MMW 自带的初始值；之后只按这里选的跑，MMW 更新不会改它。</p>
            </section>
          </div>
          <div class="sheet-foot">
            <div class="foot-status" aria-live="polite">
              <span class="foot-strong"><sc-if value="{{ v.hatch }}" hint-placeholder-val="{{ false }}"><span class="hatch"></span></sc-if>{{ v.strong }}</span>
              <span class="foot-quiet">{{ v.quiet }}</span>
            </div>
            <div class="foot-actions">
              <button type="button" class="btn" onClick="{{ close }}">{{ v.closeLabel }}</button>
              <button type="button" class="btn primary" disabled="{{ v.saveOff }}" onClick="{{ save }}">保存</button>
            </div>
          </div>
        </div>
      </div>'''.replace("@@OPTION@@", OPTION)
LOGIC = r'''        init(props) {
          const B = window.MMWBoard;
          return { st: B ? B.settingsState(props.scene || "mine") : null };
        }
        onReady() { this.setState(this.init(this.props)); }
        cleanup() { clearTimeout(this._scan); }
        // Every change to the sheet goes through here: copy the latest state, change the copy,
        // set it — so two changes made by one click both land.
        mutate(fn) {
          this.setState(prev => {
            const st = JSON.parse(JSON.stringify(prev.st));
            fn(st);
            return { st };
          });
        }
        renderVals() {
          const B = window.MMWBoard, st = this.state.st;
          if (!B || !st) return { toast: this.state.toast, v: { rows: [], chips: [], runnerOpts: [], runnerBads: [] }, rows: [] };
          const v = B.settingsView(st), sc = B.SETTINGS.scenes[st.data], L = B.LocalConfig;
          // A rescan asks the place the runner on screen points at: Paseo for paseo, the CLIs otherwise.
          const rescan = source => {
            this.mutate(s => { s.scanning = true; });
            clearTimeout(this._scan);
            this._scan = setTimeout(() => {
              this.mutate(s => { s.scanning = false; s.scannedAt = B.laterBy(1); s.scanSource = source; });
              this.toast(source === "paseo" ? "示例：真的 board 在这里向 Paseo 要每个 host 的 model；这台机器的 Paseo 没开。"
                : "示例：真的 board 在这里重新问一遍每个 host 的 CLI。");
            }, 1400);
          };
          const set = (key, cell) => e => {
            const value = e.target.value;
            this.mutate(s => { s.savedAt = null; L.setCell(sc.scans[s.scanSource], s.draft, key, cell, value); });
            const source = L.source({ runner: value });
            if (key === "runner" && source !== st.scanSource) rescan(source);
          };
          const close = () => this.emit("onClose", null, "→ 关掉本机配置，回到任务板");
          return {
            toast: this.state.toast, v,
            rows: v.rows.map(r => Object.assign({}, r, { onHost: set(r.agent, "host"), onModel: set(r.agent, "model"), onEffort: set(r.agent, "effort") })),
            onRunner: set("runner", "runner"),
            close,
            // A click beside the sheet closes it only when there is nothing to lose.
            backdrop: e => { if (e.target === e.currentTarget && !v.changed) close(); },
            save: () => {
              // The real board sends the version it read and is refused when the saved config moved on.
              if (sc.changedElsewhere && !st.reread) {
                this.mutate(s => { s.refused = B.LocalConfig.changes(s.draft, s.saved).length; });
                return;
              }
              const text = v.changeText;
              this.mutate(s => { s.saved = JSON.parse(JSON.stringify(s.draft)); s.savedAt = B.laterBy(1); });
              this.toast("示例：真的 board 在这里把「" + text + "」存进 " + B.SETTINGS.store + "。");
            },
            reread: () => {
              const now = sc.changedElsewhere.saved;
              this.mutate(s => { s.saved = JSON.parse(JSON.stringify(now)); s.draft = JSON.parse(JSON.stringify(now)); s.scanSource = L.source(now); s.refused = 0; s.reread = true; s.savedAt = null; });
              this.toast("已重新读取：reviewer 现在是 codex · gpt 5.6 sol · xhigh。");
            },
            rescan: () => rescan(L.source(st.draft)),
          };
        }'''
