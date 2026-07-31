import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Button = {
  key_index: number;
  plugin: string | null;
  component: string | null;
  span: number;
  session_id: string | null;
  action: string | null;
  action_params: Record<string, unknown>;
  window_binding: Record<string, string> | null;
};
type OllamaQuotaConfig = {
  enabled?: boolean;
  cookie_value?: string;
  settings_url?: string;
  cookie_name?: string;
  request_timeout_seconds?: number;
  refresh_interval_seconds?: number;
};
type PluginConfig =
  | { enabled?: boolean; endpoints?: string[] }
  | OllamaQuotaConfig;
type Config = {
  stream_deck: { brightness: number; device_serial: string | null };
  plugins: Record<string, PluginConfig>;
  buttons: Button[];
};
type Session = { id: string; title: string; state: string; project: string | null };
type PluginManifest = { id: string; name: string; components: string[]; actions: string[] };
type PluginHealth = { connected: boolean; detail: string; endpoint?: string | null };
type PluginSnapshot = {
  health: PluginHealth;
  sessions?: unknown[];
  signals?: Record<string, string | number | null> | null;
};
type BridgeStatus = {
  selected_session_id?: string | null;
  device: { connected: boolean; detail: string; key_count?: number };
  plugins?: Record<string, PluginSnapshot>;
};

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/${path}`, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error((await response.json().catch(() => ({}))).detail || "Bridge unavailable");
  }
  return response.json();
}

function displayName(value: string | null) {
  return value ? value.replace(/_/g, " ").replace(/\b\w/g, (letter: string) => letter.toUpperCase()) : "Not configured";
}

const SESSION_STATE_COLORS: Record<string, string> = {
  idle: "#ffffff",
  running: "#4d9de5",
  waiting: "#e5a23b",
  completed: "#4de57a",
  error: "#e55d5d",
  disconnected: "#555555",
};

function sessionStateColor(state: string) {
  return SESSION_STATE_COLORS[state] ?? "#71819a";
}

function OllamaQuotaCard({ config, status, updateConfig }: {
  config: Config | null;
  status: BridgeStatus | null;
  updateConfig: (change: (current: Config) => Config) => void;
}) {
  const pluginConfig = config?.plugins?.ollama_quota as OllamaQuotaConfig | undefined;
  const snapshot = status?.plugins?.ollama_quota;
  const health = snapshot?.health;
  const signals = snapshot?.signals;

  const setField = (field: keyof OllamaQuotaConfig, value: string | number | boolean) => {
    updateConfig((current) => ({
      ...current,
      plugins: {
        ...current.plugins,
        ollama_quota: { ...current.plugins?.ollama_quota, [field]: value } as OllamaQuotaConfig,
      },
    }));
  };

  const formatReset = (value: string | number | null | undefined) => {
    if (!value || typeof value !== "string") return "—";
    try {
      return new Date(value).toLocaleString();
    } catch {
      return value;
    }
  };

  const pctColor = (pct: number | null | undefined) => {
    if (pct == null) return "#71819a";
    if (pct >= 90) return "#ef4444";
    if (pct >= 70) return "#f59e0b";
    return "#4de57a";
  };

  return <section className="panel ollama-card">
    <p>OLLAMA USAGE</p>
    <h2>Quota</h2>
    <div className="ollama-cookie-field">
      <label>Session cookie value
        <input
          type="password"
          placeholder="Paste ollama.com __Secure-session cookie value"
          value={pluginConfig?.cookie_value ?? ""}
          onChange={(event) => setField("cookie_value", event.target.value)}
        />
      </label>
      <p className="ollama-hint">Sign in at ollama.com, open DevTools → Application → Cookies, copy the <code>__Secure-session</code> value.</p>
    </div>
    <details className="ollama-advanced">
      <summary>Advanced settings</summary>
      <label>Settings URL
        <input type="text" value={pluginConfig?.settings_url ?? "https://ollama.com/settings"} onChange={(event) => setField("settings_url", event.target.value)} />
      </label>
      <label>Cookie name
        <input type="text" value={pluginConfig?.cookie_name ?? "__Secure-session"} onChange={(event) => setField("cookie_name", event.target.value)} />
      </label>
      <label>Request timeout (seconds)
        <input type="number" min={1} value={pluginConfig?.request_timeout_seconds ?? 15} onChange={(event) => setField("request_timeout_seconds", Number(event.target.value))} />
      </label>
      <label>Refresh interval (seconds)
        <input type="number" min={1} value={pluginConfig?.refresh_interval_seconds ?? 60} onChange={(event) => setField("refresh_interval_seconds", Number(event.target.value))} />
      </label>
    </details>
    {health && (
      <div className={`ollama-health ${health.connected ? "is-connected" : "is-error"}`}>
        <span className="health-dot" />
        <span>{health.detail}</span>
      </div>
    )}
    {signals && (
      <div className="ollama-usage-grid">
        <div className="usage-bar">
          <div className="usage-bar-label"><span>Session</span><b style={{ color: pctColor(signals.session_percent as number | null) }}>{signals.session_percent != null ? `${signals.session_percent}%` : "—"}</b></div>
          <div className="usage-bar-track"><div className="usage-bar-fill" style={{ width: `${signals.session_percent ?? 0}%`, background: pctColor(signals.session_percent as number | null) }} /></div>
          <small>Resets: {formatReset(signals.session_reset_at)}</small>
        </div>
        <div className="usage-bar">
          <div className="usage-bar-label"><span>Weekly</span><b style={{ color: pctColor(signals.weekly_percent as number | null) }}>{signals.weekly_percent != null ? `${signals.weekly_percent}%` : "—"}</b></div>
          <div className="usage-bar-track"><div className="usage-bar-fill" style={{ width: `${signals.weekly_percent ?? 0}%`, background: pctColor(signals.weekly_percent as number | null) }} /></div>
          <small>Resets: {formatReset(signals.weekly_reset_at)}</small>
        </div>
      </div>
    )}
  </section>;
}

function App() {
  const [config, setConfig] = useState<Config | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [manifests, setManifests] = useState<PluginManifest[]>([]);
  const [status, setStatus] = useState<BridgeStatus | null>(null);
  const [editingKey, setEditingKey] = useState(0);
  const [dirty, setDirty] = useState(false);
  const dirtyRef = useRef(false);
  const refreshInFlightRef = useRef(false);
  const [notice, setNotice] = useState("Connecting to local Bridge...");
  const [dragSource, setDragSource] = useState<number | null>(null);
  const [dragOver, setDragOver] = useState<number | null>(null);

  const refresh = async (replaceLocalConfig = false) => {
    if (refreshInFlightRef.current) return;
    refreshInFlightRef.current = true;
    try {
      const [nextConfig, nextSessions, nextManifests, nextStatus] = await Promise.all([
        api<Config>("config"),
        api<Session[]>("opencode/sessions"),
        api<PluginManifest[]>("plugins"),
        api<BridgeStatus>("status"),
      ]);
      if (replaceLocalConfig || !dirtyRef.current) setConfig(nextConfig);
      setSessions(nextSessions);
      setManifests(nextManifests);
      setStatus(nextStatus);
      if (!dirtyRef.current) setNotice("");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Bridge unavailable");
    } finally {
      refreshInFlightRef.current = false;
    }
  };

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  }, []);

  const updateConfig = (change: (current: Config) => Config) => {
    setConfig((current) => (current ? change(current) : current));
    dirtyRef.current = true;
    setDirty(true);
    setNotice("Configuration changed. Save to apply it to the physical Deck.");
  };

  const selectedBinding = config?.buttons.find((button) => button.key_index === editingKey) ?? null;
  const selectedManifest = manifests.find((manifest) => manifest.id === selectedBinding?.plugin) ?? null;

  // Build span zone lookup: key_index -> zone parent Button
  const spanZones: Map<number, Button> = new Map();
  for (const button of config?.buttons ?? []) {
    if (button.plugin && button.component === "session") {
      for (let i = button.key_index; i < button.key_index + Math.max(button.span, 1); i++) {
        spanZones.set(i, button);
      }
    }
  }

  const sessionFor = (keyIndex: number) => {
    const parent = spanZones.get(keyIndex);
    if (!parent) return null;
    // When span > 1, sessions are auto-assigned by slot — ignore session_id.
    // session_id only applies to span=1 (single-key pinned to one session).
    if (parent.span > 1) {
      const slot = keyIndex - parent.key_index;
      return sessions[slot] ?? null;
    }
    if (parent.session_id) {
      return sessions.find((s) => s.id === parent.session_id) ?? null;
    }
    return sessions[0] ?? null;
  };

  const isZoneParent = (keyIndex: number) => {
    const parent = spanZones.get(keyIndex);
    return parent !== undefined && parent.key_index === keyIndex;
  };

  const updateBinding = (change: Partial<Button>) => {
    updateConfig((current) => ({
      ...current,
      buttons: current.buttons.map((button) =>
        button.key_index === editingKey ? { ...button, ...change } : button,
      ),
    }));
  };

  // When span changes, auto-clear child keys and session_id
  const changeSpan = (newSpan: number) => {
    const span = Math.max(1, Math.min(15 - editingKey, newSpan));
    updateConfig((current) => ({
      ...current,
      buttons: current.buttons.map((button) => {
        if (button.key_index === editingKey) return { ...button, span, session_id: span > 1 ? null : button.session_id };
        if (button.key_index > editingKey && button.key_index < editingKey + span) {
          return { ...button, plugin: null, component: null, action: null, session_id: null, action_params: {}, window_binding: null, span: 1 };
        }
        return button;
      }),
    }));
  };

  // zoneParent(keyIndex): returns the zone parent Button for the given key, or null.
  const zoneParent = (keyIndex: number, buttons: Button[]): Button | null => {
    for (const b of buttons) {
      if (b.plugin && b.component === "session") {
        const span = Math.max(b.span, 1);
        if (keyIndex >= b.key_index && keyIndex < b.key_index + span) return b;
      }
    }
    return null;
  };

  // canDropZone: checks if source zone fits at target without overflow or overlap.
  const canDropZone = (
    sourceParent: Button | null,
    targetKey: number,
    buttons: Button[],
  ): boolean => {
    if (!sourceParent) return true; // single key always fits
    const span = Math.max(sourceParent.span, 1);
    if (targetKey + span > 15) return false; // overflow right edge
    // Check overlap with OTHER zones (not the source itself)
    for (const b of buttons) {
      if (!b.plugin || b.component !== "session") continue;
      if (b.key_index === sourceParent.key_index) continue;
      const bSpan = Math.max(b.span, 1);
      const bEnd = b.key_index + bSpan;
      const srcEnd = targetKey + span;
      if (targetKey < bEnd && srcEnd > b.key_index) return false; // overlap
    }
    return true;
  };

  // emptyButton: returns a cleared (unassigned) button at the given key_index.
  const emptyButton = (keyIndex: number): Button => ({
    key_index: keyIndex,
    plugin: null,
    component: null,
    span: 1,
    session_id: null,
    action: null,
    action_params: {},
    window_binding: null,
  });

  // swapKeys: swaps button configurations between sourceKey and targetKey,
  // handling span zones as atomic units. Returns new buttons array or null if invalid.
  const swapKeys = (sourceKey: number, targetKey: number, buttons: Button[]): Button[] | null => {
    if (sourceKey === targetKey) return null;
    const srcParent = zoneParent(sourceKey, buttons);
    const tgtParent = zoneParent(targetKey, buttons);

    // If either is a span zone, validate the swap fits
    if (srcParent && !canDropZone(srcParent, targetKey, buttons)) return null;
    if (tgtParent && !canDropZone(tgtParent, sourceKey, buttons)) return null;

    // Determine the source and target key ranges
    const srcStart = srcParent ? srcParent.key_index : sourceKey;
    const srcSpan = srcParent ? Math.max(srcParent.span, 1) : 1;
    const srcEnd = srcStart + srcSpan; // exclusive

    const tgtStart = tgtParent ? tgtParent.key_index : targetKey;
    const tgtSpan = tgtParent ? Math.max(tgtParent.span, 1) : 1;
    const tgtEnd = tgtStart + tgtSpan; // exclusive

    // If zones overlap (one contains the other), reject
    if (srcStart < tgtEnd && srcEnd > tgtStart && srcStart !== tgtStart) return null;
    if (srcStart === tgtStart) return null; // same zone

    // Build the new button configs
    const newButtons = buttons.map((b) => ({ ...b }));

    // Helper: get config for a key position (the parent's config or the individual button's)
    const getConfig = (key: number): Button => {
      const parent = zoneParent(key, buttons);
      if (parent && parent.key_index !== key) {
        // child key — config is empty (children are always cleared)
        return emptyButton(key);
      }
      return { ...buttons.find((b) => b.key_index === key)! };
    };

    const srcConfig = getConfig(sourceKey);
    const tgtConfig = getConfig(targetKey);

    // Place source config at target position
    // If source is a span zone parent, keep its span; adjust key_index
    if (srcParent) {
      newButtons[targetKey] = {
        ...srcConfig,
        key_index: targetKey,
        span: srcSpan,
        // span > 1: clear session_id (auto-assign by slot)
        session_id: srcSpan > 1 ? null : srcConfig.session_id,
      };
    } else {
      newButtons[targetKey] = { ...srcConfig, key_index: targetKey, span: 1 };
    }

    // Place target config at source position
    if (tgtParent) {
      newButtons[sourceKey] = {
        ...tgtConfig,
        key_index: sourceKey,
        span: tgtSpan,
        session_id: tgtSpan > 1 ? null : tgtConfig.session_id,
      };
    } else {
      newButtons[sourceKey] = { ...tgtConfig, key_index: sourceKey, span: 1 };
    }

    // Clear child keys in both zones (old source area and old target area)
    // Old source zone children (keys between srcStart+1 and srcEnd)
    for (let i = srcStart + 1; i < srcEnd; i++) {
      if (i !== sourceKey && i !== targetKey) {
        newButtons[i] = emptyButton(i);
      }
    }
    // Old target zone children
    for (let i = tgtStart + 1; i < tgtEnd; i++) {
      if (i !== sourceKey && i !== targetKey) {
        newButtons[i] = emptyButton(i);
      }
    }

    // Clear NEW child keys in moved source zone (around targetKey)
    if (srcParent && srcSpan > 1) {
      for (let i = targetKey + 1; i < targetKey + srcSpan; i++) {
        if (i !== sourceKey) {
          newButtons[i] = emptyButton(i);
        }
      }
    }
    // Clear NEW child keys in moved target zone (around sourceKey)
    if (tgtParent && tgtSpan > 1) {
      for (let i = sourceKey + 1; i < sourceKey + tgtSpan; i++) {
        if (i !== targetKey) {
          newButtons[i] = emptyButton(i);
        }
      }
    }

    // Ensure key_index matches array position for all buttons
    return newButtons.map((b, i) => ({ ...b, key_index: i }));
  };

  const handleDragStart = (keyIndex: number) => {
    setDragSource(keyIndex);
  };

  const handleDragEnd = () => {
    setDragSource(null);
    setDragOver(null);
  };

  const handleDragOver = (event: React.DragEvent, keyIndex: number) => {
    if (dragSource === null || dragSource === keyIndex) return;
    event.preventDefault();
    setDragOver(keyIndex);
  };

  const handleDragLeave = () => {
    setDragOver(null);
  };

  const handleDrop = (keyIndex: number) => {
    if (dragSource === null || dragSource === keyIndex) {
      setDragSource(null);
      setDragOver(null);
      return;
    }
    if (!config) {
      setDragSource(null);
      setDragOver(null);
      return;
    }
    const swapped = swapKeys(dragSource, keyIndex, config.buttons);
    if (swapped) {
      updateConfig((current) => ({ ...current, buttons: swapped }));
      setEditingKey(keyIndex);
      setNotice(`Moved key ${dragSource + 1} to key ${keyIndex + 1}. Save to apply.`);
    } else {
      setNotice("Cannot drop here — span zone would overflow or overlap.");
    }
    setDragSource(null);
    setDragOver(null);
  };

  const changePlugin = (pluginId: string) => {
    if (!pluginId) {
      updateBinding({
        plugin: null,
        component: null,
        span: 1,
        action: null,
        session_id: null,
        action_params: {},
        window_binding: null,
      });
      return;
    }
    const plugin = manifests.find((manifest) => manifest.id === pluginId);
    updateBinding({
      plugin: pluginId,
      component: plugin?.components[0] ?? null,
      span: 1,
      action: plugin?.actions[0] ?? null,
      session_id: null,
      action_params: {},
      window_binding: null,
    });
  };

  const changeComponent = (component: string) => {
    updateBinding({
      component: component || null,
      action: selectedManifest?.actions[0] ?? null,
      session_id: null,
      action_params: {},
    });
  };

  const save = async () => {
    if (!config || !dirtyRef.current) return;
    try {
      const saved = await api<Config>("config", { method: "PUT", body: JSON.stringify(config) });
      setConfig(saved);
      dirtyRef.current = false;
      setDirty(false);
      setNotice("Saved. The physical Deck updates on its next refresh.");
    } catch (error) {
      setNotice(error instanceof Error ? error.message : "Could not save configuration");
    }
  };

  return <main className="app-shell">
    <header className="topbar">
      <div className="brand"><span className="brand-mark">DB</span><div><p>LOCAL CONTROL SURFACE</p><h1>Deck Bridge</h1></div></div>
      <div className="topbar-right">
        <span className={`connection ${status?.device.connected ? "online" : "offline"}`}><i /> {status?.device.connected ? "MK.2 connected" : "Deck offline"}</span>
        <button onClick={() => void refresh(true)}>Refresh</button>
        <button className="primary" disabled={!dirty} onClick={() => void save()}>{dirty ? "Save changes" : "Saved"}</button>
      </div>
    </header>
    {notice && <div className="notice">{notice}</div>}
    <div className="workspace">
      <section className="deck-panel panel">
        <div className="section-heading">
          <div><p>MK.2 CONFIGURATION PREVIEW</p><h2>Choose a key to edit</h2><span>This browser preview never runs a key action. Only the physical Stream Deck does.</span></div>
          <div className="session-count"><b>{sessions.length}</b><span>live sessions</span></div>
        </div>
        <div className="deck-frame"><div className="deck-grid">
          {Array.from({ length: 15 }, (_, index) => {
            const button = config?.buttons.find((item) => item.key_index === index);
            const session = sessionFor(index);
            const parent = spanZones.get(index);
            const isChild = parent !== undefined && parent.key_index !== index;
            const isParent = parent !== undefined && parent.key_index === index;
            const label = session?.title ?? (isChild ? "Session slot" : displayName(button?.component ?? null));
            const sublabel = session?.project ?? (isChild ? `Slot ${index - (parent?.key_index ?? 0) + 1}` : button?.plugin ? displayName(button.plugin) : "Unassigned");
            const state = session?.state ?? (button?.action ? displayName(button.action) : "No action");
            return <button
              key={index}
              type="button"
              draggable
              title={`Edit key ${index + 1}: ${label} — drag to rearrange`}
              className={`deck-key ${session ? "session-key" : "utility-key"} ${editingKey === index ? "is-editing" : ""} ${isParent && parent && parent.span > 1 ? "is-zone-parent" : ""} ${isChild ? "is-zone-child" : ""} ${dragSource === index ? "is-dragging" : ""} ${dragOver === index && dragSource !== null && dragSource !== index ? "is-drop-target" : ""}`}
              aria-pressed={editingKey === index}
              onClick={() => setEditingKey(index)}
              onDragStart={() => handleDragStart(index)}
              onDragEnd={handleDragEnd}
              onDragOver={(event) => handleDragOver(event, index)}
              onDragLeave={handleDragLeave}
              onDrop={() => handleDrop(index)}
            ><span className="key-index">{index + 1}</span><strong>{label}</strong><small>{sublabel}</small><em>{state}</em><span className="drag-handle" aria-hidden="true">⠿</span></button>;
          })}
        </div></div>
        <div className="deck-legend"><span><i className="legend-dot editing-dot" /> Editing key</span><span><i className="legend-dot session-dot" /> Live Session display</span><span><i className="legend-dot" /> Other / unassigned</span></div>
      </section>

      <aside className="detail-column">
        <section className="panel key-editor">
          <p>KEY CONFIGURATION</p>
          <h2>Key {editingKey + 1}</h2>
          <span className="editor-hint">Changes stay in this page until you choose Save. Clicking this preview cannot focus or control OpenChamber.</span>
          <label>Plugin
            <select value={selectedBinding?.plugin ?? ""} onChange={(event) => changePlugin(event.target.value)}>
              <option value="">No plugin (unassigned)</option>
              {manifests.map((plugin) => <option key={plugin.id} value={plugin.id}>{plugin.name}</option>)}
            </select>
          </label>
          <label>Display component
            <select disabled={!selectedManifest} value={selectedBinding?.component ?? ""} onChange={(event) => changeComponent(event.target.value)}>
              {!selectedManifest && <option value="">Choose a plugin first</option>}
              {selectedManifest?.components.map((component) => <option key={component} value={component}>{displayName(component)}</option>)}
            </select>
          </label>
          {selectedBinding?.component === "session" && (
            <label>Number of keys (span)
              <input type="number" min={1} max={15 - editingKey} value={selectedBinding?.span ?? 1} onChange={(event) => changeSpan(Number(event.target.value))} />
            </label>
          )}
          <label>Physical-key action
            <select disabled={!selectedManifest} value={selectedBinding?.action ?? ""} onChange={(event) => updateBinding({ action: event.target.value || null, action_params: {} })}>
              <option value="">No action</option>
              {selectedManifest?.actions.map((action) => <option key={action} value={action}>{displayName(action)}</option>)}
            </select>
          </label>
          <div className="binding-explainer">
            {selectedBinding?.plugin === "opencode" && selectedBinding.component === "session" ? <>
              <b>Session zone (span {selectedBinding.span})</b><span>This key and {(selectedBinding.span ?? 1) - 1} key{(selectedBinding.span ?? 1) > 2 ? "s" : ""} to its right show live Sessions. Each physical press focuses that slot's Session in OpenChamber.</span>
              <small>{selectedBinding.action === "select_session" ? "Physical press: focus this slot's Session in OpenChamber." : "Physical press: no Session focus action configured."}</small>
            </> : selectedBinding?.plugin ? <><b>{displayName(selectedBinding.component)}</b><span>This key renders the selected Plugin component when that Plugin supplies it.</span><small>Physical action: {displayName(selectedBinding.action)}</small></> : <><b>Unassigned key</b><span>Choose a Plugin and Component to define what this key displays.</span><small>No physical action is configured.</small></>}
          </div>
          {selectedBinding?.plugin === "opencode" && selectedBinding.component === "session" && isZoneParent(editingKey) && (selectedBinding.span ?? 1) === 1 && (() => {
            const assigned = selectedBinding.session_id ? sessions.find((session) => session.id === selectedBinding.session_id) : null;
            return <div className="session-picker">
              <div className="session-picker-head">
                <p>SESSION ASSIGNMENT</p>
                {selectedBinding.session_id && <button type="button" className="ghost-btn" onClick={() => updateBinding({ session_id: null })}>{assigned ? "Clear session" : "Session not found — clear"}</button>}
              </div>
              {selectedBinding.session_id && !assigned && <p className="session-not-found">Session not found. It may have closed. Clear the assignment to pick a new one.</p>}
              <div className="session-list">
                {sessions.map((session) => (
                  <button
                    key={session.id}
                    type="button"
                    className={`session-item ${selectedBinding.session_id === session.id ? "is-selected" : ""}`}
                    onClick={() => updateBinding({ session_id: session.id })}
                  >
                    <span className="session-state-dot" style={{ background: sessionStateColor(session.state) }} />
                    <span className="session-item-main">
                      <strong>{session.title || "Untitled session"}</strong>
                      <small>{session.project ?? "No project"}</small>
                    </span>
                    <em>{session.state}</em>
                  </button>
                ))}
                {sessions.length === 0 && <p className="session-list-empty">No live sessions available.</p>}
              </div>
            </div>;
          })()}
        </section>
        <section className="panel device-card"><p>PHYSICAL DECK</p><div><b>{status?.device.connected ? "Ready" : "Waiting"}</b><span>{status?.device.detail || "Checking hardware"}</span></div><label>Brightness<input type="range" min="0" max="100" value={config?.stream_deck.brightness ?? 40} onChange={(event) => updateConfig((current) => ({ ...current, stream_deck: { ...current.stream_deck, brightness: Number(event.target.value) } }))} /></label></section>
        <OllamaQuotaCard config={config} status={status} updateConfig={updateConfig} />
      </aside>
    </div>
  </main>;
}

createRoot(document.getElementById("root")!).render(<App />);
