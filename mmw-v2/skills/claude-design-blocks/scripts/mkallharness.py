"""Generate the all-scenario harness page: every component in every scenario (plus each boolean prop negated), so collect_dom_classes.js can read the rendered classes.
Usage (working directory): python3 mkallharness.py [app page names to exclude...] -> Harness.dc.html (override the file name with DC_HARNESS).
The exclusion arguments are matched against the NAME of each src/*.py source, so they mean something only when an app page happens to be written as a src/*.py source too; an app page written by hand as a .dc.html is never scanned, and the call takes no arguments."""
import os, importlib.util, pathlib, sys
skip = set(sys.argv[1:]); imports = []
for p in sorted(pathlib.Path("src").glob("*.py")):
    spec = importlib.util.spec_from_file_location("b", p); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    if m.NAME in skip: continue
    scenarios = m.PROPS.get("scenario", {}).get("options", [None])
    bools = [(k, v.get("default")) for k, v in m.PROPS.items() if v.get("editor") == "boolean"]
    for s in scenarios:
        attr = f' scenario="{s}"' if s else ""
        imports.append(f'<div data-blk="{m.NAME}"><dc-import name="{m.NAME}"{attr} hint-size="100%,300px"></dc-import></div>')
        for k, d in bools:
            imports.append(f'<div data-blk="{m.NAME}"><dc-import name="{m.NAME}"{attr} {k}="{{{{ {"false" if d else "true"} }}}}" hint-size="100%,300px"></dc-import></div>')
pathlib.Path(os.environ.get("DC_HARNESS","Harness.dc.html")).write_text('''<!DOCTYPE html>
<html><head><meta charset="utf-8" /><script src="./support.js"></script></head>
<body><x-dc><helmet data-dc-atomics><style>[data-blk]{height:300px;overflow:hidden;position:relative}</style></helmet>
''' + "\n".join(imports) + '''
</x-dc>
<script type="text/x-dc" data-dc-script data-props='{}'>
class Component extends DCLogic { renderVals() { return {}; } }
</script></body></html>''')
print(len(imports), "instances")
