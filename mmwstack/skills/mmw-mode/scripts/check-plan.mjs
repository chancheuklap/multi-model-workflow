#!/usr/bin/env node
import fs from "node:fs";
import process from "node:process";

const LEGACY_RULE =
	"Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.";
const RULE = "Tests alone are not sufficient verification. Check each applicable unit, live, and perf requirement against its evidence.";
const SUB_BLOCKS = [
	"Depends on.",
	"Files.",
	"Build.",
	"You see.",
	"Verify.",
	"Review gate.",
];
const PROGRAM_H3 = ["Arm the program", "Spawn owners", "PR mechanics", "Verdict and merge", "Boot recipe"];
const HOW_TO_READ_MARKERS = [
	"One box is one unit of work",
	"names the evidence",
	"Check a box only when its evidence exists",
	"playbooks/",
];
const BOX = /^\s*- \[[ x]\] /;

const file = process.argv[2];
if (!file) {
	console.error("Usage: node check-plan.mjs <plan.md>");
	process.exit(2);
}

const raw = fs.readFileSync(file, "utf8").split(/\r?\n/);
const problems = [];
const fail = (line, message) => problems.push(`${file}:${line}: ${message}`);

let start = 0;
if (raw[0] === "---") {
	start = raw.indexOf("---", 1) + 1;
}

const lines = [];
let fence = null;
const openingFence = (text) => {
	const match = text.match(/^ {0,3}(`{3,}|~{3,})(.*)$/);
	if (!match || (match[1][0] === "`" && match[2].includes("`"))) return null;
	return { char: match[1][0], length: match[1].length };
};
const closingFence = (text, opening) => {
	const match = text.match(/^ {0,3}(`+|~+)[ \t]*$/);
	return Boolean(
		match &&
		match[1][0] === opening.char &&
		match[1].length >= opening.length,
	);
};
const startsBlock = (text) =>
	!text.trim() || openingFence(text) || /^ {0,3}(?:#{1,6}(?:\s|$)|>|<!--|(?:[-+*]|\d+[.)])\s)/.test(text);
const inlineEnd = (line, offset, endOf) => {
	for (let i = line; i < raw.length; i++) {
		if (i !== line && startsBlock(raw[i])) break;
		const from = i === line ? offset : 0;
		const end = endOf(raw[i].slice(from));
		if (end !== null) return { line: i, offset: from + end };
	}
	return null;
};
const closingTicks = (text, delimiter) => {
	for (const match of text.matchAll(/`+/g)) {
		if (match[0] === delimiter) return match.index + delimiter.length;
	}
	return null;
};
const closingComment = (text) => {
	const end = text.indexOf("-->");
	return end === -1 ? null : end + 3;
};

let comment = false;
let codeEnd = null;
const inlineToken = /\\[\\`<]|`+|<!--/g;
for (let i = start; i < raw.length; i++) {
	const input = raw[i];
	const n = i + 1;
	if (fence) {
		if (closingFence(input, fence)) fence = null;
		continue;
	}
	if (!comment && !codeEnd && (fence = openingFence(input))) continue;

	let text = "";
	let prose = "";
	let offset = 0;
	while (offset < input.length) {
		if (comment) {
			const end = closingComment(input.slice(offset));
			if (end === null) break;
			offset += end;
			comment = false;
			continue;
		}
		if (codeEnd) {
			const end = codeEnd.line === i ? codeEnd.offset : input.length;
			text += input.slice(offset, end);
			prose += "`";
			offset = end;
			if (codeEnd.line === i) codeEnd = null;
			continue;
		}
		inlineToken.lastIndex = offset;
		const match = inlineToken.exec(input);
		const plain = input.slice(offset, match?.index ?? input.length);
		text += plain;
		prose += plain;
		if (!match) break;
		offset = inlineToken.lastIndex;
		const token = match[0];
		if (token === "<!--" && (/^ {0,3}$/.test(input.slice(0, match.index)) || inlineEnd(i, offset, closingComment))) {
			comment = true;
		} else if (token.startsWith("`") && (codeEnd = inlineEnd(i, offset, (rest) => closingTicks(rest, token)))) {
			offset = match.index;
		} else {
			text += token;
			prose += token;
		}
	}
	prose = prose
		.replace(/!\[[^\]]*\]\([^)]*\)/g, "")
		.replace(/\]\([^)]*\)/g, "]");
	lines.push({ n, text, prose });
	if (/[\u2013\u2014]/.test(prose)) fail(n, "long dash");
	if (/[\u2018\u2019\u201c\u201d]/.test(prose)) fail(n, "curly quote");
	if (/: \S/.test(prose)) fail(n, "mid-sentence colon");
}

const h2 = (l) => (l.prose.startsWith("## ") ? l.text.slice(3).trim() : null);
const sections = [];
for (const l of lines) {
	const title = h2(l);
	if (title !== null) sections.push({ title, n: l.n, body: [] });
	else if (sections.length) sections.at(-1).body.push(l);
}
const find = (title) => sections.find((s) => s.title === title);
const bodyText = (s) => s.body.map((l) => l.text).join("\n");
const boxCount = (ls) => ls.filter((l) => BOX.test(l.prose)).length;

const h1 = lines.findIndex((l) => l.prose.startsWith("# "));
if (h1 === -1) fail(1, "no H1 title");
const howToRead = find("How to read this");
if (!howToRead) fail(1, 'no "## How to read this" section');
if (h1 !== -1 && howToRead) {
	const intro = raw.slice(lines[h1].n, howToRead.n - 1).filter((text) => text.trim() !== "");
	if (intro.length >= 10) fail(lines[h1].n, `intro is ${intro.length} lines, under ten required`);
	const guidance = howToRead.body.map((l) => l.prose).join("\n");
	if (![RULE, LEGACY_RULE].some((rule) => guidance.includes(rule))) fail(howToRead.n, `How to read this lacks "${RULE}"`);
	for (const marker of HOW_TO_READ_MARKERS) {
		if (!bodyText(howToRead).includes(marker)) fail(howToRead.n, `How to read this lacks "${marker}"`);
	}
}

const program = find("Program checklist");
if (!program) fail(1, 'no "## Program checklist" section');
else {
	const h3s = program.body.filter((l) => l.prose.startsWith("### ")).map((l) => l.text.slice(4).trim());
	let cursor = 0;
	for (const name of PROGRAM_H3) {
		const at = h3s.findIndex((t, i) => i >= cursor && t.startsWith(name));
		if (at === -1) fail(program.n, `Program checklist lacks "### ${name}" in order`);
		else cursor = at + 1;
	}
	const checklist = bodyText(program);
	if (!/git show origin\/main:\S*playbooks\/|read the execution playbook from trunk/i.test(checklist)) fail(program.n, "Program checklist lacks a read from trunk");
	if (!/\/loop 1h\b|schedule an hourly audit/i.test(checklist)) fail(program.n, "Program checklist lacks a scheduled hourly audit");
	if (!checklist.includes("status message")) fail(program.n, 'Program checklist lacks "status message"');
}

const close = find("Close the program");
if (!close) fail(1, 'no "## Close the program" section');
const programIndex = sections.indexOf(program);
const closeIndex = sections.indexOf(close);
const phases = programIndex === -1 || closeIndex === -1 ? [] : sections.slice(programIndex + 1, closeIndex);
if (phases.length === 0) fail(1, "no phases between Program checklist and Close the program");

const report = [];
for (const phase of phases) {
	if (!/^Phase \d+\. \S/.test(phase.title)) fail(phase.n, `expected a phase goal, got "${phase.title}"`);
	const heads = [];
	for (const l of phase.body) {
		const m = l.prose.match(/^\*\*([^*]+)\*\*(.*)$/);
		if (m && SUB_BLOCKS.includes(m[1])) heads.push({ name: m[1], n: l.n, rest: m[2].trim(), lines: [] });
		else if (heads.length) heads.at(-1).lines.push(l);
	}
	const names = heads.map((h) => h.name);
	if (names.join("|") !== SUB_BLOCKS.join("|")) {
		fail(phase.n, `${phase.title}: sub-blocks are [${names.join(", ")}], expected [${SUB_BLOCKS.join(", ")}]`);
	}
	const counts = {};
	for (const block of heads) {
		const count = boxCount(block.lines);
		counts[block.name] = count;
		if (block.name === "Depends on." || block.name === "Review gate.") {
			if (!block.rest) fail(block.n, `${phase.title}: ${block.name} names nothing`);
		} else if (count === 0) {
			fail(block.n, `${phase.title}: ${block.name} has no box`);
		}
	}
	const cells = ["Files.", "Build.", "You see.", "Verify."].map((name) => `${name.slice(0, -1).replace(" ", "-").toLowerCase()}=${counts[name] ?? 0}`);
	report.push(`${phase.title}  boxes=${boxCount(phase.body)}  ${cells.join(" ")}`);
}

if (closeIndex !== -1) {
	const tail = sections.slice(closeIndex + 1);
	for (const s of tail) {
		if (!s.title.startsWith("Appendix")) fail(s.n, `"## ${s.title}" after Close the program is not an appendix`);
	}
	if (!tail.some((s) => s.title.includes("Prototype evidence"))) fail(close.n, 'no "## Appendix ... Prototype evidence" section');
}

for (const line of report) console.log(line);
console.log(`${phases.length} ${phases.length === 1 ? "phase" : "phases"}, ${problems.length} problems`);
for (const p of problems) console.error(p);
process.exit(problems.length ? 1 : 0);
