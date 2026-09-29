import json, os
H = os.path.dirname(os.path.abspath(__file__)); D0 = os.path.join(H, '..', 'data')
def rd(p): return open(os.path.join(H, p), encoding='utf-8').read()
data = {k: json.load(open(os.path.join(D0, f), encoding='utf-8')) for k, f in [('arch', 'arch.json'), ('mig', 'migration.json'), ('pb', 'playbooks.json'), ('pr', 'principles.json'), ('ops', 'ops.json')]}
import sys; sys.path.insert(0, H); from patch import patch; patch(data)
from patch_d17 import patch_d17; patch_d17(data)
from patch_r19 import patch_r19; patch_r19(data)
js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
page = rd('head.html') + rd('body.html') + '\n<script>\n/* Data: the five JSON files extracted from R18, R14, R13 (every record carries src). */\nconst D = ' + js + ';\n' + rd('lib.js') + '\n' + rd('app1.js') + '\n' + rd('app2.js') + '\n' + rd('app3.js') + '\n' + rd('app4.js') + '\n</script>\n'
out = os.path.join(H, '..', 'mmw-layering-detailed.html')
open(out, 'w', encoding='utf-8').write(page)
print(len(page))
