#!/usr/bin/env bash
# 界面 QA 的三个运行时依赖装配。
#
# 为什么要这一份：技能正文写的是能力名（浏览器自动化框架、可访问性规则引擎、
# 设计系统格式校验器），中间隔着 deps.json 与 mmw-ui-qa 两层。两层任何一处走散，
# 技能读起来完全正常，第一次运行才在起步第二步停下来。既有的十条测试没有一条
# 碰 install.sh，所以这是本次真正新增的合同面。
#
# 判的都是静态可判定的事实，不联网、不真装包：
#   1. deps.json 是合法 JSON，每条声明字段齐全，版本是精确版本不是范围
#   2. 三份脚本正文里没有 npx——用了它，版本就不受控
#   3. 技能正文出现的每个 mmw-ui-qa 动作，转发器真的支持
#   4. 转发器的用法说明与它实际的分支一致
#   5. install.sh 真的调了安装脚本、真的装了转发器
#   6. 依赖没装时 --check 非零退出，并说清缺了哪个、要哪个版本
#
# 不判的：包能不能下下来、装完跑不跑得动。那要网络和几百 MB 浏览器二进制，
# 属于本机安装的验收，不属于提交检查。

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MMW_DIR="$(cd "$HERE/../.." && pwd)"
UI_QA="$MMW_DIR/ui-qa"
DEPS_JSON="$UI_QA/deps.json"
FORWARDER="$UI_QA/mmw-ui-qa"
INSTALLER="$UI_QA/install-ui-qa-deps.sh"
INSTALL_SH="$MMW_DIR/install.sh"
SKILLS="$MMW_DIR/skills-src"

pass=0
fail=0

check() {
  local name="$1" want="$2" got="$3"
  if [ "$want" = "$got" ]; then
    echo "  过  $name"
    pass=$((pass + 1))
  else
    echo "  失败  $name"
    echo "    要的是：$want"
    echo "    得到的：$got"
    fail=$((fail + 1))
  fi
}

contains() {
  local name="$1" needle="$2" haystack="$3"
  case "$haystack" in
    *"$needle"*)
      echo "  过  $name"
      pass=$((pass + 1))
      ;;
    *)
      echo "  失败  $name"
      echo "    找不到：$needle"
      fail=$((fail + 1))
      ;;
  esac
}

echo "界面 QA 依赖声明"
check "依赖声明存在" "存在" "$([ -f "$DEPS_JSON" ] && echo 存在 || echo 缺失)"
check "转发器存在且可执行" "是" "$([ -x "$FORWARDER" ] && echo 是 || echo 否)"
check "安装脚本存在" "存在" "$([ -f "$INSTALLER" ] && echo 存在 || echo 缺失)"

if [ -f "$DEPS_JSON" ]; then
  check "依赖声明是 JSON 对象" "true" "$(jq -r 'type == "object"' "$DEPS_JSON")"
  required='["capability","package","version","kind","purpose","missing","version_note"]'
  check "每条声明字段齐全" "true" \
    "$(jq -r --argjson r "$required" \
      'all(.packages[]; ($r - (keys)) == [])' "$DEPS_JSON")"
  # 精确版本：带 ^ ~ * x 或 latest 的都不算钉死，下一次 npm install 会悄悄升上去。
  check "版本全是精确版本" "true" \
    "$(jq -r 'all(.packages[].version; test("^[0-9]+\\.[0-9]+\\.[0-9]+$"))' "$DEPS_JSON")"
  check "缺失时的行为受限" "true" \
    "$(jq -r 'all(.packages[].missing; IN("stop", "degrade"))' "$DEPS_JSON")"
  # 能力名是技能正文与这份声明之间的连接点，重复了就有一条永远取不到。
  check "能力名不重复" "true" \
    "$(jq -r '(.packages | map(.capability) | unique | length) == (.packages | length)' "$DEPS_JSON")"
  # command 要 bin，source 要 source。写错类别时转发器会去找一个不存在的字段。
  check "命令型声明都有 bin" "true" \
    "$(jq -r 'all(.packages[] | select(.kind == "command"); has("bin"))' "$DEPS_JSON")"
  check "脚本型声明都有 source" "true" \
    "$(jq -r 'all(.packages[] | select(.kind == "source"); has("source"))' "$DEPS_JSON")"
  check "类别取值受限" "true" \
    "$(jq -r 'all(.packages[].kind; IN("command", "source"))' "$DEPS_JSON")"
fi

echo
echo "不用 npx 当场拉取"
for f in "$FORWARDER" "$INSTALLER" "$INSTALL_SH"; do
  [ -f "$f" ] || continue
  # 只判可执行行，注释里解释「为什么不用 npx」是应该留的。
  hits="$(grep -n 'npx' "$f" | grep -v '^[0-9]*:[[:space:]]*#' || true)"
  check "$(basename "$f") 不调用 npx" "" "$hits"
done

echo
echo "转发器的动作与用法一致"
if [ -x "$FORWARDER" ]; then
  # 这一段全程关掉 set -e 与 pipefail：被测的三条路径本来就该非零退出，
  # 而 pipefail 会把「转发器退 2」变成整条管道退 2，直接终止这个测试脚本。
  set +e +o pipefail
  branches="$(grep -oE '^  [a-z-]+\)' "$FORWARDER" | tr -d ' )' | grep -v '^\*$' | sort | tr '\n' ' ')"
  usage_actions="$("$FORWARDER" 2>&1 | grep -oE '^  [a-z-]+' | tr -d ' ' | sort | tr '\n' ' ')"
  "$FORWARDER" >/dev/null 2>&1
  usage_status=$?
  "$FORWARDER" nonesuch >/dev/null 2>&1
  unknown_status=$?
  # design-lint 少了文件参数必须当场失败：省略它，校验器会去读当前目录碰巧有没有
  # DESIGN.md，而技能要校验的是接线文件 designSystem 指向的那一份。
  lint_err="$("$FORWARDER" design-lint 2>&1 >/dev/null)"
  set -e -o pipefail
  check "用法列出的动作与实际分支一致" "$branches" "$usage_actions"
  check "无参用法退出码" "2" "$usage_status"
  check "认不出的动作也退 2" "2" "$unknown_status"
  contains "design-lint 缺文件参数时说清语法" "mmw-ui-qa design-lint <文件>" "$lint_err"
fi

echo
echo "技能正文引用的动作都存在"
if [ -x "$FORWARDER" ] && [ -d "$SKILLS" ]; then
  known="$(grep -oE '^  [a-z-]+\)' "$FORWARDER" | tr -d ' )' | grep -v '^\*$' | sort -u)"
  used="$(grep -rhoE 'mmw-ui-qa [a-z-]+' "$SKILLS" 2>/dev/null \
    | awk '{print $2}' | sort -u || true)"
  unknown=""
  for a in $used; do
    printf '%s\n' "$known" | grep -qx "$a" || unknown="$unknown $a"
  done
  check "技能正文没有引用不存在的动作" "" "$unknown"
fi

echo
echo "install.sh 接上了"
if [ -f "$INSTALL_SH" ]; then
  contains "install.sh 调了依赖安装脚本" "ui-qa/install-ui-qa-deps.sh" "$(cat "$INSTALL_SH")"
  contains "install.sh 装了转发器" 'BIN_DIR/mmw-ui-qa' "$(cat "$INSTALL_SH")"
  contains "install.sh 主流程调了 install_ui_qa" $'\ninstall_ui_qa' "$(cat "$INSTALL_SH")"
  # 转发器和 mmw 一样要拦「覆盖别人的同名命令」，否则装一次就把用户自己的
  # mmw-ui-qa 冲掉，而且没人看得见。
  contains "装转发器前拦非 MMW 管理的同名命令" "拒绝覆盖非 MMW 管理的命令" \
    "$(cat "$INSTALL_SH")"
fi

echo
echo "依赖没装时的行为"
if [ -f "$INSTALLER" ]; then
  EMPTY="$(mktemp -d)"
  trap 'rm -rf "$EMPTY"' EXIT
  set +e
  check_out="$(MMW_UI_QA_HOME="$EMPTY" bash "$INSTALLER" --check 2>&1)"
  check_status=$?
  set -e
  check "缺依赖时 --check 非零退出" "1" "$check_status"
  while IFS= read -r pkg; do
    [ -n "$pkg" ] || continue
    contains "缺依赖时点名 $pkg" "$pkg" "$check_out"
  done < <(jq -r '.packages[].package' "$DEPS_JSON")
  # 报缺失也要报要哪个版本：只说「缺 axe-core」的话，装错版本的人看不出问题。
  while IFS= read -r ver; do
    [ -n "$ver" ] || continue
    contains "缺依赖时点名版本 $ver" "$ver" "$check_out"
  done < <(jq -r '.packages[].version' "$DEPS_JSON")
  check "只读的 --check 不建目录" "" "$(find "$EMPTY" -mindepth 1 -print)"
fi

echo
echo "过 ${pass}，失败 ${fail}"
[ "$fail" -eq 0 ]
