# Windows side

The nine checks are listed in [SKILL.md](SKILL.md) under "Checks: two classes, nine kinds". **Windows runs the same nine.** This file is what differs on this side: how the app starts, how you connect, what you prove after connect, and what you ask before editing.

The Electron renderer is Chromium. It runs HTML, CSS, and DOM. Treat it as web. Do not design a third platform from scratch.

Shell differences are different. **Mac cannot check these. The report must list them**, so the user does not think they were covered:

- Windows native menus
- Tray icon and notifications
- DPI scaling
- Line-height drift from system CJK font fallback
- Installer behavior and file associations
- Native file dialogs

## Channel: the user starts, the main agent connects

**Do not start a Windows GUI over SSH. An SSH foreground launch fails silently** — no error, no window. That is already a hard rule in the target repo. Do not try.

Correct order:

**First, give the user this command to run themselves in PowerShell on the Windows machine.** Port from wiring `launch.debugPort`, or `9222`:

```powershell
& "<full path of the app executable>" --remote-debugging-port=<port>
```

Derive the executable path from the first item of wiring `launch.command`. If you cannot, ask. **Give the command as-is. Do not rewrite it. Do not wrap it.**

**Second, attach from Mac** at `http://<windows.host>:<port>` — `windows.host` defaults to `127.0.0.1`, and is the Windows machine's address when it is a second machine.

**That is the whole difference.** Main-file step 6 already starts the app and attaches; here the user performs the start. Everything from the attach onward — proving the four capabilities, all nine checks — is that file unchanged.

If connect fails, **stop the Windows run**, name the port, and say the app must start in an interactive user session. Do not try to start it yourself.

## Count first, wait for a yes, then edit

Windows still edits class A violations, but **count first**. After the checks, tell the user:

- How many sites this run would edit
- How many rebuild-and-restart cycles the edits need

Edit only after they say continue. They may answer "report only this time": turn every item into a finding, do not edit, and the report says this run did not edit and why.

**Edits happen on Windows, in this session. Do not bring them back to Mac.** This trip exists to cover behavior Mac cannot see. Pushing the fix to Mac means you found it and cannot change or verify it.

## This trip is not AFK

Tell the user: **they start at least once; if they let the skill edit, they start once more per repair round.** When you count, say the expected number. Do not blur it into "once".
