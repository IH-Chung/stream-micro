# stream-micro

Local Agent Control Surface for **Elgato Stream Deck MK.2 only** (15 keys,
5 × 3). It discovers a locally running OpenCode Server, renders the first five
Sessions on the first row, and provides a local Dashboard at the same address.

## Run

```powershell
uv sync --dev
cd frontend; npm ci; npm run build; cd ..
uv run stream-micro serve
```

Open `http://127.0.0.1:8765`. The first run writes `bridge.yaml`; it is the
Dashboard's versioned source of truth and does not replace the legacy Ollama
`config.yaml`.

## Development hot reload

Run the Bridge with Python reload enabled:

```powershell
uv run stream-micro serve --reload
```

For Dashboard hot reload, run this in a second terminal and open the URL it
prints (normally `http://127.0.0.1:5173`). API requests are proxied to Bridge.

```powershell
cd frontend; npm run dev
```

OpenCode discovery only checks configured and listening **loopback** endpoints.
The configured fallback endpoint is `http://127.0.0.1:4096`. When OpenChamber
Desktop is running, Bridge automatically prefers its local authenticated proxy
so both surfaces use the same OpenCode Server.

## Session-key behavior

- The first row contains five Session keys.
- A Session key directly selects its matching OpenChamber Desktop Session.
- When OpenChamber Desktop is running, Bridge auto-discovers its local control
  server and reads Sessions through its authenticated `/api` proxy. This keeps
  the Deck list and the OpenChamber UI on the same OpenCode Server.

## Plugins

Plugins expose a manifest, configuration validation, a status snapshot, and a
strict allowlist of actions. OpenCode is the interactive plugin. `ollama_quota`
is a separate display-only plugin; enable it in `bridge.yaml` only if you retain
the legacy Ollama configuration.

## Verify

```powershell
uv run pytest
uv run ruff check src tests
uv run pyright src tests
cd frontend; npm run build
```
