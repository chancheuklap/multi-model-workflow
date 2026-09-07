NAME = "Component · list"
CSS = []
EXTRA_CSS = ""
PROPS = {
  "scene": {"editor": "enum", "default": "ready", "tsType": "string", "options": ["ready", "empty"]},
}
TEMPLATE = '''      <section class="list">
        <h1>{{ title }}</h1>
        <p>{{ count }}</p>
      </section>'''
LOGIC = '''        init(props) {
          const items = props.scene === "empty" ? [] : (this.fx().items || []);
          return { items };
        }
        renderVals() {
          return {
            title: this.props.scene === "empty" ? "None" : "Ready",
            count: this.state.items.length,
            items: this.state.items,
            pick: () => this.emit("onPick", this.state.items[0], "picked"),
          };
        }'''
