import http.server
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent
name = os.environ["MMW_PRODUCT"]
data = Path(os.environ["MMW_DATA_DIR"])
port = int(os.environ["MMW_PORT_BASE"])
origin = f"http://127.0.0.1:{port}"
verb = sys.argv[1]

if verb == "serve":
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(name.encode())

        def do_POST(self):
            self.send_response(200)
            self.end_headers()
            self.server.done = True

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", port), Handler)
    server.done = False
    (data / "pid").write_text(str(os.getpid()))
    while not server.done:
        server.handle_request()
    server.server_close()
    sys.exit(0)

with (root / "events.jsonl").open("a") as log:
    keys = {"MMW_INSTANCE", "MMW_SLOT", "MMW_PORT_BASE", "MMW_PORT_COUNT",
            "MMW_DATA_DIR", "MMW_AUTOMATION", "MMW_PRODUCT", "MMW_BREAK",
            "MMW_EVIDENCE_DIR", "ORIGIN", "INSTANCE", "METADATA"}
    config = json.loads((root / "target.json").read_text())
    for product in config["products"]:
        prefix = product.upper().replace("-", "_") + "_"
        keys.update(prefix + key for key in ("ORIGIN", "INSTANCE", "METADATA"))
    seen = {key: value for key, value in os.environ.items() if key in keys}
    event = {"product": name, "verb": verb, "env": seen}
    if verb == "journey":
        event["evidence_files"] = sorted(p.name for p in
                                         Path(os.environ["MMW_EVIDENCE_DIR"]).iterdir())
    log.write(json.dumps(event) + "\n")

if verb in ("start", "discover", "doctor", "command", "journey"):
    config = json.loads((root / "target.json").read_text())
    for dependency in config["needs"].get(name, []):
        address = os.environ[dependency.upper().replace("-", "_") + "_ORIGIN"]
        with urllib.request.urlopen(address, timeout=2) as response:
            assert response.read().decode() == dependency

if verb == "start":
    if (root / f"fail-{name}").exists():
        sys.exit(7)
    data.mkdir(parents=True, exist_ok=True)
    with (data / "server.log").open("a") as output:
        child = subprocess.Popen([sys.executable, __file__, "serve"], stdout=output,
                                 stderr=output, env=dict(os.environ))
    for _ in range(100):
        if (data / "pid").exists():
            break
        if child.poll() is not None:
            sys.exit(child.returncode)
        time.sleep(0.01)
    else:
        raise RuntimeError("server never bound its lease port")
elif verb == "stop":
    if (root / f"leave-{name}").exists():
        sys.exit(0)
    if (data / "pid").exists():
        with urllib.request.urlopen(urllib.request.Request(origin, method="POST"), timeout=2):
            pass
        for _ in range(100):
            with socket.socket() as probe:
                if probe.connect_ex(("127.0.0.1", port)) != 0:
                    break
            time.sleep(0.01)
        else:
            raise RuntimeError("server still listening after stop")
        (data / "pid").unlink()
elif verb == "discover":
    print(json.dumps({"origin": origin + "/discovered", "instance": os.environ["MMW_INSTANCE"],
                      "metadata": {"product": name}}))
elif verb == "command":
    record = Path(os.environ["MMW_HOME"]) / "leases" / f"slot-{os.environ['MMW_SLOT']}.json"
    print(record.read_text())
elif verb == "journey":
    with urllib.request.urlopen(os.environ["ORIGIN"], timeout=2) as response:
        assert response.read().decode() == name
    Path(os.environ["MMW_EVIDENCE_DIR"], "result.txt").write_text(name)
elif verb == "doctor":
    print(json.dumps({"pid": int((data / "pid").read_text()), "ports": [port], "version": "test"}))
