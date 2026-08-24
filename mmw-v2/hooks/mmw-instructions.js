#!/usr/bin/env node
// Shared MMW discipline builder for the hook scripts and the pi extension.
// 原件：ponytail hooks/ponytail-instructions.js @2ed6c52。精确修改：按角色（worker /
// verifier）读 discipline/<role>.md，不再按模式过滤技能正文；文件读不到时只回一行标记
// （ponytail 的 fallback 是一份改写副本，会与承重句校验冲突）。

const fs = require('fs');
const path = require('path');

const ROLES = ['worker', 'verifier'];
const DEFAULT_ROLE = 'worker';
const DISCIPLINE_DIR = path.join(__dirname, 'discipline');

function normalizeRole(role) {
  if (typeof role !== 'string') return null;
  const normalized = role.trim().toLowerCase();
  return ROLES.includes(normalized) ? normalized : null;
}

function disciplinePath(role) {
  return path.join(DISCIPLINE_DIR, (normalizeRole(role) || DEFAULT_ROLE) + '.md');
}

function getFallbackInstructions(role, reason) {
  return 'MMW DISCIPLINE ACTIVE — role: ' + role + ' (discipline file unreadable: ' + reason + ')';
}

function getDisciplineInstructions(role) {
  const effectiveRole = normalizeRole(role) || DEFAULT_ROLE;
  const file = disciplinePath(effectiveRole);
  try {
    return fs.readFileSync(file, 'utf8').replace(/\r\n/g, '\n').trim();
  } catch (e) {
    return getFallbackInstructions(effectiveRole, file);
  }
}

module.exports = {
  DEFAULT_ROLE,
  ROLES,
  disciplinePath,
  getDisciplineInstructions,
  getFallbackInstructions,
  normalizeRole,
};
