#!/usr/bin/env bash
set -euo pipefail

BUILD_DIR="$(cd "$(dirname "$0")" && pwd)"
PLUGIN_DIR="${PLUGIN_DIR:-$(cd "$BUILD_DIR/.." && pwd)}"
TEMPLATE_DIR="$BUILD_DIR/templates"

MODE=""

usage() {
  echo "Usage: build.sh [--check|--apply] [--plugin-dir <dir>] [--resolver=<name>]"
  echo "  --check   Dry-run: compare generated vs current, exit 1 on diff"
  echo "  --apply   Write generated content into SKILL.md files"
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --check) MODE="check"; shift ;;
    --apply) MODE="apply"; shift ;;
    --plugin-dir) PLUGIN_DIR="$2"; shift 2 ;;
    --plugin-dir=*) PLUGIN_DIR="${1#--plugin-dir=}"; shift ;;
    --resolver=*) FILTER_RESOLVER="${1#--resolver=}"; shift ;;
    -h|--help) usage ;;
    *) echo "Unknown option: $1" >&2; usage ;;
  esac
done

if [[ -z "$MODE" ]]; then
  echo "Error: must specify --check or --apply" >&2
  usage
fi

TEMPLATE_DIR="${PLUGIN_DIR}/build/templates"

if [[ ! -d "$TEMPLATE_DIR" ]]; then
  echo "Warning: no templates directory at $TEMPLATE_DIR" >&2
  exit 0
fi

DIFF_FLAG_FILE=$(mktemp)
echo "0" > "$DIFF_FLAG_FILE"

# Shared footer appended to every voice-directive variant (single source of truth).
VOICE_FOOTER="禁止词：delve, robust, comprehensive, nuanced, multifaceted, furthermore, moreover, crucial, additionally, pivotal."

resolve_anchor() {
  local anchor_name="$1"
  local variant="$2"

  # Canonical-converted anchors — content now lives in plugin/skills/_shared/
  # Only review-dispatch's content-only variant (used by codex-review/SKILL.md) is still template-resolved
  case "$anchor_name" in
    review-dispatch)
      if [[ "$variant" != "content-only" ]]; then
        return 1
      fi
      ;;
  esac

  case "$anchor_name" in

    # ── Type 1: pure cat ─────────────────────────────────────────────────────
    failure-protocol)
      local tmpl="$TEMPLATE_DIR/${anchor_name}.md.tmpl"
      if [[ ! -f "$tmpl" ]]; then
        echo "Error: template not found: $tmpl" >&2
        return 1
      fi
      cat "$tmpl"
      ;;

    # ── Type 2: file-level variant + cat ────────────────────────────────────
    # control-envelope, review-dispatch, worker-loop: look for <anchor>.<variant>.md.tmpl,
    # fall back to <anchor>.md.tmpl if not found.
    # worker-loop has no base .md.tmpl — every anchor must carry an explicit
    # [variant=codex|claude]; a bare worker-loop anchor will error (intentional).
    control-envelope|review-dispatch|worker-loop)
      local tmpl
      if [[ -n "$variant" ]]; then
        tmpl="$TEMPLATE_DIR/${anchor_name}.${variant}.md.tmpl"
        if [[ ! -f "$tmpl" ]]; then
          tmpl="$TEMPLATE_DIR/${anchor_name}.md.tmpl"
        fi
      else
        tmpl="$TEMPLATE_DIR/${anchor_name}.md.tmpl"
      fi
      if [[ ! -f "$tmpl" ]]; then
        echo "Error: template not found: $tmpl" >&2
        return 1
      fi
      cat "$tmpl"
      ;;

    # ── Type 3: inline variant sed extraction ───────────────────────────────
    # preamble, sendmessage-resume, signpost: extract [variant=X]...[/variant] block.
    preamble|sendmessage-resume|signpost)
      local tmpl="$TEMPLATE_DIR/${anchor_name}.md.tmpl"
      if [[ ! -f "$tmpl" ]]; then
        echo "Error: template not found: $tmpl" >&2
        return 1
      fi
      if [[ -n "$variant" ]]; then
        sed -n "/\[variant=$variant\]/,/\[\/variant\]/{ /\[variant=/d; /\[\/variant\]/d; p; }" "$tmpl"
      else
        cat "$tmpl"
      fi
      ;;

    # ── Type 3 (voice): inline variant sed + footer single-source ──────────
    # voice-directive: extract variant body, then append shared footer once.
    voice-directive)
      local tmpl="$TEMPLATE_DIR/${anchor_name}.md.tmpl"
      if [[ ! -f "$tmpl" ]]; then
        echo "Error: template not found: $tmpl" >&2
        return 1
      fi
      if [[ -n "$variant" ]]; then
        sed -n "/\[variant=$variant\]/,/\[\/variant\]/{ /\[variant=/d; /\[\/variant\]/d; p; }" "$tmpl"
        printf '%s\n' "$VOICE_FOOTER"
      else
        cat "$tmpl"
      fi
      ;;

    # ── Unknown anchor ────────────────────────────────────────────────────
    *)
      return 1
      ;;
  esac
}

process_skill_file() {
  local skill_file="$1"
  local content
  content="$(cat "$skill_file")"

  local anchors
  anchors="$(grep -n '<!-- BEGIN:' "$skill_file" 2>/dev/null || true)"
  if [[ -z "$anchors" ]]; then
    return 0
  fi

  local generated="$content"

  while IFS= read -r line; do
    [[ -z "$line" ]] && continue

    local anchor_full
    anchor_full="$(echo "$line" | sed -n 's/.*<!-- BEGIN: \([^>]*\) -->.*/\1/p')"
    [[ -z "$anchor_full" ]] && continue

    local anchor_name variant=""
    anchor_name="$(echo "$anchor_full" | sed 's/ *\[.*\]//')"
    variant="$(echo "$anchor_full" | sed -n 's/.*\[variant=\([^]]*\)\].*/\1/p')"

    if [[ -n "${FILTER_RESOLVER:-}" && "$anchor_name" != "$FILTER_RESOLVER" ]]; then
      continue
    fi

    local resolved
    resolved="$(resolve_anchor "$anchor_name" "$variant" 2>/dev/null)" || continue

    local begin_pat="<!-- BEGIN: ${anchor_full} -->"
    local end_pat="<!-- END: ${anchor_name} -->"

    local tmp_in=$(mktemp)
    local tmp_resolved=$(mktemp)
    printf '%s' "$generated" > "$tmp_in"
    printf '%s' "$resolved" > "$tmp_resolved"
    generated="$(python3 -c "
import sys
with open('$tmp_in') as f:
    lines = f.readlines()
with open('$tmp_resolved') as f:
    resolved_text = f.read().rstrip('\n')

begin_marker = '''$begin_pat'''
end_marker = '''$end_pat'''

result = []
inside = False
for line in lines:
    stripped = line.strip()
    if stripped == begin_marker:
        result.append(line)
        result.append(resolved_text + '\n')
        inside = True
    elif stripped == end_marker:
        result.append(line)
        inside = False
    elif not inside:
        result.append(line)

sys.stdout.write(''.join(result))
")"
    rm -f "$tmp_in" "$tmp_resolved"
  done <<< "$anchors"

  if [[ "$MODE" == "check" ]]; then
    if ! diff -q <(echo "$content") <(echo "$generated") >/dev/null 2>&1; then
      echo "DIFF: $skill_file"
      diff --unified=3 <(echo "$content") <(echo "$generated") || true
      echo "1" > "$DIFF_FLAG_FILE"
    fi
  elif [[ "$MODE" == "apply" ]]; then
    if ! diff -q <(echo "$content") <(echo "$generated") >/dev/null 2>&1; then
      local tmp_file="${skill_file}.build.tmp"
      echo "$generated" > "$tmp_file"
      mv "$tmp_file" "$skill_file"
      echo "UPDATED: $skill_file"
    fi
  fi
}

if [[ -d "$PLUGIN_DIR/skills" ]]; then
  find "$PLUGIN_DIR/skills" -name "SKILL.md" -type f | sort | while IFS= read -r f; do
    process_skill_file "$f"
  done || true

  find "$PLUGIN_DIR/skills" -path "*/references/*.md" -type f | sort | while IFS= read -r f; do
    process_skill_file "$f"
  done || true
fi

if [[ -d "$PLUGIN_DIR/agents" ]]; then
  find "$PLUGIN_DIR/agents" -name "*.md" -type f | sort | while IFS= read -r f; do
    process_skill_file "$f"
  done || true
fi

has_diff=$(cat "$DIFF_FLAG_FILE")
rm -f "$DIFF_FLAG_FILE"
if [[ "$MODE" == "check" && "$has_diff" != "0" ]]; then
  echo "Build check failed: generated content differs from source." >&2
  exit 1
fi
