# Usage: source serve.sh; open_page <file name>   (the token is project-scoped and reusable for ~1 hour)
TOK="t=<token from render_preview serve_url>&direct=1"
BASE="https://<projectId>.claudeusercontent.com/v1/design/projects/<projectId>/serve/"
enc(){ python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$1"; }
open_page(){ playwright-cli goto "${BASE}$(enc "$1")?${TOK}" >/dev/null 2>&1 || playwright-cli open "${BASE}$(enc "$1")?${TOK}" >/dev/null 2>&1; playwright-cli resize 1440 900 >/dev/null 2>&1; sleep 5; }
q(){ playwright-cli --raw eval "$1"; }
errs(){ playwright-cli console 2>/dev/null | grep -i "\[ERROR\]" | grep -v favicon | head -3; }
sel(){ playwright-cli select "#scenario-select" "$1" >/dev/null 2>&1; sleep 0.8; }
clk(){ playwright-cli click "$1" >/dev/null 2>&1; sleep 0.5; }
shot(){ playwright-cli screenshot --filename="$1" >/dev/null 2>&1; }
