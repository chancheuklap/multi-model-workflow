import type {
  Check,
  ChecksFastPath,
  CommitRollup,
  GitHubReader,
  OpenPullRequest,
  PrContext,
  PullRequestFacts,
  Repository,
  RawReviewThread,
  ReviewThread,
  ReviewThreadPage,
  RollupPage,
} from "./types.ts";
import { parsePrNumber } from "./types.ts";

export interface FakeReaderOptions {
  readonly facts?: Partial<Omit<PullRequestFacts, "context">>;
  readonly fastPath?: ChecksFastPath;
  readonly rollupPages?: readonly RollupPage[];
  readonly threads?: readonly ReviewThread[];
  readonly threadPages?: readonly ReviewThreadPage[];
  readonly commitRollups?: readonly CommitRollup[] | Error;
  readonly observe?: (context: PrContext, read: number) => FakeReaderOptions;
  readonly openPullRequests?: readonly OpenPullRequest[];
  readonly origin?: Repository | null;
  readonly current?: PrContext;
}

function toRawThread(thread: ReviewThread): RawReviewThread {
  return { id: thread.id, firstComment: thread.firstComment, resolved: false };
}

export function passingCheck(name = "ci"): Check {
  return {
    kind: "passed",
    name,
    reportedState: "SUCCESS",
    description: "",
    link: "",
    workflow: "",
  };
}

export function pendingCheck(name = "ci"): Check {
  return {
    kind: "pending",
    name,
    reportedState: "PENDING",
    description: "",
    link: "",
    workflow: "",
  };
}

export function failedCheck(name = "ci"): Check {
  return {
    kind: "failed",
    name,
    reportedState: "FAILURE",
    description: "",
    link: "",
    workflow: "",
  };
}

export function fakeReader(
  options: FakeReaderOptions = {}
): GitHubReader & { readonly calls: readonly string[] } {
  const calls: string[] = [];
  const context = options.current ?? {
    owner: "owner",
    repo: "repo",
    number: parsePrNumber(1),
  };
  const defaults: PullRequestFacts = {
    context,
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
  let page = 0;
  let threadPage = 0;
  const reads = new Map<string, number>();
  const observations = new Map<string, FakeReaderOptions>();
  const key = (requested: PrContext) =>
    JSON.stringify([requested.owner, requested.repo, requested.number]);
  const observation = (requested: PrContext) =>
    observations.get(key(requested)) ?? options;
  return {
    calls,
    async originRepo() {
      calls.push("originRepo");
      return options.origin === undefined
        ? { owner: "owner", repo: "repo" }
        : options.origin;
    },
    async currentPr(pr) {
      calls.push("currentPr");
      return { ...context, number: pr ?? context.number };
    },
    async pullRequest(requested) {
      calls.push("pullRequest");
      const identity = key(requested);
      const read = (reads.get(identity) ?? 0) + 1;
      reads.set(identity, read);
      const current = { ...options, ...options.observe?.(requested, read) };
      observations.set(identity, current);
      return { ...defaults, ...current.facts, context: requested };
    },
    async openPullRequests() {
      calls.push("openPullRequests");
      return options.openPullRequests ?? [];
    },
    async checksFastPath(requested) {
      calls.push("checksFastPath");
      return observation(requested).fastPath ?? {
        kind: "checks",
        checks: [passingCheck()],
      };
    },
    async checkRollupPage(requested, after) {
      calls.push(`checkRollupPage:${after ?? "null"}`);
      return observation(requested).rollupPages?.[page++] ?? {
        checks: [],
        endCursor: null,
      };
    },
    async reviewThreadPage(requested, after) {
      calls.push(`reviewThreadPage:${after ?? "null"}`);
      const current = observation(requested);
      return current.threadPages?.[threadPage++] ?? {
        threads: (current.threads ?? []).map(toRawThread),
        endCursor: null,
      };
    },
    async commitRollups(requested) {
      calls.push("commitRollups");
      const rollups = observation(requested).commitRollups;
      if (rollups instanceof Error) throw rollups;
      return rollups ?? [{ oid: "head", state: "SUCCESS" }];
    },
  };
}
