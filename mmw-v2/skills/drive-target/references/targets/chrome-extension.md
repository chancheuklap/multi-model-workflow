# Target: chrome-extension

**Designed from the platform's rules, not measured on a product.** No repository holds
one yet; this file and `ChromeExtensionAdapter` are the extension point filled in from
the Manifest V3 specification, and the first real extension will correct them. Contract:
`target.kind: chrome-extension`. Adapter class: `ChromeExtensionAdapter`.

## `discover` prints

```json
{"extension_dir": "/abs/path/to/dist", "extension_id": "abcdefghijklmnopabcdefghijklmnop",
 "popup": "popup.html"}
```

The extension id is derived at load time from the key, so it cannot be written in a
contract; `discover` loads or reads it. `popup` is the entry page (default `popup.html`).

## The seven answers

1. **attach** — a persistent context is launched with `--load-extension=<extension_dir>`;
   a page is opened in it. The **popup is opened as a plain tab**: a real popup closes on
   blur, so nothing could be driven in it; opened as a tab it has no 400 px constraint of
   its own, which is why the driver's viewport override is not optional on this target —
   the fixed popup size is one entry of `viewports`. Attach therefore takes the web shape.
   The extension is its own identity; the state is put before attach when it lives on a
   remote service, after when it lives in `chrome.storage`.
2. **ready** — a service worker is alive in the context. MV3 recycles it after about
   thirty idle seconds, so this is the clearest case of `ready` being a condition
   re-checked between scenes.
3. **address** — `chrome-extension://<extension_id>/<popup><route>`.
4. **release** — the persistent context is closed.
5. **transport** — the reach script writes `chrome.storage` through the extension's own
   API, or the remote service through its API; `via: storage` here means writing the
   storage area directly.
6. **observe** — the surface must be where the behaviour's effect really lands: an
   effect on the remote service is read from the remote API; reading `chrome.storage`
   proves only that the client wrote itself. A row whose effect never leaves the client
   leaves `observe` empty, as `contract-format.md` already allows.
7. **break the transport** — clear `chrome.storage` and stub the remote API to refuse
   writes, then restore.

## What the repository provides

The manifest and an entry page carrying `data-screen="<mount>"`; the reach script; a
stubbed extension API for `dev:` capabilities. Non-HTTP `calls` are written
`chrome.runtime.sendMessage <type>`; the wiring check performs the trigger and reads
`observe` as above.
