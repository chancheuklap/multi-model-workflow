import { execFileSync, spawnSync } from "node:child_process";
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
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

const registryFile = join(root, "registry.json");
writeFileSync(
	registryFile,
	JSON.stringify({
		home: { name: "home", path: homeRepo, remote: "git@github.com:owner/home.git", integration: "main" },
		repos: [{ name: "other", path: registeredRepo, remote: "https://github.com/owner/other.git", integration: "main" }],
	}),
);

type Decision =
	| { decision: "allow" }
	| { decision: "deny"; reason: string; fix: string }
	| { decision: "context"; text: string };

const decide = (stdin: string): Decision => {
	const result = spawnSync("node", [checker], {
		input: stdin,
		encoding: "utf8",
		env: { ...process.env, HOOK_REGISTRY: registryFile },
	});
	expect(result.status).toBe(0);
	expect(result.stdout.endsWith("\n")).toBe(true);
	expect(result.stdout.trimEnd()).not.toContain("\n");
	return JSON.parse(result.stdout);
};

const shell = (command: string, cwd = repo) => decide(JSON.stringify({ harness: "test", kind: "shell", cwd, command }));

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

test("allows a PR that targets a repository the registry does not list", () => {
	for (const flag of ["-R other/repo", "-Rother/repo", "--repo other/repo", "--repo=other/repo", "--repo $REPO"]) {
		expect(shell(`gh pr create ${flag} --body "no link"`).decision).toBe("allow");
	}
});

test("checks a PR that targets a registered repository", () => {
	for (const flag of ["-R owner/other", "-Rowner/other", "--repo owner/other", "--repo=owner/other", "--repo Owner/Other"]) {
		expect(shell(`gh pr create ${flag} --base main --body "no link"`).decision).toBe("deny");
		expect(shell(`gh pr create ${flag} --base main --body "Closes #1"`).decision).toBe("allow");
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
