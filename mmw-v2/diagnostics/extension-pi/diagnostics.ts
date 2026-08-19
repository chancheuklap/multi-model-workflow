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
import { appendFileSync, existsSync, realpathSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

// 装进 Pi 的是一条软链，本体在这个仓库里。要先解软链再算 check.py 的位置。
//
// 早先这里直接用 import.meta.url，理由是「Node 解析模块默认走 realpath」。那句话
// 对 Pi 的加载器不成立：2026-08-19 实测它拿到的是软链自己的路径，于是 check.py 被
// 算成 ~/.pi/agent/check.py，每次调用都是 Errno 2 文件不存在——而扩展照样把「有
// 诊断问题」那句话贴了上去，看起来像在工作。这个洞是 probe-subagent.sh 撞出来的。
const HERE = dirname(realpathSync(fileURLToPath(import.meta.url)));
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

// 探针：这次触发到底发生了没有，看见了哪个文件。跟四个 shell 适配器的 mmw_trace
// 写同一种行，同一个文件。只在 MMW_DIAG_TRACE 指着一个文件时写。
function trace(file: string | null): void {
  const target = process.env.MMW_DIAG_TRACE;
  if (!target) return;
  try {
    const line = JSON.stringify({ adapter: "pi", event: "tool_result", files: file ? [file] : [] });
    appendFileSync(target, line + "\n");
  } catch {
    // 探针坏掉不该挡住干活。
  }
}

export default function (pi: any) {
  // check.py 不在就当场喊出来，而且不挂处理器。
  //
  // 不加这一道的话，坏掉长得像在工作：python3 跑一个不存在的文件自己就退 2，而退出码 2
  // 在这里的约定是「查到问题了，正文在 stderr」，于是 Python 那句 "can't open file" 被
  // 当成诊断贴进工具结果，模型看到的是「有诊断问题」加一句它看不懂的报错。实测发生过。
  if (!existsSync(CHECK)) {
    console.error(`[mmw-diagnostics] 找不到 ${CHECK}，这一侧的编辑后诊断没有装上。跑一次 mmw-v2/install.sh`);
    return;
  }

  pi.on("tool_result", async (event: any) => {
    if (!event || !EDIT_TOOLS.has(event.toolName) || event.isError) return;
    const file = pickPath(event.input);
    if (!file) return;
    trace(file);

    // 不是 git 仓库也要检查，只是没有「改动行」这个概念，所以整份文件都报。
    // 早先这里直接 return，于是在一个还没 git init 的目录里改文件，一条诊断都不报，
    // 而那跟「代码干净」长得一模一样。这跟 hooks/core.sh 的 mmw_diagnose 是同一条规则。
    const root = await repoRoot(file);
    const args = root
      ? [CHECK, "--repo", root, "--changed-only", file]
      : [CHECK, "--repo", dirname(file), file];

    const findings = await run("python3", args);
    if (!findings) return;

    const note = { type: "text", text: `刚改过的文件有诊断问题，先看一遍再继续：\n${findings}` };
    const existing = Array.isArray(event.content) ? event.content : [];
    return { content: [...existing, note] };
  });
}
