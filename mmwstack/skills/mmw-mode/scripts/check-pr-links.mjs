#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { execFileSync } from "node:child_process";

const ALLOW = { decision: "allow" };
const REFERENCE = /(?:\b(close[sd]?|fix(?:e[sd])?|resolve[sd]?)\b:?\s+)?(?:([\w.-]+\/[\w.-]+))?#(\d+)/gi;
const BRANCH_TICKET = /^(?:feat|fix|docs|chore|refactor|test|ci|perf|revert)\/(\d+)-/;
const REMOTE_SLUG = /github\.com[:/]([^/]+\/[^/]+?)(?:\.git)?\/?$/;
const CREATE_COMMANDS = [
	["gh", "pr", "create"],
	["origin", "pr", "create"],
];
const FLAGS_WITHOUT_FINAL_BODY = new Set(["--fill", "-f", "--fill-first", "--fill-verbose", "--web", "-w", "--editor", "-e"]);
const VALUE_FLAGS = new Map([
	["--base", "base"],
	["-B", "base"],
	["--body", "body"],
	["-b", "body"],
	["--body-file", "bodyFile"],
	["-F", "bodyFile"],
	["--head", "head"],
	["-H", "head"],
	["--repo", "repo"],
	["-R", "repo"],
]);

const UNKNOWN = null;
const join = (a, b) => (a === UNKNOWN || b === UNKNOWN ? UNKNOWN : a + b);

function readDelimiter(src, at) {
	let i = at;
	let delimiter = "";
	let quoted = false;
	while (i < src.length && !" \t\n;&|()<>".includes(src[i])) {
		if (src[i] === "'" || src[i] === '"') {
			const end = src.indexOf(src[i], i + 1);
			if (end === -1) throw new Error("unterminated quote");
			delimiter += src.slice(i + 1, end);
			quoted = true;
			i = end + 1;
		} else if (src[i] === "\\") {
			delimiter += src[i + 1] ?? "";
			quoted = true;
			i += 2;
		} else {
			delimiter += src[i++];
		}
	}
	return { delimiter, quoted, end: i };
}

function readDouble(src, at) {
	let value = "";
	let i = at + 1;
	while (i < src.length && src[i] !== '"') {
		if (src[i] === "\\" && src[i + 1] === "\n") {
			i += 2;
		} else if (src[i] === "\\" && /[$`"\\]/.test(src[i + 1] ?? "")) {
			value = join(value, src[i + 1]);
			i += 2;
		} else if (src[i] === "$" || src[i] === "`") {
			const expanded = readExpansion(src, i);
			value = join(value, expanded.value);
			i = expanded.end;
		} else {
			value = join(value, src[i++]);
		}
	}
	if (i >= src.length) throw new Error("unterminated quote");
	return { value, end: i + 1 };
}

function heredocText(commands) {
	const [only] = commands;
	const isCat = commands.length === 1 && only.words.length === 1 && only.words[0] === "cat";
	if (!isCat || only.heredocs.length === 0 || only.heredocs.includes(UNKNOWN)) return UNKNOWN;
	return only.heredocs.join("");
}

function readExpansion(src, at) {
	if (src[at] === "`") {
		let i = at + 1;
		while (i < src.length && src[i] !== "`") i += src[i] === "\\" ? 2 : 1;
		if (i >= src.length) throw new Error("unterminated backtick");
		return { value: UNKNOWN, end: i + 1 };
	}
	if (src[at + 1] !== "(") return { value: UNKNOWN, end: at + 1 };
	const inner = parse(src, at + 2, true);
	return { value: heredocText(inner.commands), end: inner.end };
}

function parse(src, start, nested) {
	const commands = [];
	const pending = [];
	let current = { words: [], heredocs: [] };
	let word = "";
	let inWord = false;
	let depth = 0;
	let i = start;

	const append = (text) => {
		inWord = true;
		word = join(word, text);
	};
	const endWord = () => {
		if (!inWord) return;
		current.words.push(word);
		word = "";
		inWord = false;
	};
	const endCommand = () => {
		endWord();
		if (current.words.length) commands.push(current);
		current = { words: [], heredocs: [] };
	};
	const readHeredocs = () => {
		for (const { delimiter, quoted, strip, into } of pending.splice(0)) {
			let body = "";
			for (;;) {
				if (i >= src.length) throw new Error("unterminated heredoc");
				const eol = src.indexOf("\n", i);
				const line = src.slice(i, eol === -1 ? src.length : eol);
				i = eol === -1 ? src.length + 1 : eol + 1;
				if ((strip ? line.replace(/^\t+/, "") : line) === delimiter) break;
				body += `${line}\n`;
			}
			into.push(!quoted && /[$`]/.test(body) ? UNKNOWN : body);
		}
	};

	while (i < src.length) {
		const c = src[i];
		if (c === "\n") {
			i++;
			readHeredocs();
			endCommand();
		} else if (c === " " || c === "\t" || c === "\r") {
			endWord();
			i++;
		} else if (c === "#" && !inWord) {
			while (i < src.length && src[i] !== "\n") i++;
		} else if (c === "&" || c === "|" || c === ";") {
			endCommand();
			i++;
		} else if (c === "(") {
			depth++;
			endCommand();
			i++;
		} else if (c === ")") {
			endCommand();
			if (nested && depth === 0) return { commands, end: i + 1 };
			depth--;
			i++;
		} else if (src.startsWith("<<", i) && src[i + 2] !== "<") {
			endWord();
			i += 2;
			const strip = src[i] === "-";
			if (strip) i++;
			while (src[i] === " " || src[i] === "\t") i++;
			const { delimiter, quoted, end } = readDelimiter(src, i);
			pending.push({ delimiter, quoted, strip, into: current.heredocs });
			i = end;
		} else if (c === "'") {
			const end = src.indexOf("'", i + 1);
			if (end === -1) throw new Error("unterminated quote");
			append(src.slice(i + 1, end));
			i = end + 1;
		} else if (c === '"') {
			const quoted = readDouble(src, i);
			append(quoted.value);
			i = quoted.end;
		} else if (c === "$" || c === "`") {
			const expanded = readExpansion(src, i);
			append(expanded.value);
			i = expanded.end;
		} else if (c === "\\") {
			if (src[i + 1] !== "\n") append(src[i + 1] ?? "");
			i += 2;
		} else {
			append(c);
			i++;
		}
	}
	if (nested) throw new Error("unterminated substitution");
	endCommand();
	return { commands, end: i };
}

const expandHome = (file) => (file === "~" || file.startsWith("~/") ? path.join(os.homedir(), file.slice(1)) : file);

function git(dir, args) {
	if (dir === null) return null;
	try {
		return execFileSync("git", ["-C", dir, ...args], {
			encoding: "utf8",
			stdio: ["ignore", "pipe", "ignore"],
			timeout: 5000,
		}).trim();
	} catch {
		return null;
	}
}

function defaultBranch(dir) {
	const ref = git(dir, ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"]);
	return ref?.startsWith("origin/") ? ref.slice("origin/".length) : null;
}

const currentBranch = (dir) => git(dir, ["branch", "--show-current"]) || null;

const slugOf = (remote) => (typeof remote === "string" ? (REMOTE_SLUG.exec(remote)?.[1].toLowerCase() ?? null) : null);

// A registry that cannot be read registers nothing, so every `--repo` command is then allowed.
function loadRegistry() {
	const file = process.env.HOOK_REGISTRY || path.join(os.homedir(), ".agents", "repos", "registry.json");
	try {
		const { home, repos } = JSON.parse(fs.readFileSync(file, "utf8"));
		return [home, ...repos].flatMap((entry) => {
			const slug = slugOf(entry?.remote);
			return slug && typeof entry.path === "string" ? [{ name: entry.name, path: expandHome(entry.path), slug }] : [];
		});
	} catch {
		return [];
	}
}

let registered;
const registry = () => (registered ??= loadRegistry());
const isRegistered = (slug) => registry().some((entry) => entry.slug === slug);

// The repository a command acts on: the registered one a `--repo` flag names, else the one in `dir`.
// `repoDir` is where its default branch is read. Null when the flag names an unregistered or unknown repository.
function resolveTarget(repo, dir) {
	if (repo === undefined) return { slug: slugOf(git(dir, ["remote", "get-url", "origin"])), repoDir: dir, flagged: false };
	const slug = typeof repo === "string" ? repo.toLowerCase() : null;
	const entry = registry().find((candidate) => candidate.slug === slug);
	return entry ? { slug, repoDir: entry.path, flagged: true } : null;
}

function readBodyFile(file, dir) {
	if (typeof file !== "string" || file === "-" || dir === null) return null;
	try {
		return fs.readFileSync(path.resolve(dir, file), "utf8");
	} catch {
		return null;
	}
}

function cdTarget(dir, args) {
	if (dir === null || args.length !== 2 || args[1] === UNKNOWN) return null;
	return path.resolve(dir, expandHome(args[1]));
}

function readFlags(args) {
	const given = {};
	for (let k = 0; k < args.length; k++) {
		const arg = args[k];
		if (typeof arg !== "string") continue;
		const eq = arg.startsWith("--") ? arg.indexOf("=") : -1;
		const key = VALUE_FLAGS.get(eq === -1 ? arg : arg.slice(0, eq));
		if (key) given[key] = (eq === -1 ? args[++k] : arg.slice(eq + 1)) ?? null;
		else if (arg.startsWith("-R") && arg.length > 2) given.repo = arg.slice(2);
		else if (FLAGS_WITHOUT_FINAL_BODY.has(arg)) given.fill = true;
	}
	return given;
}

// The body the command carries, or null when its text is not known before the command runs.
const commandBody = (given, dir) => (given.body !== undefined ? given.body : readBodyFile(given.bodyFile, dir));

// The ticket number a branch named `<type>/<issue>-<slug>` carries, else null.
function branchTicket(head) {
	const match = head === null ? null : BRANCH_TICKET.exec(head);
	return match ? Number(match[1]) : null;
}

// "linked" when the body completes the ticket, "different" when it closes only other tickets, else "missing".
// Without a ticket number, any closing keyword counts as linked.
function judgeBody(body, ticket, target) {
	const references = [...body.matchAll(REFERENCE)].map(([, keyword, slug, number]) => ({
		closing: keyword !== undefined,
		slug: slug?.toLowerCase(),
		number: Number(number),
	}));
	const closesTicket = (ref) => {
		if (ticket === null) return ref.closing;
		if (ref.number !== ticket) return false;
		if (ref.slug === undefined || ref.slug === target.slug) return ref.closing;
		// GitHub closes only same-repository issues, so a link to another registered repository is the cross-repository form.
		return isRegistered(ref.slug);
	};
	if (references.some(closesTicket)) return "linked";
	return references.some((ref) => ref.closing) ? "different" : "missing";
}

function denial(judgment, branch, ticket, head) {
	const merge = `This PR merges into the default branch \`${branch}\``;
	if (ticket === null) {
		return {
			decision: "deny",
			reason: `${merge}, where GitHub closes issues from closing keywords, and the body has none.`,
			fix: "Add a line `Closes #<issue>` to the body for each issue this PR completes, then run the same command again; handle this yourself without asking the owner.",
		};
	}
	const reason =
		judgment === "different"
			? `${merge}, and its body names a different ticket than #${ticket}, which branch \`${head}\` carries.`
			: `${merge}, where GitHub closes issues from closing keywords, and the body does not close ticket #${ticket}, which branch \`${head}\` carries.`;
	return {
		decision: "deny",
		reason,
		fix: `Add a line \`Closes #${ticket}\` to the body, or \`owner/repo#${ticket}\` naming its repository when that ticket lives in another registered repository, then run the same command again; handle this yourself without asking the owner.`,
	};
}

// The PR as GitHub holds it, or null when it cannot be read within the hook's budget.
function readPullRequest(selector, target, dir) {
	const args = ["pr", "view", ...(selector === null ? [] : [selector]), ...(target.flagged ? ["--repo", target.slug] : [])];
	try {
		const output = execFileSync("gh", [...args, "--json", "body,baseRefName,headRefName"], {
			cwd: dir ?? undefined,
			encoding: "utf8",
			stdio: ["ignore", "pipe", "ignore"],
			timeout: 1500,
		});
		const { body, baseRefName, headRefName } = JSON.parse(output);
		return typeof baseRefName === "string" && typeof headRefName === "string" ? { body: body ?? "", baseRefName, headRefName } : null;
	} catch {
		return null;
	}
}

function checkCreate(args, { dir, phase }) {
	const given = readFlags(args);
	const target = resolveTarget(given.repo, dir);
	if (target === null) return ALLOW;

	const branch = defaultBranch(target.repoDir);
	const base = given.base === undefined ? branch : given.base;
	if (branch === null || base !== branch) return ALLOW;

	const head = given.head === undefined ? currentBranch(dir) : (given.head?.split(":").pop() ?? null);
	let body = given.fill ? null : commandBody(given, dir);
	if (body === null) {
		// Before the command runs, a body it writes or computes does not exist yet. After it runs, GitHub holds the real one.
		if (phase === "before" || head === null) return ALLOW;
		const pr = readPullRequest(head, target, dir);
		if (pr === null || pr.baseRefName !== branch) return ALLOW;
		body = pr.body;
	}

	const ticket = branchTicket(head);
	const judgment = judgeBody(body, ticket, target);
	return judgment === "linked" ? ALLOW : denial(judgment, branch, ticket, head);
}

function decide(event) {
	if (event.kind !== "shell" || typeof event.command !== "string" || typeof event.cwd !== "string") return ALLOW;
	const phase = event.phase === "after" ? "after" : "before";
	let dir = event.cwd;
	for (const { words } of parse(event.command, 0, false).commands) {
		if (words[0] === "cd") {
			dir = cdTarget(dir, words);
		} else if (CREATE_COMMANDS.some((command) => command.every((part, k) => words[k] === part))) {
			const decision = checkCreate(words.slice(3), { dir, phase });
			if (decision.decision === "deny") return decision;
		}
	}
	return ALLOW;
}

function decideOrAllow() {
	try {
		return decide(JSON.parse(fs.readFileSync(0, "utf8")));
	} catch {
		return ALLOW;
	}
}

process.stdout.write(`${JSON.stringify(decideOrAllow())}\n`);
