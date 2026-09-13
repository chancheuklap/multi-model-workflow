const PHASE_OF_EVENT = {
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

const STICKY = new Set(["ticket.claimed"]);
const NEEDS_YOU = new Set(["decision", "fault", "contract"]);
const CHILD_NAME = {
  finding: "Finding raised", contract: "Spec does not hold", deferred: "Left for a later ticket",
  decision: "Your decision needed", fault: "MMW itself broke",
};
const REFUSAL = {
  "wrong-branch": "the worktree was on the wrong branch",
  "dirty-tree": "the tree already carried uncommitted changes",
  "not-open": "the ticket was no longer open",
  "not-ready": "the ticket was not in the agent queue",
  blocked: "a ticket in front of it had not landed",
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
  if (!counts || counts.total == null) return "";
  return `${counts.met ?? counts.passed ?? 0} of ${counts.total}`;
};
const fallbackName = event => {
  const words = String(event || "Event").split(/[._-]+/).filter(Boolean);
  const text = words.join(" ");
  return text ? text[0].toUpperCase() + text.slice(1) : "Event";
};

function eventText(event, payload) {
  switch (event) {
    case "worker.started":
    case "worker.resumed":
    case "reviewer.started":
    case "verifier.started":
      return payload.model ? `${payload.host} ${payload.model}, ${payload.effort} effort` : "";
    case "worker.touched":
      return `#${payload.by} changed ${plural((payload.files || []).length, "file")} this ticket owns`;
    case "worker.queued":
      return QUEUE[payload.reason] || "waiting for a product slot";
    case "worker.decided":
      return "the calls the worker made on its own, written down for the review";
    case "ticket.claimed":
      return "";
    case "ticket.refused":
      return `it would not start: ${REFUSAL[payload.reason] || payload.reason || "the preflight refused it"}`;
    case "ticket.released":
      return `back in the queue: ${RELEASE[payload.reason] || payload.reason || "the claim ended"}`;
    case "ticket.checked": {
      const counts = countsText(payload.counts);
      if (payload.run === "repo-checks") {
        return `${counts || "the"} repository check${payload.counts?.total === 1 ? "" : "s"} passed`;
      }
      const failed = (payload.failed || []).length ? ` — ${listOf(payload.failed, 3)} unmet` : "";
      return `${counts || "the"} criteria met${failed}`;
    }
    case "ticket.passed":
      return `${countsText(payload.counts) || "all"} criteria met, ticket closed`;
    case "ticket.returned":
      return "handed back with criteria it could not meet";
    case "ticket.landed":
      return payload.into ? `merged into ${payload.into}` : "merged into its base branch";
    case "ticket.bounced":
      return payload.reason === "conflict"
        ? `conflict with ${payload.into} in ${plural((payload.files || []).length, "file")}`
        : `checks failed after merging into ${payload.into}`;
    case "ticket.regressed":
      return `${listOf(payload.failed, 3)} stopped passing on the base branch`;
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
      return payload.project ? `into the project branch ${payload.project}` : "";
    default:
      return "";
  }
}

function eventName(event, payload) {
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
  }[event] || fallbackName(event);
}

function eventTone(event, payload) {
  if (event === "child.opened" && NEEDS_YOU.has(payload.kind)) return "needs-you";
  if (["ticket.returned", "ticket.bounced", "ticket.regressed"].includes(event)) return "needs-you";
  if (event === "ticket.refused" || /\.lost$|^worker\.(retracted|replaced)$/.test(event)) return "warn";
  if (event === "ticket.checked" && payload.result !== "met") return "warn";
  if (event === "verifier.failed") return "warn";
  if (/^ticket\.(landed|passed)$|^verifier\.passed$/.test(event)) return "good";
  return "plain";
}

function eventPhase(event, payload) {
  if (event === "ticket.checked") {
    if (payload.run === "repo-checks") return "verify";
    if (payload.run === "reverify") return payload.stage === "regress" ? "landed" : "verify";
    return "working";
  }
  return PHASE_OF_EVENT[event] || "working";
}

function backendDetails(payload, line) {
  const rows = [];
  for (const [key, value] of Object.entries(payload)) {
    if (COMMON.has(key)) continue;
    if (key === "criteria" && Array.isArray(value)) {
      rows.push([key, value.map(item => `${item.id} ${item.met ? "met" : "unmet"}`).join(", ")]);
      continue;
    }
    rows.push([key, Array.isArray(value) ? value.map(item => typeof item === "object" ? JSON.stringify(item) : item).join(", ")
      : typeof value === "object" && value !== null ? JSON.stringify(value) : String(value)]);
  }
  rows.push(["comment", line || ""]);
  return rows;
}

export function describeEvent(raw = {}) {
  const payload = raw.payload || {};
  const event = raw.event || "";
  const at = raw.at || "";
  return {
    at,
    time: at ? at.slice(11, 16) : raw.time || "",
    event,
    name: eventName(event, payload),
    text: eventText(event, payload) || raw.text || "",
    phase: eventPhase(event, payload),
    tone: eventTone(event, payload),
    sticky: STICKY.has(event),
    detail: backendDetails(payload, raw.line || ""),
  };
}

export function groupEventBlocks(events = []) {
  const blocks = [];
  for (const raw of events) {
    const item = describeEvent(raw);
    const last = blocks[blocks.length - 1];
    if (last && (last.phase === item.phase || item.sticky)) last.items.push(item);
    else blocks.push({phase: item.phase, items: [item]});
  }
  for (const block of blocks) {
    block.from = block.items[0].time;
    block.to = block.items[block.items.length - 1].time;
    block.tone = block.items.some(item => item.tone === "needs-you") ? "needs-you"
      : block.items.some(item => item.tone === "warn") ? "warn" : "plain";
  }
  return blocks;
}
