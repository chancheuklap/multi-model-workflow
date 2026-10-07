// The board surface: one spec's night, organised. Reads the tracker through the
// daemon RPC and the live agents through Paseo's own client state. Shows; never acts.
import { usePaseo, useRpc, type PluginSurfaceProps } from "@getpaseo/plugin";
import { useQuery } from "@tanstack/react-query";
import React, { useMemo, useState } from "react";
import { Pressable, ScrollView, Text, View } from "react-native";
import { boardRpc, specsRpc, type Board, type Problem, type Ticket } from "./board.shared";

type Project = { projectId: string; projectDisplayName: string; projectRootPath: string; projectKind: string };
type LiveAgent = {
  id: string;
  title: string | null;
  status: string;
  cwd: string;
  createdAt: string;
  labels: Record<string, string>;
  pendingPermissions: unknown[];
  archivedAt?: string | null;
  provider: string;
  model: string | null;
  lastUsage?: { totalCostUsd?: number } | null;
};

const WINDOWS: { label: string; hours: number }[] = [
  { label: "since NIGHT SUMMARY", hours: 0 },
  { label: "12 h", hours: 12 },
  { label: "24 h", hours: 24 },
  { label: "3 d", hours: 72 },
  { label: "7 d", hours: 168 },
];

const PROBLEM_TITLES: Record<Problem["kind"], string> = {
  "handed-back": "Handed back (HANDOFF REQUIRED)",
  decision: "Decisions only a person can settle",
  baseline: "Baseline does not fit",
  review: "Out-of-ticket review findings",
  "outside-owns": "Changes outside Owns, parked",
  touched: "Owned files touched by another ticket",
  "reverify-red": "Red after the night's reverify",
  blocked: "Waiting on a blocker",
  triage: "Needs triage (other)",
};

function ago(iso: string | null | undefined, now: number): string {
  if (!iso) return "";
  const s = Math.max(0, Math.floor((now - Date.parse(iso)) / 1000));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  if (s < 86400) return `${Math.floor(s / 3600)}h${Math.floor((s % 3600) / 60)}m`;
  return `${Math.floor(s / 86400)}d${Math.floor((s % 86400) / 3600)}h`;
}

function clock(iso: string): string {
  const d = new Date(iso);
  return `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;
}

export function BoardSurface({ theme, layout, navigation }: PluginSurfaceProps) {
  const paseo = usePaseo();
  const getBoard = useRpc(boardRpc);
  const getSpecs = useRpc(specsRpc);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [spec, setSpec] = useState<number | null>(null);
  const [hours, setHours] = useState(0);
  const [tab, setTab] = useState<"night" | "tickets" | "problems">("night");
  const now = Date.now();

  const c = theme.colors;
  const pad = layout.compact ? 12 : 20;
  const st = useMemo(
    () => ({
      screen: { flex: 1, backgroundColor: c.surface0 },
      body: { padding: pad, gap: pad },
      row: { flexDirection: "row" as const, flexWrap: "wrap" as const, gap: 8, alignItems: "center" as const },
      chip: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 8, borderWidth: 1, borderColor: c.border, backgroundColor: c.surface1 },
      chipOn: { backgroundColor: c.accent, borderColor: c.accent },
      chipText: { color: c.foreground, fontSize: 13 },
      chipTextOn: { color: c.accentForeground, fontSize: 13 },
      h1: { color: c.foreground, fontSize: layout.compact ? 18 : 22, fontWeight: "600" as const },
      h2: { color: c.foreground, fontSize: 15, fontWeight: "600" as const, marginTop: 4 },
      muted: { color: c.foregroundMuted, fontSize: 12 },
      text: { color: c.foreground, fontSize: 13 },
      card: { borderWidth: 1, borderColor: c.border, borderRadius: 10, backgroundColor: c.surface1, padding: 12, gap: 6 },
      stat: { borderWidth: 1, borderColor: c.border, borderRadius: 10, backgroundColor: c.surface1, paddingVertical: 10, paddingHorizontal: 14, minWidth: 96 },
      statN: { color: c.foreground, fontSize: 22, fontWeight: "600" as const },
      ok: { color: c.statusSuccess },
      warn: { color: c.statusWarning },
      bad: { color: c.statusDanger },
      link: { color: c.accent, fontSize: 13 },
      tr: { flexDirection: "row" as const, gap: 8, paddingVertical: 6, borderBottomWidth: 1, borderBottomColor: c.border, alignItems: "flex-start" as const },
    }),
    [c, pad, layout.compact],
  );

  const projects = useQuery({
    queryKey: ["mmw-board", "projects"],
    queryFn: async () => {
      const r = (await paseo.projects.list()) as unknown as { projects: Project[] };
      return (r.projects ?? []).filter((p) => p.projectKind === "git");
    },
  });
  const project = projects.data?.find((p) => p.projectId === projectId) ?? projects.data?.[0] ?? null;
  const repoPath = project?.projectRootPath ?? null;

  const specs = useQuery({
    queryKey: ["mmw-board", "specs", repoPath],
    enabled: !!repoPath,
    queryFn: () => getSpecs({ repoPath: repoPath! }),
  });
  const chosenSpec = spec ?? specs.data?.specs.find((s) => s.open > 0)?.number ?? specs.data?.specs[0]?.number ?? null;

  const board = useQuery({
    queryKey: ["mmw-board", "board", repoPath, chosenSpec, hours],
    enabled: !!repoPath && chosenSpec !== null,
    refetchInterval: 60_000,
    queryFn: () => getBoard({ repoPath: repoPath!, spec: chosenSpec!, sinceHours: hours }),
  });

  const agents = useQuery({
    queryKey: ["mmw-board", "agents"],
    refetchInterval: 15_000,
    queryFn: async () => {
      const r = await paseo.agents.list({ filter: { includeArchived: false } } as never);
      return (r.entries as unknown as { agent: LiveAgent }[]).map((e) => e.agent);
    },
  });

  const agentsByTicket = useMemo(() => {
    const map = new Map<number, LiveAgent[]>();
    for (const a of agents.data ?? []) {
      if (a.archivedAt) continue;
      const fromLabel = Number(a.labels?.["mmw.ticket"]);
      const fromCwd = /\/issue-(\d+)(?:\/|$)/.exec(a.cwd ?? "")?.[1];
      const fromTitle = /^#(\d+)\b/.exec(a.title ?? "")?.[1];
      const n = Number.isFinite(fromLabel) && fromLabel > 0 ? fromLabel : fromCwd ? Number(fromCwd) : fromTitle ? Number(fromTitle) : NaN;
      if (!Number.isFinite(n)) continue;
      const list = map.get(n) ?? [];
      list.push(a);
      map.set(n, list);
    }
    return map;
  }, [agents.data]);

  const data = board.data;
  const byNumber = useMemo(() => new Map((data?.tickets ?? []).map((t) => [t.number, t])), [data]);

  function Chip({ on, label, onPress }: { on: boolean; label: string; onPress: () => void }) {
    return (
      <Pressable accessibilityRole="button" onPress={onPress} style={[st.chip, on ? st.chipOn : null]}>
        <Text style={on ? st.chipTextOn : st.chipText}>{label}</Text>
      </Pressable>
    );
  }

  function TicketRef({ n }: { n: number }) {
    const t = byNumber.get(n);
    return (
      <Text style={st.text}>
        <Text style={{ color: c.accent }}>#{n}</Text>
        {t ? ` ${t.title}` : ""}
      </Text>
    );
  }

  function AgentLine({ n }: { n: number }) {
    const list = agentsByTicket.get(n) ?? [];
    if (!list.length) return null;
    return (
      <View style={{ gap: 2 }}>
        {list.map((a) => {
          const kind = a.labels?.["mmw.kind"] ?? (/(reviewer|verifier)/.exec(a.title ?? "")?.[1] ?? "worker");
          const tone = a.status === "error" ? st.bad : a.pendingPermissions?.length ? st.warn : a.status === "running" ? st.ok : st.muted;
          return (
            <Pressable key={a.id} accessibilityRole="button" onPress={() => navigation?.openAgent({ agentId: a.id })} disabled={!navigation}>
              <Text style={st.muted}>
                <Text style={tone}>●</Text> {kind} · {a.provider}
                {a.model ? `/${a.model}` : ""} · {a.status}
                {a.pendingPermissions?.length ? ` · ${a.pendingPermissions.length} permission` : ""} · up {ago(a.createdAt, now)}
                {a.lastUsage?.totalCostUsd ? ` · $${a.lastUsage.totalCostUsd.toFixed(2)}` : ""}
                {navigation ? "  open ›" : ""}
              </Text>
            </Pressable>
          );
        })}
      </View>
    );
  }

  function phaseTone(t: Ticket) {
    if (t.state === "CLOSED") return st.ok;
    if (t.phase === "handoff" || t.labels.includes("needs-triage")) return st.bad;
    if (t.blockers.length) return st.muted;
    return st.text;
  }

  return (
    <ScrollView style={st.screen} contentContainerStyle={st.body}>
      <Text style={st.h1}>mmw board</Text>

      <View style={st.row}>
        <Text style={st.muted}>Project</Text>
        {(projects.data ?? []).map((p) => (
          <Chip key={p.projectId} on={p.projectId === project?.projectId} label={p.projectDisplayName} onPress={() => { setProjectId(p.projectId); setSpec(null); }} />
        ))}
      </View>
      <View style={st.row}>
        <Text style={st.muted}>Spec</Text>
        {(specs.data?.specs ?? []).slice(0, 12).map((s) => (
          <Chip key={s.number} on={s.number === chosenSpec} label={`#${s.number} · ${s.open} open / ${s.closed} closed`} onPress={() => setSpec(s.number)} />
        ))}
        {specs.isLoading ? <Text style={st.muted}>loading…</Text> : null}
      </View>
      <View style={st.row}>
        <Text style={st.muted}>Night</Text>
        {WINDOWS.map((w) => (
          <Chip key={w.hours} on={w.hours === hours} label={w.label} onPress={() => setHours(w.hours)} />
        ))}
        <Pressable accessibilityRole="button" onPress={() => { void board.refetch(); void agents.refetch(); }} style={st.chip}>
          <Text style={st.chipText}>{board.isFetching ? "refreshing…" : "refresh"}</Text>
        </Pressable>
      </View>

      {board.error ? <Text style={st.bad}>{String(board.error)}</Text> : null}
      {!data ? <Text style={st.muted}>{board.isLoading ? "reading the tracker…" : "pick a project and a spec"}</Text> : null}

      {data ? (
        <>
          <View style={st.card}>
            <Text style={st.h2}>#{data.spec.number} {data.spec.title}</Text>
            <Text style={st.muted}>
              window {clock(data.since)} → {clock(data.until)} ({ago(data.since, now)} ago) · {data.tickets.length} tickets · generated {clock(data.generatedAt)}
            </Text>
          </View>

          <View style={st.row}>
            {[
              ["closed tonight", data.summary.closed.length, st.ok],
              ["opened tonight", data.summary.opened.length, st.warn],
              ["handed back", data.summary.handedBack.length, st.bad],
              ["reopened", data.summary.reopened.length, st.bad],
              ["frontier", data.summary.frontier.length, st.text],
              ["in queue", data.summary.inQueue.length, st.text],
              ["blocked", data.summary.blocked.length, st.muted],
              ["problems", data.problems.length, data.problems.length ? st.warn : st.ok],
            ].map(([label, n, tone]) => (
              <View key={String(label)} style={st.stat}>
                <Text style={[st.statN, tone as object]}>{String(n)}</Text>
                <Text style={st.muted}>{String(label)}</Text>
              </View>
            ))}
          </View>

          <View style={st.row}>
            <Chip on={tab === "night"} label="Tonight" onPress={() => setTab("night")} />
            <Chip on={tab === "problems"} label={`Problems (${data.problems.length})`} onPress={() => setTab("problems")} />
            <Chip on={tab === "tickets"} label={`Tickets (${data.tickets.length})`} onPress={() => setTab("tickets")} />
          </View>

          {tab === "night" ? (
            <View style={{ gap: pad }}>
              <View style={st.card}>
                <Text style={st.h2}>Closed tonight · {data.summary.closed.length}</Text>
                {data.summary.closed.length === 0 ? <Text style={st.muted}>none</Text> : null}
                {data.events.filter((e) => e.kind === "closed").map((e) => {
                  const t = byNumber.get(e.ticket);
                  return (
                    <View key={`c${e.ticket}`} style={{ gap: 2 }}>
                      <Text style={st.text}>
                        <Text style={st.muted}>{clock(e.at)} </Text>
                        <TicketRef n={e.ticket} />
                      </Text>
                      <Text style={st.muted}>{e.text}{t?.opened.length ? ` · opened ${t.opened.map((n) => `#${n}`).join(", ")}` : ""}</Text>
                      {t?.decisions.length ? <Text style={st.muted}>decided alone: {t.decisions.slice(0, 3).join(" · ")}{t.decisions.length > 3 ? " …" : ""}</Text> : null}
                    </View>
                  );
                })}
              </View>

              <View style={st.card}>
                <Text style={st.h2}>Opened tonight · {data.summary.opened.length}</Text>
                {data.summary.opened.length === 0 ? <Text style={st.muted}>none</Text> : null}
                {groupBy(data.events.filter((e) => e.kind === "opened"), (e) => e.origin ?? 0).map(([origin, list]) => (
                  <View key={`o${origin}`} style={{ gap: 2 }}>
                    <Text style={st.text}>{origin ? <>from <TicketRef n={origin} /></> : "no originating ticket found"}</Text>
                    {list.map((e) => {
                      const p = data.problems.find((q) => q.ticket === e.ticket);
                      return (
                        <Text key={e.ticket} style={st.muted}>
                          {"   "}{clock(e.at)} <Text style={{ color: c.accent }}>#{e.ticket}</Text> {e.text}
                          {p ? ` · ${p.kind}` : ""}
                          {byNumber.get(e.ticket)?.state === "CLOSED" ? " · already closed" : ""}
                        </Text>
                      );
                    })}
                  </View>
                ))}
              </View>

              {data.summary.handedBack.length || data.summary.reopened.length ? (
                <View style={st.card}>
                  <Text style={st.h2}>Handed back / reopened tonight</Text>
                  {data.events.filter((e) => e.kind === "handed-back" || e.kind === "reopened").map((e) => (
                    <Text key={`${e.kind}${e.ticket}`} style={st.text}>
                      <Text style={st.muted}>{clock(e.at)} </Text>
                      <Text style={st.bad}>{e.kind}</Text> <TicketRef n={e.ticket} />
                      <Text style={st.muted}> — {e.text}</Text>
                    </Text>
                  ))}
                </View>
              ) : null}

              <View style={st.card}>
                <Text style={st.h2}>Timeline</Text>
                {data.events.length === 0 ? <Text style={st.muted}>nothing in this window</Text> : null}
                {data.events.map((e, i) => (
                  <Text key={i} style={st.muted}>
                    {clock(e.at)} {e.kind} <Text style={{ color: c.accent }}>#{e.ticket}</Text>
                    {e.origin ? ` ← #${e.origin}` : ""} {e.text.split("\n")[0].slice(0, 90)}
                  </Text>
                ))}
              </View>

              {data.summary.frontier.length ? (
                <View style={st.card}>
                  <Text style={st.h2}>Ready to start (frontier)</Text>
                  {data.summary.frontier.map((n) => <TicketRef key={n} n={n} />)}
                </View>
              ) : null}
            </View>
          ) : null}

          {tab === "problems" ? (
            <View style={{ gap: pad }}>
              {data.problems.length === 0 ? <Text style={st.ok}>no problems on this spec</Text> : null}
              {groupBy(data.problems, (p) => p.kind).map(([kind, list]) => (
                <View key={kind} style={st.card}>
                  <Text style={st.h2}>{PROBLEM_TITLES[kind as Problem["kind"]] ?? kind} · {list.length}</Text>
                  {list.map((p, i) => (
                    <View key={`${p.ticket}-${i}`} style={{ gap: 2 }}>
                      <Text style={st.text}>
                        <TicketRef n={p.ticket} />
                        {p.origin ? <Text style={st.muted}>  ← #{p.origin}</Text> : null}
                      </Text>
                      <Text style={st.muted}>{p.detail}</Text>
                      <AgentLine n={p.ticket} />
                    </View>
                  ))}
                </View>
              ))}
            </View>
          ) : null}

          {tab === "tickets" ? (
            <View style={st.card}>
              {data.tickets.map((t) => (
                <View key={t.number} style={st.tr}>
                  <View style={{ width: layout.compact ? 56 : 64 }}>
                    <Text style={[st.text, phaseTone(t)]}>#{t.number}</Text>
                    <Text style={st.muted}>{t.state === "CLOSED" ? "closed" : t.phase || "-"}</Text>
                  </View>
                  <View style={{ flex: 1, gap: 2 }}>
                    <Text style={st.text}>{t.title}</Text>
                    <Text style={st.muted}>
                      AC {t.ac || "-"} · {t.labels.filter((l) => l !== "ready-for-agent" || true).join(", ") || "no label"}
                      {t.assignees.length ? ` · ${t.assignees.join(", ")}` : ""}
                      {t.blockers.length ? ` · blocked by ${t.blockers.map((b) => `#${b}`).join(", ")}` : ""}
                      {t.closedAt ? ` · closed ${ago(t.closedAt, now)} ago` : ` · opened ${ago(t.createdAt, now)} ago`}
                    </Text>
                    {t.head ? <Text style={st.muted} numberOfLines={1}>last: {t.head}</Text> : null}
                    {t.abandoned.length ? <Text style={st.bad}>{t.abandoned.map((a) => `${a.ac} ${a.kind}`).join(" · ")}</Text> : null}
                    <AgentLine n={t.number} />
                  </View>
                </View>
              ))}
            </View>
          ) : null}
        </>
      ) : null}
    </ScrollView>
  );
}

function groupBy<T, K extends string | number>(items: T[], key: (item: T) => K): [K, T[]][] {
  const map = new Map<K, T[]>();
  for (const item of items) {
    const k = key(item);
    const list = map.get(k) ?? [];
    list.push(item);
    map.set(k, list);
  }
  return Array.from(map.entries());
}
