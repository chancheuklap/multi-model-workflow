# Smallest complete component source for mk.py. Build: DC_FX=FIXTURES python3 mk.py "src/Component · settings.py" -> "Component · settings.dc.html"
NAME = "Component · settings"          # kind prefix (see "Page naming") + name; also the <dc-import name="…"> and the file name
CSS = ["tokens.css", "app.css"]        # stylesheets under styles/, copied from the mockup unchanged
EXTRA_CSS = "          .workspace { height: 100%; }"    # fills the fixed frame mk.py draws (DC_FRAME)
PROPS = {                              # every key here appears in the Tweaks panel
  "scene": {"editor": "enum", "default": "saved", "tsType": "string", "options": ["saved", "service-down"]},   # one value per state; these are the page's scene names
}
TEMPLATE = '''      <section class="workspace" data-screen-label="settings">
        <button class="btn-secondary" type="button" disabled="{{ serviceDown }}" onClick="{{ choose }}">Choose folder</button>
        <output>{{ path }}</output>
      </section>'''
LOGIC = '''        init(props) { return { path: (this.fx().defaultPath) || "" }; }   // runs before fixtures arrive: return a skeleton
        onReady() { this.setState(this.init(this.props)); }                  // fixtures are on window.<FX> now
        renderVals() {
          return { toast: this.state.toast, path: this.state.path, serviceDown: this.props.scene === "service-down",
            choose: () => { this.setState({ path: "D:/exports" }); this.emit("onPathChanged", "D:/exports", "Default export path updated."); } };
        }'''
