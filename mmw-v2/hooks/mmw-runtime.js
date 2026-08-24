// MMW 纪律注入层的分流 runtime。原件：ponytail hooks/ponytail-runtime.js @2ed6c52。
// 精确修改：去掉 mode 状态文件（本层没有 lite/full/ultra 模式）；宿主判定加 --host 命令行
// 声明（install.sh 写进各宿主的 hook 配置）与 Grok 的 GROK_HOOK_EVENT；writeHookOutput
// 按本机取证补 Cursor（additional_context / followup_message）、Grok（Stop 的 decision:block）
// 与 Stop 事件的 decision 形状。pi 没有 JSON 协议，它的形状在 pi-extension/index.js。
const path = require('path');

// ponytail: VS Code Copilot never sets COPILOT_PLUGIN_DATA — it only injects
// CLAUDE_PLUGIN_ROOT, pointed at an install path under .vscode/agent-plugins/
// (#528). Without this fallback isCopilot was false, so ponytail assumed
// native Claude Code and emitted the statusline nudge, which VS Code Copilot
// doesn't read.
function isVsCodeCopilotRoot(pluginRoot) {
  if (!pluginRoot) return false;
  return pluginRoot.split(/[\\/]+/).includes('agent-plugins') &&
    pluginRoot.toLowerCase().includes('.vscode');
}

// mmw: 用户级 hook 配置下 Codex 与 Cursor 不给 hook 进程设任何可辨识的环境变量，
// 所以由 install.sh 把宿主名写进命令行；Grok 会把 Claude/Cursor 的配置也扫进来跑，
// 它给 hook 进程设 GROK_HOOK_EVENT，优先于命令行声明。
function argHost() {
  const i = process.argv.indexOf('--host');
  return i === -1 ? '' : String(process.argv[i + 1] || '').trim().toLowerCase();
}

const declaredHost = argHost();
const isGrok = Boolean(process.env.GROK_HOOK_EVENT) || declaredHost === 'grok';
const isCursor = !isGrok && declaredHost === 'cursor';
const isCopilot = !isGrok && !isCursor && (Boolean(process.env.COPILOT_PLUGIN_DATA) ||
  isVsCodeCopilotRoot(process.env.CLAUDE_PLUGIN_ROOT));
const isCodex = !isGrok && !isCursor && !isCopilot && (declaredHost === 'codex' || Boolean(process.env.PLUGIN_DATA));
const isQoder = !isGrok && !isCursor && !isCopilot && !isCodex && Boolean(process.env.QODER_SESSION_ID);

const DISCIPLINE_DIR = path.join(__dirname, 'discipline');

function writeHookOutput(event, role, context = '') {
  if (isCursor) {
    // mmw: Cursor 的 sessionStart / subagentStart 响应读 additional_context（string），
    // stop 响应只有 followup_message（追加后续消息，没有 decision 字段）。本机取证见
    // docs/specs/discipline-hooks/host-hook-matrix.md ①③④。
    if (event === 'Stop') {
      process.stdout.write(JSON.stringify(context ? { followup_message: context } : {}));
      return;
    }
    process.stdout.write(JSON.stringify(context ? { additional_context: context } : {}));
    return;
  }
  if (isGrok) {
    // mmw: Grok 的 SessionStart / SubagentStart 是被动事件（输出不进模型），只有
    // Stop / SubagentStop 的 {"decision":"block","reason"} 会回到模型。取证同上 ④。
    if (event === 'Stop') {
      process.stdout.write(JSON.stringify(context ? { decision: 'block', reason: context } : {}));
      return;
    }
    const output = {};
    if (context) {
      output.hookSpecificOutput = {
        hookEventName: event,
        additionalContext: context,
      };
    }
    process.stdout.write(JSON.stringify(output));
    return;
  }
  if (event === 'Stop') {
    // mmw: Claude 与 Codex（StopCommandOutputWire）同形。
    process.stdout.write(JSON.stringify(context ? { decision: 'block', reason: context } : {}));
    return;
  }
  if (isCopilot) {
    // Copilot reads additionalContext on SessionStart; ignores output elsewhere.
    process.stdout.write(JSON.stringify(
      event === 'SessionStart' && context ? { additionalContext: context } : {}));
    return;
  }
  if (isCodex) {
    const output = { systemMessage: `MMW:${role.toUpperCase()}` };
    if (context) {
      output.hookSpecificOutput = {
        hookEventName: event,
        additionalContext: context,
      };
    }
    process.stdout.write(JSON.stringify(output));
    return;
  }
  if (isQoder) {
    // Qoder: hookSpecificOutput JSON, same shape as Codex minus systemMessage.
    // UserPromptSubmit additionalContext is injected into the Agent's conversation.
    const output = {};
    if (context) {
      output.hookSpecificOutput = {
        hookEventName: event,
        additionalContext: context,
      };
    }
    process.stdout.write(JSON.stringify(output));
    return;
  }
  // Native Claude: SessionStart accepts raw stdout, but SubagentStart needs the
  // hookSpecificOutput JSON form or the context is dropped.
  if (event === 'SubagentStart') {
    process.stdout.write(JSON.stringify(
      { hookSpecificOutput: { hookEventName: event, additionalContext: context } }));
    return;
  }
  process.stdout.write(context);
}

module.exports = {
  DISCIPLINE_DIR,
  declaredHost,
  isCodex,
  isCopilot,
  isCursor,
  isGrok,
  isQoder,
  writeHookOutput,
};
