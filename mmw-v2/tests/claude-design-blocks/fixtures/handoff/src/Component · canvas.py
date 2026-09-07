NAME = "Component · canvas"
CSS = []
EXTRA_CSS = ""
PROPS = {
  "scene": {"editor": "enum", "default": "idle", "tsType": "string", "options": ["idle", "dragging"]},
}
TEMPLATE = '''      <section class="canvas">
        <p>{{ label }}</p>
      </section>'''
LOGIC = '''        init(props) {
          return { label: "", scene: props.scene };
        }
        onReady() {
          window.addEventListener("pointermove", () => {
            this.setState({ hovering: true });
          });
          this.setState({ label: this.fx().canvasLabel || "" });
        }
        renderVals() {
          return { label: this.state.label, scene: this.state.scene, fx: this.state.fx };
        }'''
