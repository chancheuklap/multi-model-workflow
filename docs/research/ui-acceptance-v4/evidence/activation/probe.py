import json, os, socket, subprocess, sys, tempfile, time, urllib.request
from playwright.sync_api import sync_playwright
GW = "http://127.0.0.1:8788"
AF = os.path.expanduser("~/agentflow")
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
root = tempfile.mkdtemp(prefix="parrot-act-")
env = {**os.environ,
       "PARROT_DUBBING_PORT": str(port),
       "PARROT_DUBBING_RUNTIME_ROOT": root,
       "PARROT_DUBBING_SOURCE_RUN_LOG_ROOT": os.path.join(root, "srclogs"),
       "PARROT_DUBBING_STRUCTURED_LOG_ROOT": os.path.join(root, "slogs"),
       "PARROT_GATEWAY_BASE_URL": GW,
       "PARROT_DUBBING_REDIRECT_URI": f"http://127.0.0.1:{port}/auth/callback",
       "PARROT_DUBBING_INSTANCE_FINGERPRINT": "e2e-probe-" + os.urandom(6).hex(),
       "PARROT_DUBBING_BACKEND_INSTANCE_TOKEN": "probe"}
print("port", port, "root", root)
log = open(os.path.join(root, "backend.out"), "w")
p = subprocess.Popen(["uv", "run", "--extra", "parrot-dubbing", "python", "-m", "parrot_dubbing"], cwd=AF, env=env, stdout=log, stderr=subprocess.STDOUT)
B = f"http://127.0.0.1:{port}"
def get(u):
    with urllib.request.urlopen(u, timeout=5) as r: return r.status, r.read().decode()
def post(u, body=None):
    req = urllib.request.Request(u, data=(json.dumps(body).encode() if body is not None else b""), headers=({"Content-Type": "application/json"} if body is not None else {}), method="POST")
    with urllib.request.urlopen(req, timeout=30) as r: return r.status, json.loads(r.read())
try:
    for i in range(240):
        try:
            if get(B + "/live")[0] == 200: break
        except Exception: time.sleep(0.5)
    else: sys.exit("backend never came up")
    print("backend live after ~%.0fs" % (i * 0.5))
    print("status before:", get(B + "/api/activation/status")[1][:200])
    st, started = post(B + "/api/activation/start")
    print("start", st, "kind", started.get("kind"), "auth host", started["authorization_url"].split("?")[0])
    with sync_playwright() as pw:
        br = pw.chromium.launch(); pg = br.new_page()
        pg.goto(GW + "/login", wait_until="domcontentloaded")
        pg.locator("#phone_number").fill(os.environ.get("PHONE","13700137000")); pg.locator("#password").fill(os.environ["PASSWORD"])
        pg.locator("#login-btn").click(); pg.wait_for_load_state("domcontentloaded"); time.sleep(1)
        print("after login url:", pg.url.replace(GW, "GW"))
        pg.goto(started["authorization_url"], wait_until="domcontentloaded")
        print("consent page:", pg.url.replace(GW, "GW"), "|", pg.title())
        btns = pg.locator("form button[type=submit], form input[type=submit]")
        print("buttons:", [b.inner_text() if b.evaluate("e=>e.tagName")=="BUTTON" else b.get_attribute("value") for b in btns.all()])
        print("forms:", pg.evaluate("""() => [...document.forms].map(f => ({a: f.action.replace(location.origin,''), m: f.method, inputs: [...f.elements].map(e => [e.tagName, e.type, e.name, e.disabled, e.checked])}))"""))
        resps = []
        pg.on("response", lambda r: resps.append((r.request.method, r.url.split("?")[0], r.status, (r.headers.get("location") or "")[:80])))
        pg.on("dialog", lambda d: (print("dialog:", d.message), d.accept()))
        if "已经在另一台电脑上使用" in pg.locator("body").inner_text():
            print("BOUND ELSEWHERE - not replacing"); br.close(); raise SystemExit(3)
        btns.first.click(); time.sleep(4)
        print("responses:", resps[:8])
        print("landed:", pg.url.split("?")[0]); print("BODY:", pg.locator("body").inner_text()[:1500].replace("\n", " / "))
        br.close()
    print("status after:", get(B + "/api/activation/status")[1][:300])
finally:
    p.terminate()
    try: p.wait(10)
    except Exception: p.kill()
    t=open(os.path.join(root, "backend.out")).read()
    print("backend errors:", [l[:300] for l in t.splitlines() if "error" in l.lower()][-5:])
