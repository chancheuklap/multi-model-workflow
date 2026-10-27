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
}

noscopestrict() {
  setup_repo strict
  expect "$(bash "$RF" same-commit parrot hedgehog)" "$(printf 'OK parrot\nOK hedgehog')"
  change hedgehog/app
  expect "$(bash "$RF" same-commit parrot)" "MISMATCH parrot $RECORDED"
  expect "$(bash "$RF" same-commit missing)" 'MISMATCH missing none'
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
