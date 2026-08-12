#!/usr/bin/env bash
# 工具链探测必须看见本轮新建但尚未提交的工作区。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DETECT="$HERE/../lib/toolchain_detect.py"
APPLY="$HERE/../lib/toolchain_apply.py"
RULES="$HERE/../../config/toolchain-rules.json"
TEMPLATES="$HERE/../../toolchain/templates"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

REPO="$WORK/repo"
git init -q -b main "$REPO"
git -C "$REPO" config user.name "MMW Toolchain"
git -C "$REPO" config user.email "toolchain@example.invalid"
mkdir -p "$REPO/.github/workflows" "$REPO/desktop-existing/src"
printf 'node_modules/\nignored-app/\n' > "$REPO/.gitignore"
printf '{"devDependencies":{"typescript":"5.9.3"}}\n' > "$REPO/desktop-existing/package.json"
printf 'export const existing = true;\n' > "$REPO/desktop-existing/src/index.ts"
git -C "$REPO" add .gitignore .github desktop-existing
git -C "$REPO" commit -qm seed

# 模拟 worker 同一轮新建 Electron 工作区、在第一次提交前运行 toolchain apply。
mkdir -p "$REPO/desktop-new/src" "$REPO/ignored-app/src"
printf '{"devDependencies":{"typescript":"5.9.3"}}\n' > "$REPO/desktop-new/package.json"
printf 'export const fresh = true;\n' > "$REPO/desktop-new/src/index.ts"
printf '{"devDependencies":{"typescript":"5.9.3"}}\n' > "$REPO/ignored-app/package.json"
printf 'export const ignored = true;\n' > "$REPO/ignored-app/src/index.ts"

python3 "$DETECT" --repo "$REPO" --rules "$RULES" --json > "$WORK/detect.json"

actual_workspaces="$(
  jq -r '.rules[] | select(.id == "typescript") | .workspaces[].workspace' "$WORK/detect.json" |
    sort |
    paste -sd, -
)"
if [ "$actual_workspaces" != "desktop-existing,desktop-new" ]; then
  echo "TypeScript 工作区不完整：$actual_workspaces" >&2
  exit 1
fi

python3 "$APPLY" "$REPO" "$RULES" "$TEMPLATES" > "$WORK/apply.out"
test -f "$REPO/desktop-existing/.oxlintrc.json"
test -f "$REPO/desktop-new/.oxlintrc.json"
test ! -e "$REPO/ignored-app/.oxlintrc.json"
grep -q '^          - desktop-existing$' "$REPO/.github/workflows/mmw-typescript.yml"
grep -q '^          - desktop-new$' "$REPO/.github/workflows/mmw-typescript.yml"
! grep -q 'ignored-app' "$REPO/.github/workflows/mmw-typescript.yml"

echo "工具链探测与生成通过"
