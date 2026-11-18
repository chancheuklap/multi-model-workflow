import { describe, expect, it } from "bun:test";
import { spawnSync } from "node:child_process";
import { mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  ChecksUnavailable,
  WatcherQueryError,
  buildReviewThreads,
  mapRollupNode,
  orderStack,
  parseFastCheck,
  parsePullRequest,
  parseReviewThreadPage,
  resolveChecks,
  resolveContext,
  resolveReviewThreads,
} from "./github.ts";
import {
  fakeReader,
  failedCheck,
  passingCheck,
  pendingCheck,
} from "./fakes.test-helper.ts";
import { renderPretty } from "./render.ts";
import { parsePrNumber } from "./types.ts";
import type * as T from "./types.ts";
import type { FakeReaderOptions } from "./fakes.test-helper.ts";
import { readSnapshot, runQueued, runSimple } from "./policy.ts";

const context = {
  owner: "owner",
  repo: "repo",
  number: parsePrNumber(42),
};

const emptyChecks = { kind: "checks", checks: [] } satisfies T.ChecksFastPath;
const noChecksOptions = {
  interval: 1,
  sweepInterval: 2,
  timeout: 1000,
  maxQueryErrors: 5,
  allowDraft: false,
} satisfies T.PollingOptions;

function noChecksRun(reader: T.GitHubReader, options = noChecksOptions) {
  let now = 0;
  const events: T.ProgressVerdict[] = [];
  const sleeps: number[] = [];
  const dependencies = {
    reader,
    emit: (event: T.ProgressVerdict) => events.push(event),
    clock: {
      now: () => now,
      observedAt: () => new Date(now * 1000).toISOString(),
      async sleep(seconds: number) {
        sleeps.push(seconds);
        now += seconds;
      },
    },
  };
  return {
    events,
    sleeps,
    simple(
      contexts: T.NonEmpty<T.PrContext> = [context],
      mode: T.WatchMode = "single",
      statusOnly = false
    ) {
      return runSimple({ dependencies, contexts, mode, statusOnly, options });
    },
    queued(contexts: T.NonEmpty<T.PrContext> = [context]) {
      return runQueued({ dependencies, contexts, options });
    },
  };
}

describe("no-checks confirmation", () => {
  it("requires two CLEAN observations and preserves the first-empty retry", async () => {
    const reader = fakeReader({ fastPath: emptyChecks });
    const run = noChecksRun(reader);
    const verdict = await run.simple();
    expect(verdict).toMatchObject({
      kind: "READY",
      scope: { pr: { proof: { ci: {
        kind: "ci-clean", source: "no-checks", all: [], failed: [], pending: [],
        github: { kind: "allowed", basis: "merge-state", mergeStateStatus: "CLEAN" },
      } } } },
    });
    expect(run.events.map((event) => event.kind)).toEqual(["RETRY"]);
    expect(run.events[0]).toMatchObject({
      failure: { kind: "checks-unavailable" }, consecutiveFailures: 1,
    });
    expect(run.sleeps).toEqual([60]);
    expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(2);
    expect(reader.calls.filter((call) => call === "commitRollups")).toHaveLength(2);
  });

  it("reports the confirmation wait and distinguishes empty CI in the status table", async () => {
    const run = noChecksRun(fakeReader({ fastPath: emptyChecks }));
    const status = await run.simple([context], "single", true);
    expect(run.events.map(renderPretty)).toEqual([
      "RETRY: empty checks require a second CLEAN observation of the same head. Retrying in 60s\n",
    ]);
    expect(renderPretty(status)).toContain("| No checks |");
  });

  it("retains the one-error budget and one-shot snapshot behavior", async () => {
    const reader = fakeReader({ fastPath: emptyChecks });
    const run = noChecksRun(reader, { ...noChecksOptions, maxQueryErrors: 1 });
    expect(await run.simple()).toMatchObject({
      kind: "BLOCKER", blocker: { kind: "status-query", failures: 1 },
    });
    await expect(readSnapshot({
      reader, context, pendingHistory: "include", allowDraft: false,
    })).rejects.toBeInstanceOf(ChecksUnavailable);
  });

  it("waits rather than accepting empty once followed by pending checks", async () => {
    const run = noChecksRun(fakeReader({
      fastPath: emptyChecks,
      observe: (_context, read) => read === 1 ? {} : {
        fastPath: { kind: "checks", checks: [pendingCheck()] },
      },
    }), { ...noChecksOptions, timeout: 61 });
    expect(await run.simple()).toMatchObject({
      kind: "TIMEOUT", reason: { kind: "pending-checks" },
    });
    expect(run.events.map((event) => event.kind)).toEqual(["RETRY", "WAITING", "WAITING"]);
  });

  const nonCleanStates: readonly Exclude<T.MergeStateStatus, "CLEAN">[] = [
    "BLOCKED", "BEHIND", "DIRTY", "UNKNOWN", "CONFLICTING", "DRAFT",
    "HAS_HOOKS", "UNSTABLE",
  ];
  for (const mergeStateStatus of nonCleanStates)
    it(`does not confirm empty checks in ${mergeStateStatus}`, async () => {
      const run = noChecksRun(fakeReader({
        fastPath: emptyChecks, facts: { mergeStateStatus },
      }), { ...noChecksOptions, maxQueryErrors: 2 });
      expect(await run.simple()).toMatchObject({
        kind: "BLOCKER",
        blocker: { kind: "status-query", failure: { kind: "checks-unavailable" } },
      });
      expect(run.events.map((event) => event.kind)).toEqual(["RETRY"]);
    });

  for (const headRefOid of [null, ""])
    it(`cannot confirm a missing head ${JSON.stringify(headRefOid)}`, async () => {
      const run = noChecksRun(fakeReader({
        fastPath: emptyChecks, facts: { headRefOid },
      }), { ...noChecksOptions, maxQueryErrors: 2 });
      expect(await run.simple()).toMatchObject({
        kind: "BLOCKER", blocker: { kind: "status-query" },
      });
    });

  const queryError = () => new WatcherQueryError({
    kind: "command-exit", retryable: true, code: 1, detail: "temporary failure",
  });
  const interruptions: readonly [
    string,
    (read: number) => FakeReaderOptions,
    T.ProgressVerdict["kind"][],
  ][] = [
    ["head A/B/A", (read) => ({
      facts: { headRefOid: read === 2 ? "B" : "A" },
    }), ["RETRY", "RETRY", "RETRY"]],
    ["facts error", (read) => {
      if (read === 2) throw queryError();
      return {};
    }, ["RETRY", "RETRY", "RETRY"]],
    ["history error", (read) => ({
      commitRollups: read === 2 ? queryError() : [{ oid: "head", state: null }],
    }), ["RETRY", "RETRY", "RETRY"]],
    ["non-CLEAN", (read) => ({
      facts: { mergeStateStatus: read === 2 ? "UNKNOWN" : "CLEAN" },
    }), ["RETRY", "RETRY", "RETRY"]],
    ["pending checks", (read) => read === 2 ? {
      fastPath: { kind: "checks", checks: [pendingCheck()] },
    } : {}, ["RETRY", "WAITING", "RETRY"]],
  ];
  for (const [name, observe, expected] of interruptions)
    it(`restarts confirmation after ${name}`, async () => {
      const reader = fakeReader({ fastPath: emptyChecks, observe: (_context, read) => observe(read) });
      const run = noChecksRun(reader);
      expect(await run.simple()).toMatchObject({ kind: "READY" });
      expect(run.events.map((event) => event.kind)).toEqual(expected);
      expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(4);
    });

  it("resets confirmed evidence after nonempty passing checks in queued mode", async () => {
    const reader = fakeReader({
      fastPath: emptyChecks,
      observe: (_context, read) => {
        if (read === 3) return { fastPath: { kind: "checks", checks: [passingCheck()] } };
        if (read >= 6) return { facts: { state: "MERGED", mergedAt: "merged" } };
        return {};
      },
    });
    const run = noChecksRun(reader);
    expect(await run.queued()).toMatchObject({ kind: "COMPLETE" });
    expect(run.events.filter((event) => event.kind === "RETRY")).toHaveLength(2);
    expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(6);
  });

  it("keeps confirmation private to sequential and concurrent runs sharing a reader", async () => {
    const reader = fakeReader({ fastPath: emptyChecks });
    for (const run of [noChecksRun(reader), noChecksRun(reader)]) {
      expect(await run.simple()).toMatchObject({ kind: "READY" });
      expect(run.events.filter((event) => event.kind === "RETRY")).toHaveLength(1);
    }
    const runs = [noChecksRun(reader), noChecksRun(reader)];
    expect((await Promise.all(runs.map((run) => run.simple()))).map((v) => v.kind))
      .toEqual(["READY", "READY"]);
    expect(runs.map((run) => run.events.filter((event) => event.kind === "RETRY").length))
      .toEqual([1, 1]);
  });

  for (const mode of ["single", "stack", "queued-stack"] satisfies T.WatchMode[])
    it(`confirms status-only ${mode} using full PR identity`, async () => {
      const contexts: T.NonEmpty<T.PrContext> = mode === "single" ? [context] : [
        context, { ...context, repo: "another" }, { ...context, owner: "another" },
      ];
      const reads: string[] = [];
      const run = noChecksRun(fakeReader({
        fastPath: emptyChecks,
        observe: (requested) => {
          reads.push(`${requested.owner}/${requested.repo}`);
          return {};
        },
      }));
      const verdict = await run.simple(contexts, mode, true);
      expect(verdict.kind).toBe("STATUS");
      if (verdict.kind !== "STATUS") throw new Error("expected status");
      expect(verdict.rows.map((row) => row.kind === "open" ? row.ci.source : row.kind))
        .toEqual(contexts.map(() => "no-checks"));
      expect(reads).toEqual([...contexts, ...contexts].map((pr) => `${pr.owner}/${pr.repo}`));
      expect(run.events.map((event) => event.kind)).toEqual(["RETRY"]);
    });

  it("confirms six empty PRs together within the default five-error budget", async () => {
    const contexts: T.NonEmpty<T.PrContext> = [context, ...[43, 44, 45, 46, 47].map(
      (number) => ({ ...context, number: parsePrNumber(number) })
    )];
    const reader = fakeReader({ fastPath: emptyChecks });
    const run = noChecksRun(reader);
    expect(await run.simple(contexts, "stack")).toMatchObject({ kind: "READY" });
    expect(run.events.map((event) => event.kind)).toEqual(["RETRY", "STATUS"]);
    expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(12);
    expect(run.sleeps).toEqual([60]);
  });

  it("preserves queued sweep retries and waits for each actual merge", async () => {
    const second = { ...context, number: parsePrNumber(43) };
    const reads: number[] = [];
    const run = noChecksRun(fakeReader({
      fastPath: emptyChecks,
      observe: (requested, read) => {
        reads.push(requested.number);
        return read >= 4 ? { facts: { state: "MERGED", mergedAt: "merged" } } : {};
      },
    }));
    expect(await run.queued([context, second])).toMatchObject({ kind: "COMPLETE" });
    expect(reads.slice(0, 4)).toEqual([42, 42, 43, 43]);
    expect(run.events.filter((event) => event.kind === "RETRY")).toHaveLength(2);
    expect(run.events).toContainEqual(expect.objectContaining({
      kind: "WAITING", reason: { kind: "merge-queue", unmergedCount: 2 },
    }));
    expect(run.events.some((event) => event.kind === "ADVANCE")).toBe(true);
    expect(run.events.filter((event) => event.kind === "STATUS").length).toBeGreaterThan(1);
    const status = run.events.find((event) => event.kind === "STATUS");
    expect(status).toMatchObject({
      rows: [
        { kind: "open", ci: { kind: "ci-clean", source: "no-checks", all: [] } },
        { kind: "open", ci: { kind: "ci-clean", source: "no-checks", all: [] } },
      ],
    });
  });
});

describe("empty-checks same-poll evidence", () => {
  const nonNullStates: readonly Exclude<T.RollupState, null>[] = [
    "FAILURE", "ERROR", "PENDING", "EXPECTED", "SUCCESS",
  ];
  for (const state of nonNullStates) {
    it(`rejects a same-head ${state} rollup despite empty checks and CLEAN facts`, async () => {
      const reader = fakeReader({
        fastPath: emptyChecks,
        commitRollups: [{ oid: "head", state }],
      });
      const run = noChecksRun(reader, { ...noChecksOptions, maxQueryErrors: 2 });
      expect(await run.simple()).toMatchObject({
        kind: "BLOCKER",
        blocker: { kind: "status-query", failure: { kind: "checks-unavailable" } },
      });
      expect(run.events.map((event) => event.kind)).toEqual(["RETRY"]);
      expect(reader.calls.filter((call) => call === "commitRollups")).toHaveLength(2);
    });

    it(`resets an eligible observation after a ${state} rollup`, async () => {
      const reader = fakeReader({
        fastPath: emptyChecks,
        observe: (_context, read) => ({
          commitRollups: [{ oid: "head", state: read === 2 ? state : null }],
        }),
      });
      const run = noChecksRun(reader);
      expect(await run.simple()).toMatchObject({ kind: "READY" });
      expect(run.events.map((event) => event.kind)).toEqual(["RETRY", "RETRY", "RETRY"]);
      expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(4);
    });
  }

  it("confirms two explicit same-head null rollups", async () => {
    const reader = fakeReader({
      fastPath: emptyChecks,
      facts: { headRefOid: "A" },
      commitRollups: [{ oid: "older", state: "SUCCESS" }, { oid: "A", state: null }],
    });
    const run = noChecksRun(reader);
    expect(await run.simple()).toMatchObject({
      kind: "READY",
      scope: { pr: { proof: { ci: {
        source: "no-checks", hadPreviousPassingCi: true,
        github: { headRollupState: null },
      } } } },
    });
    expect(run.events.map((event) => event.kind)).toEqual(["RETRY"]);
    expect(reader.calls.filter((call) => call === "commitRollups")).toHaveLength(2);
  });

  it("rejects a same-poll advanced head and requires two fresh reads of the later head", async () => {
    const reader = fakeReader({
      fastPath: emptyChecks,
      observe: (_context, read) => ({
        facts: { headRefOid: read <= 2 ? "A" : "B" },
        commitRollups: read === 1
          ? [{ oid: "A", state: null }]
          : [{ oid: "A", state: null }, { oid: "B", state: null }],
      }),
    });
    const run = noChecksRun(reader);
    expect(await run.simple()).toMatchObject({ kind: "READY" });
    expect(run.events.map((event) => event.kind)).toEqual(["RETRY", "RETRY", "RETRY"]);
    expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(4);
    expect(reader.calls.filter((call) => call === "commitRollups")).toHaveLength(4);
  });

  const missingHeads: readonly [string, readonly T.CommitRollup[]][] = [
    ["empty history", []],
    ["history without the facts head", [{ oid: "older", state: null }]],
  ];
  for (const [name, commitRollups] of missingHeads) {
    it(`cannot confirm ${name}`, async () => {
      const run = noChecksRun(fakeReader({ fastPath: emptyChecks, commitRollups }), {
        ...noChecksOptions, maxQueryErrors: 2,
      });
      expect(await run.simple()).toMatchObject({
        kind: "BLOCKER", blocker: { kind: "status-query" },
      });
    });

    it(`resets an eligible observation after ${name}`, async () => {
      const reader = fakeReader({
        fastPath: emptyChecks,
        observe: (_context, read) => ({
          commitRollups: read === 2 ? commitRollups : [{ oid: "head", state: null }],
        }),
      });
      const run = noChecksRun(reader);
      expect(await run.simple()).toMatchObject({ kind: "READY" });
      expect(run.events.map((event) => event.kind)).toEqual(["RETRY", "RETRY", "RETRY"]);
      expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(4);
    });
  }

  it("keeps resolveChecks errors unavailable at policy level despite explicit null head evidence", async () => {
    const reader = fakeReader({
      fastPath: { kind: "unusable", exitCode: 1, stderr: "authentication failed" },
      rollupPages: [{ checks: [], endCursor: null }],
      commitRollups: [{ oid: "head", state: null }],
    });
    const run = noChecksRun(reader, { ...noChecksOptions, maxQueryErrors: 2 });
    expect(await run.simple()).toMatchObject({
      kind: "BLOCKER",
      blocker: {
        kind: "status-query", failures: 2,
        failure: { kind: "checks-unavailable", detail: expect.stringContaining("fast path exit=1") },
      },
    });
    expect(run.events.map((event) => event.kind)).toEqual(["RETRY"]);
    expect(reader.calls.filter((call) => call === "pullRequest")).toHaveLength(2);
  });

  it("independently retries queued repositories sharing PR number and head", async () => {
    const first = { owner: "o", repo: "a", number: context.number };
    const second = { ...first, repo: "b" };
    const reads: string[] = [];
    const run = noChecksRun(fakeReader({
      fastPath: emptyChecks,
      commitRollups: [{ oid: "head", state: null }],
      observe: (requested) => {
        reads.push(`${requested.owner}/${requested.repo}#${requested.number}`);
        return {};
      },
    }), { ...noChecksOptions, timeout: 120 });
    expect(await run.queued([first, second])).toMatchObject({ kind: "TIMEOUT" });
    expect(reads).toEqual(["o/a#42", "o/a#42", "o/b#42", "o/b#42"]);
    expect(run.events.filter((event) => event.kind === "RETRY")).toHaveLength(2);
    expect(run.sleeps).toEqual([60, 60]);
  });
});

function noChecksAdapter(args: {
  code: number;
  stdout: string;
  stderr: string;
  nodes?: readonly unknown[];
  operation?: "page";
}) {
  const directory = mkdtempSync(join(tmpdir(), "watch-pr-empty-"));
  try {
    const response = {
      data: { repository: { pullRequest: { commits: { nodes: [{
        commit: { statusCheckRollup: { contexts: {
          nodes: args.nodes ?? [],
          pageInfo: { hasNextPage: false, endCursor: null },
        } } },
      }] } } } },
    };
    writeFileSync(join(directory, "gh"), `#!${process.execPath}
if (process.argv[2] === "pr" && process.argv[3] === "checks") {
  process.stdout.write(${JSON.stringify(args.stdout)});
  process.stderr.write(${JSON.stringify(args.stderr)});
  process.exit(${args.code});
}
if (process.argv[2] !== "api") process.exit(2);
process.stdout.write(${JSON.stringify(JSON.stringify(response))});
`, { mode: 0o755 });
    const program = `import { GhGitHubReader, resolveChecks } from ${JSON.stringify(import.meta.dir + "/github.ts")};
      const reader = new GhGitHubReader();
      const context = ${JSON.stringify(context)};
      try {
        if (${args.operation === "page"}) {
          console.log(JSON.stringify({ ok: true, page: await reader.checkRollupPage(context, null) }));
          process.exit(0);
        }
        const fast = await reader.checksFastPath(context);
        console.log(JSON.stringify({ ok: true, fast, read: await resolveChecks(reader, context) }));
      } catch (error) {
        console.log(JSON.stringify({ ok: false, name: error.name, failure: error.failure }));
      }`;
    const child = spawnSync(process.execPath, ["-e", program], {
      encoding: "utf8", timeout: 4000,
      env: { ...process.env, PATH: directory + ":" + process.env.PATH },
    });
    expect(child.error).toBeUndefined();
    expect(child.status).toBe(0);
    return JSON.parse(child.stdout);
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
}

describe("no-checks transport evidence", () => {
  const diagnostic = "no checks reported on the 'fix/1533-pr-links-real-body' branch\n";
  it("normalizes the captured gh exit-1 diagnostic and explicit JSON emptiness", () => {
    for (const stdout of ["", " \n", "[]"])
      expect(noChecksAdapter({ code: 1, stdout, stderr: diagnostic })).toMatchObject({
        ok: true, fast: { kind: "checks", checks: [] },
        read: { source: "empty", checks: [] },
      });
  });

  it("rejects arbitrary failures rather than treating an empty rollup as proof", () => {
    for (const args of [
      { code: 1, stdout: "", stderr: "authentication failed" },
      { code: 1, stdout: "", stderr: "" },
      { code: 8, stdout: "", stderr: diagnostic },
      { code: 0, stdout: "", stderr: diagnostic },
      { code: 1, stdout: "not JSON", stderr: diagnostic },
      { code: 1, stdout: "", stderr: diagnostic + "authentication failed\n" },
    ])
      expect(noChecksAdapter(args)).toMatchObject({
        ok: false, failure: { kind: "checks-unavailable" },
      });
  });

  it("still uses nonempty GraphQL fallback after explicit emptiness or CLI errors", () => {
    for (const stderr of [diagnostic, "authentication failed"])
      expect(noChecksAdapter({
        code: 1, stdout: "", stderr,
        nodes: [{ __typename: "StatusContext", context: "ci", state: "PENDING" }],
      })).toMatchObject({
        ok: true, read: { source: "graphql-rollup", checks: [{ kind: "pending" }] },
      });
  });

  it("rejects unknown raw rollup nodes instead of claiming empty checks", () => {
    expect(noChecksAdapter({
      code: 1, stdout: "[]", stderr: "",
      nodes: [{ __typename: "FutureNode" }],
      operation: "page",
    })).toMatchObject({ ok: false });
    expect(mapRollupNode({ __typename: "FutureNode" })).toBeNull();
  });
});

describe("checks fallback chain", () => {
  it("uses a non-empty fast-path result without a rollup query", async () => {
    const reader = fakeReader({
      fastPath: { kind: "checks", checks: [passingCheck("fast")] },
    });
    const read = await resolveChecks(reader, context);
    expect(read.source).toBe("gh-pr-checks");
    expect(read.checks.map((check) => check.name)).toEqual(["fast"]);
    expect(reader.calls).toEqual(["checksFastPath"]);
  });

  it("paginates GraphQL when the fast path is unusable", async () => {
    const reader = fakeReader({
      fastPath: { kind: "unusable", exitCode: 8, stderr: "" },
      rollupPages: [
        { checks: [passingCheck("first")], endCursor: "next" },
        { checks: [failedCheck("second")], endCursor: null },
      ],
    });
    const read = await resolveChecks(reader, context);
    expect(read.source).toBe("graphql-rollup");
    expect(read.checks.map((check) => check.name)).toEqual(["first", "second"]);
    expect(reader.calls).toEqual([
      "checksFastPath",
      "checkRollupPage:null",
      "checkRollupPage:next",
    ]);
  });

  it("falls back when valid fast-path JSON represented an empty list", async () => {
    const reader = fakeReader({
      fastPath: { kind: "checks", checks: [] },
      rollupPages: [{ checks: [pendingCheck("fallback")], endCursor: null }],
    });
    expect((await resolveChecks(reader, context)).checks.map((check) => check.name))
      .toEqual(["fallback"]);
    expect(reader.calls).toEqual(["checksFastPath", "checkRollupPage:null"]);
  });

  it("fails closed when both paths are empty", async () => {
    const reader = fakeReader({
      fastPath: {
        kind: "unusable",
        exitCode: 8,
        stderr: "credential cannot read checks",
      },
    });
    await expect(resolveChecks(reader, context)).rejects.toBeInstanceOf(
      ChecksUnavailable
    );
    expect(reader.calls).toEqual(["checksFastPath", "checkRollupPage:null"]);
  });
});

describe("rollup node mapping", () => {
  it("maps terminal and non-terminal CheckRun states fail closed", () => {
    const cases = [
      ["IN_PROGRESS", null, "pending", "PENDING"],
      ["COMPLETED", "SUCCESS", "passed", "SUCCESS"],
      ["COMPLETED", "NEUTRAL", "skipped", "NEUTRAL"],
      ["COMPLETED", "SKIPPED", "skipped", "SKIPPED"],
      ["COMPLETED", "ACTION_REQUIRED", "failed", "ACTION_REQUIRED"],
      ["COMPLETED", "TIMED_OUT", "failed", "FAILURE"],
      ["COMPLETED", "FUTURE_VALUE", "failed", "FAILURE"],
    ] as const;
    for (const [status, conclusion, kind, reportedState] of cases) {
      expect(
        mapRollupNode({
          __typename: "CheckRun",
          name: "ci",
          status,
          conclusion,
        })
      ).toMatchObject({ kind, reportedState });
    }
  });

  it("classifies an in-progress Code Review Gate from the rollup as the gate", () => {
    expect(
      mapRollupNode({
        __typename: "CheckRun",
        name: "Code Review Gate",
        status: "IN_PROGRESS",
        conclusion: null,
      })
    ).toMatchObject({ kind: "code-review-gate" });
    expect(
      mapRollupNode({
        __typename: "StatusContext",
        context: "Code Review Gate",
        state: "PENDING",
      })
    ).toMatchObject({ kind: "code-review-gate" });
  });

  it("classifies a Code Review Gate waiting on an owner approval as the gate", () => {
    expect(
      mapRollupNode({
        __typename: "CheckRun",
        name: "Code Review Gate",
        status: "COMPLETED",
        conclusion: "ACTION_REQUIRED",
        description: "1 of 2 policies",
      })
    ).toMatchObject({
      kind: "code-review-gate",
      reportedState: "ACTION_REQUIRED",
    });
  });

  it("classifies a fast-path Code Review Gate waiting on an owner approval as the gate", () => {
    expect(
      parseFastCheck({
        name: "Code Review Gate",
        state: "ACTION_REQUIRED",
        bucket: "fail",
      })
    ).toMatchObject({
      kind: "code-review-gate",
      reportedState: "ACTION_REQUIRED",
    });
    expect(
      parseFastCheck({ name: "ci", state: "ACTION_REQUIRED", bucket: "fail" })
    ).toMatchObject({ kind: "failed", reportedState: "ACTION_REQUIRED" });
  });

  it("maps StatusContext states and drops unknown typenames", () => {
    expect(
      mapRollupNode({
        __typename: "StatusContext",
        context: "ci",
        state: "EXPECTED",
      })
    ).toMatchObject({ kind: "pending", reportedState: "PENDING" });
    expect(
      mapRollupNode({
        __typename: "StatusContext",
        context: "ci",
        state: "FUTURE_VALUE",
      })
    ).toMatchObject({ kind: "failed", reportedState: "FUTURE_VALUE" });
    expect(mapRollupNode({ __typename: "FutureNode" })).toBeNull();
  });
});

describe("closed enum parsing", () => {
  const rawPullRequest = {
    mergeable: "MERGEABLE",
    mergeStateStatus: "CLEAN",
    reviewDecision: "APPROVED",
    headRefOid: "head",
    headRefName: "feature",
    baseRefName: "main",
    state: "OPEN",
    mergedAt: null,
    isDraft: false,
  };

  it("accepts mergeStateStatus CONFLICTING", () => {
    expect(
      parsePullRequest(
        { ...rawPullRequest, mergeStateStatus: "CONFLICTING" },
        context
      ).mergeStateStatus
    ).toBe("CONFLICTING");
  });

  it("reads gh's empty reviewDecision as no decision rather than a parse failure", () => {
    expect(
      parsePullRequest({ ...rawPullRequest, reviewDecision: "" }, context)
        .reviewDecision
    ).toBeNull();
  });

  it("still rejects an unknown reviewDecision", () => {
    expect(() =>
      parsePullRequest({ ...rawPullRequest, reviewDecision: "MAYBE" }, context)
    ).toThrow(WatcherQueryError);
  });

  it("rejects unknown enum values as retryable errors carrying the raw value", () => {
    try {
      parsePullRequest(
        { ...rawPullRequest, mergeStateStatus: "FUTURE_STATE" },
        context
      );
      throw new Error("expected parser to throw");
    } catch (error) {
      expect(error).toBeInstanceOf(WatcherQueryError);
      if (!(error instanceof WatcherQueryError)) throw error;
      expect(error.failure).toMatchObject({
        kind: "missing-key",
        retryable: true,
        rawValue: '"FUTURE_STATE"',
      });
    }
  });
});

it("annotates Bugbot threads with distinct review-pass counts", () => {
  const response = {
    data: {
      repository: {
        pullRequest: {
          reviewThreads: {
            pageInfo: { hasNextPage: false, endCursor: null },
            nodes: [
              {
                id: "one",
                isResolved: false,
                comments: {
                  nodes: [
                    {
                      body: "RUN_ID: run-1",
                      createdAt: "now",
                      path: "a.ts",
                      line: 1,
                      author: { login: "bugbot" },
                    },
                  ],
                },
              },
              {
                id: "two",
                isResolved: false,
                comments: {
                  nodes: [
                    {
                      body: "CURSOR_AUTOMATION_ID: run-2 severity high",
                      createdAt: "now",
                      path: null,
                      line: null,
                      author: { login: "cursor" },
                    },
                  ],
                },
              },
              {
                id: "resolved",
                isResolved: true,
                comments: {
                  nodes: [
                    {
                      body: "RUN_ID: run-3",
                      createdAt: "now",
                      path: null,
                      line: null,
                      author: { login: "bugbot" },
                    },
                  ],
                },
              },
            ],
          },
        },
      },
    },
  };
  const threads = buildReviewThreads(parseReviewThreadPage(response).threads);
  expect(threads).toHaveLength(2);
  expect(threads.map((thread) => thread.isBugbot)).toEqual([true, true]);
  expect(threads.map((thread) => thread.bugbotReviewPasses)).toEqual([3, 3]);
});

describe("review thread pagination", () => {
  const thread = (id: string, resolved = false) => ({
    id,
    firstComment: {
      authorLogin: "someone",
      body: "please fix",
      path: "a.ts",
      line: 1,
      createdAt: "now",
    },
    resolved,
  });

  it("keeps walking pages until the cursor is exhausted", async () => {
    const reader = fakeReader({
      threadPages: [
        { threads: [thread("one")], endCursor: "next" },
        { threads: [thread("two")], endCursor: "last" },
        { threads: [thread("three")], endCursor: null },
      ],
    });
    const threads = await resolveReviewThreads(reader, context);
    expect(threads.map((item) => item.id)).toEqual(["one", "two", "three"]);
    expect(reader.calls).toEqual([
      "reviewThreadPage:null",
      "reviewThreadPage:next",
      "reviewThreadPage:last",
    ]);
  });

  it("sees an unresolved thread that sits past the first page", async () => {
    const reader = fakeReader({
      threadPages: [
        { threads: [thread("early", true)], endCursor: "next" },
        { threads: [thread("late")], endCursor: null },
      ],
    });
    const threads = await resolveReviewThreads(reader, context);
    expect(threads.map((item) => item.id)).toEqual(["late"]);
  });

  it("stops after a single page when the cursor is exhausted", async () => {
    const reader = fakeReader({
      threadPages: [{ threads: [thread("only")], endCursor: null }],
    });
    expect((await resolveReviewThreads(reader, context)).length).toBe(1);
    expect(reader.calls).toEqual(["reviewThreadPage:null"]);
  });

  it("counts Bugbot review passes across every page", async () => {
    const bugbot = (id: string, runId: string) => ({
      id,
      firstComment: {
        authorLogin: "bugbot",
        body: `RUN_ID: ${runId}`,
        path: "a.ts",
        line: 1,
        createdAt: "now",
      },
      resolved: false,
    });
    const reader = fakeReader({
      threadPages: [
        { threads: [bugbot("one", "run-1")], endCursor: "next" },
        { threads: [bugbot("two", "run-2")], endCursor: null },
      ],
    });
    const threads = await resolveReviewThreads(reader, context);
    expect(threads.map((item) => item.bugbotReviewPasses)).toEqual([2, 2]);
  });

  it("drops resolved threads from later pages too", async () => {
    const reader = fakeReader({
      threadPages: [
        { threads: [thread("one")], endCursor: "next" },
        { threads: [thread("two", true)], endCursor: null },
      ],
    });
    expect(
      (await resolveReviewThreads(reader, context)).map((item) => item.id)
    ).toEqual(["one"]);
  });

  it("rejects a page that omits pageInfo instead of assuming one page", async () => {
    const response = {
      data: {
        repository: {
          pullRequest: { reviewThreads: { nodes: [] } },
        },
      },
    };
    expect(() => parseReviewThreadPage(response)).toThrow(WatcherQueryError);
  });
});

describe("context and stack discovery", () => {
  it("returns a fully explicit context without any reader call", async () => {
    const reader = fakeReader();
    expect(
      await resolveContext({
        reader,
        owner: "explicit",
        repo: "repo",
        pr: context.number,
      })
    ).toEqual({ owner: "explicit", repo: "repo", number: context.number });
    expect(reader.calls).toEqual([]);
  });

  it("uses the local origin before currentPr for an explicit number", async () => {
    const reader = fakeReader({ origin: { owner: "local", repo: "checkout" } });
    expect(
      await resolveContext({
        reader,
        owner: null,
        repo: null,
        pr: context.number,
      })
    ).toEqual({ owner: "local", repo: "checkout", number: context.number });
    expect(reader.calls).toEqual(["originRepo"]);
  });

  it("orders the connected stack bottom-to-top", () => {
    const ordered = orderStack(context, [
      {
        number: parsePrNumber(41),
        headRefName: "base-feature",
        isCrossRepository: false,
        baseRefName: "main",
      },
      {
        number: context.number,
        headRefName: "feature",
        isCrossRepository: false,
        baseRefName: "base-feature",
      },
      {
        number: parsePrNumber(43),
        headRefName: "upstack",
        isCrossRepository: false,
        baseRefName: "feature",
      },
    ]);
    expect(ordered.map((item) => Number(item.number))).toEqual([41, 42, 43]);
  });
  it("does not use a fork's same-named head as a stack parent", () => {
    const ordered = orderStack(context, [
      { number: parsePrNumber(41), headRefName: "base-feature", baseRefName: "main", isCrossRepository: true },
      { number: context.number, headRefName: "feature", baseRefName: "base-feature", isCrossRepository: false },
    ]);
    expect(ordered.map((item) => Number(item.number))).toEqual([42]);
  });

  it("does not attach upstream branch children to a fork head", () => {
    const ordered = orderStack(context, [
      { number: context.number, headRefName: "feature", baseRefName: "main", isCrossRepository: true },
      { number: parsePrNumber(43), headRefName: "upstack", baseRefName: "feature", isCrossRepository: false },
    ]);
    expect(ordered.map((item) => Number(item.number))).toEqual([42]);
  });

  it("terminates when an unrelated fork opens main against main", () => {
    // Bound the subprocess so this regression reports a failure instead of hanging the suite.
    const program = `import { orderStack } from ${JSON.stringify(import.meta.dir + "/github.ts")};
      console.log(JSON.stringify(orderStack(${JSON.stringify(context)}, [
        { number: 41, headRefName: "main", baseRefName: "main", isCrossRepository: true },
        { number: 42, headRefName: "feature", baseRefName: "main", isCrossRepository: false }
      ])));`;
    const child = spawnSync(process.execPath, ["-e", program], { encoding: "utf8", timeout: 2000 });
    expect(child.error).toBeUndefined();
    expect(child.status).toBe(0);
    expect(JSON.parse(child.stdout).map((item: { number: number }) => item.number)).toEqual([42]);
  });

  it("requests and parses fork identity from gh before stack discovery", () => {
    const directory = mkdtempSync(join(tmpdir(), "watch-pr-fork-"));
    try {
      writeFileSync(join(directory, "gh"), `#!/bin/sh
case "$*" in
  *number,headRefName,baseRefName,isCrossRepository*) ;;
  *) exit 2 ;;
esac
printf '%s\\n' '[{"number":42,"headRefName":"feature","baseRefName":"main","isCrossRepository":true}]'
`, { mode: 0o755 });
      const program = `import { GhGitHubReader } from ${JSON.stringify(import.meta.dir + "/github.ts")};
        console.log(JSON.stringify(await new GhGitHubReader().openPullRequests({ owner: "owner", repo: "repo" })));`;
      const child = spawnSync(process.execPath, ["-e", program], {
        encoding: "utf8", timeout: 2000,
        env: { ...process.env, PATH: directory + ":" + process.env.PATH },
      });
      expect(child.error).toBeUndefined();
      expect(child.status).toBe(0);
      expect(JSON.parse(child.stdout)).toEqual([
        { number: 42, headRefName: "feature", baseRefName: "main", isCrossRepository: true },
      ]);
    } finally {
      rmSync(directory, { recursive: true, force: true });
    }
  });

});
