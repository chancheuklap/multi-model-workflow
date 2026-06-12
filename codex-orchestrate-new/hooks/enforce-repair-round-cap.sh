#!/usr/bin/env bash
# Codex repair-round cap hook placeholder.
#
# Repair-round enforcement needs the review prompt envelope and gate name. In the
# Codex runtime that information is available to dispatch-review.sh validate
# before spawn_agent, not to a generic shell hook after the fact. This hook stays
# registered as a no-op so older hook trust records remain structurally stable;
# the load-bearing check lives in scripts/dispatch-review.sh.
set -euo pipefail
exit 0
