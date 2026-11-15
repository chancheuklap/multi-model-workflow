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

type Decision =
	| { decision: "allow" }
	| { decision: "deny"; reason: string; fix: string }
	| { decision: "context"; text: string };

const decide = (stdin: string): Decision => {
	const result = spawnSync("node", [checker], { input: stdin, encoding: "utf8" });
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

test("allows a PR that targets another repository", () => {
	expect(shell('gh pr create -R other/repo --body "no link"').decision).toBe("allow");
	expect(shell('gh pr create --repo other/repo --body "no link"').decision).toBe("allow");
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
