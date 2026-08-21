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

**First, give the user this command to run themselves in PowerShell on the Windows machine.** Port from wiring `windows.debugPort`. **If the wiring file has no `windows` block** — setup does not ask for one — offer `9222`, let the user change it, and write their answer into wiring before going on. Ask this once per product, here, on the first Windows run:

```powershell
& "<full path of the app executable>" --remote-debugging-port=<windows.debugPort>
```

Derive the executable path from the first item of wiring `launch.command`. If you cannot, ask. **Give the command as-is. Do not rewrite it. Do not wrap it.**

**Second, the main agent connects from Mac.** Use the browser automation's CDP connect entry, URL `http://<windows.host>:<windows.debugPort>` (`host` defaults to `127.0.0.1`; two machines: the Windows machine's address). The module root for `require` is in main-file step 2. After connect, recognize the main window from wiring `mainWindow` `titlePattern` or `urlPattern`.

**Third, the check is automatic.** Main-file step 6's "start the app" becomes the two steps above. The other eight steps stay the same.

If connect fails, **stop the Windows run**, name the port, and say the app must start in an interactive user session. Do not try to start it yourself.

## After connect, prove capabilities

Taking over an existing instance through the debug port yields fewer capabilities than starting the instance. **Connect success is not four capabilities present.** Right after the main window, verify each by actually doing it:

| # | Capability | How | Pass |
| --- | --- | --- | --- |
| 1 | Accessibility-tree snapshot | One ARIA snapshot of the main window | Non-empty, and at least one element with an accessible name |
| 2 | Batch computed style | One `getComputedStyle` on `document.body` | Non-empty `font-family` |
| 3 | Cropped screenshot | One shot of any visible element in the main window | Non-empty bytes |
| 4 | Inject the accessibility engine | Inject its whole script file, located as main-file step 2 says | After inject, the engine's window global is readable |

What each miss does:

| Missing | Effect |
| --- | --- |
| 1 Accessibility-tree snapshot | **Stop.** No element location. None of the nine can run |
| 2 Batch computed style | Skip A1 and A3. Run the other seven |
| 3 Cropped screenshot | Do not skip a check. B2 question 2 judges from structured visual-salience numbers only, and that finding notes there was no screenshot |
| 4 Inject the accessibility engine | Skip A2. Run the other eight |

Skipped check ids go in the report header "Skipped this run". **Do not treat a missing-capability result as a complete QA.**

## Count first, wait for a yes, then edit

Windows still edits class A violations, but **count first**. After the checks, tell the user:

- How many sites this run would edit
- How many rebuild-and-restart cycles the edits need

Edit only after they say continue. They may answer "report only this time": turn every item into a finding, do not edit, and the report says this run did not edit and why.

**Edits happen on Windows, in this session. Do not bring them back to Mac.** This trip exists to cover behavior Mac cannot see. Pushing the fix to Mac means you found it and cannot change or verify it.

## This trip is not AFK

Tell the user: **they start at least once; if they let the skill edit, they start once more per repair round.** When you count, say the expected number. Do not blur it into "once".
