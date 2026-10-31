import assert from "node:assert/strict";
import {spawn, execFileSync} from "node:child_process";
import {readFileSync, writeFileSync} from "node:fs";

const [executorPath, command, root] = process.argv.slice(2);
const statePath = `${root}/native-sessions.json`;
let sessions;
try { sessions = JSON.parse(readFileSync(statePath, "utf8")); } catch { sessions = []; }
const save = () => writeFileSync(statePath, JSON.stringify(sessions));
const receipt = value => ({content: [{type: "text", text: JSON.stringify(value)}]});
const processes = new Map();
let sequence = 0;

async function output(id) {
  const run = processes.get(id);
  if (!run.output && run.code === null)
    await new Promise(resolve => {
      const done = () => {
        clearTimeout(timer);
        run.child.off("readable-output", done);
        resolve();
      };
      const timer = setTimeout(done, 30);
      run.child.once("readable-output", done);
    });
  const result = {output: run.output};
  run.output = "";
  if (run.code === null) result.session_id = id;
  else { result.exit_code = run.code; processes.delete(id); }
  return result;
}

const tools = {
  async exec_command(args) {
    const id = ++sequence;
    const child = spawn("bash", ["-c", args.cmd], {
      cwd: args.cwd, env: process.env, detached: true, stdio: ["pipe", "pipe", "pipe"],
    });
    const run = {child, output: "", code: null};
    processes.set(id, run);
    for (const stream of [child.stdout, child.stderr])
      stream.on("data", data => { run.output += data; child.emit("readable-output"); });
    child.on("close", code => { run.code = code; child.emit("readable-output"); });
    return output(id);
  },
  async write_stdin(args) {
    const run = processes.get(args.session_id);
    if (args.chars) run.child.stdin.write(args.chars);
    return output(args.session_id);
  },
  async mcp__codex_app__send_message_to_thread(args) {
    sessions = JSON.parse(readFileSync(statePath, "utf8"));
    if (args.model !== undefined) {
      assert.equal(args.model, "gpt-5.6-sol");
      assert.equal(args.thinking, "high");
    }
    const session = sessions.find(row => row.id === args.threadId);
    assert.ok(session);
    const cwd = session.cwd;
    assert.equal(execFileSync("git", ["branch", "--show-current"], {cwd, encoding: "utf8"}).trim(), "issue-61");
    session.prompt ||= args.prompt;
    session.messages = [...(session.messages || []), args.prompt];
    session.active = true;
    save();
    return receipt({threadId: session.id});
  },
  async mcp__codex_app__read_thread(args) {
    const session = sessions.find(row => row.id === args.threadId);
    assert.ok(session);
    return receipt({thread: {id: session.id, cwd: session.cwd,
      status: {type: session.active ? "active" : "notLoaded"}},
    turns: [{id: "turn", status: session.active ? "inProgress" : "interrupted"}]});
  },
  async mcp__codex_app__set_thread_archived(args) {
    assert.equal(args.archived, true);
    if (process.env.FAKE_NATIVE_STOP_FAIL) throw new Error("fixture archive refusal");
    const session = sessions.find(row => row.id === args.threadId);
    assert.ok(session);
    session.active = false;
    save();
    return receipt({threadId: session.id, archived: true});
  },
};

try {
  const execute = eval(readFileSync(executorPath, "utf8"));
  const result = await execute(tools, command);
  process.stdout.write(result.output);
  process.exitCode = result.exitCode;
} finally {
  for (const run of processes.values()) {
    try { process.kill(-run.child.pid, "SIGTERM"); } catch {}
  }
}
