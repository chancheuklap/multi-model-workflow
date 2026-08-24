#!/usr/bin/env node
// MMW — SessionStart 开场纪律注入 hook。
// 原件：ponytail hooks/ponytail-activate.js @2ed6c52。精确修改：去掉模式标志文件与
// statusline 设置提示（本层没有这两样），注入内容换成 discipline/worker.md。
//
// Runs on every session start:
//   Emits the worker discipline as hidden SessionStart context

const { getDisciplineInstructions } = require('./mmw-instructions');
const { writeHookOutput } = require('./mmw-runtime');

const role = 'worker';

const output = getDisciplineInstructions(role);

try {
  writeHookOutput('SessionStart', role, output);
} catch (e) {
  // Silent fail — stdout closed/EPIPE at hook exit must not surface as a hook failure
}
