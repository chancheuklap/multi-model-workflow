// @ts-nocheck
// Pi 那一侧的编辑后诊断。
//
// Pi 至今没有 hook（0.84.2 的代码里没有 hookEventName 也没有 PostToolUse），它有的
// 是扩展。所以这一家是一份 TypeScript，不是一个 shell 适配器；跑的检查器和另外四家
// 完全一样，都是 diagnostics/check.py。
//
// 用 tool_result 而不是 tool_call 加 tool_execution_end 那一对：tool_result 同时拿得到
// 工具输入和工具结果，还能改结果本身。上一代要维护一个 Map 把两个事件按 toolCallId
// 配对，现在不需要。
//
// 诊断贴在工具结果后面，不另发一条跟进消息：模型在同一个地方看到「这次写入成功了」
// 和「它引入了这些问题」，因果是连着的。

import { execFile } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const HERE = dirname(fileURLToPath(import.meta.url));
const CHECK = resolve(HERE, "..", "check.py");

const EDIT_TOOLS = new Set(["write", "edit", "multiedit", "apply_patch", "str_replace"]);
const PATH_KEYS = ["path", "filePath", "file_path", "abs_path", "absPath"];
const CHECK_TIMEOUT_MS = 120_000;

function pickPath(input: any): string | null {
  if (!input || typeof input !== "object") return null;
  for (const key of PATH_KEYS) {
    const value = input[key];
    if (typeof value === "string" && value.trim()) return value;
  }
  return null;
}

function run(command: string, args: string[], cwd?: string): Promise<string | null> {
  return new Promise((done) => {
    execFile(command, args, { timeout: CHECK_TIMEOUT_MS, cwd }, (error, stdout, stderr) => {
      // check.py 用退出码 2 表示查到问题，正文在 stderr。其他非零一律当作
      // "诊断跑不起来"，安静放过：检查器的故障不该挡住 Pi 干活。
      if (error && (error as any).code === 2) {
        done((stderr || stdout || "").trim() || null);
        return;
      }
      if (error) {
        done(null);
        return;
      }
      done((stdout || "").trim());
    });
  });
}

async function repoRoot(file: string): Promise<string | null> {
  const out = await run("git", ["-C", dirname(file), "rev-parse", "--show-toplevel"]);
  return out || null;
}

export default function (pi: any) {
  pi.on("tool_result", async (event: any) => {
    if (!event || !EDIT_TOOLS.has(event.toolName) || event.isError) return;
    const file = pickPath(event.input);
    if (!file) return;

    const root = await repoRoot(file);
    if (!root) return;

    const findings = await run("python3", [CHECK, "--repo", root, "--changed-only", file]);
    if (!findings) return;

    const note = { type: "text", text: `刚改过的文件有诊断问题，先看一遍再继续：\n${findings}` };
    const existing = Array.isArray(event.content) ? event.content : [];
    return { content: [...existing, note] };
  });
}
