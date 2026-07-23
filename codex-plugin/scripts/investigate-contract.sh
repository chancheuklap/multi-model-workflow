#!/usr/bin/env bash
# Codex native investigate 的无状态返回合同：校验 topic/report，并过滤弱证据。
set -euo pipefail

die() {
  echo "ERROR: $*" >&2
  exit 2
}

kind="${1:-}"
[ -n "$kind" ] || die "用法: investigate-contract.sh topic --mode <internal|external> --expected-topic <angle> | report"
shift
payload="$(cat)"
[ -n "$payload" ] || die "stdin 为空"

case "$kind" in
  topic)
    mode=""
    expected_topic=""
    while [ $# -gt 0 ]; do
      case "$1" in
        --mode) mode="$2"; shift 2 ;;
        --expected-topic) expected_topic="$2"; shift 2 ;;
        *) die "未知参数:$1" ;;
      esac
    done
    case "$mode" in internal|external) ;; *) die "--mode 只能 internal|external" ;; esac
    [ -n "$expected_topic" ] || die "--expected-topic 必填"

    jq -e --arg expected "$expected_topic" '
      type=="object"
      and ((keys_unsorted | sort)==(["findings","gaps","summary","topic"] | sort))
      and (.topic==$expected)
      and (.summary|type=="string")
      and (.findings|type=="array")
      and (all(.findings[];
        type=="object"
        and ((keys_unsorted | sort)==(["claim","confidence","locator"] | sort))
        and (.claim|type=="string")
        and (.locator|type=="string")
        and (.confidence=="high" or .confidence=="medium" or .confidence=="low")))
      and (.gaps|type=="array")
      and (all(.gaps[]; type=="string"))
    ' <<<"$payload" >/dev/null 2>&1 || die "topic result 不符合合同或 topic 名不匹配"

    jq --arg mode "$mode" '
      def locator_ok:
        if $mode=="internal"
        then (test("^[^[:space:]]+:[0-9]+(-[0-9]+)?$") and (contains("://")|not))
        else test("^https?://[^[:space:]/]+(/[^[:space:]]*)?$")
        end;
      . as $topic
      | .findings |= map(select((.locator|locator_ok) and .confidence!="low"))
      | . + {
          mode:$mode,
          dropped:($topic.findings
            | map(select((.locator|locator_ok|not) or .confidence=="low")))
        }
    ' <<<"$payload"
    ;;

  report)
    [ "$#" -eq 0 ] || die "report 不接受参数"
    jq -e '
      type=="object"
      and ((keys_unsorted | sort)==(["markdown","open_questions","spinoff_candidates"] | sort))
      and (.markdown|type=="string" and length>0)
      and (.open_questions|type=="array")
      and (all(.open_questions[]; type=="string"))
      and (.spinoff_candidates|type=="array")
      and (all(.spinoff_candidates[];
        type=="object"
        and ((keys_unsorted | sort)==(["finding","tag"] | sort))
        and (.tag=="bug" or .tag=="optimize" or .tag=="out-of-scope" or .tag=="needs-evaluation")
        and (.finding|type=="string")))
    ' <<<"$payload" >/dev/null 2>&1 || die "synthesis report 不符合合同"
    jq '.' <<<"$payload"
    ;;

  *)
    die "未知合同:$kind"
    ;;
esac
