#!/usr/bin/env node
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { execFileSync } from "node:child_process";

const ALLOW = { decision: "allow" };
const KEYWORD = /\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\b:?\s+([\w.-]+\/[\w.-]+)?#\d+/i;
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

function defaultBranch(dir) {
	if (dir === null) return null;
	try {
		const ref = execFileSync("git", ["-C", dir, "symbolic-ref", "--short", "refs/remotes/origin/HEAD"], {
			encoding: "utf8",
			stdio: ["ignore", "pipe", "ignore"],
			timeout: 5000,
		}).trim();
		return ref.startsWith("origin/") ? ref.slice("origin/".length) : null;
	} catch {
		return null;
	}
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
	if (args[1] === "~" || args[1].startsWith("~/")) return path.join(os.homedir(), args[1].slice(1));
	return path.resolve(dir, args[1]);
}

function checkCreate(args, dir) {
	const flags = args.filter((arg) => typeof arg === "string");
	if (flags.some((arg) => arg.startsWith("-R") || arg === "--repo" || arg.startsWith("--repo="))) return ALLOW;
	if (flags.some((arg) => FLAGS_WITHOUT_FINAL_BODY.has(arg))) return ALLOW;

	const given = {};
	for (let k = 0; k < args.length; k++) {
		const arg = args[k];
		if (typeof arg !== "string") continue;
		const eq = arg.startsWith("--") ? arg.indexOf("=") : -1;
		const key = VALUE_FLAGS.get(eq === -1 ? arg : arg.slice(0, eq));
		if (key) given[key] = (eq === -1 ? args[++k] : arg.slice(eq + 1)) ?? null;
	}

	const body = given.body !== undefined ? given.body : readBodyFile(given.bodyFile, dir);
	if (body === null || KEYWORD.test(body)) return ALLOW;

	const branch = defaultBranch(dir);
	const base = given.base === undefined ? branch : given.base;
	if (branch === null || base !== branch) return ALLOW;
	return {
		decision: "deny",
		reason: `This PR merges into the default branch \`${branch}\`, where GitHub closes issues from closing keywords, and the body has none.`,
		fix: "Add a line `Closes #<issue>` to the body for each issue this PR completes, then run the same command again. Handle this yourself; do not ask the owner.",
	};
}

function decide(event) {
	if (event.kind !== "shell" || typeof event.command !== "string" || typeof event.cwd !== "string") return ALLOW;
	let dir = event.cwd;
	for (const { words } of parse(event.command, 0, false).commands) {
		if (words[0] === "cd") {
			dir = cdTarget(dir, words);
		} else if (CREATE_COMMANDS.some((command) => command.every((part, k) => words[k] === part))) {
			const decision = checkCreate(words.slice(3), dir);
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
