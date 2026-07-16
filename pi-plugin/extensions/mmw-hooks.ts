/**
 * mmw pi 宿主接线:分诊注入 + 红线闸 + 提交记账。
 *
 * 事件映射（与其他宿主镜像的分诊、红线、记账语义同源）:
 * - session_start / session_compact → 置待注入标记,下一次 before_agent_start 把
 *   hooks/session-triage.sh 的 stdout 以 message 注入一次(pi 的 session_start 只能通知 UI,
 *   可注入消息的是 before_agent_start,见 pi docs/extensions.md)。
 * - tool_call(bash) → hooks/guard-redline.sh:exit 2 = 红线命中——有 UI 弹 confirm 人批,
 *   无 UI(headless)fail-closed 直接 block;其他非零退出按 CC hook 语义不拦但留痕。
 * - tool_result(bash, git commit/git -C) → hooks/record-step.sh 记账(commit 即进度)。
 *
 * 脚本入参契约:命令文本经 argv[1] 与 MMW_TOOL_COMMAND 双通道传入;MMW_PLUGIN_ROOT 指插件根。
 */
import { execFile } from "node:child_process";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const PLUGIN_ROOT = dirname(dirname(fileURLToPath(import.meta.url)));
const HOOKS_DIR = join(PLUGIN_ROOT, "hooks");

interface HookRun {
	code: number;
	stdout: string;
	stderr: string;
}

function runHook(script: string, command: string, timeoutMs: number): Promise<HookRun> {
	return new Promise((resolve) => {
		execFile(
			"bash",
			[join(HOOKS_DIR, script), command],
			{
				timeout: timeoutMs,
				cwd: process.cwd(),
				env: { ...process.env, MMW_TOOL_COMMAND: command, MMW_PLUGIN_ROOT: PLUGIN_ROOT },
			},
			(err, stdout, stderr) => {
				const code = err && typeof (err as NodeJS.ErrnoException & { code?: unknown }).code === "number"
					? ((err as unknown as { code: number }).code)
					: err
						? 1
						: 0;
				resolve({ code, stdout: String(stdout ?? ""), stderr: String(stderr ?? "") });
			},
		);
	});
}

function isGitCommitLike(command: string): boolean {
	return /\bgit\s+commit\b/.test(command) || /\bgit\s+-C\b/.test(command);
}

export default function mmwHooks(pi: any) {
	let pendingTriage = true; // 会话首个回合注入一次

	pi.on("session_start", async () => {
		pendingTriage = true;
	});

	pi.on("session_compact", async () => {
		// compaction 恢复后重报书签(两态一门:仅开场与 compaction 后注锚,不逐条消息)
		pendingTriage = true;
	});

	pi.on("before_agent_start", async (_event: any, _ctx: any) => {
		if (!pendingTriage) return;
		pendingTriage = false;
		const triage = await runHook("session-triage.sh", "", 10_000);
		if (triage.code !== 0 || !triage.stdout.trim()) return; // 不在管辖 worktree/无任务:安静跳过
		return {
			message: {
				customType: "mmw-triage",
				content: triage.stdout.trim(),
				display: true,
			},
		};
	});

	pi.on("tool_call", async (event: any, ctx: any) => {
		if (event.toolName !== "bash") return;
		const command = String(event.input?.command ?? "");
		if (!command) return;
		const guard = await runHook("guard-redline.sh", command, 5_000);
		if (guard.code === 0) return;
		if (guard.code !== 2) {
			// 守卫脚本自身异常:按 CC hook 语义不拦,但必须留痕(失败可见)
			ctx.ui?.notify?.(`mmw guard-redline 异常(exit ${guard.code}):${guard.stderr.trim().slice(0, 200)}`, "warning");
			return;
		}
		const reason = guard.stderr.trim() || "mmw 红线:出站动作需人工批准";
		if (ctx.hasUI) {
			const ok = await ctx.ui.confirm("mmw 红线拦截", `${reason}\n\n确认放行?`);
			if (ok) return;
			return { block: true, reason: `${reason}(用户拒绝放行)` };
		}
		// headless:无人可批,fail-closed
		return { block: true, reason: `${reason}(无 UI 会话,fail-closed 拒绝;需人批请在交互会话执行)` };
	});

	pi.on("tool_result", async (event: any, ctx: any) => {
		if (event.toolName !== "bash") return;
		const command = String(event.input?.command ?? "");
		if (!command || !isGitCommitLike(command)) return;
		const rec = await runHook("record-step.sh", command, 10_000);
		if (rec.code !== 0) {
			ctx.ui?.notify?.(`mmw record-step 失败(exit ${rec.code}):${rec.stderr.trim().slice(0, 200)}`, "warning");
		}
	});
}
