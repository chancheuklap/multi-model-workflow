"""Flatten the mockup CSS selectors into the forms the Claude Design editor resolves (.a / .a.b / .a .b, pseudo-classes allowed)
and write the new classes into the TEMPLATE of src/*.py. Usage (in the working directory, next to domclasses.json): flatten.py <src dir> <css files...>"""
import sys, re, json, pathlib, importlib.util
import tinycss2
from bs4 import BeautifulSoup
import soupsieve as sv

srcdir = pathlib.Path(sys.argv[1]); cssfiles = [pathlib.Path(p) for p in sys.argv[2:]]
PSEUDO = re.compile(r'(::?[a-zA-Z-]+(\([^)]*\))?)+$')
ELEMENT_GLOBAL = {"html","body","button","input","select","textarea","a","h1","h2","h3","p","ul","li","dl","dt","dd","small","strong","b","span","output","label","svg","*"}

def load_templates():
    out = {}
    for p in sorted(srcdir.glob("*.py")):
        txt = p.read_text()
        m = re.search(r"TEMPLATE = '''(.*?)'''", txt, re.S)
        if not m: continue
        out[p] = [txt, m.start(1), m.group(1)]
    return out

templates = load_templates()
# parse templates; html.parser keeps source positions
parsed = {}
DOM = json.load(open("domclasses.json"))
while isinstance(DOM, str): DOM = json.loads(DOM)  # tolerate a double-encoded eval result  # in the working directory, produced by collect_dom_classes.js
for p, (txt, off, tpl) in templates.items():
    soup = BeautifulSoup(tpl, "html.parser")
    parsed[p] = soup
    css_n = len(re.findall(r'"[^"]+\.css"', txt.split("TEMPLATE")[0])); helmet_n = css_n + 2
    obs = DOM.get(p.stem, {})
    for i, tag in enumerate(soup.find_all(True)):
        attr = tag.get('class'); attr = ' '.join(attr) if isinstance(attr, list) else (attr or '')
        if '{{' in attr:
            tag['data-dyn'] = '1'
            seen = obs.get(str(helmet_n + i + 1), {})
            static = [c for c in attr.split() if '{{' not in c and '}}' not in c]
            tag['class'] = ' '.join(static + [c for c in seen if c not in static])

def tokens(base):
    return [t for t in re.split(r'\s*[>+~]\s*|\s+', base.strip()) if t]

def is_ok(sel):
    base = PSEUDO.sub('', sel).strip()
    # strip pseudo-classes in the middle before judging
    base = re.sub(r'::?[a-zA-Z-]+(\([^)]*\))?', '', base)
    base = re.sub(r'\[[^\]]*\]', '', base)
    toks = tokens(base)
    if len(toks) == 1 and toks[0] in ELEMENT_GLOBAL: return True  # global element reset
    if '#' in base: return False
    if any(re.match(r'^[a-zA-Z*]', t) for t in toks): return False
    if len(toks) > 2: return False
    if sum(t.count('.') for t in toks) > 2: return False
    return True

def new_name(toks):
    last = toks[-1]
    last_cls = [c for c in last.split('.')[1:]]
    last_el = last.split('.')[0]
    prev = None
    for t in reversed(toks[:-1]):
        if '.' in t: prev = t.split('.')[1]; break
    tail = '-'.join(last_cls) if last_cls else last_el
    if not prev: return tail
    if tail.startswith(prev): return tail
    return f"{prev}-{tail}"

edits = {}   # path -> list of (pos, class)
log = {"flattened": [], "unmatched": [], "dynamic": [], "manual": [], "dropped": []}
names_used = {}

def add_class_to_tag(p, tag, cls):
    soup_txt = templates[p][2]
    line, col = tag.sourceline, tag.sourcepos
    # locate the start tag text
    lines = soup_txt.split('\n'); pos = sum(len(l) + 1 for l in lines[:line-1]) + col
    end = soup_txt.index('>', pos)
    start_tag = soup_txt[pos:end]
    m = re.search(r'\sclass="([^"]*)"', start_tag)
    if m:
        if cls in m.group(1).split(): return "has"
        if '{{' in m.group(1):
            edits.setdefault(p, []).append((pos + m.start(1), cls + " "))
            return "ok"
        key = (pos + m.end(1))
        edits.setdefault(p, []).append((key, " " + cls))
    else:
        tagname_end = pos + 1 + len(tag.name)
        edits.setdefault(p, []).append((tagname_end, f' class="{cls}"'))
    return "ok"

def match_all(match_sel, toks):
    res = []
    for p, soup in parsed.items():
        res += [(p, t) for t in sv.select(match_sel, soup)]
    return res

def process_selector(sel):
    sel = sel.strip()
    if is_ok(sel): return sel
    pseudo_m = PSEUDO.search(sel); suffix = pseudo_m.group(0) if pseudo_m else ''
    base = sel[:len(sel) - len(suffix)]
    if re.search(r':[a-zA-Z-]+', base) or '[' in base or '#' in base:
        log["manual"].append(sel); return sel
    toks = tokens(base)
    # one state class on the ancestor (.A.s .B...): flatten the tail, then emit .s .B (two-class descendant, editor-resolvable)
    if toks[0].count('.') == 2 and all(t.count('.') <= 1 for t in toks[1:]):
        a, st = toks[0].split('.')[1:]
        tail = toks[1:]
        if len(tail) == 1 and tail[0].startswith('.') and tail[0].count('.') == 1:
            log["flattened"].append(f"{sel} -> .{st} {tail[0]}{suffix}"); return f".{st} {tail[0]}{suffix}"
        inner = process_selector('.' + a + ' ' + ' '.join(tail))
        if inner is None: log["dropped"].append(sel); return None
        if inner.startswith('.') and ' ' not in inner and inner.count('.') == 1:
            log["flattened"].append(f"{sel} -> .{st} {inner}{suffix}"); return f".{st} {inner}{suffix}"
        log["manual"].append(sel); return sel
    # one state class on a middle ancestor (.A .B.s .C): emit .s .C when the tail is a single class
    mids = [i for i, t in enumerate(toks[:-1]) if t.count('.') >= 2]
    if len(mids) == 1 and toks[mids[0]].count('.') == 2 and mids[0] == len(toks) - 2 and toks[-1].startswith('.') and toks[-1].count('.') == 1:
        st = toks[mids[0]].split('.')[-1]
        log["flattened"].append(f"{sel} -> .{st} {toks[-1]}{suffix}"); return f".{st} {toks[-1]}{suffix}"
    if mids:
        log["manual"].append(sel); return sel
    # trailing state class (button.on / .b.on): flatten the base first, then append the state -> .base.on (two-class compound)
    last = toks[-1]; parts = last.split('.')
    if (parts[0] and len(parts) >= 2) or (not parts[0] and len(parts) >= 3):
        base_last = parts[0] if parts[0] else '.' + parts[1]
        states = parts[1:] if parts[0] else parts[2:]
        inner = process_selector(' '.join(toks[:-1] + [base_last]))
        if inner is None: log["dropped"].append(sel); return None
        if inner.startswith('.') and ' ' not in inner and inner.count('.') == 1:
            out = inner + '.' + '.'.join(states) + suffix
            log["flattened"].append(f"{sel} -> {out}"); return out
        log["manual"].append(sel); return sel
    name = new_name(toks)
    # same generated name from a different selector: add a suffix
    if name in names_used and names_used[name] != base:
        i = 2
        while f"{name}-{i}" in names_used and names_used[f"{name}-{i}"] != base: i += 1
        name = f"{name}-{i}"
    names_used[name] = base
    matched = 0; dyn = 0
    match_sel = re.sub(r'\s*>\s*', ' ', base)
    try: found = match_all(match_sel, tokens(match_sel))
    except Exception as e: log["manual"].append(sel + f"  ({e})"); return sel
    for p, tag in found:
        r = add_class_to_tag(p, tag, name)
        if r == "dynamic": dyn += 1
        else: matched += 1
    if matched == 0:
        log["unmatched"].append(sel)
        # a ".class element" chain with no target element in any template only matches the runtime wrapper span: drop it
        if not toks[-1].startswith('.') and '.' not in toks[-1]: log["dropped"].append(sel); return None
        return sel
    log["flattened"].append(f"{sel} -> .{name}{suffix}" + (f"  [{dyn} dynamic skipped]" if dyn else ""))
    return f".{name}{suffix}"

def rewrite_css(text):
    out = []; i = 0
    # rule by rule: selector { ... }, leaving @keyframes untouched
    def walk(s):
        res = []
        pos = 0
        while pos < len(s):
            b = s.find('{', pos)
            if b < 0: res.append(s[pos:]); break
            head = s[pos:b]
            # find the matching }
            depth = 1; j = b + 1
            while j < len(s) and depth:
                if s[j] == '{': depth += 1
                elif s[j] == '}': depth -= 1
                j += 1
            body = s[b+1:j-1]
            hs = head.strip()
            if hs.startswith('@keyframes') or hs.startswith('@font-face'):
                res.append(head + '{' + body + '}')
            elif hs.startswith('@'):
                res.append(head + '{' + walk(body) + '}')
            else:
                lead = head[:len(head) - len(head.lstrip())]
                cm = re.match(r'((?:/\*.*?\*/\s*)+)', hs, re.S)
                pre = cm.group(1) if cm else ''
                hs2 = hs[len(pre):]
                sels = [y for y in (process_selector(x) for x in hs2.split(',')) if y]
                if sels: res.append(lead + pre + ',\n    '.join(sels) + ' {' + body + '}')
                elif pre: res.append(lead + pre.rstrip() + '\n')
            pos = j
        return ''.join(res)
    return walk(text)

for c in cssfiles:
    new = rewrite_css(c.read_text())
    c.write_text(new)

for p, lst in edits.items():
    txt, off, tpl = templates[p]
    # dedupe same position + same class
    seen = set(); ins = []
    for pos, s in lst:
        if (pos, s) in seen: continue
        seen.add((pos, s)); ins.append((pos, s))
    for pos, s in sorted(ins, reverse=True):
        tpl = tpl[:pos] + s + tpl[pos:]
    # merge repeated class="x" class="y" insertions
    tpl = re.sub(r'class="([^"]*)" class="([^"]*)"', r'class="\1 \2"', tpl)
    txt = txt[:off] + tpl + txt[off + len(templates[p][2]):]
    p.write_text(txt)

for k, v in log.items():
    print(f"## {k}: {len(v)}")
    for x in v[:400]: print("  ", x)
