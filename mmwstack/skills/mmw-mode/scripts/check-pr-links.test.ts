import { execFileSync, spawnSync } from "node:child_process";
import { chmodSync, existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterAll, expect, test } from "bun:test";

const checker = join(import.meta.dir, "check-pr-links.mjs");

const root = mkdtempSync(join(tmpdir(), "check-pr-links-test-"));
afterAll(() => rmSync(root, { recursive: true, force: true }));

const repo = join(root, "repo");
execFileSync("git", ["init", "-q", "-b", "main", repo]);
execFileSync("git", ["-C", repo, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main"]);

const plainDirectory = join(root, "plain");
mkdirSync(plainDirectory);

const initRepo = (dir: string, remote: string) => {
	execFileSync("git", ["init", "-q", "-b", "main", dir]);
	execFileSync("git", ["-C", dir, "symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main"]);
	execFileSync("git", ["-C", dir, "remote", "add", "origin", remote]);
};

const registeredRepo = join(root, "registered");
initRepo(registeredRepo, "https://github.com/owner/other.git");

// The home repository is registered too; its entry exercises the ssh remote form.
const homeRepo = join(root, "home");
initRepo(homeRepo, "git@github.com:owner/home.git");

// The checked-out branch carries ticket 7 and the remote is the repository the command targets.
const ticketedRepo = join(root, "ticketed");
initRepo(ticketedRepo, "git@github.com:owner/ticketed.git");
execFileSync("git", ["-C", ticketedRepo, "symbolic-ref", "HEAD", "refs/heads/feat/7-x"]);

// The registry writes some paths as `~/...`; the checker runs with HOME set to the fixture root so they resolve here.
const tildeRepo = join(root, "tilde-repo");
initRepo(tildeRepo, "https://github.com/owner/tilde.git");

const registry = {
	home: { name: "home", path: homeRepo, remote: "git@github.com:owner/home.git", integration: "main" },
	repos: [
		{ name: "other", path: registeredRepo, remote: "https://github.com/owner/other.git", integration: "main" },
		{ name: "tilde", path: "~/tilde-repo", remote: "https://github.com/owner/tilde.git", integration: "main" },
	],
};
const registryFile = join(root, "registry.json");
writeFileSync(registryFile, JSON.stringify(registry));
mkdirSync(join(root, ".agents", "repos"), { recursive: true });
writeFileSync(join(root, ".agents", "repos", "registry.json"), JSON.stringify(registry));

// A stand-in for `gh` that logs its arguments and prints the reply file of the directory FAKE_GH_DIR names,
// after the seconds its `delay` file holds. Without a reply file it fails, as `gh` does when the PR cannot be read.
const fakeBin = join(root, "bin");
mkdirSync(fakeBin);
writeFileSync(
	join(fakeBin, "gh"),
	'#!/bin/sh\necho "$*" >> "$FAKE_GH_DIR/calls"\n[ -f "$FAKE_GH_DIR/delay" ] && sleep "$(cat "$FAKE_GH_DIR/delay")"\n[ -f "$FAKE_GH_DIR/reply.json" ] || exit 1\ncat "$FAKE_GH_DIR/reply.json"\n',
);
chmodSync(join(fakeBin, "gh"), 0o755);

type PullRequestReply = { body: string; baseRefName: string; headRefName: string };

const fakeGh = (reply?: PullRequestReply) => {
	const dir = mkdtempSync(join(root, "gh-"));
	if (reply) writeFileSync(join(dir, "reply.json"), JSON.stringify(reply));
	const calls = () => (existsSync(join(dir, "calls")) ? readFileSync(join(dir, "calls"), "utf8").trim().split("\n") : []);
	return { dir, calls };
};

type Decision =
	| { decision: "allow" }
	| { decision: "deny"; reason: string; fix: string }
	| { decision: "context"; text: string };

type Env = Record<string, string | undefined>;

const decide = (stdin: string, gh = fakeGh(), env: Env = {}): Decision => {
	const result = spawnSync("node", [checker], {
		input: stdin,
		encoding: "utf8",
		env: { ...process.env, HOME: root, HOOK_REGISTRY: registryFile, PATH: `${fakeBin}:${process.env.PATH}`, FAKE_GH_DIR: gh.dir, ...env },
	});
	expect(result.status).toBe(0);
	expect(result.stdout.endsWith("\n")).toBe(true);
	expect(result.stdout.trimEnd()).not.toContain("\n");
	return JSON.parse(result.stdout);
};

const shell = (command: string, cwd = repo, phase?: "before" | "after", gh?: ReturnType<typeof fakeGh>) =>
	decide(JSON.stringify({ harness: "test", kind: "shell", cwd, command, phase }), gh);

const heredoc = (text: string) => `gh pr create --title t --body "$(cat <<'EOF'\n${text}\nEOF\n)"`;

test("allows a body that closes an issue", () => {
	expect(shell('gh pr create --title t --body "Closes #12"').decision).toBe("allow");
});

test("accepts each closing keyword form", () => {
	for (const body of ["fixes owner/repo#3", "closes #12", "Closes: #5", "Resolved #7"]) {
		expect(shell(`gh pr create --title t --body "${body}"`).decision).toBe("allow");
	}
});

test("denies a body with no closing keyword when the PR merges into the default branch", () => {
	const result = shell('gh pr create --title t --body "no link"');
	expect(result.decision).toBe("deny");
	if (result.decision !== "deny") return;
	expect(result.reason).toContain("`main`");
	expect(result.fix).toContain("Closes #<issue>");
});

test("allows a PR whose base is not the default branch", () => {
	expect(shell('gh pr create --base project/x --body "no link"').decision).toBe("allow");
});

test("denies when the base is the default branch, however it is written", () => {
	expect(shell('gh pr create -B main -b "no link"').decision).toBe("deny");
	expect(shell('gh pr create --base=main --body "no link"').decision).toBe("deny");
});

test("reads the body from a file", () => {
	writeFileSync(join(repo, "linked.md"), "Closes #1\n");
	writeFileSync(join(repo, "unlinked.md"), "no link\n");
	expect(shell("gh pr create --body-file linked.md").decision).toBe("allow");
	expect(shell("gh pr create --body-file unlinked.md").decision).toBe("deny");
	expect(shell("gh pr create -F unlinked.md").decision).toBe("deny");
});

test("allows when the body file is missing or is standard input", () => {
	writeFileSync(join(repo, "-"), "no link\n");
	expect(shell("gh pr create --body-file missing.md").decision).toBe("allow");
	expect(shell("gh pr create -F -").decision).toBe("allow");
});

test("reads the body from a heredoc", () => {
	expect(shell(heredoc("Closes #1")).decision).toBe("allow");
	expect(shell(heredoc("no link")).decision).toBe("deny");
});

test("allows a body whose text is computed by the shell", () => {
	for (const body of ['"$(cat notes.md)"', '"$BODY"', '"Closes #$ISSUE"']) {
		expect(shell(`gh pr create --body ${body}`).decision).toBe("allow");
	}
});

test("resolves the default branch in the directory the command changes into", () => {
	const command = `cd ${repo} && gh pr create --body "no link"`;
	expect(shell(command, plainDirectory).decision).toBe("deny");
});

test("checks an Origin pr create command", () => {
	expect(shell('origin pr create --base main --body "no link"').decision).toBe("deny");
});

test("finds the invocation after each shell separator", () => {
	for (const prefix of ["git push && ", "false || ", "true; ", "echo x | ", "echo x\n", "(", "cd . && "]) {
		expect(shell(`${prefix}gh pr create --body "no link"`).decision).toBe("deny");
	}
});

test("allows when the final body is not the body argument", () => {
	for (const flags of ["--fill", "--web", "--fill-first --body 'no link'", "--editor --body 'no link'", "--fill --body 'no link'"]) {
		expect(shell(`gh pr create ${flags}`).decision).toBe("allow");
	}
});

test("reads registry paths written with a leading ~", () => {
	expect(shell('gh pr create --repo owner/tilde --body "no link"', plainDirectory).decision).toBe("deny");
});

test("reads ~/.agents/repos/registry.json when HOOK_REGISTRY is not set", () => {
	const event = JSON.stringify({ harness: "test", kind: "shell", cwd: repo, command: 'gh pr create --repo owner/other --body "no link"' });
	expect(decide(event, fakeGh(), { HOOK_REGISTRY: undefined }).decision).toBe("deny");
});

test("allows a PR that targets another repository when the registry cannot be read", () => {
	const event = JSON.stringify({ harness: "test", kind: "shell", cwd: repo, command: 'gh pr create --repo owner/other --body "no link"' });
	expect(decide(event, fakeGh(), { HOOK_REGISTRY: join(root, "missing.json") }).decision).toBe("allow");
});

test("allows a PR that targets a repository the registry does not list", () => {
	for (const flag of ["-R other/repo", "-Rother/repo", "--repo other/repo", "--repo=other/repo", "--repo $REPO"]) {
		expect(shell(`gh pr create ${flag} --body "no link"`).decision).toBe("allow");
	}
});

test("checks a PR that targets a registered repository, however the flag is written", () => {
	for (const flag of ["-R owner/other", "-Rowner/other", "--repo owner/other", "--repo=owner/other", "--repo Owner/Other"]) {
		expect(shell(`gh pr create ${flag} --base main --body "no link"`, plainDirectory).decision).toBe("deny");
		expect(shell(`gh pr create ${flag} --base main --body "Closes #1"`, plainDirectory).decision).toBe("allow");
	}
});

test("reads the default branch of the registered repository, not of the directory the command runs in", () => {
	expect(shell('gh pr create --repo owner/other --body "no link"', plainDirectory).decision).toBe("deny");
});

test("allows a PR into a registered repository when its base is not the default branch", () => {
	expect(shell('gh pr create --repo owner/other --base project/x --body "no link"').decision).toBe("allow");
	expect(shell('gh pr create --repo=owner/other --base=project/x --body "no link"').decision).toBe("allow");
});

test("reads a body file for a registered repository from the directory the command runs in", () => {
	writeFileSync(join(repo, "other-linked.md"), "Closes #1\n");
	writeFileSync(join(repo, "other-unlinked.md"), "no link\n");
	expect(shell("gh pr create --repo owner/other --body-file other-linked.md").decision).toBe("allow");
	expect(shell("gh pr create --repo owner/other --body-file other-unlinked.md").decision).toBe("deny");
});

test("takes the ticket from the head branch the command names", () => {
	const named = (head: string, body: string) => shell(`gh pr create --repo owner/other --head ${head} --body "${body}"`);
	expect(named("feat/7-x", "Closes #7").decision).toBe("allow");
	expect(named("feat/7-x", "Closes #8").decision).toBe("deny");
	expect(named("someone:feat/7-x", "Closes #8").decision).toBe("deny");
	expect(named("project/x", "Closes #8").decision).toBe("allow");
});

test("takes the ticket from the current branch and requires that ticket to be named", () => {
	const create = (body: string) => shell(`gh pr create --body "${body}"`, ticketedRepo);
	expect(create("Closes #7").decision).toBe("allow");
	expect(create("Fixes: #7 and Closes #8").decision).toBe("allow");
	expect(create("Closes owner/ticketed#7").decision).toBe("allow");
	expect(create("Closes #8").decision).toBe("deny");
	expect(create("no link").decision).toBe("deny");
	expect(create("mentions #7").decision).toBe("deny");
});

test("denies a body that closes only another ticket, and says so", () => {
	const result = shell('gh pr create --body "Closes #8"', ticketedRepo);
	expect(result.decision).toBe("deny");
	if (result.decision !== "deny") return;
	expect(result.reason).toContain("names a different ticket");
	expect(result.reason).toContain("`main`");
	expect(result.reason).toContain("#7");
	expect(result.fix).toContain("`Closes #7`");
	expect(result.fix).toContain("without asking the owner");
	expect(result.fix).not.toContain("\n");
});

test("names the branch ticket when the body links nothing", () => {
	const result = shell('gh pr create --body "no link"', ticketedRepo);
	expect(result.decision).toBe("deny");
	if (result.decision !== "deny") return;
	expect(result.reason).toContain("`main`");
	expect(result.reason).toContain("#7");
	expect(result.fix).toContain("`Closes #7`");
});

test("allows a full-name reference to another registered repository for the branch ticket", () => {
	for (const body of ["owner/other#7", "Delivers owner/other#7", "Closes owner/other#7", "Part of Owner/Home#7"]) {
		expect(shell(`gh pr create --body "${body}"`, ticketedRepo).decision).toBe("allow");
	}
});

test("denies a full-name reference that is not a registered repository or not the branch ticket", () => {
	for (const body of ["nobody/else#7", "Closes nobody/else#7", "owner/other#8", "owner/ticketed#7"]) {
		expect(shell(`gh pr create --body "${body}"`, ticketedRepo).decision).toBe("deny");
	}
});

test("ignores the command text inside quotes and heredocs", () => {
	expect(shell('echo "gh pr create --body x"').decision).toBe("allow");
	expect(shell('git commit -m "gh pr create"').decision).toBe("allow");
	expect(shell("cat <<'EOF'\ngh pr create --body x\nEOF").decision).toBe("allow");
});

test("allows commands that do not create a PR", () => {
	expect(shell("gh pr view 1").decision).toBe("allow");
});

test("allows events that are not a shell command", () => {
	const write = { harness: "test", kind: "write", cwd: repo, paths: ["a.md"], command: 'gh pr create --body "no link"' };
	expect(decide(JSON.stringify(write)).decision).toBe("allow");
	const withoutCommand = { harness: "test", kind: "shell", cwd: repo };
	expect(decide(JSON.stringify(withoutCommand)).decision).toBe("allow");
});

test("allows input that is not JSON", () => {
	expect(decide("not json").decision).toBe("allow");
	expect(decide("").decision).toBe("allow");
});

test("allows when the default branch cannot be found", () => {
	expect(shell('gh pr create --body "no link"', plainDirectory).decision).toBe("allow");
});

test("allows a command it cannot parse", () => {
	expect(shell('gh pr create --body "no link').decision).toBe("allow");
});

const written = (file: string, text: string) => `cat > ${file} <<'EOF'\n${text}\nEOF\ngh pr create --body-file ${file}`;

test("allows before and denies after when the command writes its own body file", () => {
	const file = join(repo, "late.md");
	rmSync(file, { force: true });
	const command = written("late.md", "no link");
	const before = fakeGh({ body: "no link", baseRefName: "main", headRefName: "main" });
	expect(shell(command, repo, "before", before).decision).toBe("allow");
	expect(before.calls()).toEqual([]);
	expect(shell(command, repo, "after", before).decision).toBe("deny");
	writeFileSync(file, "Closes #1\n");
	expect(shell(command, repo, "after", before).decision).toBe("deny");
	expect(shell(command, repo, "after", fakeGh({ body: "Closes #1", baseRefName: "main", headRefName: "main" })).decision).toBe("allow");
});

test("treats an event without a phase, or with an unknown one, as before", () => {
	const file = join(repo, "phaseless.md");
	rmSync(file, { force: true });
	const event = { harness: "test", kind: "shell", cwd: repo, command: written("phaseless.md", "no link") };
	const replying = () => fakeGh({ body: "no link", baseRefName: "main", headRefName: "main" });
	expect(decide(JSON.stringify(event), replying()).decision).toBe("allow");
	expect(decide(JSON.stringify({ ...event, phase: "unknown" }), replying()).decision).toBe("allow");
	expect(decide(JSON.stringify({ ...event, phase: "after" }), replying()).decision).toBe("deny");
});

test("reads the PR after the command when the command does not carry the body", () => {
	const unlinked = { body: "no link", baseRefName: "main", headRefName: "feat/7-x" };
	for (const flags of ["--fill", "--web", "--editor", '--body "$(cat notes.md)"', "--body-file -"]) {
		const gh = fakeGh(unlinked);
		const result = shell(`gh pr create ${flags}`, ticketedRepo, "after", gh);
		expect(result.decision).toBe("deny");
		if (result.decision === "deny") expect(result.fix).toContain("gh pr edit feat/7-x --body-file");
		expect(gh.calls()).toEqual(["pr view feat/7-x --json body,baseRefName,headRefName,url"]);
		expect(shell(`gh pr create ${flags}`, ticketedRepo, "after", fakeGh({ ...unlinked, body: "Closes #7" })).decision).toBe("allow");
	}
});

test("does not read the PR before the command runs", () => {
	const gh = fakeGh({ body: "no link", baseRefName: "main", headRefName: "feat/7-x" });
	expect(shell("gh pr create --fill", ticketedRepo, "before", gh).decision).toBe("allow");
	expect(shell('gh pr create --body "$(cat notes.md)"', ticketedRepo, undefined, gh).decision).toBe("allow");
	expect(gh.calls()).toEqual([]);
});

test("reads the PR of a registered repository by its head branch and slug", () => {
	const gh = fakeGh({ body: "no link", baseRefName: "main", headRefName: "feat/7-x" });
	expect(shell("gh pr create --repo owner/other --head feat/7-x --fill", repo, "after", gh).decision).toBe("deny");
	expect(gh.calls()).toEqual(["pr view feat/7-x --repo owner/other --json body,baseRefName,headRefName,url"]);
});

test("keeps the saved PR pending when it cannot be read", () => {
	expect(shell("gh pr create --fill", ticketedRepo, "after").decision).toBe("deny");
});

test("keeps a timed-out read pending", () => {
	const gh = fakeGh({ body: "no link", baseRefName: "main", headRefName: "feat/7-x" });
	writeFileSync(join(gh.dir, "delay"), "4");
	expect(shell("gh pr create --fill", ticketedRepo, "after", gh).decision).toBe("deny");
});

test("allows after the command when the PR it opened does not merge into the default branch", () => {
	const gh = fakeGh({ body: "no link", baseRefName: "feat/parent", headRefName: "feat/7-x" });
	expect(shell("gh pr create --fill", ticketedRepo, "after", gh).decision).toBe("allow");
});

test("judges the saved body even when the command supplied another body", () => {
	const gh = fakeGh({ body: "Closes #7", baseRefName: "main", headRefName: "feat/7-x" });
	expect(shell('gh pr create --body "no link"', ticketedRepo, "after", gh).decision).toBe("allow");
	expect(gh.calls().length).toBe(1);
});

const viewing = (body: string, headRefName = "feat/7-x", baseRefName = "feat/parent") => fakeGh({ body, baseRefName, headRefName });
const VIEW = "--json body,baseRefName,headRefName,url";

test("denies retargeting a PR onto the default branch when its current body does not close the branch ticket", () => {
	const gh = viewing("no link");
	const result = shell("gh pr edit 5 --base main", repo, undefined, gh);
	expect(result.decision).toBe("deny");
	if (result.decision !== "deny") return;
	expect(result.reason).toContain("retargeted onto the default branch `main`");
	expect(result.reason).toContain("#7");
	expect(result.fix).toContain("`Closes #7`");
	expect(result.fix).toContain("without asking the owner");
	expect(result.fix).not.toContain("\n");
	expect(gh.calls()).toEqual([`pr view 5 ${VIEW}`]);
});

test("allows retargeting onto the default branch when the current body closes the branch ticket", () => {
	expect(shell("gh pr edit 5 --base main", repo, undefined, viewing("Closes #7")).decision).toBe("allow");
	expect(shell("gh pr edit 5 -B main", repo, undefined, viewing("Closes #7")).decision).toBe("allow");
	expect(shell("gh pr edit 5 --base=main", repo, undefined, viewing("owner/other#7")).decision).toBe("allow");
});

test("denies retargeting when the current body closes only another ticket", () => {
	const result = shell("gh pr edit 5 --base main", repo, undefined, viewing("Closes #8"));
	expect(result.decision).toBe("deny");
	if (result.decision !== "deny") return;
	expect(result.reason).toContain("names a different ticket");
});

test("allows retargeting onto any base that is not the default branch without reading the PR", () => {
	for (const command of ["gh pr edit 5 --base feat/parent", "gh pr edit 5 --title t", "gh pr edit 5 --body 'no link'"]) {
		const gh = viewing("no link");
		expect(shell(command, repo, undefined, gh).decision).toBe("allow");
		expect(gh.calls()).toEqual([]);
	}
});

test("checks the body an edit sets instead of the current body, and still reads the head branch", () => {
	const gh = viewing("Closes #7");
	expect(shell('gh pr edit 5 --base main --body "no link"', repo, undefined, gh).decision).toBe("deny");
	expect(gh.calls()).toEqual([`pr view 5 ${VIEW}`]);
	expect(shell('gh pr edit 5 --base main --body "Closes #7"', repo, undefined, viewing("no link")).decision).toBe("allow");
});

test("reads the body file an edit sets from the directory the command runs in", () => {
	writeFileSync(join(repo, "edit-linked.md"), "Closes #7\n");
	writeFileSync(join(repo, "edit-unlinked.md"), "no link\n");
	expect(shell("gh pr edit 5 --base main --body-file edit-linked.md", repo, undefined, viewing("no link")).decision).toBe("allow");
	expect(shell("gh pr edit 5 --base main -F edit-unlinked.md", repo, undefined, viewing("Closes #7")).decision).toBe("deny");
});

test("waits for the PR after the command when an edit sets a body it cannot read yet", () => {
	const gh = viewing("no link", "feat/7-x", "main");
	expect(shell("gh pr edit 5 --base main --body-file absent.md", repo, "before", gh).decision).toBe("allow");
	expect(gh.calls()).toEqual([]);
	expect(shell("gh pr edit 5 --base main --body-file absent.md", repo, "after", gh).decision).toBe("deny");
	expect(shell("gh pr edit 5 --base main --body-file absent.md", repo, "after", viewing("Closes #7", "feat/7-x", "main")).decision).toBe("allow");
});

test("reads the PR of a registered repository by its slug when editing", () => {
	const gh = viewing("no link");
	expect(shell("gh pr edit 5 --repo owner/other --base main", plainDirectory, undefined, gh).decision).toBe("deny");
	expect(gh.calls()).toEqual([`pr view 5 --repo owner/other ${VIEW}`]);
});

test("allows editing a PR of an unregistered repository without reading it", () => {
	const gh = viewing("no link");
	expect(shell("gh pr edit 5 --repo other/repo --base main", repo, undefined, gh).decision).toBe("allow");
	expect(gh.calls()).toEqual([]);
});

test("reads the PR of the current branch when the edit names none", () => {
	const gh = viewing("no link");
	expect(shell("gh pr edit --base main", repo, undefined, gh).decision).toBe("deny");
	expect(gh.calls()).toEqual([`pr view ${VIEW}`]);
});

test("allows an edit whose PR the shell chooses or whose PR cannot be read", () => {
	const gh = viewing("no link");
	expect(shell("gh pr edit $PR --base main", repo, undefined, gh).decision).toBe("allow");
	expect(gh.calls()).toEqual([]);
	expect(shell("gh pr edit 5 --base main").decision).toBe("allow");
});

test("allows an edit when the default branch cannot be found", () => {
	expect(shell("gh pr edit 5 --base main", plainDirectory, undefined, viewing("no link")).decision).toBe("allow");
});

test("checks the returned PR even when a create command names another head or base", () => {
	const gh = fakeGh({ body: "Closes #8", baseRefName: "main", headRefName: "feat/7-x" });
	const prUrl = "https://github.com/owner/ticketed/pull/55";
	const result = decide(JSON.stringify({ kind: "shell", command: "gh pr create --head another --base project/x --fill", cwd: ticketedRepo, phase: "after", prUrl }), gh);
	expect(result.decision).toBe("deny");
	expect(gh.calls()[0]).toContain(`pr view ${prUrl} `);
});

test("checks a saved body-only correction, including an Origin write and a native PR tool", () => {
	for (const command of ["gh pr edit 5 --body ok", "origin pr edit 5 --body ok"]) {
		expect(shell(command, repo, "after", viewing("Closes #8", "feat/7-x", "main")).decision).toBe("deny");
		expect(shell(command, repo, "after", viewing("Closes #7", "feat/7-x", "main")).decision).toBe("allow");
	}
	const event = { kind: "pr", cwd: plainDirectory, repo: "owner/other", selector: "5" };
	expect(decide(JSON.stringify(event), viewing("Closes #8", "feat/7-x", "main")).decision).toBe("deny");
	expect(decide(JSON.stringify(event), viewing("Closes #7", "feat/7-x", "main")).decision).toBe("allow");
});

test("keeps both failed PRs from a compound write for independent rechecks", () => {
	const event = { kind: "shell", phase: "after", cwd: repo, command: "gh pr edit 5 --body x && gh pr edit 6 --body y" };
	const result = decide(JSON.stringify(event), viewing("Closes #8", "feat/7-x", "main"));
	expect(result).toMatchObject({ decision: "deny", retries: [{ selector: "5" }, { selector: "6" }] });
});

test("reads the saved PR before merge and allows a non-default base", () => {
	expect(shell("gh pr merge 5 --squash", repo, "before", viewing("Closes #8", "feat/7-x", "main")).decision).toBe("deny");
	expect(shell("origin pr merge 5", repo, "before", viewing("Closes #7", "feat/7-x", "main")).decision).toBe("allow");
	expect(shell("gh pr merge 5", repo, "before", viewing("Refs #7")).decision).toBe("allow");
});
