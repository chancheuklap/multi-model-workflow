// @ts-nocheck
// Pi 那一侧的编辑后诊断通道。
//
// Pi 没有原生 LSP，也没有 Codex 那种 hooks.json——它有的是扩展。这个扩展做的事和
// Codex 的 PostToolUse hook 完全一样：编辑类工具跑完之后，对被改的文件调
// `mmw toolchain check --changed-only`，把问题交回给 agent。三家调的是同一个命令、
// 同一份规则表、同一批检查器，所以看到的诊断是同一套。
//
// 事件用两个而不是一个：tool_execution_end 只带 toolName / result / isError，
// 不带工具输入，拿不到文件路径；tool_call 带 input 但那时工具还没跑完。所以在
// tool_call 时按 toolCallId 记下路径，在 tool_execution_end 时取出来用。
//
// 事件形状是在 Pi 0.84.1 上跑探针实测的：tool_call 给 toolName="write"、
// input={path, content}、toolCallId；tool_execution_end 给 toolName、isError、
// 同一个 toolCallId。write 工具的路径字段就叫 path。其余编辑类工具的字段名没有逐个
// 实测，所以按 path / filePath / file_path / abs_path 依次试，取到哪个算哪个。

import { execFile } from "node:child_process";

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

function runCheck(file: string): Promise<string | null> {
  return new Promise((resolve) => {
    execFile(
      "mmw",
      ["toolchain", "check", "--changed-only", file],
      { timeout: CHECK_TIMEOUT_MS },
      (error, stdout, stderr) => {
        // 退出码 2 = 查到问题，stderr 里是正文。其他非零一律当作"诊断跑不起来"，
        // 安静放过：检查器的故障不该挡住 Pi 干活。
        if (error && (error as any).code === 2) {
          resolve((stderr || stdout || "").trim() || null);
          return;
        }
        resolve(null);
      },
    );
  });
}

export default function (pi: any) {
  const pending = new Map<string, string>();

  pi.on("tool_call", (event: any) => {
    if (!event || !EDIT_TOOLS.has(event.toolName)) return;
    const file = pickPath(event.input);
    if (file && event.toolCallId) pending.set(event.toolCallId, file);
  });

  pi.on("tool_execution_end", async (event: any, ctx: any) => {
    const file = event?.toolCallId ? pending.get(event.toolCallId) : undefined;
    if (event?.toolCallId) pending.delete(event.toolCallId);
    if (!file || event?.isError) return;

    const findings = await runCheck(file);
    if (!findings) return;

    const target = ctx ?? pi;
    if (typeof target.sendUserMessage !== "function") return;
    // deliverAs "followUp"：接在当前这一轮之后交给 agent，不打断正在跑的工具链。
    await target.sendUserMessage(
      `刚改过的 ${file} 有诊断问题，先看一遍再继续：\n${findings}`,
      { deliverAs: "followUp" },
    );
  });
}
