// The one contract between the surface and the daemon: ask for a spec's board,
// get back the night organised. Everything here is JSON so it can cross the RPC.
import { defineRpc } from "@getpaseo/plugin/server";
import { z } from "zod";

export const TicketSchema = z.object({
  number: z.number(),
  title: z.string(),
  state: z.enum(["OPEN", "CLOSED"]),
  labels: z.array(z.string()),
  assignees: z.array(z.string()),
  blockers: z.array(z.number()),
  createdAt: z.string(),
  closedAt: z.string().nullable(),
  // Where the ticket stands, read off its comments' first lines.
  phase: z.string(),
  // "<met>/<total>" off the newest self-run or reverify comment, or "".
  ac: z.string(),
  // First line of the newest comment.
  head: z.string(),
  // Sub-issues this ticket opened, read from its closing comment's `Sub-issues opened:` line.
  opened: z.array(z.number()),
  // Tickets whose worker touched a file this ticket owns (`TOUCHED BY #<n>`).
  touchedBy: z.array(z.number()),
  // Every `ABANDON: AC<n> <kind> …` line on the ticket.
  abandoned: z.array(z.object({ ac: z.string(), kind: z.string(), reason: z.string() })),
  // A worker's `Decisions I made on my own` lines, newest comment wins.
  decisions: z.array(z.string()),
});
export type Ticket = z.output<typeof TicketSchema>;

export const ProblemSchema = z.object({
  kind: z.enum([
    "handed-back",
    "decision",
    "baseline",
    "review",
    "outside-owns",
    "touched",
    "reverify-red",
    "blocked",
    "triage",
  ]),
  ticket: z.number(),
  // The ticket this problem belongs to, when it is not the ticket itself
  // (a sub-issue's originating ticket).
  origin: z.number().nullable(),
  title: z.string(),
  detail: z.string(),
});
export type Problem = z.output<typeof ProblemSchema>;

export const EventSchema = z.object({
  at: z.string(),
  kind: z.enum(["closed", "opened", "handed-back", "reopened", "summary"]),
  ticket: z.number(),
  origin: z.number().nullable(),
  text: z.string(),
});
export type Event = z.output<typeof EventSchema>;

export const BoardSchema = z.object({
  spec: z.object({ number: z.number(), title: z.string() }),
  repo: z.string(),
  // The window the "night" columns count: ISO timestamps.
  since: z.string(),
  until: z.string(),
  tickets: z.array(TicketSchema),
  problems: z.array(ProblemSchema),
  events: z.array(EventSchema),
  summary: z.object({
    closed: z.array(z.number()),
    opened: z.array(z.number()),
    handedBack: z.array(z.number()),
    reopened: z.array(z.number()),
    blocked: z.array(z.number()),
    frontier: z.array(z.number()),
    inQueue: z.array(z.number()),
  }),
  generatedAt: z.string(),
});
export type Board = z.output<typeof BoardSchema>;

export const boardRpc = defineRpc({
  name: "mmw.board",
  input: z.object({
    // Absolute path of a checkout; `gh` infers the repository from it.
    repoPath: z.string(),
    spec: z.number(),
    // Hours before now that count as "tonight". 0 means: since the newest
    // NIGHT SUMMARY comment on the spec, falling back to 24 hours.
    sinceHours: z.number(),
  }),
  output: BoardSchema,
});

export const specsRpc = defineRpc({
  name: "mmw.specs",
  input: z.object({ repoPath: z.string() }),
  output: z.object({
    specs: z.array(z.object({ number: z.number(), title: z.string(), open: z.number(), closed: z.number() })),
  }),
});
