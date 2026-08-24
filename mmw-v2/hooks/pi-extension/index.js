// MMW 纪律注入层的 pi 扩展：before_agent_start 返回追加了纪律的系统提示。
// 原件：ponytail pi-extension/index.js @2ed6c52。精确修改：只保留 spec 点名的 before_agent_start
// 一支（ponytail 的 /ponytail 命令、模式记忆、状态栏都建立在本层没有的模式概念上，整段删除）；
// 注入内容换成 discipline/worker.md。pi 的这个事件对 subagent 同样触发，所以 pi 上不存在
// subagent 盲区（docs/specs/discipline-hooks/host-hook-matrix.md ③）。
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { getDisciplineInstructions } = require("../mmw-instructions.js");

export default function mmwDisciplineExtension(pi) {
  pi.on("before_agent_start", async (event) => {
    // Guard a null/undefined event or a missing systemPrompt: don't crash, and
    // don't prepend the literal string "undefined" to the prompt (#439, #440).
    const base = event?.systemPrompt ? `${event.systemPrompt}\n\n` : "";
    return { systemPrompt: `${base}${getDisciplineInstructions("worker")}` };
  });
}
