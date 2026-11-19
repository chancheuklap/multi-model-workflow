// Shared gate parsing and the states a criterion can be in.
// Zero dependencies. Node 16+.

import { readFileSync, statSync } from "node:fs";
import { createHash } from "node:crypto";
import { basename } from "node:path";

export const MAX_CHECK_OUTPUT_BYTES = 1024 * 1024;
export const MAX_AUTOMATIC_EVIDENCE_CHARS = 900;
const MAX_LEDGER_BYTES = 8 * 1024 * 1024;

export const sha256 = (value) => createHash("sha256").update(String(value)).digest("hex");

// A ledger is a regular file of bounded size. Anything else (a FIFO would block the
// read) is refused before it is opened.
export function readLedger(path) {
  const info = statSync(path);
  if (!info.isFile()) throw new Error("gate ledger is not a regular file: " + path);
  if (info.size > MAX_LEDGER_BYTES) throw new Error("gate ledger exceeds " + MAX_LEDGER_BYTES + " bytes: " + path);
  return readFileSync(path, "utf8");
}

const GATE_RE = /^- \[( |x|X)\] (.*)$/;
const ATTR_RE = /^(\s+)(CHECK|EXPECT|EVIDENCE|CWD):\s?(.*)$/;
const UNINDENTED_ATTR_RE = /^(CHECK|EXPECT|EVIDENCE|CWD):\s?(.*)$/;
const ABANDON_RE = /^ABANDON:\s*(\S*)\s*(.*)$/;
const INDENTED_ABANDON_RE = /^\s+ABANDON:/;
const FENCE_OPEN_RE = /^( {0,3})(`{3,}|~{3,})(.*)$/;
const REGEX_RE = /^\/([\s\S]*)\/([a-z]*)$/;
// A pattern author escapes an inner slash or has none. A literal path always
// carries one, so an unescaped inner slash marks the ambiguous reading.
const UNESCAPED_SLASH_RE = /(^|[^\\])\//;

function parseRegex(expect) {
  const match = String(expect).match(REGEX_RE);
  if (!match) return { kind: "text", value: String(expect) };
  if (match[1].length > 1000) return { error: "EXPECT regex is longer than 1000 characters" };
  try {
    // Matching happens in a disposable worker so catastrophic backtracking
    // cannot hang the checker.
    new RegExp(match[1], match[2]);
  } catch (error) {
    return { error: "invalid EXPECT regex: " + error.message };
  }
  return {
    kind: "regex",
    source: match[1],
    flags: match[2],
    pathLike: UNESCAPED_SLASH_RE.test(match[1]),
  };
}

// gate-check and gate-lint both consume this exact result. Diagnostics are
// returned together so callers can report all malformed input in one pass.
export function parseGates(text, options = {}) {
  const source = String(text);
  const eol = source.includes("\r\n") ? "\r\n" : "\n";
  const finalNewline = source.endsWith("\n");
  const lines = source.split(/\r?\n/);
  const gates = [];
  const abandoned = new Map();
  const errors = [];
  const warnings = [];
  const ids = new Map();
  const attrs = new Map();
  let current = null;
  let fence = null;

  let lastAttr = null;
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    const previousAttr = lastAttr;
    lastAttr = null;
    if (fence) {
      const close = line.match(/^( {0,3})(`+|~+)[ \t]*$/);
      if (close && close[2][0] === fence.character && close[2].length >= fence.length) {
        if (fence.gate) {
          // The command is what the author wrote inside the fence, less the fence's
          // own indentation: a heredoc body cannot carry the two spaces the ledger
          // puts on an attribute line and still be the script it was written as.
          fence.gate.check = fence.body
            .map((row) => (row.startsWith(fence.indent) ? row.slice(fence.indent.length) : row.trimStart()))
            .join("\n");
          fence.gate.attrEnd = index + 1;
        }
        fence = null;
      } else if (fence.gate) fence.body.push(line);
      continue;
    }
    const fenceMatch = line.match(FENCE_OPEN_RE);
    if (fenceMatch && !(fenceMatch[2][0] === "`" && fenceMatch[3].includes("`"))) {
      // A fence anywhere else in the ledger is prose — a ticket quotes example gate
      // lines and must not have them read as gates, which is why every other fence is
      // skipped whole. A fence directly under a gate's own `CHECK:` is the exception,
      // and only that one: it is where the command lives. Inside it nothing is scanned
      // for gates, attributes or ABANDON either way, so the guard still holds.
      const owner = previousAttr === "check" && current ? current : null;
      if (owner && owner.check) {
        errors.push("line " + (index + 1) + ": gate " + owner.id +
          " has both a CHECK value and a fenced block; put the command in one or the other");
      }
      fence = {
        character: fenceMatch[2][0],
        length: fenceMatch[2].length,
        indent: fenceMatch[1],
        gate: owner,
        body: [],
      };
      continue;
    }

    const gateMatch = line.match(GATE_RE);
    if (gateMatch) {
      const rawTitle = gateMatch[2].trim();
      const idMatch = rawTitle.match(/^(\S+?):(?:\s+|$)/);
      const id = idMatch ? idMatch[1] : "L" + (index + 1);
      const title = idMatch ? rawTitle.slice(idMatch[0].length).trim() : rawTitle;
      current = {
        line: index,
        checked: gateMatch[1].toLowerCase() === "x",
        id,
        title,
        check: null,
        expect: null,
        evidence: null,
        evidenceLine: -1,
        cwd: null,
        attrEnd: index + 1,
      };
      gates.push(current);
      attrs.set(current, new Set());
      if (!idMatch) errors.push("line " + (index + 1) + ": gate needs an explicit ID followed by a colon");
      else if (!/^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(id)) {
        errors.push("line " + (index + 1) + ": invalid gate id " + id);
      }
      if (!title) errors.push("line " + (index + 1) + ": gate outcome is blank");
      if (ids.has(id)) {
        errors.push("line " + (index + 1) + ": duplicate gate id " + id +
          " (first declared on line " + ids.get(id) + ")");
      } else ids.set(id, index + 1);
      continue;
    }

    // Attributes must be indented and ABANDON must not be, so the two rules
    // point opposite ways. Diagnose the indented abandonment rather than
    // ignoring it, or the author's honest exit fails with no explanation.
    if (INDENTED_ABANDON_RE.test(line)) {
      errors.push("line " + (index + 1) +
        ": indented ABANDON is not applied; start ABANDON at column 1");
      current = null;
      continue;
    }

    const unindented = line.match(UNINDENTED_ATTR_RE);
    if (unindented) {
      errors.push("line " + (index + 1) + ": unindented " + unindented[1] +
        " is not attached to a gate; indent attribute lines with spaces");
      current = null;
      continue;
    }

    const anyAttr = line.match(ATTR_RE);
    if (anyAttr && !current) {
      errors.push("line " + (index + 1) + ": orphan " + anyAttr[2] + " is not attached to a gate");
      continue;
    }
    const attrMatch = current && anyAttr;
    if (attrMatch) {
      const key = attrMatch[2].toLowerCase();
      const value = attrMatch[3].trim();
      if (attrs.get(current).has(key)) {
        errors.push("line " + (index + 1) + ": duplicate " + attrMatch[2] +
          " for gate " + current.id);
      }
      attrs.get(current).add(key);
      lastAttr = key;
      current.attrEnd = index + 1;
      if (key === "evidence") {
        current.evidence = value;
        current.evidenceLine = index;
      } else current[key] = value;
      continue;
    }

    const abandonMatch = line.match(ABANDON_RE);
    if (abandonMatch) {
      const id = abandonMatch[1].replace(/:$/, "");
      const reason = abandonMatch[2].trim();
      if (!id) errors.push("line " + (index + 1) + ": ABANDON needs a gate id and reason");
      else if (!reason) errors.push("line " + (index + 1) + ": ABANDON " + id + " needs a non-blank reason");
      else if (abandoned.has(id)) errors.push("line " + (index + 1) + ": duplicate ABANDON for " + id);
      else abandoned.set(id, reason);
      current = null;
      continue;
    }

    // A CHECK is a shell command and may run to several lines, but where it ends has
    // to be written down rather than inferred. A bare line under a CHECK was once read
    // as part of it; the rule that decided where that stopped was invisible, every
    // reader of a ledger had to reproduce it, and a blank line, a ``` or a `- [ ]`
    // inside the command each broke it in a different silent way. Say it with a fence.
    if (previousAttr === "check" && current && line.trim()) {
      // Keep the gate open: the EXPECT and EVIDENCE below still belong to it, and
      // orphaning them buries the one error worth reading under three that follow.
      errors.push("line " + (index + 1) + ": gate " + current.id +
        " continues its CHECK onto another line; wrap the command in a fenced block " +
        "under `CHECK:` instead");
      continue;
    }
    if (/^#|^- /.test(line)) current = null;
  }

  if (fence) errors.push("unclosed fenced block");

  for (const gate of gates) {
    const hasCheck = gate.check !== null && gate.check !== "";
    const hasExpect = gate.expect !== null && gate.expect !== "";
    if (hasCheck !== hasExpect) {
      errors.push("gate " + gate.id + ": runnable gates require both non-blank CHECK and EXPECT");
    }
    if (gate.check === "" || gate.expect === "") {
      errors.push("gate " + gate.id + ": CHECK and EXPECT cannot be blank");
    }
    if (hasExpect) {
      const parsed = parseRegex(gate.expect);
      if (parsed.error) errors.push("gate " + gate.id + ": " + parsed.error);
      else if (parsed.pathLike) {
        // Warn rather than reject: the pattern reading may be intended, and a
        // literal path cannot be expressed once the wrapping slashes sniff.
        warnings.push("gate " + gate.id + ": EXPECT " + JSON.stringify(gate.expect) +
          " is read as a regular expression, so its dots and other metacharacters" +
          " are wildcards. Escape the inner slashes to keep the pattern, or drop" +
          " the wrapping slashes to match a literal substring.");
      }
      gate.expectation = parsed;
    } else gate.expectation = null;
  }

  for (const id of abandoned.keys()) {
    if (!ids.has(id)) errors.push("ABANDON references unknown gate " + id);
  }
  if (options.requireGates !== false && gates.length === 0) errors.push("ledger contains zero live gates");

  return { lines, eol, finalNewline, gates, abandoned, errors, warnings };
}

export function formatDocument(doc) {
  let output = doc.lines.join(doc.eol);
  if (doc.finalNewline && !output.endsWith(doc.eol)) output += doc.eol;
  return output;
}

export function qualify(fileOrLabel, id) {
  return basename(String(fileOrLabel)).replace(/\.md$/i, "") + ":" + id;
}

export function gateDefinitionDigest(gate) {
  if (!gate || typeof gate.check !== "string" || gate.check === "" ||
      typeof gate.expect !== "string" || gate.expect === "") return null;
  return sha256(JSON.stringify([
    "unlazy.gate-definition",
    1,
    gate.check,
    gate.expect,
    gate.cwd === null || gate.cwd === undefined ? null : String(gate.cwd),
  ]));
}

export function automaticEvidencePrefix(definitionDigest) {
  if (!/^[a-f0-9]{64}$/.test(String(definitionDigest || ""))) {
    throw new Error("automatic evidence needs a full lowercase SHA-256 definition digest");
  }
  return "automatic-evidence=v1; definition-sha256=" + definitionDigest + ";";
}

export function classifyGateEvidence(gate) {
  const evidence = gate && gate.evidence === null ? "" : String((gate && gate.evidence) || "");
  if (evidence === "" || /^pending$/i.test(evidence)) return "pending";
  const definitionDigest = gateDefinitionDigest(gate);
  if (definitionDigest !== null) {
    const prefix = automaticEvidencePrefix(definitionDigest);
    const decidingFields = evidence.slice(prefix.length);
    const success = decidingFields.match(
      /^ exit=0; EXPECT=matched; output-sha256=[a-f0-9]{64}; output-bytes=(0|[1-9][0-9]{0,6}); shell=./,
    );
    if (evidence.length <= MAX_AUTOMATIC_EVIDENCE_CHARS && evidence.startsWith(prefix) &&
        success && Number(success[1]) <= MAX_CHECK_OUTPUT_BYTES) {
      return "automatic-current";
    }
  }
  if (evidence.startsWith("automatic-evidence=") || evidence.startsWith("exit=0; shell=")) {
    return "automatic-stale";
  }
  return "human";
}

export function gateState(gate, abandoned) {
  if (abandoned.has(gate.id)) return "abandoned";
  if (!gate.checked) return "unmet";
  const evidence = classifyGateEvidence(gate);
  const runnable = gateDefinitionDigest(gate) !== null;
  if (runnable) return evidence === "automatic-current" ? "met" : "stale-unmet";
  if (evidence === "pending") return "unmet-no-evidence";
  if (evidence === "automatic-current" || evidence === "automatic-stale") return "stale-unmet";
  return "met";
}
