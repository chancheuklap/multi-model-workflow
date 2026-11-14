#!/usr/bin/env bash
set -euo pipefail
HERE="$(CDPATH='' cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
RF="$HERE/../../skills/exe-release/scripts/release-flow.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
export GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE || true

fail() { echo "FAIL ${1}: ${2}" >&2; exit 1; }
expect() { [ "$1" = "$2" ] || fail "$CASE" "expected [$2], got [$1]"; }

setup_repo() {
  mkdir -p "$TMP/$1"
  cd "$TMP/$1"
  git init -q
  git config user.email test@example.invalid
  git config user.name test
  mkdir -p parrot hedgehog shared docs .release/delivered
  printf '.release/\nscope.json\n' > .gitignore
  echo initial > parrot/app
  echo initial > hedgehog/app
  echo initial > shared/build
  echo initial > docs/readme
  git add .
  git commit -qm initial
  RECORDED="$(git rev-parse HEAD)"
  for product in parrot hedgehog; do
    printf '{"product":"%s","source_commit":"%s"}\n' "$product" "$RECORDED" > ".release/delivered/$product.json"
  done
  cat > scope.json <<'JSON'
{
  "all_products_paths": ["shared/*"],
  "ignored_paths": ["docs/*", "shared/*", "parrot/*.md"],
  "products": [
    {"product": "parrot", "paths": ["parrot/*"]},
    {"product": "hedgehog", "paths": ["hedgehog/*"]}
  ]
}
JSON
}

change() {
  mkdir -p "$(dirname "$1")"
  echo changed >> "$1"
  git add -- "$1"
  git commit -qm change
}

unchangedinputsok() {
  setup_repo unchanged
  expect "$(bash "$RF" same-commit --scope scope.json parrot)" 'OK parrot'
  change hedgehog/deep/app
  change docs/deep/说明.txt
  expect "$(bash "$RF" same-commit --scope scope.json parrot)" "OK parrot (inputs unchanged since $RECORDED)"
  out="$(bash "$RF" same-commit --scope scope.json parrot hedgehog)"
  [[ "$out" == "OK parrot (inputs unchanged since $RECORDED)"$'\n'"MISMATCH hedgehog $RECORDED"* ]] || fail "$CASE" "wrong per-product result [$out]"
  bash "$RF" --help 2>&1 | grep -q -- '--scope' || fail "$CASE" 'usage does not name --scope'
}

changedinputsmismatch() {
  for path in parrot/deep/app parrot/readme.md shared/deep/build hedgehog/deep/app; do
    setup_repo "changed-${path//\//-}"
    change "$path"
    if [[ "$path" == hedgehog/* ]]; then product=hedgehog; else product=parrot; fi
    out="$(bash "$RF" same-commit --scope scope.json "$product")"
    [[ "$out" == "MISMATCH $product $RECORDED"* ]] || fail "$CASE" "affected $path passed [$out]"
  done
  setup_repo renamed
  git mv parrot/app docs/app
  git commit -qm rename
  out="$(bash "$RF" same-commit --scope scope.json parrot)"
  [[ "$out" == "MISMATCH parrot $RECORDED"* ]] || fail "$CASE" "removed product input passed [$out]"
}

unclassifiedpathmismatch() {
  setup_repo unclassified
  change 'new/deep/未分类 file'
  out="$(bash "$RF" same-commit --scope scope.json parrot)"
  [[ "$out" == "MISMATCH parrot $RECORDED"*'new/deep/未分类 file'* ]] || fail "$CASE" "unclassified path not rejected and named [$out]"

  setup_repo missing
  expect "$(bash "$RF" same-commit --scope scope.json absent)" 'MISMATCH absent none (product not listed in scope.json)'
  cp .release/delivered/parrot.json .release/delivered/absent.json
  expect "$(bash "$RF" same-commit --scope scope.json absent)" "MISMATCH absent $RECORDED (product not listed in scope.json)"
  rm .release/delivered/parrot.json
  expect "$(bash "$RF" same-commit --scope scope.json parrot)" 'MISMATCH parrot none'
  printf '{"source_commit":"deadbeef"}\n' > .release/delivered/parrot.json
  expect "$(bash "$RF" same-commit --scope scope.json parrot)" 'MISMATCH parrot deadbeef'

  # 范围文件本身有问题时不能靠猜:坏的范围文件、没给文件、没给产品都是错误,不是「全都对得上」。
  printf '{"all_products_paths":"shared/*","ignored_paths":[],"products":[]}\n' > bad-scope.json
  if err="$(bash "$RF" same-commit --scope bad-scope.json parrot 2>&1 >/dev/null)"; then
    fail "$CASE" 'malformed scope file was accepted'
  fi
  [[ "$err" == *"invalid release package scope file"* ]] || fail "$CASE" "malformed scope file not named [$err]"
  if err="$(bash "$RF" same-commit --scope 2>&1 >/dev/null)"; then
    fail "$CASE" '--scope without a file was accepted'
  fi
  [[ "$err" == *"--scope"* ]] || fail "$CASE" "missing scope file not explained [$err]"
  if err="$(bash "$RF" same-commit --scope scope.json 2>&1 >/dev/null)"; then
    fail "$CASE" 'same-commit with no product was accepted'
  fi
  [[ "$err" == *"usage"* ]] || fail "$CASE" "missing product not explained [$err]"
}

noscopestrict() {
  setup_repo strict
  expect "$(bash "$RF" same-commit parrot hedgehog)" "$(printf 'OK parrot\nOK hedgehog')"
  change hedgehog/app
  expect "$(bash "$RF" same-commit parrot)" "MISMATCH parrot $RECORDED"
  expect "$(bash "$RF" same-commit missing)" 'MISMATCH missing none'

  # 交付记录在主检出的根:从任务 worktree 里问,读的也得是同一份。
  setup_repo linked-main
  git worktree add -q ../linked-main-wt -b task-branch
  expect "$(cd ../linked-main-wt && bash "$RF" same-commit parrot)" 'OK parrot'
}

CASE="${1:-}"
case "$CASE" in
  unchangedinputsok) unchangedinputsok ;;
  changedinputsmismatch) changedinputsmismatch ;;
  unclassifiedpathmismatch) unclassifiedpathmismatch ;;
  noscopestrict) noscopestrict ;;
  *) fail usage 'pass a named case' ;;
esac
echo "PASS $CASE"
