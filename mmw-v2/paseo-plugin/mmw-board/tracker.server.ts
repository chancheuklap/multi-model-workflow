// Reads one spec's batch off the issue tracker through `gh` and organises it into the
// board. Runs in the plugin's daemon subprocess: Node, the daemon user's `gh` login.
// Nothing here decides anything; it reads, classifies by fixed first lines, and counts.
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import type { Board, Event, Problem, Ticket } from "./board.shared";

const run = promisify(execFile);

// `gh` writes ANSI escapes into --json output under CLICOLOR_FORCE (Grok Build sets it).
// The daemon subprocess is started by the desktop app, whose PATH may lack the
// directories a login shell has, so the usual homes of `gh` are appended.
const EXTRA_PATH = ["/opt/homebrew/bin", "/usr/local/bin", `${process.env.HOME ?? ""}/.local/bin`];
const GH_ENV = {
  ...Object.fromEntries(Object.entries(process.env).filter(([k]) => k !== "CLICOLOR_FORCE" && k !== "CLICOLOR")),
  PATH: [process.env.PATH ?? "", ...EXTRA_PATH].filter(Boolean).join(":"),
};

async function gh(cwd: string, args: string[]): Promise<string> {
  const { stdout } = await run("gh", args, { cwd, env: GH_ENV, maxBuffer: 64 * 1024 * 1024 });
  return stdout;
}

async function ghJson<T>(cwd: string, args: string[], fallback: T): Promise<T> {
  try {
    return JSON.parse(await gh(cwd, args)) as T;
  } catch (error) {
    console.error("gh failed", args.join(" "), error);
    return fallback;
  }
}

// ------------------------------------------------------------------ raw tickets

interface RawComment {
  body: string;
  createdAt: string;
}

interface RawTicket {
  number: number;
  title: string;
  state: string;
  body: string;
  createdAt: string;
  closedAt: string | null;
  labels: { name: string }[];
  assignees: { login: string }[];
  blockedBy?: { nodes?: { number: number; state: string }[] };
  comments: RawComment[];
}

async function subIssues(cwd: string, spec: number): Promise<number[]> {
  const pages = await ghJson<unknown[]>(
    cwd,
    ["api", "--paginate", "--slurp", `repos/{owner}/{repo}/issues/${spec}/sub_issues?per_page=100`],
    [],
  );
  const flat: unknown[] = [];
  for (const page of pages) {
    if (Array.isArray(page)) flat.push(...page);
    else flat.push(page);
  }
  return flat
    .map((r) => (r && typeof r === "object" ? (r as { number?: unknown }).number : undefined))
    .filter((n): n is number => typeof n === "number");
}

const TICKET_FIELDS = "number,title,state,body,createdAt,closedAt,labels,assignees,blockedBy,comments";

async function readTicket(cwd: string, number: number): Promise<RawTicket | null> {
  const raw = await ghJson<RawTicket | null>(cwd, ["issue", "view", String(number), "--json", TICKET_FIELDS], null);
  return raw && typeof raw.number === "number" ? raw : null;
}

async function mapLimit<T, R>(items: T[], limit: number, fn: (item: T) => Promise<R>): Promise<R[]> {
  const out: R[] = new Array(items.length);
  let next = 0;
  async function worker() {
    while (next < items.length) {
      const i = next++;
      out[i] = await fn(items[i]);
    }
  }
  await Promise.all(Array.from({ length: Math.min(limit, items.length) }, worker));
  return out;
}

// ------------------------------------------------------------------ first lines

function firstLine(text: string): string {
  const t = (text ?? "").trim();
  return t ? (t.split("\n", 1)[0] ?? "").trim() : "";
}

// The three summary lines gate-check prints; the same regexes board.py uses.
const ALL_MET_RE = /^ALL MET\s*\((\d+)\s+met\b/;
const UNMET_RE = /^UNMET:\s*(\d+)\s*\(met:\s*(\d+)\b/;
const HANDOFF_RE = /^HANDOFF REQUIRED:\s*(\d+)\s+abandoned\s*\(met:\s*(\d+)(?:,\s*unmet:\s*(\d+))?/;
const ABANDON_RE = /ABANDON:\s*AC(\d+)\s+(failed|stuck|decision)\s*(.*)$/;
const ISSUE_REF_RE = /#(\d+)/g;

function newestWithFirstLine(comments: RawComment[], ...prefixes: string[]): RawComment | null {
  for (let i = comments.length - 1; i >= 0; i--) {
    const head = firstLine(comments[i].body);
    if (prefixes.some((p) => head.startsWith(p))) return comments[i];
  }
  return null;
}

function countedAc(comments: RawComment[]): string {
  const body = newestWithFirstLine(comments, "self-run", "reverify")?.body ?? "";
  for (const raw of body.split("\n")) {
    const line = raw.trim();
    let m = ALL_MET_RE.exec(line);
    if (m) return `${m[1]}/${m[1]}`;
    m = HANDOFF_RE.exec(line);
    if (m) {
      const abandoned = Number(m[1]);
      const met = Number(m[2]);
      const unmet = Number(m[3] ?? 0);
      return `${met}/${met + unmet + abandoned}`;
    }
    m = UNMET_RE.exec(line);
    if (m) {
      const unmet = Number(m[1]);
      const met = Number(m[2]);
      return `${met}/${met + unmet}`;
    }
  }
  return "";
}

// Where the ticket stands, from the newest protocol comment. Closing comments open
// `ALL MET` or `HANDOFF REQUIRED`; the others are the fixed first lines of the pipeline.
function phaseOf(t: RawTicket): string {
  const head = firstLine(t.comments[t.comments.length - 1]?.body ?? "");
  const closing = newestWithFirstLine(t.comments, "ALL MET", "HANDOFF REQUIRED");
  if (closing) return firstLine(closing.body).startsWith("ALL MET") ? "closed" : "handoff";
  const order: [string, string][] = [
    ["REVIEW", "review"],
    ["DECISIONS", "decisions"],
    ["VERDICT", "verdict"],
    ["reverify", "verify"],
    ["self-run", "selfcheck"],
    ["READY:", "implement"],
    ["NOT_READY:", "not-ready"],
  ];
  for (let i = t.comments.length - 1; i >= 0; i--) {
    const h = firstLine(t.comments[i].body);
    for (const [prefix, phase] of order) if (h.startsWith(prefix)) return phase;
  }
  if (t.state === "CLOSED") return "closed";
  if (head) return "";
  return "";
}

function refsIn(text: string): number[] {
  const out: number[] = [];
  for (const m of text.matchAll(ISSUE_REF_RE)) out.push(Number(m[1]));
  return out;
}

// `Sub-issues opened:` line of the closing comment (or the newest comment carrying one).
function openedBy(t: RawTicket): number[] {
  for (let i = t.comments.length - 1; i >= 0; i--) {
    for (const line of t.comments[i].body.split("\n")) {
      const s = line.trim();
      if (s.startsWith("Sub-issues opened:")) {
        return Array.from(new Set(refsIn(s.slice("Sub-issues opened:".length))));
      }
    }
  }
  return [];
}

function touchedBy(t: RawTicket): number[] {
  const out = new Set<number>();
  for (const c of t.comments) {
    const m = /^TOUCHED BY #(\d+)/.exec(firstLine(c.body));
    if (m) out.add(Number(m[1]));
  }
  return Array.from(out);
}

function abandonedIn(t: RawTicket): Ticket["abandoned"] {
  const seen = new Map<string, Ticket["abandoned"][number]>();
  const texts = [...t.comments.map((c) => c.body)];
  for (const body of texts) {
    for (const line of body.split("\n")) {
      const m = ABANDON_RE.exec(line.trim());
      if (m) seen.set(m[1], { ac: `AC${m[1]}`, kind: m[2], reason: m[3].trim() });
    }
  }
  return Array.from(seen.values());
}

function decisionsIn(t: RawTicket): string[] {
  for (let i = t.comments.length - 1; i >= 0; i--) {
    const lines = t.comments[i].body.split("\n");
    const start = lines.findIndex((l) => l.trim().replace(/^#+\s*/, "").startsWith("Decisions I made on my own"));
    if (start < 0) continue;
    const out: string[] = [];
    for (const raw of lines.slice(start + 1)) {
      const l = raw.trim();
      if (!l) {
        if (out.length) break;
        continue;
      }
      if (/^#+\s/.test(l)) break;
      out.push(l.replace(/^[-*]\s*/, ""));
    }
    return out;
  }
  return [];
}

function toTicket(t: RawTicket): Ticket {
  const nodes = t.blockedBy?.nodes ?? [];
  return {
    number: t.number,
    title: t.title ?? "",
    state: t.state === "CLOSED" ? "CLOSED" : "OPEN",
    labels: (t.labels ?? []).map((l) => l.name).filter(Boolean),
    assignees: (t.assignees ?? []).map((a) => a.login).filter(Boolean),
    blockers: nodes.filter((n) => n.state !== "CLOSED").map((n) => n.number),
    createdAt: t.createdAt,
    closedAt: t.closedAt ?? null,
    phase: phaseOf(t),
    ac: countedAc(t.comments),
    head: firstLine(t.comments[t.comments.length - 1]?.body ?? ""),
    opened: openedBy(t),
    touchedBy: touchedBy(t),
    abandoned: abandonedIn(t),
    decisions: decisionsIn(t),
  };
}

// ------------------------------------------------------------------ the board

function inWindow(at: string | null | undefined, since: string, until: string): boolean {
  return !!at && at >= since && at <= until;
}

// `SUB-ISSUE <kind> from #<n>` is the fixed first line the pipeline is moving to; until
// then a sub-issue's kind is read off its origin's ABANDON line, or falls back to triage.
const SUB_ISSUE_RE = /^SUB-ISSUE\s+(baseline|outside-owns|review|decision)\s+from\s+#(\d+)/;

export async function buildBoard(cwd: string, spec: number, sinceHours: number): Promise<Board> {
  const until = new Date().toISOString();
  const specRaw = await readTicket(cwd, spec);
  const numbers = await subIssues(cwd, spec);
  const raws = (await mapLimit(numbers, 6, (n) => readTicket(cwd, n))).filter((r): r is RawTicket => !!r);
  const rawByNumber = new Map(raws.map((r) => [r.number, r]));
  const tickets = raws.map(toTicket).sort((a, b) => a.number - b.number);
  const byNumber = new Map(tickets.map((t) => [t.number, t]));

  // The night window.
  let since: string;
  if (sinceHours > 0) {
    since = new Date(Date.now() - sinceHours * 3600_000).toISOString();
  } else {
    const summary = newestWithFirstLine(specRaw?.comments ?? [], "NIGHT SUMMARY");
    since = summary?.createdAt ?? new Date(Date.now() - 24 * 3600_000).toISOString();
  }

  // A batch ticket is one `to-tickets` published: it carries a worker grade or sits in
  // the agent queue. Everything else under the spec was opened along the way — by a
  // worker, a reviewer, or the morning's reverify — and is what "opened tonight" counts.
  // The closeout takes `ready-for-agent` off, so a closed batch ticket is recognised by
  // its body: the `<issue-template>` sections a worker's sub-issue never has.
  const isBatchTicket = (t: Ticket) => {
    const body = rawByNumber.get(t.number)?.body ?? "";
    return (
      t.labels.some((l) => l.endsWith("-worker")) ||
      t.labels.includes("ready-for-agent") ||
      t.labels.includes("ready-for-human") ||
      /^## (Acceptance criteria|What to build|Parent)\b/m.test(body)
    );
  };

  // Who opened which sub-issue: the closing comments' `Sub-issues opened:` lines first,
  // then the fixed first line, then — for a non-batch ticket only — the first sibling
  // its body mentions outside its own `## Blocked by` section.
  const origin = new Map<number, number>();
  for (const t of tickets) for (const n of t.opened) if (byNumber.has(n)) origin.set(n, t.number);
  for (const raw of raws) {
    if (origin.has(raw.number)) continue;
    const m = SUB_ISSUE_RE.exec(firstLine(raw.body));
    if (m && byNumber.has(Number(m[2]))) {
      origin.set(raw.number, Number(m[2]));
      continue;
    }
    const me = byNumber.get(raw.number);
    if (!me || isBatchTicket(me)) continue;
    const bodyWithoutBlockers = raw.body.replace(/## Blocked by[\s\S]*?(?=\n## |$)/, "");
    const mentioned = refsIn(bodyWithoutBlockers).find((n) => n !== raw.number && byNumber.has(n));
    if (mentioned !== undefined) origin.set(raw.number, mentioned);
  }

  const problems: Problem[] = [];
  const events: Event[] = [];

  for (const t of tickets) {
    const raw = rawByNumber.get(t.number)!;
    const isNew = inWindow(t.createdAt, since, until) && !isBatchTicket(t);
    const from = origin.get(t.number) ?? null;

    if (t.state === "CLOSED" && inWindow(t.closedAt, since, until)) {
      events.push({ at: t.closedAt!, kind: "closed", ticket: t.number, origin: null, text: `${t.phase === "closed" ? "ALL MET" : t.head} · ${t.ac || "-"}` });
    }
    if (isNew) {
      const subKind = SUB_ISSUE_RE.exec(firstLine(raw.body))?.[1];
      const originAbandon = from !== null ? byNumber.get(from)?.abandoned.find((a) => a.kind === "decision") : undefined;
      const kind: Problem["kind"] = subKind === "baseline" ? "baseline"
        : subKind === "outside-owns" ? "outside-owns"
        : subKind === "review" ? "review"
        : subKind === "decision" || originAbandon ? "decision"
        : "triage";
      events.push({ at: t.createdAt, kind: "opened", ticket: t.number, origin: from, text: t.title });
      if (t.state === "OPEN") {
        problems.push({ kind, ticket: t.number, origin: from, title: t.title, detail: from !== null ? `opened by #${from}` : "opened tonight" });
      }
    }
    const handoff = newestWithFirstLine(raw.comments, "HANDOFF REQUIRED");
    if (handoff && t.state === "OPEN") {
      if (inWindow(handoff.createdAt, since, until)) {
        events.push({ at: handoff.createdAt, kind: "handed-back", ticket: t.number, origin: null, text: firstLine(handoff.body) });
      }
      problems.push({
        kind: "handed-back",
        ticket: t.number,
        origin: null,
        title: t.title,
        detail: t.abandoned.map((a) => `${a.ac} ${a.kind}: ${a.reason}`).join(" · ") || firstLine(handoff.body),
      });
    }
    if (t.state === "OPEN" && t.closedAt) {
      // Closed once and open again: the after-night reverify reopened it.
      const red = newestWithFirstLine(raw.comments, "reverify");
      events.push({ at: red?.createdAt ?? t.closedAt, kind: "reopened", ticket: t.number, origin: null, text: red ? firstLine(red.body) : "reopened" });
      problems.push({ kind: "reverify-red", ticket: t.number, origin: null, title: t.title, detail: red ? red.body.split("\n").slice(1, 3).join(" ") : "reopened after closing" });
    }
    for (const n of t.touchedBy) {
      problems.push({ kind: "touched", ticket: t.number, origin: n, title: t.title, detail: `#${n} changed a file under this ticket's Owns` });
    }
    if (t.state === "OPEN" && t.labels.includes("ready-for-agent") && t.blockers.length) {
      problems.push({ kind: "blocked", ticket: t.number, origin: null, title: t.title, detail: `waiting on ${t.blockers.map((b) => `#${b}`).join(", ")}` });
    }
    if (t.state === "OPEN" && t.labels.includes("needs-triage") && !isNew && !handoff && !t.closedAt) {
      problems.push({ kind: "triage", ticket: t.number, origin: from, title: t.title, detail: t.head || "needs-triage" });
    }
  }

  for (const c of specRaw?.comments ?? []) {
    if (firstLine(c.body).startsWith("NIGHT SUMMARY") && inWindow(c.createdAt, since, until)) {
      events.push({ at: c.createdAt, kind: "summary", ticket: spec, origin: null, text: c.body.split("\n").slice(0, 6).join("\n") });
    }
  }
  events.sort((a, b) => (a.at < b.at ? -1 : a.at > b.at ? 1 : 0));

  const frontier = tickets
    .filter((t) => t.state === "OPEN" && t.labels.includes("ready-for-agent") && !t.blockers.length && !t.assignees.length)
    .map((t) => t.number);
  const inQueue = tickets.filter((t) => t.state === "OPEN" && t.labels.includes("ready-for-agent")).map((t) => t.number);

  return {
    spec: { number: spec, title: specRaw?.title ?? `#${spec}` },
    repo: cwd,
    since,
    until,
    tickets,
    problems,
    events,
    summary: {
      closed: events.filter((e) => e.kind === "closed").map((e) => e.ticket),
      opened: events.filter((e) => e.kind === "opened").map((e) => e.ticket),
      handedBack: events.filter((e) => e.kind === "handed-back").map((e) => e.ticket),
      reopened: events.filter((e) => e.kind === "reopened").map((e) => e.ticket),
      blocked: problems.filter((p) => p.kind === "blocked").map((p) => p.ticket),
      frontier,
      inQueue,
    },
    generatedAt: until,
  };
}

// Open issues that hold sub-issues: the specs a night can run on.
export async function listSpecs(cwd: string): Promise<{ number: number; title: string; open: number; closed: number }[]> {
  const rows = await ghJson<{ number: number; title: string; sub_issues_summary?: { total?: number; completed?: number } }[]>(
    cwd,
    ["api", "--paginate", "--slurp", "repos/{owner}/{repo}/issues?state=all&per_page=100&sort=updated"],
    [],
  );
  const flat: typeof rows = [];
  for (const page of rows as unknown[]) {
    if (Array.isArray(page)) flat.push(...(page as typeof rows));
  }
  return flat
    .filter((r) => (r.sub_issues_summary?.total ?? 0) > 0)
    .map((r) => ({
      number: r.number,
      title: r.title,
      open: (r.sub_issues_summary?.total ?? 0) - (r.sub_issues_summary?.completed ?? 0),
      closed: r.sub_issues_summary?.completed ?? 0,
    }))
    .sort((a, b) => b.number - a.number);
}
