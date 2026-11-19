import assert from "node:assert/strict";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { expect, test } from "bun:test";

const checker = join(import.meta.dir, "check-plan.mjs");
const rule =
	"Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.";
const currentRule = "Tests alone are not sufficient verification. Check each applicable unit, live, and perf requirement against its evidence.";
const actions = "Read the execution playbook from trunk. Schedule an hourly audit and send a status message when something changes.";

const validPlan = `# Demo

## How to read this
One box is one unit of work and names the evidence. Check a box only when its evidence exists. See playbooks/.
${rule}

## Program checklist
### Arm the program
### Spawn owners
### PR mechanics
### Verdict and merge
### Boot recipe
${actions}

## Phase 1. Restore both reading paths
**Depends on.** None.
**Files.**
- [ ] Do the thing.
**Build.**
- [ ] Do the thing.
**You see.**
- [ ] Do the thing.
**Verify.**
- [ ] Open each reading path and capture its expected result.
**Review gate.** None.

## Close the program
Close.

## Appendix Prototype evidence
Recorded.
`;

const runPlan = (example: string, expectedExit: number, plan = validPlan) => {
	const directory = mkdtempSync(join(tmpdir(), "check-plan-test-"));
	const file = join(directory, "plan.md");
	writeFileSync(file, plan + example);
	try {
		const result = spawnSync("node", [checker, file], { encoding: "utf8" });
		expect(result.status).toBe(expectedExit);
		return result;
	} finally {
		rmSync(directory, { recursive: true, force: true });
	}
};

test("accepts ticket-specific verification and plans already in progress", () => {
	expect(runPlan("", 0, validPlan.replace(rule, currentRule)).stdout).toContain("0 problems");
	expect(runPlan("", 0, validPlan).stdout).toContain("0 problems");
	expect(runPlan("", 1, validPlan.replace(rule, "")).stderr).toContain("How to read this lacks");
});

test("plan requirements must appear outside fenced examples and comments", () => {
	for (const hide of [
		(text: string) => `~~~text\n${text}\n~~~`,
		(text: string) => `<!--\n${text}\n-->`,
	]) {
		expect(runPlan("", 1, validPlan.replace(rule, hide(currentRule))).stderr).toContain(`How to read this lacks "${currentRule}"`);
		const missing = runPlan("", 1, validPlan.replace(actions, hide(actions))).stderr;
		expect(missing).toContain("read from trunk");
		expect(missing).toContain("scheduled hourly audit");
		expect(missing).toContain('lacks "status message"');
	}
});

test("a fenced example still counts towards the intro length", () => {
	const longIntro = validPlan.replace("## How to read this", `~~~text\n${"example\n".repeat(8)}~~~\n\n## How to read this`);
	expect(runPlan("", 1, longIntro).stderr).toContain("intro is 10 lines, under ten required");
});

test("accepts the multi-phase plan template", () => {
	const playbook = readFileSync(join(import.meta.dir, "../playbooks/multi-phase-plan.md"), "utf8");
	const template = playbook.match(/^````markdown\n([\s\S]*?)^````$/m);
	assert(template, "multi-phase plan template is missing");
	expect(runPlan("", 0, template[1]).stdout).toContain("1 phase, 0 problems");
});

test("checks the phases before tickets or PRs exist", () => {
	const result = runPlan("", 0);
	expect(result.stdout).toContain("1 phase, 0 problems");
	const preassigned = validPlan.replace("Phase 1. Restore both reading paths", "PR 1");
	expect(runPlan("", 1, preassigned).stderr).toContain("expected a phase goal");
	const noProof = validPlan.replace("- [ ] Open each reading path and capture its expected result.", "");
	expect(runPlan("", 1, noProof).stderr).toContain("Verify. has no box");
});

test("requires the playbook from trunk and a scheduled hourly audit", () => {
	const local = validPlan.replace("from trunk", "from the installed copy");
	expect(runPlan("", 1, local).stderr).toContain("read from trunk");
	const unrelated = local.replace("from the installed copy", "from the installed copy after reading `git show origin/main:README.md`");
	expect(runPlan("", 1, unrelated).stderr).toContain("read from trunk");
	const unscheduled = validPlan.replace("Schedule an hourly audit", "Show hourly build statistics");
	expect(runPlan("", 1, unscheduled).stderr).toContain("scheduled hourly audit");
});

test("accepts the existing command-based plan checklist", () => {
	const legacy = validPlan.replace("Read the execution playbook from trunk. Schedule an hourly audit", "`git show origin/main:mmwstack/skills/mmw-mode/playbooks/shipping.md` /loop 1h");
	runPlan("", 0, legacy);
});

test("accepts ordinary, indented, and longer closing fences", () => {
	for (const indent of ["", " ", "  ", "   "])
		runPlan(`${indent}\`\`\`markdown\n## Example only\n${indent}\`\`\`\n`, 0);
	runPlan("```markdown\n## Example only\n````\n", 0);
});

test("accepts nested backticks and tilde info strings", () => {
	runPlan("````markdown\n```markdown\n## Example only\n```\n````\n", 0);
	runPlan("~~~markdown `info`\n## Example only\n ~~~\n", 0);
});

test("keeps mismatched, shorter, and suffixed closers inside the fence", () => {
	runPlan("````markdown\n~~~\n## Example only\n````\n", 0);
	runPlan("````markdown\n```\n## Example only\n````\n", 0);
	runPlan("````markdown\n``` info\n## Example only\n````\n", 0);
});

test("rejects headings and prose outside a proper close", () => {
	for (const suffix of ["  ", "\t"]) {
		const heading = runPlan(`\`\`\`markdown\n## Example only\n\`\`\`${suffix}\n## Example only\n`, 1);
		expect(heading.stderr).toContain('"## Example only" after Close the program is not an appendix');
	}

	const prose = runPlan("```markdown\nThis prose has a mid-sentence colon: inside code\n```\nThis prose has a mid-sentence colon: bad.\n", 1);
	expect(prose.stderr).toContain("mid-sentence colon");
});

test("rejects backtick info strings containing a backtick", () => {
	const result = runPlan("```markdown `invalid`\n## Example only\n```\n", 1);
	expect(result.stderr).toContain('"## Example only" after Close the program is not an appendix');
});

test("ignores prose punctuation inside matching multi-backtick code spans", () => {
	for (const count of [2, 3, 4]) {
		const delimiter = "`".repeat(count);
		runPlan(`Use ${delimiter}echo \`x\`: “quoted” — example${delimiter}.\n`, 0);
	}
});

test("checks prose following a multi-backtick span and unmatched delimiters", () => {
	const outside = runPlan("Use ``echo `x`: y``. Bad: prose.\n", 1);
	expect(outside.stderr).toContain("mid-sentence colon");
	const unmatched = runPlan("Use ``unclosed: bad` here.\n", 1);
	expect(unmatched.stderr).toContain("mid-sentence colon");
});

test("skips punctuation inside multiline inline code and HTML comments", () => {
	runPlan("Run `example:\noutput — “here”`. <!-- Hidden: “punctuation” — draft -->\n", 0);
	runPlan("<!-- Hidden:\n## Not a section — draft\n```\n-->\n", 0);
	const outside = runPlan("Run `example:\noutput — here`. Bad: prose.\n", 1);
	expect(outside.stderr).toContain("mid-sentence colon");
	expect(outside.stderr).not.toContain("long dash");
	const unmatched = runPlan("Run `example: bad.\n\nA new paragraph ends with `.\n", 1);
	expect(unmatched.stderr).toContain("mid-sentence colon");
	const unclosedComment = runPlan("Draft <!-- visible — this comment has no close.\n", 1);
	expect(unclosedComment.stderr).toContain("long dash");
});
