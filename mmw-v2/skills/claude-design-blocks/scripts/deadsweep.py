"""Remove class rules that neither templates, logic, nor fixtures reference. Read the printed list before accepting it.
Usage: deadsweep.py <src dir> <fixtures.js> <css files...>"""
import re,pathlib,sys
srcdir,fx=pathlib.Path(sys.argv[1]),pathlib.Path(sys.argv[2])
corpus=''.join(p.read_text() for p in srcdir.glob('*.py'))+fx.read_text()+(srcdir.parent/'mk.py').read_text()
dyn_prefixes=set(re.findall(r'"([a-z][\w-]*-)"\s*\+', corpus))
def used(c): return re.search(r'[^\w-]'+re.escape(c)+r'(?![\w-])', corpus) is not None
def alive(sel):
    base=re.sub(r'::?[a-zA-Z-]+(\([^)]*\))?','',sel); base=re.sub(r'\[[^\]]*\]','',base)
    cls=re.findall(r'\.([\w-]+)',base)
    return all(used(c) or any(c.startswith(p) for p in dyn_prefixes) for c in cls)
for f in sys.argv[3:]:
    css=open(f).read(); removed=[]
    def walk(s):
        res=[];pos=0
        while pos<len(s):
            b=s.find('{',pos)
            if b<0: res.append(s[pos:]); break
            head=s[pos:b]; depth=1; j=b+1
            while j<len(s) and depth:
                if s[j]=='{': depth+=1
                elif s[j]=='}': depth-=1
                j+=1
            body=s[b+1:j-1]; hs=head.strip()
            pre=re.match(r'((?:/\*.*?\*/\s*)+)',hs,re.S); cm=pre.group(1) if pre else ''; sel=hs[len(cm):]
            lead=head[:len(head)-len(head.lstrip())]
            if sel.startswith('@keyframes') or sel.startswith('@font-face'): res.append(head+'{'+body+'}')
            elif sel.startswith('@'):
                inner=walk(body)
                if inner.strip(): res.append(head+'{'+inner+'}')
            else:
                parts=[x.strip() for x in sel.split(',')]
                keep=[x for x in parts if alive(x)]; removed.extend(x for x in parts if not alive(x))
                if keep: res.append(lead+cm+',\n    '.join(keep)+' {'+body+'}')
                elif cm: res.append(lead+cm.rstrip()+'\n')
            pos=j
        return ''.join(res)
    new=re.sub(r'\n{3,}','\n\n',walk(css)); open(f,'w').write(new)
    print(f,"removed",len(removed),len(css),"->",len(new)); print("  ",sorted(set(removed)))
