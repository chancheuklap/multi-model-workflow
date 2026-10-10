#!/usr/bin/env bash
# Read-only worktree prune audit. Classifies every git worktree by size, merge
# state, uncommitted work, remote/PR state, and the most recent chat that
# operated in it. Emits a table sorted by size with a suggested bucket. Never
# deletes anything; deletion stays a human-gated step in the playbook.
#
# Usage: worktree-audit.sh [repo-path]   (defaults to the current repo)
set -u

repo="${1:-$(git rev-parse --show-toplevel 2>/dev/null)}"
[ -z "$repo" ] && { echo "not in a git repo; pass a repo path" >&2; exit 1; }
cd "$repo" || exit 1

# Main worktree is the first entry; everything else is a candidate.
main_wt=$(git worktree list --porcelain | awk '/^worktree /{print $2; exit}')

# origin/main drives the merge check. Best-effort; stale is fine for a first pass.
git fetch origin main --quiet 2>/dev/null || echo "warn: could not fetch origin/main; merged column may be stale" >&2

# PR state by branch, fetched once. Empty if gh is unavailable.
prs=$(mktemp)
gh pr list --author "@me" --state all --limit 1000 \
	--json number,state,headRefName 2>/dev/null > "$prs" || echo "[]" > "$prs"

# Session records. Each host keeps its own, keyed by the session's working
# directory; a host that is not installed simply has no directory.
#   Claude Code: ~/.claude/projects/<path, "/" and "." as "-">/*.jsonl
#   Grok:        ~/.grok/sessions/<url-encoded path>/
#   Codex:       ~/.codex/sessions/YYYY/MM/DD/*.jsonl, cwd in the first line
#   Cursor:      ~/.cursor/projects/<repo slug>/agent-transcripts, searched for the path
slug=$(printf '%s' "$main_wt" | sed 's#^/##; s#/#-#g')
transcripts="$HOME/.cursor/projects/$slug/agent-transcripts"

# Codex has no per-directory folder, so index the last 30 days once: "mtime cwd".
codex=$(mktemp)
if [ -d "$HOME/.codex/sessions" ]; then
	find "$HOME/.codex/sessions" -name '*.jsonl' -mtime -30 2>/dev/null | while read -r f; do
		cwd=$(head -c 4096 "$f" | LC_ALL=C sed -n 's/.*"cwd":"\([^"]*\)".*/\1/p' | head -1)
		[ -n "$cwd" ] && echo "$(stat -f %m "$f") $cwd"
	done > "$codex"
fi

# Newest modification time among the files named on stdin, or nothing.
newest() { while read -r f; do stat -f %m "$f" 2>/dev/null; done | sort -rn | head -1; }
now=$(date +%s)

printf "SIZE\tAGE\tMERGED\tDIRTY\tREMOTE\tPR\tLAST_CHAT\tBUCKET\tWORKTREE\n"

git worktree list --porcelain | awk '/^worktree /{print $2}' | while read -r wt; do
	[ "$wt" = "$main_wt" ] && continue

	size=$(du -sh "$wt" 2>/dev/null | awk '{print $1}')
	head=$(git -C "$wt" rev-parse HEAD 2>/dev/null)
	head_ts=$(git -C "$wt" log -1 --format='%ct' HEAD 2>/dev/null || echo 0)
	age=$([ "$head_ts" -gt 0 ] 2>/dev/null && echo "$(( (now - head_ts) / 86400 ))d" || echo "?")

	# Squash-merged branches are not ancestors of main, so PR state is the
	# real signal; merge-base only catches fast-forward/rebase merges.
	git merge-base --is-ancestor "$head" origin/main 2>/dev/null && merged=YES || merged=no

	# Distinguish real WIP (tracked edits) from disposable untracked scratch.
	porcelain=$(git -C "$wt" status --porcelain 2>/dev/null)
	if [ -z "$porcelain" ]; then dirty=clean
	elif printf '%s\n' "$porcelain" | grep -qv '^??'; then
		dirty="wip:$(printf '%s\n' "$porcelain" | grep -cv '^??')"
	else dirty="scratch:$(printf '%s\n' "$porcelain" | grep -c '^??')"; fi

	branch=$(git -C "$wt" symbolic-ref --quiet --short HEAD 2>/dev/null || echo "")
	if [ -z "$branch" ]; then remote=detached
	elif git -C "$wt" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
		[ "$(git -C "$wt" rev-parse "origin/$branch" 2>/dev/null)" = "$head" ] \
			&& remote=pushed \
			|| remote="ahead$(git -C "$wt" rev-list --count "origin/$branch..HEAD" 2>/dev/null)"
	else remote=no-remote; fi

	pr=$([ -n "$branch" ] && jq -r --arg b "$branch" \
		'.[] | select(.headRefName==$b) | "#\(.number)/\(.state)"' "$prs" 2>/dev/null | head -1)
	[ -z "$pr" ] && pr="-"

	# Most recent session of any host that ran in this worktree or a directory
	# under it. Match the path followed by "/" or its end, so glint-482 does not
	# match glint-482-r37.
	last="-"
	cslug=$(printf '%s' "$wt" | sed 's#[/.]#-#g')
	gslug=$(python3 -c 'import sys, urllib.parse; print(urllib.parse.quote(sys.argv[1], safe=""))' "$wt")
	last_ts=$( {
		find "$HOME/.claude/projects" -maxdepth 2 -name '*.jsonl' \( -path "*/projects/$cslug/*" -o -path "*/projects/$cslug-*/*" \) 2>/dev/null | newest
		find "$HOME/.grok/sessions" -mindepth 2 -maxdepth 2 \( -path "*/sessions/$gslug/*" -o -path "*/sessions/$gslug%2F*/*" \) 2>/dev/null | newest
		awk -v wt="$wt" '$2 == wt || index($2, wt "/") == 1 {print $1}' "$codex"
		[ -d "$transcripts" ] && rg -l -e "${wt}/" -e "${wt}\"" "$transcripts" 2>/dev/null | newest
	} | sort -rn | head -1)
	[ -z "$last_ts" ] && last_ts=0
	[ "$last_ts" -gt 0 ] && last=$(date -r "$last_ts" '+%Y-%m-%d' 2>/dev/null)
	recent=$([ "$last_ts" -gt 0 ] 2>/dev/null && [ $(( (now - last_ts) / 86400 )) -le 4 ] && echo yes || echo no)

	case "$dirty" in wip:*) bucket=hold-wip ;; *)
		case "$pr" in *OPEN*) bucket=hold-open-pr ;; *)
			if [ "$recent" = yes ]; then bucket=verify-recent-chat
			elif [ "$merged" = YES ] || [ "$pr" != "-" ]; then bucket=safe
			else bucket=review; fi ;;
		esac ;;
	esac

	printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
		"$size" "$age" "$merged" "$dirty" "$remote" "$pr" "$last" "$bucket" "$wt"
done | sort -t$'\t' -k1,1 -rh

rm -f "$prs" "$codex"
