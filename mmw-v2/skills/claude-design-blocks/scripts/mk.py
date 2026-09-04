"""Build one component: python3 mk.py src/<name>.py -> ./<name>.dc.html (run in the working directory).
Each src/<name>.py defines NAME, CSS (list of file names under styles/), EXTRA_CSS, TEMPLATE, PROPS (dict), LOGIC (class body).
Fixtures live on window.<FX>, loaded from <FX_FILE>; DC_FX names the global (default FIXTURES), DC_FX_FILE the file (default data/fixtures.js); components read them via this.fx().
The helmet fixes #dc-root to the application window size (DC_FRAME, default 1440x900; transform: translateZ(0) makes position: fixed overlays contain to the frame) and sets #dc-root > * { height: 100% } so a component fills it; a component that keeps its natural height (a header bar) re-declares height: auto in EXTRA_CSS."""
import sys, json, importlib.util, pathlib, os
FX = os.environ.get("DC_FX", "FIXTURES")
FX_FILE = os.environ.get("DC_FX_FILE", "data/fixtures.js")  # project-relative path of the fixtures script
W, H = (int(v) for v in os.environ.get("DC_FRAME", "1440x900").split("x"))  # the application window the mockup was designed for
spec = importlib.util.spec_from_file_location("blk", sys.argv[1]); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
links = "\n".join(f'        <link rel="stylesheet" href="./styles/{c}" />' for c in m.CSS)
props = {"$preview": {"width": W, "height": H}, **m.PROPS}
html = f'''<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <script src="./support.js"></script>
  </head>
  <body>
    <x-dc>
      <helmet data-dc-atomics>
{links}
        <script src="./{FX_FILE}"></script>
        <style>
          body {{ margin: 0; min-height: 100vh; background: #e6e3df; }}
          #dc-root {{ width: {W}px; height: {H}px; margin: 0 auto; overflow: hidden; position: relative; transform: translateZ(0); }}
          #dc-root > * {{ height: 100%; }}
          .dc-toast {{ position: fixed; left: 50%; bottom: 28px; transform: translateX(-50%); z-index: 50; padding: 10px 16px; border-radius: 10px; background: var(--ink); color: #fff; font-size: 12px; box-shadow: 0 12px 32px rgba(45, 25, 34, 0.25); }}
          .dc-backdrop {{ position: fixed; inset: 0; background: rgba(40, 25, 32, 0.38); z-index: 40; }}
          .dc-modal {{ position: fixed; inset: 0; margin: auto; height: fit-content; z-index: 41; }}
{m.EXTRA_CSS}
        </style>
      </helmet>
{m.TEMPLATE}
      <sc-if value="{{{{ toast }}}}" hint-placeholder-val="{{{{ false }}}}">
        <div class="dc-toast" role="status">{{{{ toast }}}}</div>
      </sc-if>
    </x-dc>
    <script
      type="text/x-dc"
      data-dc-script
      data-props='{json.dumps(props, ensure_ascii=False, indent=2)}'
    >
      class Component extends DCLogic {{
        constructor(props) {{
          super(props);
          this.state = Object.assign({{ fx: false, toast: "" }}, this.init(props));
        }}
        componentDidMount() {{
          const tick = () => {{
            if (window.{FX}) {{ this.setState({{ fx: true }}, () => this.onReady && this.onReady()); return; }}
            this._w = setTimeout(tick, 50);
          }};
          tick();
        }}
        componentWillUnmount() {{ clearTimeout(this._w); clearTimeout(this._t); this.cleanup && this.cleanup(); }}
        componentDidUpdate(prev) {{
          if (prev.scene !== this.props.scene) this.setState(this.init(this.props), () => this.onReady && this.onReady());
          this.afterUpdate && this.afterUpdate(prev);
        }}
        toast(msg) {{
          this.setState({{ toast: msg }});
          clearTimeout(this._t); this._t = setTimeout(() => this.setState({{ toast: "" }}), 2400);
        }}
        emit(name, detail, fallback) {{
          if (this.props[name]) this.props[name](detail); else this.toast(fallback);
        }}
        fx() {{ return window.{FX} || {{}}; }}
{m.LOGIC}
      }}
    </script>
  </body>
</html>
'''
out = pathlib.Path(m.NAME + ".dc.html"); out.write_text(html); print(out, len(html))
