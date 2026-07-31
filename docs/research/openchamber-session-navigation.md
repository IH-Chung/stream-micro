# OpenChamber: selecting an existing OpenCode Session

## Question

Can a Stream Micro button select an existing OpenCode Session in the
OpenChamber app, without relying on screen coordinates, window dimensions, or
DOM automation?

## Conclusion

**Yes, for OpenChamber Desktop.** It has an application-owned deep-link
contract for exactly this operation:

```text
openchamber://session/<URL-encoded-session-id>
```

On Windows, dispatching that URI invokes the registered OpenChamber Desktop
protocol handler. The Desktop source then focuses its main window, forwards
the ID to the renderer, and the renderer selects the Session by its ID. This
is a real app-level integration path, unlike the previous OpenCode Desktop
coordinate/DevTools workaround.

The ID, not the title, must be the selection key. A title is only presentation
data and can be duplicated.

## Official source evidence

The sources below are pinned to OpenChamber commit
[`9a0f0b8`](https://github.com/openchamber/openchamber/tree/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee),
checked on 2026-07-31.

### Desktop availability and runtime model

- The project documents a Desktop build for **macOS, Windows, and Linux** in
  its [README](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/README.md#L60-L66).
- Its own architecture guide says the Electron Desktop starts the OpenChamber
  web server in the Electron main process and loads the UI from loopback (or
  the packaged UI protocol), rather than treating the OpenCode GUI as the
  navigation surface. [AGENTS.md](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/AGENTS.md#L23-L32)
- OpenChamber can instead connect to an already-running OpenCode server via
  `OPENCODE_HOST` / `OPENCODE_PORT` with `OPENCODE_SKIP_START=true`.
  [README](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/README.md#L112-L121)

This means Stream Micro should keep the current OpenCode HTTP API for
discovery, recency and status, but use OpenChamber only as the GUI target.

### Desktop Session deep link

1. Electron defines `openchamber` as the deep-link scheme and registers itself
   as its default protocol client. [main.mjs](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/electron/main.mjs#L43-L45)
   [main.mjs](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/electron/main.mjs#L179-L185)
2. The shared deep-link vocabulary makes a Session link as
   `openchamber://session/${encodeURIComponent(sessionId)}`. It also accepts
   an optional `dir` query argument at the shared-UI layer.
   [deepLinks.ts](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/apps/deepLinks.ts#L23-L27)
   [deepLinks.ts](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/apps/deepLinks.ts#L65-L72)
   [deepLinks.ts](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/apps/deepLinks.ts#L122-L128)
3. The Electron main process parses `openchamber://session/<id>` and emits the
   `openchamber:open-session` event with that ID.
   [main.mjs](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/electron/main.mjs#L1934-L1951)
   [main.mjs](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/electron/main.mjs#L2188-L2190)
4. A second activation brings the existing foreground/main window forward,
   restoring it if it was minimized. [main.mjs](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/electron/main.mjs#L1178-L1195)
   [main.mjs](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/electron/main.mjs#L5127-L5136)
5. The UI receives the event, activates the Chat tab and calls its Session
   store with the exact Session ID. [App.tsx](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/App.tsx#L596-L612)
   That store resolves the Session directory from its own session/worktree
   metadata before falling back to the current directory.
   [session-ui-store.ts](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/sync/session-ui-store.ts#L585-L634)

### Web/PWA alternative

For browser/PWA OpenChamber, the official URL route is:

```text
http://<openchamber-host>/?session=<URL-encoded-session-id>
```

The PWA's recent-session shortcut generator creates that exact URL, and the
router maps its `session` query parameter to the current Session ID.
[index.html](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/web/index.html#L210-L218)
[router types](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/lib/router/types.ts#L38-L45)
[parseRoute.ts](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/lib/router/parseRoute.ts#L10-L18)
[parseRoute.ts](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/ui/src/lib/router/parseRoute.ts#L40-L49)

That is useful if the user intentionally runs OpenChamber in a browser. It is
not a replacement for Desktop focus: opening a URL can produce or reuse a
browser tab, whose focus behavior is controlled by the browser and Windows.

## CLI and API boundary

OpenChamber's CLI exposes Session listing, creation, sending, forking, status
and messages, but its own documented help has **no select/focus/open existing
GUI Session command**. [commands-session.js](https://github.com/openchamber/openchamber/blob/9a0f0b8aa5ded271615fc20b6c96fd04782ed7ee/packages/web/bin/lib/commands-session.js#L159-L185)

This is not a limitation for the Bridge: the Desktop deep link is the
official GUI-selection mechanism. The Bridge should not call OpenCode's
`/tui/select-session`, because that controls OpenCode's terminal UI rather
than OpenChamber's desktop session view.

## Recommended Stream Micro implementation contract

1. Retain the existing OpenCode-plugin discovery pipeline. It already yields
   the authoritative `session.id`, `session.title`, `session.directory`,
   activity status and recency.
2. Replace the current OpenCode Desktop selection adapter with an
   `OpenChamberDesktopController` on Windows:

   ```python
   uri = f"openchamber://session/{quote(session_id, safe='')}"
   os.startfile(uri)
   ```

   This is semantic app navigation; it contains no coordinates, DOM selectors,
   image matching, viewport assumptions or title matching.
3. Return success only after the OS accepted the protocol launch. Mark the
   button itself as selected immediately; do not promise a verified rendered
   title unless a future OpenChamber API exposes its active Session.
4. If no registered `openchamber` protocol handler exists, return a clear
   failure such as `OpenChamber Desktop is not installed or has not registered
   its openchamber:// handler`. Do not silently fall back to OpenCode Desktop.
5. Treat selection as scoped to the OpenChamber Desktop instance's currently
   selected host. The desktop Session URI carries a Session ID, but Electron's
   native parser currently does not forward the optional `dir` query to its
   event payload. The Session store can normally resolve its directory from
   local metadata, but an ID belonging only to a different remote host cannot
   be guaranteed to resolve in the active instance.

## Verification plan after implementation

Use a known existing Session ID and test these Windows cases on the installed
OpenChamber Desktop build:

1. App visible at a non-maximized arbitrary size: press its Stream Deck key;
   verify the selected Session ID/title in the UI.
2. App maximized: repeat; verify it remains maximized.
3. App minimized: repeat; verify it restores/focuses and selects the Session.
4. Press two different Stream Deck Session keys in sequence; verify the UI
   ends on the second exact ID, including if titles are similar or duplicated.
5. Shut down OpenChamber or unregister its protocol handler; verify Stream
   Micro reports the explicit failure rather than claiming a switch.

These checks validate the operating-system protocol path and application
selection behavior; testing mere `os.startfile` return without inspecting the
app is insufficient.
