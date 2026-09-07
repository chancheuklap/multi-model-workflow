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
          return { items: [], ready: false };
        }
        onReady() {
          const items = this.props.scene === "empty" ? [] : (this.fx().items || []);
          this.setState({ items, ready: true });
        }
        renderVals() {
          if (!this.state.fx) {
            return { title: "", count: 0, items: [], ready: false, fx: false };
          }
          return {
            title: this.props.scene === "empty" ? "None" : "Ready",
            count: this.state.items.length,
            items: this.state.items,
            ready: this.state.ready,
            fx: this.state.fx,
            pick: () => this.emit("onPick", this.state.items[0], "picked"),
          };
        }'''
