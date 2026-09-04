"""Generate a single-component harness: a <select> drives the component's scene prop. Usage: mkharness.py <name> '<JSON array of scene values>' [extra dc-import attributes] -> Harness.dc.html (override the file name with DC_HARNESS)"""
import os, sys, json
name, opts = sys.argv[1], json.loads(sys.argv[2])
extra = sys.argv[3] if len(sys.argv) > 3 else ""
open(os.environ.get('DC_HARNESS','Harness.dc.html'),'w').write(f'''<!DOCTYPE html>
<html><head><meta charset="utf-8" /><script src="./support.js"></script></head>
<body><x-dc>
<helmet data-dc-atomics><style>html, body {{ margin: 0; height: 100%; }} #dc-root, #dc-root > * {{ height: 100%; }} .tb {{ position: fixed; top: 0; right: 0; z-index: 999; font: 11px monospace; }}</style></helmet>
<select class="tb" id="scene-select" onChange="{{{{ pick }}}}"><sc-for list="{{{{ options }}}}" as="o"><option value="{{{{ o }}}}">{{{{ o }}}}</option></sc-for></select>
<dc-import name="{name}" scene="{{{{ cur }}}}" {extra} hint-size="100%,100%"></dc-import>
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{{}}'>
class Component extends DCLogic {{
  constructor(p) {{ super(p); this.state = {{ cur: {json.dumps(opts[0])} }}; }}
  renderVals() {{ return {{ cur: this.state.cur, options: {json.dumps(opts, ensure_ascii=False)}, pick: (e) => this.setState({{ cur: e.target.value }}) }}; }}
}}
</script></body></html>''')
