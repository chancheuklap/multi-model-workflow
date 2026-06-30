#!/usr/bin/env bash
# Pack 2.11: generate (or validate) the "## Pack Execution Manifest" section in
# a plan document. Scans `### Task Pack N.M[: title]` headers, derives per-pack
# title / anchor / risk / dependencies / owned files from the pack body, and:
#   - default mode: rewrites the Manifest section in place
#   - --check mode: compares the existing Manifest to the regenerated content and
#                   exits non-zero on drift (no file mutation)
#
# Used by:
#   - plan-writer (optional helper to fill the Manifest table)
#   - Coordinator pre-dispatch sanity check (via Pack 2.13 validate-pack-manifest.sh)
#   - CI: `--check` to catch plans where Manifest drifted from Pack bodies
set -euo pipefail

MODE="apply"
PLAN_FILE=""
usage() {
  cat <<'USAGE'
Usage: generate-pack-manifest.sh [--check] <plan-file>

Modes:
  apply (default)  rewrite the "## Pack Execution Manifest" section in place
  --check          do not modify the file; exit 0 if Manifest matches the Pack bodies, non-zero otherwise
USAGE
  exit 2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --help|-h) usage ;;
    -*) echo "Error: unknown flag $1" >&2; usage ;;
    *) PLAN_FILE="$1"; shift ;;
  esac
done

if [[ -z "$PLAN_FILE" || ! -f "$PLAN_FILE" ]]; then
  echo "Error: plan file required and must exist" >&2
  usage
fi

# Extract per-pack rows from the plan body.
# Strategy: walk the file line by line, when we see `### Task Pack N.M[: title]`
# open a new record and capture title + body until the next `### ` heading. From
# the body extract:
#   - risk: line beginning "**Risk flags:**" or "Risk flags:" (markdown allows
#     both bold and plain in current templates)
#   - dependencies: line "Dependencies:" / "**Dependencies:**"
#   - owned files: lines under "Owned files / responsibilities:" or under
#     "Owned files:" until the next blank line / next labelled field
# Anchor: derived deterministically from the heading via the same rule GitHub
# markdown renderers use — lowercase, spaces->hyphens, strip punctuation; with
# a "pack-N-M-" prefix when the heading starts with "Task Pack N.M".

build_rows() {
  local plan="$1"
  python3 - "$plan" <<'PY'
import re
import sys

plan_path = sys.argv[1]
with open(plan_path, encoding="utf-8") as f:
    lines = f.read().splitlines()

# Find all "### Task Pack N.M[: title]" headings and record the line index.
heading_re = re.compile(r"^###\s+Task\s+Pack\s+(\d+\.\d+)\s*[:：]?\s*(.*)$")
sec_re = re.compile(r"^###\s+")

packs = []
current = None

def flush():
    global current
    if current is not None:
        packs.append(current)
        current = None

for idx, line in enumerate(lines):
    m = heading_re.match(line)
    if m:
        flush()
        pack_id = m.group(1)
        title = m.group(2).strip()
        current = {
            "pack_id": pack_id,
            "title": title,
            "heading_line": line,
            "body": [],
        }
        continue
    if current is not None:
        if sec_re.match(line):
            # Next ### heading — close current pack record.
            flush()
            # Don't continue capturing this heading as body
        else:
            current["body"].append(line)

flush()

def slugify(s):
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "-", s.strip())
    return s

def find_field(body, label):
    # Match plain or bold label, returning the inline value after the colon.
    pat = re.compile(rf"^\s*\*{{0,2}}{re.escape(label)}\*{{0,2}}\s*[:：]\s*(.*)$")
    for line in body:
        m = pat.match(line)
        if m:
            return m.group(1).strip()
    return ""

def find_block(body, label):
    # Multi-line block: collect lines after "label:" until the next blank line
    # or the next labelled field heading.
    pat = re.compile(rf"^\s*\*{{0,2}}{re.escape(label)}\*{{0,2}}\s*[:：]\s*$")
    out = []
    capture = False
    for line in body:
        if capture:
            if line.strip() == "":
                break
            if re.match(r"^\s*\*{0,2}[A-Za-z]", line) and ":" in line and not line.lstrip().startswith("-"):
                # New labelled field starts; stop.
                break
            out.append(line)
            continue
        if pat.match(line):
            capture = True
    return out

rows = []
for p in packs:
    pack_id = p["pack_id"]
    title = p["title"] or "—"
    # Heading slug: GitHub-style anchor for the entire ### Task Pack N.M[: title] line.
    raw = p["heading_line"][len("### "):]
    anchor = slugify(raw)

    risk = find_field(p["body"], "Risk flags") or "normal"
    deps = find_field(p["body"], "Dependencies") or "—"

    owned_block = find_block(p["body"], "Owned files / responsibilities")
    if not owned_block:
        owned_block = find_block(p["body"], "Owned files")
    owned_files = []
    for ol in owned_block:
        ol_strip = ol.strip()
        if not ol_strip.startswith("-"):
            continue
        # Extract first backtick-quoted path, else the text after "- "
        m = re.search(r"`([^`]+)`", ol_strip)
        if m:
            owned_files.append(m.group(1))
        else:
            owned_files.append(ol_strip.lstrip("- ").strip())
    owned_str = ", ".join(f"`{f}`" for f in owned_files) if owned_files else "—"

    rows.append(f"| {pack_id} | {title} | `#{anchor}` | {risk} | {deps} | {owned_str} |")

print("\n".join(rows))
PY
}

ROWS=$(build_rows "$PLAN_FILE")
HEADER='| pack_id | title | anchor | risk | dependencies | owned_files (核心) |'
DIVIDER='| --- | --- | --- | --- | --- | --- |'

NEW_TABLE=$(printf '%s\n%s\n%s\n' "$HEADER" "$DIVIDER" "$ROWS")

# Compose the full Manifest section content.
SECTION=$(cat <<MEOF
## Pack Execution Manifest

Worker 入口查询表。每行：pack_id → 章节锚点 + 关键字段索引。Worker 自治读 Manifest 即可定位每个 Pack，不必线性扫描全文。

${NEW_TABLE}

（生成器：plugin/build/generate-pack-manifest.sh；Coordinator 派 Worker 前以 validate-pack-manifest.sh 做 Manifest / Pack 主体 / execution-state.packs keys 三方对账）
MEOF
)

# Locate existing "## Pack Execution Manifest" section (until next "## ") so we can
# replace it; if absent, append the section at end of file.
TMP="$(mktemp)"
python3 - "$PLAN_FILE" "$TMP" "$SECTION" <<'PY'
import re
import sys

plan_path, tmp_path, section = sys.argv[1], sys.argv[2], sys.argv[3]
with open(plan_path, encoding="utf-8") as f:
    text = f.read()

start_re = re.compile(r"^## Pack Execution Manifest\s*$", re.MULTILINE)
m = start_re.search(text)

if m is None:
    # Append at end (with separating blank line) and a trailing newline so
    # the file ends in exactly one '\n' regardless of input shape.
    new = text
    if not new.endswith("\n"):
        new += "\n"
    if not new.endswith("\n\n"):
        new += "\n"
    new += section.rstrip("\n") + "\n"
else:
    start = m.start()
    # Stop replacement at the next heading of any depth (## or ###) OR a
    # horizontal rule ('---'). The Manifest section lives between two such
    # boundaries; we must not engulf subsequent Pack bodies that follow it.
    end_re = re.compile(r"^(?:##\s|###\s|---\s*$)", re.MULTILINE)
    nm = end_re.search(text, m.end())
    if nm is None:
        end = len(text)
        new = text[:start] + section.rstrip("\n") + "\n"
    else:
        end = nm.start()
        new = text[:start] + section.rstrip("\n") + "\n\n" + text[end:]

# Normalize: file must end in exactly one '\n'.
new = new.rstrip("\n") + "\n"

with open(tmp_path, "w", encoding="utf-8") as f:
    f.write(new)
PY

if [[ "$MODE" == "check" ]]; then
  if diff -q "$PLAN_FILE" "$TMP" >/dev/null; then
    rm -f "$TMP"
    echo "OK: Manifest matches Pack bodies in $PLAN_FILE"
    exit 0
  else
    echo "DRIFT: Pack Execution Manifest in $PLAN_FILE does not match Pack bodies." >&2
    echo "Run without --check to regenerate. Diff (current → regenerated):" >&2
    diff -u "$PLAN_FILE" "$TMP" >&2 || true
    rm -f "$TMP"
    exit 2
  fi
fi

mv "$TMP" "$PLAN_FILE"
echo "Updated Pack Execution Manifest in $PLAN_FILE"
