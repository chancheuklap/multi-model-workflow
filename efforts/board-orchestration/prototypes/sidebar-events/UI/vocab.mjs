// The dictionary the three variants share: for every event of the pipeline, the English
// name a person reads, the phase pill the ticket card would have shown at that moment, and
// one sentence built from the payload fields worth reading. Session ids, runners,
// machines, worktrees, commits and per-criterion evidence are not dropped — they are
// collected under `detail`, so each variant can put them behind a click.
//
// The pill rule: an event carries the phase its ticket card would have shown while that
// event was the newest one. That is what makes the pills here and the pills on the canvas
// card the same vocabulary — `queued`, `working`, `waiting`, `review`, `verify`, `landed`.

// Which phase pill each event carries: the phase the ticket card reads while that event is
// the newest one on the ticket. `queued` is the card with nothing running on it, which is
// what a refusal, a release, a retraction and a lost session all leave behind.
const STEP_OF_EVENT = {
  "worker.started": "working", "worker.resumed": "working", "ticket.claimed": "working",
  "worker.touched": "working", "worker.decided": "working", "child.opened": "working",
  "worker.queued": "waiting",
  "reviewer.started": "review", "reviewer.reported": "review",
  "verifier.started": "verify", "verifier.passed": "verify", "verifier.failed": "verify",
  "ticket.passed": "verify", "ticket.returned": "verify", "ticket.bounced": "verify",
  "ticket.refused": "queued", "ticket.released": "queued", "worker.retracted": "queued",
  "worker.replaced": "queued", "worker.lost": "queued", "reviewer.lost": "queued",
  "verifier.lost": "queued",
  "ticket.landed": "landed", "ticket.regressed": "landed", "child.closed": "landed",
  "spec.merged": "landed", "spec.opened": "queued", "spec.suspended": "queued",
  "spec.closed": "queued",
};

// The word each pill carries, on the card and here alike.
export const STEP_LABEL = {
  queued: "queued", working: "working", waiting: "waiting",
  review: "review", verify: "verify", landed: "landed",
};

// A claim never opens a block of its own: `dispatch.sh` starts the session and the worker
// claims the ticket a minute later, and a person reads those two as one act.
const STICKY = new Set(["ticket.claimed"]);

const CHILD_NAME = {
  finding: "Finding raised", contract: "Spec does not hold", deferred: "Left for a later ticket",
  decision: "Your decision needed", fault: "MMW itself broke",
};
const NEEDS_YOU = new Set(["decision", "fault", "contract"]);
const REFUSAL = {
  "wrong-branch": "the worktree was on the wrong branch",
  "dirty-tree": "the tree already carried uncommitted changes",
  "not-open": "the ticket was no longer open",
  "not-ready": "the ticket was not in the agent queue",
  "blocked": "a ticket in front of it had not landed",
  "claimed-by-other": "someone else already held it",
};
const RELEASE = {
  landed: "it had landed", suspended: "the night was suspended",
  "worker-lost": "its worker's session was gone",
};
const QUEUE = {
  "product-full": "every instance of the product was in use",
  "machine-full": "every slot on this machine was in use",
};
const RESOLUTION = {fixed: "fixed", stale: "no longer applies", "became-ticket": "became a ticket"};
const COMMON = new Set(["v", "event", "stage", "actor", "spec", "ticket", "at"]);
const RUN_NAME = {self: "Criteria run", reverify: "Criteria re-run", "repo-checks": "Repository checks"};

const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;
const listOf = (items, max = 2) => {
  const all = items || [];
  if (all.length <= max) return all.join(", ");
  return `${all.slice(0, max).join(", ")} and ${all.length - max} more`;
};
const countsText = counts => {
  if (!counts) return "";
  if (counts.total == null) return "";
  const met = counts.met ?? counts.passed ?? 0;
  return `${met} of ${counts.total}`;
};

function text(event, payload) {
  const kind = payload.kind;
  switch (event) {
    case "worker.started":
    case "worker.resumed":
      return payload.model ? `${payload.host} ${payload.model}, ${payload.effort} effort` : "";
    case "worker.touched":
      return `#${payload.by} changed ${plural((payload.files || []).length, "file")} this ticket owns`;
    case "worker.queued":
      return QUEUE[payload.reason] || "";
    case "worker.decided":
      return "the calls the worker made on its own, written down for the review";
    case "ticket.claimed":
      return "";
    case "ticket.refused":
      return `it would not start: ${REFUSAL[payload.reason] || payload.reason}`;
    case "ticket.released":
      return `back in the queue: ${RELEASE[payload.reason] || payload.reason}`;
    case "ticket.checked": {
      const counts = countsText(payload.counts);
      if (payload.run === "repo-checks") {
        return `${counts || "the"} repository check${payload.counts?.total === 1 ? "" : "s"} passed`;
      }
      const failed = (payload.failed || []).length ? ` — ${listOf(payload.failed, 3)} unmet` : "";
      return `${counts} criteria met${failed}`;
    }
    case "ticket.passed":
      return `${countsText(payload.counts)} criteria met, ticket closed`;
    case "ticket.returned":
      return "handed back with criteria it could not meet";
    case "ticket.landed":
      return `merged into ${payload.into}`;
    case "ticket.bounced":
      return payload.reason === "conflict"
        ? `conflict with ${payload.into} in ${plural((payload.files || []).length, "file")}`
        : `checks failed after merging into ${payload.into}`;
    case "ticket.regressed":
      return `${listOf(payload.failed, 3)} stopped passing on the base branch`;
    case "reviewer.started":
    case "verifier.started":
      return payload.model ? `${payload.host} ${payload.model}, ${payload.effort} effort` : "";
    case "reviewer.reported":
      return "the three-axis review is on the ticket";
    case "verifier.passed":
    case "verifier.failed":
      return payload.says || "";
    case "worker.lost":
    case "reviewer.lost":
    case "verifier.lost":
      return "its session stopped without finishing";
    case "child.opened":
      return payload.title || "";
    case "child.closed":
      return payload.resolution === "became-ticket"
        ? `#${payload.child} became ticket #${payload.became}`
        : `#${payload.child}: ${RESOLUTION[payload.resolution] || payload.resolution}`;
    case "spec.merged":
      return `into the project branch ${payload.project}`;
    default:
      return "";
  }
}

function name(event, payload) {
  if (event === "ticket.checked") {
    if (payload.run === "reverify" && payload.stage === "regress") return "Criteria re-run after landing";
    return RUN_NAME[payload.run] || "Criteria run";
  }
  if (event === "child.opened") return CHILD_NAME[payload.kind] || "Sub-issue opened";
  if (event === "child.closed") {
    return payload.resolution === "became-ticket" ? "Finding became a ticket" : "Sub-issue closed";
  }
  return {
    "spec.opened": "Night opened", "spec.suspended": "Night suspended",
    "spec.closed": "Night closed", "spec.merged": "Base branch merged",
    "ticket.claimed": "Ticket claimed", "ticket.refused": "Preflight refused",
    "ticket.passed": "Ticket passed", "ticket.returned": "Ticket handed back",
    "ticket.released": "Claim released", "ticket.landed": "Landed",
    "ticket.regressed": "Regressed after landing", "ticket.bounced": "Merge bounced",
    "worker.started": "Worker started", "worker.resumed": "Worker resumed",
    "worker.retracted": "Worker retracted", "worker.replaced": "Worker replaced",
    "worker.decided": "Decisions recorded", "worker.queued": "Waiting for a slot",
    "worker.touched": "Another ticket touched its files", "worker.lost": "Worker session lost",
    "reviewer.started": "Reviewer started", "reviewer.reported": "Review posted",
    "reviewer.lost": "Reviewer session lost", "verifier.started": "Verifier started",
    "verifier.passed": "Verification passed", "verifier.failed": "Verification failed",
    "verifier.lost": "Verifier session lost",
  }[event] || event;
}

function tone(event, payload) {
  if (event === "child.opened" && NEEDS_YOU.has(payload.kind)) return "needs-you";
  if (event === "ticket.returned" || event === "ticket.bounced" || event === "ticket.regressed") return "needs-you";
  if (event === "ticket.refused" || /\.lost$|^worker\.(retracted|replaced)$/.test(event)) return "warn";
  if (event === "ticket.checked" && payload.result !== "met") return "warn";
  if (event === "verifier.failed") return "warn";
  if (/^ticket\.(landed|passed)$|^verifier\.passed$/.test(event)) return "good";
  return "plain";
}

function phase(event, payload) {
  if (event === "ticket.checked") {
    if (payload.run === "repo-checks") return "verify";
    if (payload.run === "reverify") return payload.stage === "regress" ? "landed" : "verify";
    return "working";
  }
  return STEP_OF_EVENT[event] || "working";
}

// Everything the payload carries that the sentence above leaves out, in the payload's own
// field names: the prototype hides backend detail, it does not delete it.
function detail(payload, line) {
  const rows = [];
  for (const [key, value] of Object.entries(payload)) {
    if (COMMON.has(key)) continue;
    if (key === "criteria") {
      rows.push([key, value.map(item => `${item.id} ${item.met ? "met" : "unmet"}`).join(", ")]);
      continue;
    }
    if (key === "details") continue;
    rows.push([key, Array.isArray(value) ? value.join(", ")
      : typeof value === "object" && value !== null ? JSON.stringify(value) : String(value)]);
  }
  rows.push(["comment", line]);
  return rows;
}

export function describe(event) {
  const payload = event.payload || {};
  const what = event.event;
  const at = event.at;
  return {
    at,
    time: at ? at.slice(11, 16) : "",
    event: what,
    name: name(what, payload),
    text: text(what, payload),
    phase: phase(what, payload),
    tone: tone(what, payload),
    sticky: STICKY.has(what),
    actor: payload.actor,
    child: what.startsWith("child.") ? payload.child : null,
    became: payload.became ?? null,
    evidence: payload.criteria || null,
    files: payload.files || (payload.details || []).map(item => item.path) || [],
    detail: detail(payload, event.line || ""),
  };
}

// The events of one ticket in order, cut into blocks wherever the phase pill changes: the
// second worker start after a refusal opens a second `working` block, which is what a
// second attempt looks like without inventing a word for it.
export function blocks(events) {
  const out = [];
  for (const raw of events || []) {
    const item = describe(raw);
    const last = out[out.length - 1];
    if (last && (last.phase === item.phase || item.sticky)) last.items.push(item);
    else out.push({phase: item.phase, items: [item]});
  }
  for (const block of out) {
    block.from = block.items[0].time;
    block.to = block.items[block.items.length - 1].time;
    block.tone = block.items.some(item => item.tone === "needs-you") ? "needs-you"
      : block.items.some(item => item.tone === "warn") ? "warn" : "plain";
  }
  return out;
}

// The same events cut a second way: one group per worker start, plus one for whatever
// happened before the first start and one for whatever happened after the ticket landed.
// A ticket that was started twice reads as two attempts rather than one long strip.
export function runs(events) {
  const out = [];
  let landed = false;
  for (const raw of events || []) {
    const item = describe(raw);
    const openRun = item.event === "worker.started";
    const openAfter = landed && out.length && out[out.length - 1].kind !== "after";
    if (!out.length || openRun || openAfter) {
      out.push({kind: openRun ? "run" : out.length ? "after" : "before", head: null, items: []});
    }
    const group = out[out.length - 1];
    if (openRun) group.head = item;
    group.items.push(item);
    if (item.event === "ticket.landed") landed = true;
  }
  let n = 0;
  for (const group of out) {
    if (group.kind === "run") group.n = ++n;
    group.from = group.items[0].time;
    group.to = group.items[group.items.length - 1].time;
    group.phases = [...new Set(group.items.map(item => item.phase))];
    group.last = group.items[group.items.length - 1];
    group.tone = group.items.some(item => item.tone === "needs-you") ? "needs-you"
      : group.items.some(item => item.tone === "warn") ? "warn" : "plain";
  }
  return out;
}
