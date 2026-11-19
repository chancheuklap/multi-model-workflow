import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { test } from "node:test";
import { fileURLToPath, pathToFileURL } from "node:url";
import { inspect } from "node:util";
import {
  type Identifier,
  isBindingElement,
  isCallExpression,
  isExportDeclaration,
  isExpressionWithTypeArguments,
  isExternalModuleReference,
  isHeritageClause,
  isIdentifier,
  isImportDeclaration,
  isImportEqualsDeclaration,
  isImportTypeNode,
  isInterfaceDeclaration,
  isNamedExports,
  isNamedImports,
  isShorthandPropertyAssignment,
  isStringLiteral,
  isTypeNode,
  type Node,
  NodeFlags,
  type SourceFile,
  SyntaxKind,
} from "typescript/unstable/ast";
import { API, type Project, SymbolFlags } from "typescript/unstable/sync";
import { checkView } from "../frontends/view.ts";
import {
  type CheckResult,
  EC,
  LEVEL,
  type Rule,
  type Spec,
  stateRules,
  type Verdict,
} from "../ir.ts";
import { compile } from "../pipeline.ts";

const scripts = path.join(path.dirname(fileURLToPath(import.meta.url)), "..");

const sources = (target: string) => {
  const full = path.join(scripts, target);
  if (!fs.statSync(full).isDirectory()) return [target];
  return fs
    .readdirSync(full, { recursive: true, encoding: "utf8" })
    .map((entry) => path.join(target, entry))
    .filter((file) => fs.statSync(path.join(scripts, file)).isFile());
};

const RECORD = `
import { registerHooks } from "node:module";
const edges = [];
registerHooks({
  resolve(specifier, context, nextResolve) {
    const resolved = nextResolve(specifier, context);
    if (context.parentURL !== import.meta.url) edges.push([context.parentURL, resolved.url]);
    return resolved;
  },
});
for (const url of process.argv.slice(1)) await import(url);
console.log(JSON.stringify(edges));
`;
const loads = (...targets: string[]) => {
  const urls = targets.flatMap(sources).map((file) => pathToFileURL(path.join(scripts, file)).href);
  const out = execFileSync(process.execPath, ["--input-type=module", "-e", RECORD, ...urls], {
    encoding: "utf8",
  });
  const name = (url: string) =>
    url.startsWith("file:") ? path.relative(scripts, fileURLToPath(url)) : url;
  return (JSON.parse(out) as string[][]).map(([from, to]) => [name(from), name(to)]);
};

const runtimeGlobals = new Set([
  "process", "require", "globalThis", "global", "Deno", "Bun", "Buffer",
  "setImmediate", "clearImmediate", "fetch",
]);
const isReference = (node: Identifier) => {
  const parent = node.parent;
  if (!parent) return false;
  if ("label" in parent && parent.label === node) return false;
  if (isBindingElement(parent) && parent.propertyName === node) return false;
  return !("name" in parent && parent.name === node) || isShorthandPropertyAssignment(parent);
};

const inspectSources = <T>(
  files: string[],
  inspectSource: (source: SourceFile, file: string, project: Project) => T[],
) => {
  const api = new API({ cwd: scripts });
  try {
    const config = path.join(scripts, "tsconfig.json");
    const snapshot = api.updateSnapshot({ openProjects: [config] });
    const project = snapshot.getProject(config);
    assert.ok(project, `TypeScript did not load ${config}`);
    return files.flatMap((file) => {
      const source = project.program.getSourceFile(path.join(scripts, file));
      assert.ok(source, `TypeScript did not load ${file}`);
      return inspectSource(source, file, project);
    });
  } finally {
    api.close();
  }
};

const forbiddenUses = (files: string[]) =>
  inspectSources(files, (source, file, project) => {
    const uses: string[] = [];
    const walk = (node: Node, runtime: boolean): void => {
      if (isImportDeclaration(node) || isExportDeclaration(node)) return;
      if (isImportTypeNode(node)) {
        uses.push(`${file} uses type import()`);
        return;
      }
      const hasRuntime = runtime
        && !(node.flags & NodeFlags.Ambient)
        && !isInterfaceDeclaration(node)
        && !(isHeritageClause(node) && node.token === SyntaxKind.ImplementsKeyword)
        && !(isTypeNode(node) && !isExpressionWithTypeArguments(node));
      if (hasRuntime && isCallExpression(node) && node.expression.kind === SyntaxKind.ImportKeyword) {
        uses.push(`${file} uses import()`);
      }
      if (hasRuntime && isIdentifier(node) && runtimeGlobals.has(node.text) && isReference(node)) {
        const local = project.checker.resolveName(node.text, SymbolFlags.Value, node, true);
        const declaration = (local?.valueDeclaration ?? local?.declarations[0])?.resolve();
        if (!declaration || declaration.flags & NodeFlags.Ambient)
          uses.push(`${file} uses ${node.text}`);
      }
      node.forEachChild((child) => walk(child, hasRuntime));
    };
    walk(source, true);
    return uses;
  });

const typeSpecifier = (node: Node) => {
  if (isImportDeclaration(node)) {
    const clause = node.importClause;
    const named = clause?.namedBindings;
    if (clause?.phaseModifier === SyntaxKind.TypeKeyword
      || (named && isNamedImports(named) && named.elements.some((item) => item.isTypeOnly)))
      return node.moduleSpecifier;
  } else if (isExportDeclaration(node)) {
    const named = node.exportClause;
    if (node.isTypeOnly
      || (named && isNamedExports(named) && named.elements.some((item) => item.isTypeOnly)))
      return node.moduleSpecifier;
  } else if (isImportEqualsDeclaration(node)
    && node.isTypeOnly && isExternalModuleReference(node.moduleReference)) {
    return node.moduleReference.expression;
  }
};

const typeImports = (files: string[]) =>
  inspectSources(files, (source, file) => source.statements.flatMap<[string, string]>((node) => {
    const specifier = typeSpecifier(node);
    if (!specifier || !isStringLiteral(specifier)) return [];
    const target = specifier.text;
    return [[file, target.startsWith("./") || target.startsWith("../")
      ? path.join(path.dirname(file), target)
      : `non-relative module ${target}`]];
  }));

test("ir.ts imports nothing", () => {
  assert.deepEqual(loads("ir.ts"), []);
  assert.deepEqual(typeImports(["ir.ts"]), []);
});

test("each pass imports only ir.ts", () => {
  const files = sources("passes");
  assert.deepEqual(
    files.filter((file) => !file.endsWith(".ts")),
    [],
  );
  const found = loads("passes");
  assert.ok(found.length > 0);
  for (const [from, to] of found) assert.equal(to, "ir.ts", `${from} imports ${to}`);
  for (const [from, to] of typeImports(files))
    assert.equal(to, "ir.ts", `${from} imports types from ${to}`);
});

test("pipeline.ts reaches no node: module", () => {
  assert.deepEqual(
    loads("pipeline.ts").filter(([, to]) => to.startsWith("node:")),
    [],
  );
  for (const [, to] of typeImports(["pipeline.ts"]))
    assert.equal(to, "ir.ts", `pipeline.ts imports types from ${to}`);
});

test("ir.ts, the passes, pipeline.ts, the frontends, the backends, and every file they load are .ts files that use no listed runtime global or import()", () => {
  const targets = ["ir.ts", "passes", "pipeline.ts", "frontends", "backends"];
  const reached = loads(...targets).flatMap(([, to]) => (to.startsWith("node:") ? [] : [to]));
  const files = [...new Set([...targets.flatMap(sources), ...reached])];
  assert.deepEqual(
    files.filter((file) => !file.endsWith(".ts")),
    [],
  );
  assert.deepEqual(forbiddenUses(files), []);
});

test("no frontend or backend loads a node: module when imported, even through another file", () => {
  for (const folder of ["frontends", "backends"]) {
    const files = fs
      .readdirSync(path.join(scripts, folder), { encoding: "utf8", recursive: true })
      .filter((f) => f.endsWith(".ts"));
    assert.ok(files.length > 0, folder);
    for (const f of files)
      for (const [, to] of loads(path.join(folder, f)))
        assert.ok(!to.startsWith("node:"), `${folder}/${f} reaches ${to}`);
  }
});

const small: Rule = { kind: "invariant", name: "Small" };

const noView = checkView({}, inspect);

const holding = (spec: Spec) => {
  const verdicts: Verdict[] = [];
  for (const rule of stateRules(spec))
    verdicts.push({ rule, outcome: "holds", messages: undefined });
  return verdicts;
};

const twoStates = (breaks: Rule[], property = "Settles"): CheckResult => ({
  spec: {
    module: "Two",
    variables: ["x"],
    invariants: ["Small"],
    properties: [property],
    deadlock: false,
    written: [],
    folder: "",
  },
  paths: undefined,
  graph: {
    states: new Map([
      ["1", { vars: { x: 0 }, start: true, breaks: [] }],
      ["2", { vars: { x: 1 }, start: false, breaks }],
    ]),
    steps: [{ from: "1", to: "2", action: "Grow" }],
  },
  rules: [{ rule: small, outcome: breaks.length ? "broken" : "holds", messages: undefined }],
  properties: [
    {
      rule: { kind: "property", name: property },
      outcome: breaks.length ? "broken" : "holds",
      messages: [
        {
          code: EC.TLC_STATE_PRINT2,
          level: LEVEL.STATE,
          body: ["1: <Initial predicate>", "x = 0"],
        },
      ],
      bug: undefined,
      initialOnly: false,
    },
  ],
  exit: breaks.length ? 1 : 0,
  stop: undefined,
  drawing: undefined,
  states: { distinct: 2, initial: 1, complete: true, cut: false },
  messages: [{ code: EC.TLC_FINISHED, level: LEVEL.NONE, body: ["Finished in 394ms at (T)"] }],
});

const body = (files: Map<string, Iterable<string | Uint8Array>>, name: string) => {
  let text = "";
  for (const part of files.get(name) ?? [])
    text += typeof part === "string" ? part : new TextDecoder().decode(part);
  return text;
};

test("the pipeline turns a hand-built graph into the out folder's files with no TLC", () => {
  const broken = compile(twoStates([small]), noView);
  assert.equal(broken.exit, 1);
  assert.deepEqual(
    [...broken.files.keys()],
    ["chart.mmd", "report.md", "tlc.out", "tlc-Settles.out"],
  );
  assert.equal(body(broken.files, "report.md"), broken.report);
  assert.equal(body(broken.files, "tlc.out"), "Finished in 00s at (T)\n");
  assert.equal(body(broken.files, "tlc-Settles.out"), "State 1: <Initial predicate>\nx = 0\n");
  assert.equal(
    broken.report,
    [
      "# Two",
      "",
      "TLC reached 2 states and 1 steps. The chart draws 2 states and 1 arrows.",
      "",
      "## Small breaks",
      "The shortest path has 1 step:",
      "0. 0",
      "1. Grow: 1",
      "",
      "## Settles breaks",
      "TLC found a counterexample. It is in tlc-Settles.out.",
    ].join("\n"),
  );
  assert.match(
    body(broken.files, "chart.mmd"),
    /^ {2}(s\d+) --> (s\d+): Grow\n[\s\S]*^ {2}class \2 breaks$/m,
  );

  const holds = compile(twoStates([]), noView);
  assert.equal(holds.exit, 0);
  assert.deepEqual([...holds.files.keys()], ["chart.mmd", "report.md", "tlc.out"]);
  assert.match(holds.report, /^## Rules that hold\nSmall, Settles$/m);
  assert.doesNotMatch(body(holds.files, "chart.mmd"), /breaks/);
});

test("an invariant and a property with one name stay two rules", () => {
  const reportWithSmallProperty = (breaks: Rule[]) => {
    const result = twoStates(breaks);
    const step = result.graph.steps[0];
    result.spec.properties = ["Small"];
    result.properties = [
      {
        rule: { kind: "property", name: "Small" },
        outcome: "broken",
        messages: [],
        bug: { start: "1", path: [{ action: "Grow", state: "2", step }], loop: 1, stutters: true },
        initialOnly: false,
      },
    ];
    return compile(result, noView).report;
  };
  const both = reportWithSmallProperty([small]);
  assert.match(both, /^## Small breaks\nThe shortest path has 1 step:$/m);
  assert.match(
    both,
    /^## Small breaks\nTLC's counterexample is in tlc-Small\.out\. It has 1 step:$/m,
  );
  assert.match(reportWithSmallProperty([]), /^## Rules that hold\nSmall$/m);
});

test("a PROPERTY that breaks with no path writes TLC's counterexample", () => {
  const result = twoStates([]);
  result.properties[0].outcome = "broken";
  const { report, files } = compile(result, noView);
  assert.match(
    report,
    /^## Settles breaks\nTLC found a counterexample\. It is in tlc-Settles\.out\.$/m,
  );
  assert.equal(body(files, "tlc-Settles.out"), "State 1: <Initial predicate>\nx = 0\n");
});

test("a rule named NoDeadlock leaves the deadlock rule a name of its own", () => {
  const holds = (result: CheckResult) => {
    result.spec.deadlock = true;
    result.rules = holding(result.spec);
    return compile(result, noView).report.match(/^## Rules that hold\n(.*)$/m)?.[1];
  };
  const invariant = twoStates([]);
  invariant.spec.invariants = ["NoDeadlock"];
  assert.equal(holds(invariant), "NoDeadlock, CHECK_DEADLOCK, Settles");
  assert.equal(holds(twoStates([], "NoDeadlock")), "Small, CHECK_DEADLOCK, NoDeadlock");
  assert.equal(holds(twoStates([])), "Small, NoDeadlock, Settles");
});

test("a run that does not check for deadlock never names CHECK_DEADLOCK", () => {
  const invariant = twoStates([]);
  invariant.spec.invariants = ["Small", "NoDeadlock"];
  for (const result of [invariant, twoStates([], "NoDeadlock")]) {
    result.rules = holding(result.spec);
    assert.doesNotMatch(compile(result, noView).report, /CHECK_DEADLOCK/);
  }
});
