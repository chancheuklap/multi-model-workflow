// Stop hook 的本地状态：sha256、原子写、文件锁、状态文件路径。
// 原件：unlazy scripts/lib/gates.mjs @265fbd5 里被 stop-hook.mjs 用到的那几段，逐字抄录。
// 精确修改：状态目录 .unlazy → .mmw，钩子状态文件 .unlazy-hook-state.json → .mmw-hook-state.json，
// 去掉 scope 参数（本层没有 pipeline scope）。
// Zero dependencies. Node 16+.

import {
  closeSync, existsSync, fsyncSync, lstatSync, mkdirSync,
  openSync, readFileSync, renameSync, statSync, unlinkSync,
  writeFileSync,
} from "node:fs";
import { createHash, randomBytes } from "node:crypto";
import { dirname, join, resolve } from "node:path";

export const MMW_DIR = ".mmw";
export const LOCK_DIR = join(MMW_DIR, "locks");

export const sleep = (ms) => new Promise((done) => setTimeout(done, ms));
export const sha256 = (value) => createHash("sha256").update(String(value)).digest("hex");

const WINDOWS_TRANSIENT_FS_ERRORS = new Set(["EACCES", "EBUSY", "EPERM"]);
const SYNC_SLEEP_CELL = new Int32Array(new SharedArrayBuffer(4));

function isTransientWindowsFsError(error) {
  return process.platform === "win32" && WINDOWS_TRANSIENT_FS_ERRORS.has(error && error.code);
}

function replaceAtomic(temp, target) {
  const deadline = Date.now() + 2000;
  let delay = 5;
  for (;;) {
    try {
      renameSync(temp, target);
      return;
    } catch (error) {
      const remaining = deadline - Date.now();
      if (!isTransientWindowsFsError(error) || remaining <= 0) throw error;
      Atomics.wait(SYNC_SLEEP_CELL, 0, 0, Math.min(delay, remaining));
      delay = Math.min(delay * 2, 100);
    }
  }
}

export function hookStatePath(root) {
  return join(root, ".mmw-hook-state.json");
}

function assertSafeStatePath(root, target) {
  const stateRoot = join(resolve(root), MMW_DIR);
  if (existsSync(stateRoot)) {
    const info = lstatSync(stateRoot);
    if (info.isSymbolicLink() || !info.isDirectory()) throw new Error(stateRoot + " must be a real directory, not a link or file");
  }
  const parent = dirname(target);
  mkdirSync(parent, { recursive: true, mode: 0o700 });
  const info = lstatSync(parent);
  if (info.isSymbolicLink() || !info.isDirectory()) throw new Error(parent + " must be a real directory");
}

export function writeAtomic(file, text, options = {}) {
  const target = resolve(file);
  if (options.root) assertSafeStatePath(options.root, target);
  else {
    const parent = dirname(target);
    mkdirSync(parent, { recursive: true });
    const info = lstatSync(parent);
    if (info.isSymbolicLink() || !info.isDirectory()) throw new Error(parent + " must be a real directory");
  }
  try {
    const existing = lstatSync(target);
    if (existing.isSymbolicLink()) throw new Error("refusing to replace symlink " + target);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  let temp = "";
  let fd = null;
  for (let attempt = 0; attempt < 8; attempt++) {
    temp = target + "." + process.pid + "." + randomBytes(8).toString("hex") + ".tmp";
    try { fd = openSync(temp, "wx", 0o600); break; }
    catch (error) { if (error.code !== "EEXIST") throw error; }
  }
  if (fd === null) throw new Error("could not create a unique temporary file for " + target);
  try {
    writeFileSync(fd, String(text), "utf8");
    fsyncSync(fd);
    closeSync(fd);
    fd = null;
    replaceAtomic(temp, target);
  } finally {
    if (fd !== null) try { closeSync(fd); } catch { /* ignore */ }
    if (temp) try { unlinkSync(temp); } catch { /* renamed or absent */ }
  }
}

function lockDirectory(root) {
  const directory = join(resolve(root), LOCK_DIR);
  assertSafeStatePath(root, directory);
  mkdirSync(directory, { recursive: true, mode: 0o700 });
  const info = lstatSync(directory);
  if (info.isSymbolicLink() || !info.isDirectory()) throw new Error(directory + " must be a real directory");
  return directory;
}

export async function withFileLock(root, target, fn, options = {}) {
  const timeoutMs = options.timeoutMs === undefined ? 30000 : options.timeoutMs;
  const lock = join(lockDirectory(root), sha256(resolve(target)).slice(0, 24) + ".filelock");
  const deadline = Date.now() + timeoutMs;
  const token = randomBytes(16).toString("hex");
  let fd = null;
  for (;;) {
    try { fd = openSync(lock, "wx", 0o600); break; }
    catch (error) {
      // On Windows, opening or inspecting an existing file held by another
      // process can surface as EPERM/EACCES/EBUSY rather than EEXIST. Treat
      // only those platform-specific sharing errors as lock contention.
      if (error.code !== "EEXIST" && !isTransientWindowsFsError(error)) throw error;
      // Never unlink a lock observed by path: between stat and unlink its
      // prior owner can release and a successor can acquire the same name
      // (the classic ABA race). Missing-after-EEXIST simply means retry. A
      // crashed owner's lock fails closed at timeout and can be removed by a
      // human after inspecting its JSON metadata.
      let missing = false;
      try { statSync(lock); } catch (statError) {
        if (statError.code === "ENOENT") missing = true;
        else if (!isTransientWindowsFsError(statError)) throw statError;
      }
      if (Date.now() >= deadline) {
        throw new Error("timed out waiting for lock on " + target + " (last filesystem error: " + error.code + ")");
      }
      if (missing && error.code === "EEXIST") continue;
      await sleep(15 + Math.floor(Math.random() * 25));
    }
  }
  let identified = false;
  try {
    writeFileSync(fd, JSON.stringify({ token, pid: process.pid, target: resolve(target), at: Date.now() }));
    identified = true;
  } catch { /* leave for manual cleanup rather than risk deleting a successor */ }
  try { return await fn(); }
  finally {
    try { closeSync(fd); } catch { /* ignore */ }
    if (identified) {
      const deadline = Date.now() + 2000;
      let delay = 5;
      for (;;) {
        try {
          const current = JSON.parse(readFileSync(lock, "utf8"));
          if (current.token === token) unlinkSync(lock);
          break;
        } catch (error) {
          if (error && error.code === "ENOENT") break;
          const remaining = deadline - Date.now();
          if (!isTransientWindowsFsError(error) || remaining <= 0) break;
          await sleep(Math.min(delay, remaining));
          delay = Math.min(delay * 2, 100);
        }
      }
    }
  }
}
