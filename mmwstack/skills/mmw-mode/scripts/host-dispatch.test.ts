import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";
import { expect, test } from "bun:test";

const repoRoot = resolve(import.meta.dir, "../../../..");
const mmwstackRoot = join(repoRoot, "mmwstack");
const hostDispatchDir = join(mmwstackRoot, "skills/host-dispatch");

function walkMarkdownFiles(dir: string): string[] {
	const results: string[] = [];
	for (const entry of readdirSync(dir, { withFileTypes: true })) {
		if (entry.name === "node_modules" || entry.name === ".git") continue;
		const fullPath = join(dir, entry.name);
		if (entry.isDirectory()) {
			results.push(...walkMarkdownFiles(fullPath));
		} else if (entry.isFile() && entry.name.endsWith(".md")) {
			results.push(fullPath);
		}
	}
	return results;
}

test("host-dispatch has 3-layer progressive skill structure and replaces monolithic reference", () => {
	const skillPath = join(hostDispatchDir, "SKILL.md");
	expect(existsSync(skillPath)).toBe(true);
	const skillText = readFileSync(skillPath, "utf8");
	expect(skillText).toMatch(/^---\r?\n[\s\S]*name:\s*host-dispatch\r?\n[\s\S]*description:\s*"?.+"?\r?\n---/);

	for (const refName of ["agy.md", "agy-lifecycle.md", "droid.md", "native.md"]) {
		const refPath = join(hostDispatchDir, "references", refName);
		expect(existsSync(refPath)).toBe(true);
		expect(readFileSync(refPath, "utf8").trim().length).toBeGreaterThan(0);
	}

	expect(skillText).toContain("references/agy.md");
	expect(skillText).toContain("references/droid.md");
	expect(skillText).toContain("references/native.md");
	expect(existsSync(join(mmwstackRoot, "skills/mmw-mode/references/host-dispatch.md"))).toBe(false);
});

test("references/agy.md documents unified --role CLI, dynamic inputs, cloud fallback, and 4x redlines", () => {
	const agyText = readFileSync(join(hostDispatchDir, "references/agy.md"), "utf8");
	for (const required of [
		"--role",
		"<<'EOF'",
		"--prompt-file",
		"--prompt",
		"--add-dir",
		"--issue",
		"--resume",
		"close",
		"--all-mine",
		"--force",
		"--seat",
		"--lifecycle",
		"--model",
		"--prompt-role",
		"invoke_subagent",
		"research",
		"agents/",
		"--agent",
		".agents/agents/",
		"define_subagent",
		"agy-lifecycle.md",
	]) {
		expect(agyText).toContain(required);
	}
});

test("zero lingering references/host-dispatch.md links and all host-dispatch links resolve", () => {
	const mdFiles = [
		join(repoRoot, "AGENTS.md"),
		join(mmwstackRoot, "README.md"),
		...walkMarkdownFiles(join(mmwstackRoot, "docs")),
		...walkMarkdownFiles(join(mmwstackRoot, "skills")),
	];

	const linkRe = /\[[^\]]+\]\(([^)#]+?host-dispatch[^)#]*)(?:#[^)]*)?\)/g;

	for (const file of mdFiles) {
		const text = readFileSync(file, "utf8");
		expect(text).not.toContain("references/host-dispatch.md");
		for (const match of text.matchAll(linkRe)) {
			const target = match[1];
			if (/^https?:\/\//.test(target)) continue;
			const resolved = resolve(dirname(file), target);
			expect(existsSync(resolved)).toBe(true);
		}
	}
});

test("mmw-mode, playbooks, and delegating skills route directly to host-dispatch", () => {
	const callers = [
		"AGENTS.md",
		"mmwstack/skills/mmw-mode/SKILL.md",
		"mmwstack/skills/advisor/SKILL.md",
		"mmwstack/skills/no-comments/SKILL.md",
		"mmwstack/skills/research/SKILL.md",
		"mmwstack/skills/ambiguity-scan/SKILL.md",
		"mmwstack/skills/recall/SKILL.md",
		"mmwstack/skills/figure-it-out/SKILL.md",
		"mmwstack/skills/arena/SKILL.md",
		"mmwstack/skills/how/SKILL.md",
		"mmwstack/skills/grilling/SKILL.md",
		"mmwstack/skills/code-review/SKILL.md",
		"mmwstack/skills/automate-me/SKILL.md",
		"mmwstack/skills/maintain-verification-skill/SKILL.md",
		"mmwstack/skills/show-me-your-work/SKILL.md",
		"mmwstack/skills/mmw-mode/playbooks/refactoring.md",
		"mmwstack/skills/mmw-mode/playbooks/perf-issue.md",
		"mmwstack/skills/mmw-mode/playbooks/visual-parity.md",
		"mmwstack/skills/mmw-mode/playbooks/feature.md",
		"mmwstack/skills/mmw-mode/playbooks/autopilot-stack.md",
		"mmwstack/skills/mmw-mode/playbooks/pause-safely.md",
		"mmwstack/skills/mmw-mode/playbooks/hillclimb.md",
		"mmwstack/skills/mmw-mode/playbooks/autopilot-full.md",
		"mmwstack/skills/mmw-mode/playbooks/prototype.md",
		"mmwstack/skills/mmw-mode/playbooks/bug-fix.md",
	];

	for (const relPath of callers) {
		const text = readFileSync(join(repoRoot, relPath), "utf8");
		expect(text).toContain("host-dispatch/SKILL.md");
	}
});

test("setup docs prohibit AGY custom-agent registration and document scripts/agy-delegate --role", () => {
	const setupFiles = [
		"mmwstack/docs/guide/01-setup.md",
		"mmwstack/skills/setup-mmwstack/SKILL.md",
		"mmwstack/skills/mmw-help/SKILL.md",
		"mmwstack/README.md",
	];
	for (const relPath of setupFiles) {
		const text = readFileSync(join(repoRoot, relPath), "utf8");
		expect(text).toContain("scripts/agy-delegate --role");
		expect(text).not.toContain("sync the native registrations for `mmw-agent`");
		expect(text).not.toContain("native role files in `.agents/agents/<name>.md`");
		expect(text).not.toContain("`.agents/agents/` is synced");
	}

	for (const roleFile of ["mmw-agent.md", "advisor.md", "comment-sicko.md"]) {
		expect(existsSync(join(mmwstackRoot, "agents", roleFile))).toBe(true);
	}
});
