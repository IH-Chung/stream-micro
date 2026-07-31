# OpenCode Desktop: selecting an existing Session

## Question

Can the Stream Micro Python service tell OpenCode Desktop to open or select a
specific existing Session in its graphical interface?

## Conclusion

**No supported OpenCode API, CLI flag, or documented desktop deep link currently
does this.** The local OpenCode server API can read and operate on Session data,
but it does not own the Desktop application's active tab or route.

`POST /tui/select-session` must not be used as a substitute: its contract is
explicitly to navigate the **TUI**, not the Desktop GUI. It can return success
while the Desktop window remains on another Session.

## Evidence

### Server API

- OpenCode's official [Server API: Sessions](https://opencode.ai/docs/server#sessions)
  documents Session listing, creation, retrieval, updates, messages and other
  Session operations. It does not define a Desktop-navigation operation.
- OpenCode's official [Server API: TUI](https://opencode.ai/docs/server#tui)
  exposes UI control specifically for the terminal interface.
- The locally running OpenCode `1.18.7` OpenAPI document at
  `http://127.0.0.1:4096/doc` defines `POST /tui/select-session` as:
  "Navigate the TUI to display the specified session." Its request is only a
  `sessionID`; it has no Desktop window/tab target.
- The same local OpenAPI document exposes `/api/session/active`, but describes
  it as foreground Session drains owned by the **OpenCode process**. It is an
  execution-state endpoint, not a Desktop GUI selection endpoint.

### Desktop deep links

- The official Desktop source's
  [deep-links.ts](https://github.com/anomalyco/opencode/blob/017a5977d2107092007623e507fc5c6eb337d3b2/packages/app/src/pages/layout/deep-links.ts)
  accepts only these application deep links:

  - `opencode://open-project?directory=...`
  - `opencode://new-session?directory=...&prompt=...`

  It has no deep link that identifies an existing Session.
- The Desktop main process forwards `opencode://` links to the renderer, rather
  than providing a separate Session-selection interface. See
  [Desktop main process](https://github.com/anomalyco/opencode/blob/017a5977d2107092007623e507fc5c6eb337d3b2/packages/desktop/src/main/index.ts#L192-L208).
- On this Windows installation, the `opencode` URI registration invokes
  `OpenCode.exe "%1"`, confirming that such links are delivered to the
  Desktop app. The installed package contains the same `open-project` and
  `new-session` handlers, but no existing-session handler.

### CLI and remote debugging

- `opencode --session <id>` resumes a Session in a new **terminal TUI**. It is
  not a command to navigate an already-running Desktop GUI.
- The installed Desktop process was not launched with an Electron
  `--remote-debugging-port` argument. The packaged application source only
  enables this development facility outside the packaged build, so it is not a
  stable integration surface for Stream Micro.

## Recommendation for Stream Micro

1. Use the OpenCode HTTP API as the authoritative interface for discovery,
   Session titles, project directories, recency, and agent/status data.
2. Do **not** report `/tui/select-session` as Desktop navigation, and remove it
   from any Desktop-switch success path.
3. If selecting the Desktop GUI remains a requirement, implement it as an
   explicitly labelled, best-effort Windows automation adapter. Its job is to
   focus OpenCode and use the Desktop's own visible Session picker/search UI.
   It needs verification after each OpenCode Desktop update and a clearly
   distinguishable failure result.
4. Prefer a future official Desktop Session-navigation API/deep link if
   OpenCode adds one; then replace the automation adapter without changing the
   Stream Deck button contract.

This separation is important: API-first behavior is reliable for agent work;
Windows automation is a compatibility fallback for a GUI feature OpenCode does
not currently expose programmatically.
