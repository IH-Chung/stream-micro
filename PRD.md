# Product Requirements Document (PRD)
# Codex Micro — AI Agent Control Surface

| Field | Value |
|---|---|
| **Document Version** | 1.0 |
| **Product Name** | Codex Micro |
| **SKU** | `kbd-1.0-codex-micro` |
| **Date** | July 26, 2026 |
| **Status** | Research & Specification |
| **Manufacturers** | OpenAI × Work Louder |
| **Price** | $230 USD |
| **Launch Date** | July 15, 2026 |
| **Availability** | Limited run — sold out within 48 hours |

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision & Goals](#3-product-vision--goals)
4. [Target Audience & Personas](#4-target-audience--personas)
5. [Market Context & Competitive Landscape](#5-market-context--competitive-landscape)
6. [Hardware Specifications](#6-hardware-specifications)
7. [Software Architecture](#7-software-architecture)
8. [Feature Requirements](#8-feature-requirements)
9. [User Flows & Interaction Design](#9-user-flows--interaction-design)
10. [Agent Key Status System](#10-agent-key-status-system)
11. [Command Keys & Default Mappings](#11-command-keys--default-mappings)
12. [Analog Controls — Joystick & Dial](#12-analog-controls--joystick--dial)
13. [Push-to-Talk Voice Input](#13-push-to-talk-voice-input)
14. [Layer System](#14-layer-system)
15. [Lighting & Visual Feedback](#15-lighting--visual-feedback)
16. [Configuration & Customization](#16-configuration--customization)
17. [Connectivity & Platform Support](#17-connectivity--platform-support)
18. [Power & Battery](#18-power--battery)
19. [Troubleshooting & Recovery](#19-troubleshooting--recovery)
20. [Out of Box Experience](#20-out-of-box-experience)
21. [Packaging & Inclusions](#21-packaging--inclusions)
22. [Success Metrics](#22-success-metrics)
23. [Risks & Constraints](#23-risks--constraints)
24. [Open Questions](#24-open-questions)
25. [References](#25-references)

---

## 1. Executive Summary

The **Codex Micro** is a limited-run, programmable mechanical macropad — OpenAI's first branded hardware product — co-designed with Montreal keyboard maker **Work Louder** and built on their Creator Micro 2 chassis. Priced at **$230 USD**, it launched July 15, 2026, through the OpenAI Supply Co. store and sold out within 48 hours.

The device is not a keyboard in the traditional sense. It is a **physical control surface for AI coding agents**, designed to sit beside a developer's primary keyboard. Its headline feature is **six frosted Agent Keys** with live RGB status lighting that mirrors the real-time state of up to six parallel Codex agent threads — idle, thinking, complete, needs input, or error — without requiring the developer to switch windows or poll notifications.

Beyond agent monitoring, the Codex Micro provides tactile shortcuts for high-frequency Codex actions (accept/reject code changes, push-to-talk voice input, start new chats, send messages, toggle fast mode), a **reasoning dial** for adjusting how deeply an agent thinks on the fly, and an **analog joystick** for triggering skills and workflows. It connects via USB-C or Bluetooth, supports macOS and Windows, and integrates natively with the ChatGPT desktop app (the required bridge for Agent Key RGB feedback).

The Codex Micro represents a bet that **supervising parallel AI agents** — not writing code line by line — will become the developer's core activity. It treats agent state as a first-class UI problem, bringing ambient, glanceable status from server racks and mixing consoles to the AI development desk.

---

## 2. Problem Statement

### The Core Problem

Developers using OpenAI's Codex AI coding agent spend significant time on **context-switching overhead**:

- **Tabbing back and forth** to check whether an agent is still thinking, has completed, or has silently errored out.
- **Polling multiple windows** to track the status of parallel agent runs, each in its own chat thread.
- **Navigating menus and dropdowns** to approve/reject code changes, adjust reasoning effort, trigger skills, or start new chats.
- **Interrupting flow state** to perform repetitive actions that should be instantaneous.

This friction scales linearly with the number of agents a developer runs in parallel. As AI-assisted development moves toward multi-agent workflows, the cost of monitoring and controlling agents through traditional GUI windows becomes a bottleneck.

### Current Workarounds (and Why They Fall Short)

| Workaround | Limitation |
|---|---|
| Keyboard shortcuts in ChatGPT desktop | No ambient status feedback; must remember combos |
| Desktop notifications | Compete with every other notification; easy to miss |
| Terminal multiplexers | No visual agent state; text-only |
| Elgato Stream Deck | Sends HID keystrokes but has **no awareness** of live Codex thread state; can't light up when an agent errors |
| Standard QMK numpad | Fully remappable but zero Codex integration; no status LEDs |

The fundamental gap: **no existing peripheral receives push-based state data from AI agent platforms.** All current solutions are unidirectional (send commands) or require the developer to actively poll. The Codex Micro is bidirectional — it both sends commands AND receives live thread-state events that it renders as colored LED feedback.

---

## 3. Product Vision & Goals

### Vision Statement

> Make supervising AI agents as tactile and glanceable as monitoring a mixing console — turn agent state into ambient peripheral information that a developer reads without looking away from their code.

### Product Goals

| Goal | Description | Success Indicator |
|---|---|---|
| **G1: Ambient agent visibility** | Surface live agent thread state through RGB lighting without requiring window focus | Agent Keys reflect real-time thread state within 500ms of state change |
| **G2: Tactile action shortcuts** | Reduce high-frequency Codex actions to single keypresses | 90% of common Codex actions (accept, reject, new chat, send, PTT) accessible without alt-tabbing |
| **G3: Reasoning as a physical control** | Make reasoning effort a continuous, user-facing knob rather than a dropdown setting | Developers adjust reasoning effort mid-task without opening any menu |
| **G4: Seamless Codex integration** | Zero-config detection and setup when connected to ChatGPT desktop | Device auto-detected; setup wizard completes in under 60 seconds |
| **G5: General-purpose fallback** | Device remains useful outside Codex as a standard programmable macropad | 5 additional layers configurable via Work Louder Input + VIA |

### Non-Goals

- The Codex Micro is **not** a standalone AI device. It contains no model, no display, and no microphone.
- It is **not** the rumored Jony Ive consumer AI companion device (expected ~2027). The two projects share nothing beyond the OpenAI brand.
- It does **not** replace a primary keyboard. It is a companion peripheral.
- It is **not** designed for casual Codex users. Keyboard shortcuts are free.

---

## 4. Target Audience & Personas

### Primary Persona: "The Agent Orchestrator"

**Name:** Alex Chen
**Role:** Senior software engineer at a mid-size startup
**Workflow:** Runs 3–6 parallel Codex agents simultaneously — one refactoring a module, one writing tests, one debugging, one reviewing a PR, one generating documentation.

**Pain points:**
- Constantly alt-tabbing to check if agents have finished or errored
- Loses flow state when an agent needs approval mid-task
- Finds it tedious to adjust reasoning effort per task through dropdown menus
- Wants to trigger common skills (debug, refactor, PR review) without navigating menus

**Why Codex Micro fits:** Six Agent Keys give Alex a physical dashboard for all parallel agents. The reasoning dial lets them crank up thinking for architecture work, dial it down for boilerplate. Push-to-talk lets them dictate follow-up prompts without touching the keyboard.

### Secondary Persona: "The Flow-State Coder"

**Name:** Jordan Patel
**Role:** Independent developer / consultant
**Workflow:** Runs 1–2 Codex agents at a time for focused coding sessions. Values minimal interruption and tactile satisfaction.

**Pain points:**
- Desktop notifications interrupt focus; misses important agent state changes
- Wants physical confirmation that an action was received (key press > silent shortcut)
- Finds voice input faster than typing follow-up prompts

**Why Codex Micro fits:** Even with 1–2 agents, the RGB feedback prevents "is it still running?" anxiety. Push-to-talk and command keys reduce friction. The joystick serves as both a fidget toy and a skill launcher.

### Tertiary Persona: "The Collector / Enthusiast"

**Name:** Sam Rivera
**Role:** Developer and mechanical keyboard enthusiast
**Workflow:** Heavy Codex user who also appreciates boutique hardware, limited drops, and tasteful design.

**Why Codex Micro fits:** Limited-run collaboration, Work Louder build quality, hot-swapable switches, VIA support, custom icon keycaps. It's both a tool and a collectible artifact of the AI-agent era.

### Anti-Persona: "The Occasional Codex User"

- Uses Codex once a week or less
- Runs a single agent at a time
- Keyboard shortcuts are sufficient
- **Verdict: Skip.** The $230 price is not justified. A $50 QMK numpad or built-in shortcuts cover all needs.

---

## 5. Market Context & Competitive Landscape

### Product Positioning

The Codex Micro occupies a new product category: **AI agent control surfaces**. It is conceptually adjacent to streaming controllers (Elgato Stream Deck), productivity macropads (Work Louder Creator Micro 2, Keychron QMK numpads), and boutique mechanical keyboards — but differentiated by its bidirectional integration with the Codex agent platform.

### Competitive Matrix

| Product | Price | Keys | Display | Agent State Awareness | Reasoning Control | Mic/PTT | Platform |
|---|---|---|---|---|---|---|---|
| **Codex Micro** | $230 | 13 mech + dial + joystick + touch | RGB per-key (no LCD) | ✅ Live Codex thread state via JSON-RPC | ✅ Physical dial | ✅ PTT (uses computer mic) | Mac, Windows |
| Elgato Stream Deck Plus | $200 | 32 LCD keys + dial strip | LCD per-key | ❌ No agent state (unidirectional) | ❌ | ❌ | Mac, Windows |
| Elgato Stream Deck (15-key) | $150 | 15 LCD keys | LCD per-key | ❌ | ❌ | ❌ | Mac, Windows |
| Work Louder Creator Micro 2 | $144–174 | 13 mech + dial + joystick + touch | RGB per-key | ❌ (no Codex firmware) | ❌ | ❌ | Mac, Windows |
| Keychron QMK Numpad | $50–70 | 17 mech | RGB per-key | ❌ | ❌ | ❌ | Mac, Windows, Linux |
| Loupdeck+ | $119 | 15+ dials | LCD + dials | ❌ | ❌ | ❌ | Mac, Windows |

### Key Differentiators

1. **Bidirectional agent state**: The only macropad that receives push-based thread-state events from an AI agent platform and renders them as colored LED feedback. A Stream Deck can trigger hotkeys; it cannot know when an agent errors.
2. **Reasoning dial**: Physical control for reasoning effort — a setting previously buried in dropdown menus and config files. Reframes compute-per-task as a continuous user-facing knob.
3. **Native Codex firmware**: Layer 1 is Codex-native. No third-party plugins or hotkey mappings required. The ChatGPT desktop app auto-detects the device and offers a setup wizard.
4. **Limited-run collectibility**: Sold as a limited drop through OpenAI Supply Co., not a mass-market peripheral. Positions as an artifact of the first AI-agent era.

### Market Risks

- **Price sensitivity**: $230 is 3–4x more expensive than a basic QMK numpad. The value proposition requires running 3+ parallel agents daily.
- **Platform lock-in**: Agent Key RGB feedback requires the ChatGPT desktop app. CLI-only, web-only, or IDE-extension-only Codex users get a static device.
- **Category novelty**: "AI agent control surface" is an unproven product category. If multi-agent supervision doesn't become mainstream, the device's core value proposition narrows.
- **Limited run**: Sold out in 48 hours. No announced restock. Scalper market and DIY alternatives (10+ GitHub projects) emerged immediately.

---

## 6. Hardware Specifications

### Physical Build

| Spec | Detail |
|---|---|
| **Chassis** | Work Louder Creator Micro 2 (reskinned) |
| **Top frame** | CNC machined polycarbonate, unibody, sandblasted finish |
| **Bottom plate** | CNC machined aluminum, sandblasted anodized |
| **Anti-slip** | Strong anti-slip ring on base |
| **Dimensions** | Compact square footprint (sits beside primary keyboard) |
| **Weight** | TBD (aluminum base provides desk stability) |

### Input Controls

| Control | Count | Type | Details |
|---|---|---|---|
| Mechanical switches | 13 | Low-profile POM (clicky) or POK (silent) | 40±10gf actuation, 2.8mm travel, rated 50M keystrokes |
| Agent Keys | 6 (of the 13) | Frosted shine-through RGB keycaps | Top row; live thread-state lighting |
| Command Keys | 7 (of the 13) | Standard keycaps | Bottom rows; default Codex actions |
| Rotary encoder | 1 | Clickable dial | Reasoning effort adjustment / composer navigation |
| Touch sensor | 1 | Capacitive | Cycles through 6 programmable layers |
| Planar joystick | 1 | 2D analog | 4 directional triggers; also functions as fidget input |
| Edge LED strip | 1 | LED-lit acrylic edge | Glows during push-to-talk recording |

### Switch Options

| Option | Switch Type | Actuation Force | Sound | Best For |
|---|---|---|---|---|
| Clicky | POM | 40±10gf | Audible click | Private office, tactile confirmation |
| Silent | POK | 40±10gf | Near-silent | Shared office, recordings, low-noise environments |

Both options have identical software features. The choice is comfort/noise, not performance.

### Keycaps

| Item | Count | Type |
|---|---|---|
| Custom Codex icon keycaps | 32 | 30×1U + 1×2U, PBT and PC material |
| Solid color keycaps | 11 | PBT |
| Rubber joystick cap | 1 | Covers analog stick |

### Lighting

| Feature | Detail |
|---|---|
| Per-key RGB | Full RGB under all 13 keys |
| Agent Key keycaps | Frosted for shine-through status display |
| Edge lighting | LED-lit acrylic edge strip (active during PTT recording) |
| Brightness | Adjustable in Settings > Codex Micro |
| Auto-off | Configurable timeout (default: 3 minutes of inactivity) |
| Re-activation | Lights return on keyboard use or Agent Key status change |

### Connectivity

| Method | Detail |
|---|---|
| USB-C | Wired connection; cable included |
| Bluetooth | Wireless; supports 3 Bluetooth channels |
| Hardware IDs | VID 0x303A, PID 0x8360 |
| Firmware | v0.4.1 (as of launch) |

### Included in Box

| Item | Quantity |
|---|---|
| Codex Micro unit | 1 |
| USB-C to USB-C cable | 1 |
| Codex icon keyset | 32 caps (30×1U, 1×2U) |
| Solid color keycaps | 11 caps |

---

## 7. Software Architecture

### System Architecture Overview

```
┌─────────────┐        JSON-RPC         ┌──────────────────┐      USB-C / BLE      ┌──────────────┐
│  Codex      │ ◄─────────────────────► │  ChatGPT Desktop │ ◄──────────────────► │  Codex Micro │
│  Platform   │   Thread-state events   │  App (Bridge)    │   HID + RGB control   │  (Hardware)  │
│  (Cloud)    │   (idle, thinking,      │                  │   commands             │              │
│             │    running, awaiting   │  - Reads thread  │                        │  13 keys     │
│             │    input, done, error) │    state via     │                        │  Dial        │
│             │                         │    JSON-RPC      │                        │  Joystick    │
│             │                         │  - Translates    │                        │  Touch sensor│
│             │                         │    to LED signals│                        │  RGB LEDs    │
└─────────────┘                         └──────────────────┘                        └──────────────┘
```

### Critical Architecture Constraint

**The hardware does NOT connect directly to Codex's cloud infrastructure.** The ChatGPT desktop app serves as the intermediary bridge:

1. Codex platform streams thread-state events (idle, thinking, running, awaiting input, done, error) via JSON-RPC.
2. ChatGPT desktop app reads these events as the JSON-RPC client.
3. ChatGPT desktop app translates thread-state into RGB LED control signals.
4. LED control signals sent to Codex Micro via USB or Bluetooth.

**Implication:** The Agent Key RGB feedback **requires the ChatGPT desktop app to be running**. Developers using Codex exclusively through CLI, VS Code extension, browser, or JetBrains plugin will see Agent Keys static or dark.

### Protocol Details

| Layer | Protocol | Purpose |
|---|---|---|
| Codex ↔ ChatGPT Desktop | Bidirectional JSON-RPC | Thread-state streaming (Items, Turns, Threads) |
| ChatGPT Desktop ↔ Hardware | USB HID / BLE HID | Key press events (upstream), RGB LED commands (downstream) |
| Hardware ↔ Work Louder Input | USB HID / BLE | Layer configuration, key remapping, firmware updates |
| Hardware ↔ VIA | USB HID | Open-source keymap configuration |

### Software Components

| Software | Role | Required For |
|---|---|---|
| ChatGPT desktop app | Bridge between Codex cloud and hardware; settings UI | Agent Key RGB feedback, Command Key remapping, PTT, joystick/dial config |
| Work Louder Input | Layer management, Bluetooth pairing, resets, general-purpose macros | Layers 2–6, hardware troubleshooting, non-Codex use |
| VIA (open-source) | Keymap configuration | Advanced key remapping, QMK-level customization |

### Settings Location

All Codex-specific configuration is accessible via:
- **ChatGPT desktop app → Settings → Codex Micro**
- Or: Press and hold the dial for 500ms
- Or: Click the Codex Micro icon beside the account name in ChatGPT's sidebar

---

## 8. Feature Requirements

### 8.1 Agent Keys (P0 — Must Have)

**FR-001:** The device shall have 6 frosted Agent Keys in the top row, each capable of displaying RGB status lighting.

**FR-002:** Each Agent Key shall display one of 6 status colors representing the live state of an assigned Codex chat thread:
- White = Idle
- Blue = Thinking
- Green = Complete (with unread update)
- Amber = Requires input (approval/response needed)
- Red = Error
- Off = No assigned chat

**FR-003:** Pressing an Agent Key once shall switch to the associated chat without bringing ChatGPT to the foreground.

**FR-004:** Pressing an Agent Key twice within 350ms shall switch to the associated chat AND bring the ChatGPT window forward.

**FR-005:** The selected chat's Agent Key shall pulse with its status light to indicate active selection.

**FR-006:** The user shall be able to choose which chats the Agent Keys follow via "Agent source" setting:
- Most recent chats (default): 6 most recently updated chats (pinned or unpinned)
- Pinned chats: First 6 chats in Pinned
- Priority chats: Chats waiting for input → unread → active, ordered first
- Custom assignments: User manually assigns a chat to each Agent Key

**FR-007:** When "Custom assignments" is selected, pressing an unassigned Agent Key shall open a new chat. When the chat starts, it is assigned to that key.

**FR-008:** Agent Keys shall NOT be convertible to Command Keys. They are exclusively for agent monitoring.

**FR-009:** RGB status updates shall reflect thread-state changes within 500ms of the event.

### 8.2 Command Keys (P0 — Must Have)

**FR-010:** The device shall have 7 Command Keys (bottom rows) with default mappings:
- Toggle Fast mode on/off
- Approve the current request
- Decline the current request
- Continue the current chat in a new chat
- Start push-to-talk
- Send the message in the composer
- (1 additional configurable key)

**FR-011:** All Command Keys shall be remappable in Settings > Codex Micro. Available actions include:
- Open browser / terminal
- Review changes
- Commit with Git
- Create a pull request
- Attach files or photos
- Manage scheduled tasks
- Change reasoning effort
- Open Skills
- Any enabled ChatGPT desktop command

**FR-012:** When remapping a key to a keycap icon already in use, ChatGPT shall swap the two keycaps' assignments rather than allowing duplicates.

**FR-013:** Standard HID keystrokes from Command Keys (accept, reject, PTT, new chat, send) shall work with any application, not just ChatGPT desktop. These are standard keyboard events.

### 8.3 Analog Joystick (P1 — Should Have)

**FR-014:** The device shall have 1 planar (2D analog) joystick capable of detecting directional push.

**FR-015:** Pushing the joystick far enough from center in any of 4 directions (up, right, down, left) shall trigger a configurable action.

**FR-016:** Default joystick mappings:
- Up: Toggle Plan mode on/off
- Right: Go forward in app history
- Down: Show or hide the sidebar
- Left: Go back in app history

**FR-017:** Each directional action shall be configurable in Settings > Codex Micro to any available ChatGPT desktop command or enabled skill.

### 8.4 Rotary Dial / Encoder (P1 — Should Have)

**FR-018:** The device shall have 1 clickable rotary encoder (dial).

**FR-019:** The dial shall operate in one of two modes (selectable in Settings):
- **Composer navigation mode (default):** Turn dial to move through composer controls/options (with Reasoning selected by default). Press dial to open/select the focused control. When a control/menu is open, the Agent Key immediately to the right of the dial lights red; pressing that key cancels.
- **Reasoning only mode:** Turning the dial opens and adjusts reasoning effort directly. Pressing the dial opens the reasoning slider or its advanced options.

**FR-020:** Pressing and holding the dial for 500ms shall open Codex Micro Settings.

### 8.5 Push-to-Talk (P0 — Must Have)

**FR-021:** The device shall have a dedicated Mic key (bottom row, largest key) that activates push-to-talk voice input using the **computer's** microphone (the device has no microphone of its own).

**FR-022:** Hold the Mic key to start recording; release to stop and submit.

**FR-023:** Double-press the Mic key within 350ms to toggle hands-free (continuous) recording. Press once more to stop.

**FR-024:** During recording, a sea-green light shall move around the keyboard edge.

**FR-025:** While ChatGPT processes speech, the light shall change to a moving white light.

**FR-026:** When the prompt is ready, the light shall turn solid white. Press the Codex key to send.

### 8.6 Touch Sensor & Layer Switching (P1 — Should Have)

**FR-027:** The device shall have 1 capacitive touch sensor (bottom-left) for cycling through up to 6 programmable layers.

**FR-028:** Layer 1 shall be Codex-native (configured via ChatGPT desktop app).

**FR-029:** Layers 2–6 shall be configurable via Work Louder Input app for non-Codex use (other applications, general-purpose macros).

### 8.7 Lighting Control (P2 — Nice to Have)

**FR-030:** The user shall be able to adjust RGB brightness in Settings > Codex Micro.

**FR-031:** The user shall be able to configure auto-off timeout (lights turn off after a period of inactivity, default 3 minutes).

**FR-032:** Lights shall re-activate when the keyboard is used or an Agent Key status changes.

### 8.8 Auto-Detection & Setup (P0 — Must Have)

**FR-033:** When the Codex Micro is connected via USB-C or Bluetooth, the ChatGPT desktop app shall detect it automatically and display a setup wizard.

**FR-034:** On macOS, the setup wizard shall prompt for Input Monitoring permission (required for ChatGPT to respond to key presses).

**FR-035:** After first detection, a "Codex Micro" section shall appear in ChatGPT Settings.

### 8.9 Battery Status (P2 — Nice to Have)

**FR-036:** When the keyboard reports battery status (Bluetooth mode), it shall be visible in Settings > Codex Micro and in the Codex Micro icon's sidebar tooltip.

---

## 9. User Flows & Interaction Design

### Flow 1: First-Time Setup

```
User receives Codex Micro
    │
    ├── Opens ChatGPT desktop app
    ├── Connects Codex Micro via USB-C cable or Bluetooth
    ├── ChatGPT auto-detects device → setup wizard appears
    ├── (macOS) Prompted for Input Monitoring permission → user grants
    ├── User navigates to Settings > Codex Micro
    ├── Chooses Agent source (default: Most recent chats)
    ├── Reviews/adjusts Command Key mappings
    ├── Reviews/adjusts joystick directional mappings
    ├── Reviews/adjusts dial mode (Composer nav vs Reasoning only)
    ├── Adjusts lighting brightness and auto-off timer
    └── Setup complete — Agent Keys light up with current chat statuses
```

**Time to complete:** < 60 seconds (excluding OS permission grant)

### Flow 2: Monitoring Parallel Agents

```
Developer has 4 Codex agents running:
  - Agent A: Refactoring authentication module (thinking → blue)
  - Agent B: Writing unit tests (complete → green)
  - Agent C: Debugging race condition (needs input → amber)
  - Agent D: Generating API documentation (error → red)
    │
    ├── Developer glances at Agent Keys (peripheral vision)
    ├── Sees Agent C is amber (needs input) → presses Agent C key
    ├── ChatGPT switches to Agent C's chat (no window bring-forward)
    ├── Reviews the approval request → presses Approve Command Key
    ├── Agent C resumes → key turns blue
    ├── Sees Agent D is red (error) → double-presses Agent D key
    ├── ChatGPT window comes forward with Agent D's chat
    ├── Reads error → presses Decline, then types corrective instruction
    └── Returns to primary work — Agent Keys continue updating in periphery
```

### Flow 3: Push-to-Talk Voice Input

```
Developer wants to give a follow-up prompt verbally
    │
    ├── Holds Mic key → sea-green light moves around edge (recording active)
    ├── Speaks: "Also add integration tests for the new auth flow"
    ├── Releases Mic key → light changes to moving white (processing)
    ├── ChatGPT transcribes speech → light turns solid white (prompt ready)
    ├── Developer reviews transcription in composer
    ├── Presses Send Command Key (or Codex key)
    └── Prompt submitted to agent
```

### Flow 4: Reasoning Dial Adjustment

```
Developer is working on a complex architectural refactor
    │
    ├── Turns dial clockwise → reasoning effort increases (agent thinks deeper)
    ├── Submits prompt → agent runs with high reasoning
    ├── Task switches to a simple boilerplate change
    ├── Turns dial counter-clockwise → reasoning effort decreases (faster response)
    ├── Submits prompt → agent runs with low reasoning
    └── Dial provides continuous, physical modulation of compute-per-task
```

### Flow 5: Joystick Skill Triggering

```
Developer wants to trigger a common workflow
    │
    ├── Pushes joystick Up → triggers "Toggle Plan mode" (default)
    ├── OR: Pushes joystick Right → triggers "Go forward in app history"
    ├── OR: Pushes joystick Down → triggers "Show/hide sidebar"
    ├── OR: Pushes joystick Left → triggers "Go back in app history"
    ├── (Custom: any direction can be mapped to any skill/command)
    └── Action triggers instantly without menu navigation
```

---

## 10. Agent Key Status System

### Status Color Mapping

| Light Color | Status | Meaning | User Action Needed |
|---|---|---|---|
| **White** | Idle | The chat is idle, no active work | None — agent is waiting |
| **Blue** | Thinking | ChatGPT is actively working on the task | None — wait for completion |
| **Green** | Complete | The chat completed with an unread update | Review the output |
| **Amber** | Requires input | ChatGPT needs approval or a response | Approve, decline, or respond |
| **Red** | Error | Something went wrong | Review error, retry, or adjust prompt |
| **Off** | No assigned chat | The key doesn't follow any chat | Assign a chat or start a new one |

### Active Selection

The selected chat's Agent Key **pulses** with its status light, distinguishing it from non-selected chats that display a steady light.

### Agent Source Modes

| Mode | Behavior | Use Case |
|---|---|---|
| **Most recent chats** (default) | Follows the 6 most recently updated chats (pinned or unpinned) | General workflow with many agents |
| **Pinned chats** | Follows the first 6 chats in the Pinned section | Curated set of important agents |
| **Priority chats** | Orders by: waiting for input → unread → active | Focus on agents needing attention |
| **Custom assignments** | User manually assigns a specific chat to each key | Fixed dashboard for specific agents |

---

## 11. Command Keys & Default Mappings

### Default Layout

| Key Position | Default Action | Icon |
|---|---|---|
| Command Key 1 | Toggle Fast mode on/off | Fast mode icon |
| Command Key 2 | Approve the current request | Checkmark |
| Command Key 3 | Decline the current request | X mark |
| Command Key 4 | Continue current chat in a new chat | Branch icon |
| Command Key 5 (Mic) | Start push-to-talk | Microphone icon |
| Command Key 6 | Send the message in the composer | Send/arrow icon |

### Remappable Actions

All Command Keys can be remapped in Settings > Codex Micro to any of:

- Open browser
- Open terminal
- Review changes
- Commit with Git
- Create a pull request
- Attach files or photos
- Manage scheduled tasks
- Change reasoning effort
- Open Skills
- Any enabled ChatGPT desktop command
- Any enabled Skill

### Keycap Swap Behavior

When remapping a Command Key to a keycap icon already in use elsewhere, ChatGPT **swaps** the two keycaps' assignments rather than allowing the same icon on two keys. This prevents visual confusion. The user should physically swap the keycaps to match.

---

## 12. Analog Controls — Joystick & Dial

### Joystick

| Property | Detail |
|---|---|
| Type | Planar (2D analog) |
| Detection | 4 directional triggers (up, right, down, left) |
| Activation threshold | Push far enough from center to trigger directional action |
| Default Up | Toggle Plan mode on/off |
| Default Right | Go forward in app history |
| Default Down | Show or hide the sidebar |
| Default Left | Go back in app history |
| Customization | Each direction mappable to any ChatGPT desktop command or enabled skill |
| Additional use | Functions as a fidget toy while waiting for agent completion |

### Dial (Rotary Encoder)

| Mode | Behavior |
|---|---|
| **Composer navigation** (default) | Turn to cycle through composer controls/options (Reasoning selected first). Press to open/select. When a control is open, the Agent Key to the right of the dial lights red — press it to cancel. |
| **Reasoning only** | Turn to directly adjust reasoning effort. Press to open the reasoning slider or advanced options. |

| Action | Detail |
|---|---|
| Turn | Navigate / adjust |
| Press (click) | Open / select |
| Hold 500ms | Open Codex Micro Settings |

---

## 13. Push-to-Talk Voice Input

### How It Works

The Codex Micro has **no microphone of its own**. The Mic key activates the **computer's built-in microphone** (or connected mic) for voice input to Codex.

### Interaction Modes

| Mode | Trigger | Behavior |
|---|---|---|
| **Push-to-talk** | Hold Mic key | Recording starts when held, stops when released. Prompt is transcribed and ready to send. |
| **Hands-free toggle** | Double-press within 350ms | Recording starts and stays on. Press Mic key once more to stop. |

### Visual Feedback During PTT

| Light State | Meaning |
|---|---|
| Sea-green light moving around keyboard edge | Recording active |
| Moving white light | ChatGPT is processing speech |
| Solid white light | Prompt is ready — press Codex key to send |

### LED Edge Strip

An LED-lit acrylic edge strip around the device illuminates when the microphone is active. This serves as a visual indicator to prevent accidentally leaving an open recording channel, especially in shared office environments.

---

## 14. Layer System

### Layer Overview

| Layer | Configured Via | Purpose |
|---|---|---|
| Layer 1 | ChatGPT desktop app (Settings > Codex Micro) | Codex-native: Agent Keys, Command Keys, joystick, dial |
| Layer 2–6 | Work Louder Input app | Custom shortcuts and actions for other applications |

### Layer Switching

- **Method:** Capacitive touch sensor (bottom-left of device)
- **Behavior:** Tap to cycle to next layer
- **Indicator:** TBD (likely RGB color change or layer number display)

### Non-Codex Use

Without Codex, the device functions as a **general-purpose programmable macropad**. Layers 2–6 can be configured with:
- Application-specific shortcuts (e.g., Figma, Framer, IDE, DAW)
- System-level macros
- Media controls
- Any HID-compatible key sequence

The Codex-specific features (Agent Key status lighting, default Command Key mappings) **only work with the Codex desktop app**. Without it, the device is a $230 generic macropad — expensive relative to alternatives.

---

## 15. Lighting & Visual Feedback

### Lighting Components

| Component | Location | Function |
|---|---|---|
| Per-key RGB | Under all 13 keys | Agent Key status + general aesthetics |
| Frosted keycaps | Agent Keys (top row) | Diffuse RGB for status visibility |
| LED-lit acrylic edge | Perimeter of device | PTT recording indicator |

### Lighting States

| State | Trigger |
|---|---|
| Agent Key status colors | Live Codex thread state (white/blue/green/amber/red/off) |
| Pulsing | Selected chat's Agent Key |
| Sea-green moving | PTT recording active |
| White moving | Speech processing |
| Solid white | Prompt ready |
| Red (single Agent Key) | Cancel control open (composer/menu) |
| Auto-off | 3 minutes inactivity (configurable) |
| Re-activation | Keyboard use or Agent Key status change |

### User Controls

| Setting | Location | Default |
|---|---|---|
| Brightness | Settings > Codex Micro | Medium |
| Auto-off timeout | Settings > Codex Micro | 3 minutes |
| Battery status display | Settings > Codex Micro + sidebar tooltip | When available (BT mode) |

---

## 16. Configuration & Customization

### Configuration Hierarchy

```
Settings > Codex Micro (ChatGPT desktop app)
├── Agent source
│   ├── Most recent chats (default)
│   ├── Pinned chats
│   ├── Priority chats
│   └── Custom assignments
├── Command Keys
│   ├── Key 1: [action] + [keycap icon]
│   ├── Key 2: [action] + [keycap icon]
│   ├── ...
│   └── Key 7: [action] + [keycap icon]
├── Joystick directions
│   ├── Up: [action]
│   ├── Right: [action]
│   ├── Down: [action]
│   └── Left: [action]
├── Dial mode
│   ├── Composer navigation (default)
│   └── Reasoning only
├── Lighting
│   ├── Brightness slider
│   └── Auto-off timeout
└── Input Monitoring status (macOS)
    └── Open System Settings (if not granted)
```

### Work Louder Input App

Used for:
- Bluetooth pairing and channel management
- Layers 2–6 configuration
- Hardware resets
- Firmware updates
- General-purpose macro configuration outside Codex

### VIA (Open-Source)

Used for:
- Advanced keymap editing (QMK-level)
- Community-shared layouts
- Key remapping at the firmware level

### Accessing Settings

| Method | Detail |
|---|---|
| ChatGPT Settings > Codex Micro | Primary configuration UI |
| Hold dial for 500ms | Quick access shortcut |
| Codex Micro icon in sidebar | Click to open settings |

---

## 17. Connectivity & Platform Support

### Connection Methods

| Method | Detail |
|---|---|
| USB-C | Wired; cable included in box |
| Bluetooth | Wireless; 3 channels supported |
| Bluetooth pairing | Hold bottom-left touch control for 3s → tap to select channel 1/2/3 → hold 3s on channel to pair. Light flashes while pairing, turns solid when paired. |

### Operating System Support

| OS | Support | Notes |
|---|---|---|
| macOS | ✅ Full | Requires Input Monitoring permission for key press detection |
| Windows | ✅ Full | Standard HID support |
| Linux | ❌ Not officially | Community driver exists ([work-louder-oai](https://github.com/boopdotpng/work-louder-oai)) |

### macOS Input Monitoring

On macOS, ChatGPT requires **Input Monitoring** permission to respond to Codex Micro key presses:

1. Open System Settings > Privacy & Security > Input Monitoring
2. Enable access for ChatGPT (if listed)
3. If ChatGPT is not listed: drag ChatGPT from Applications into the list, or select Add (+) and choose ChatGPT
4. Quit and reopen ChatGPT
5. Confirm ChatGPT detects Codex Micro on layer 1

If Settings > Codex Micro shows Input Monitoring isn't set up, select "Open System Settings" to jump to the right panel.

### Required Software

| Software | Required? | Purpose |
|---|---|---|
| ChatGPT desktop app | ✅ Required for Agent Key RGB | Bridge between Codex cloud and hardware |
| Work Louder Input | Optional (for non-Codex layers) | Layers 2–6, Bluetooth, resets |
| VIA | Optional (advanced users) | QMK-level keymap editing |

---

## 18. Power & Battery

### Power

| Mode | Source |
|---|---|
| USB-C wired | USB bus power |
| Bluetooth wireless | Internal battery |

### Battery

| Property | Detail |
|---|---|
| Battery type | Internal rechargeable (details TBD) |
| Battery status | Visible in Settings > Codex Micro (when reported) |
| Battery status (alt) | Codex Micro icon sidebar tooltip |
| Charging | USB-C connection |

---

## 19. Troubleshooting & Recovery

### Bluetooth Re-Pairing

```
1. Hold the bottom-left touch control for 3 seconds → enters communication mode
2. Tap the control to choose Bluetooth channel 1, 2, or 3
3. Hold the control for 3 seconds on the desired channel
4. Channel light flashes while pairing → turns solid when paired
```

Note: The rear button controls power and does NOT start pairing. Use the bottom-left touch control.

### macOS Input Monitoring Fix

If Settings > Codex Micro indicates Input Monitoring isn't set up:

1. Select "Open System Settings" from the prompt
2. Navigate to System Settings > Privacy & Security > Input Monitoring
3. Enable ChatGPT access (if listed)
4. If not listed: drag ChatGPT from Applications into the list, or Add (+) → select ChatGPT
5. Quit and reopen ChatGPT
6. Confirm Codex Micro is detected on layer 1

Reference: [Apple's Input Monitoring guide](https://support.apple.com/guide/mac-help/mchl4cedafb6/mac)

### General Hardware Support

For Bluetooth, cables, power, or keyboard reset issues:
- See the [Creator Micro 2 setup guide from Work Louder](https://worklouder.cc/micro-setup)
- Email: hello@worklouder.cc

### Settings Access

If Settings > Codex Micro is not visible:
- Ensure ChatGPT desktop app is running and updated (post-July 9, 2026 ChatGPT Work merger)
- Ensure Codex Micro is on Layer 1
- Ensure device is connected (USB-C or paired Bluetooth)
- Try holding the dial for 500ms

---

## 20. Out of Box Experience

### Unboxing

The Codex Micro ships in premium packaging consistent with Work Louder's boutique keyboard aesthetic and OpenAI's brand standards.

### First Connection

1. **Open** the ChatGPT desktop app
2. **Connect** Codex Micro via USB-C cable (recommended for first setup) or Bluetooth
3. **Follow** the setup wizard that appears when ChatGPT detects the device
4. **Grant** Input Monitoring permission on macOS (if prompted)
5. **Configure** Agent source, Command Keys, joystick, dial, and lighting
6. **Start** using — Agent Keys immediately light up with current chat statuses

### Default State

Out of the box, the device is ready for Codex use with:
- Layer 1 active (Codex-native)
- Agent source: Most recent chats
- Command Keys: Default 6 actions
- Joystick: Default 4 directional actions
- Dial: Composer navigation mode (Reasoning selected first)
- Lighting: Medium brightness, 3-minute auto-off

---

## 21. Packaging & Inclusions

### In the Box

| Item | Quantity | Description |
|---|---|---|
| Codex Micro unit | 1 | Work Louder Creator Micro 2 chassis, Codex branding, CNC polycarbonate + aluminum |
| USB-C to USB-C cable | 1 | For wired connection and charging |
| Codex icon keycaps | 32 | 30×1U + 1×2U, PBT/PC material, custom Codex icons |
| Solid color keycaps | 11 | PBT, for non-icon assignments |
| Rubber joystick cap | 1 | Covers the analog joystick |

### Shipping

- Available through OpenAI Supply Co. (https://openai.com/supply/co-lab/work-louder/) while supplies last
- Also available through Work Louder directly (https://worklouder.cc/codex-micro)
- Limited quantity — first-come, first-served
- Expected to ship shortly after purchase

---

## 22. Success Metrics

### Product Success

| Metric | Target | Measurement |
|---|---|---|
| Sell-through rate | 100% of limited run | Units sold / units produced |
| Time to sell out | < 7 days | Achieved: < 48 hours (July 15 → July 17) |
| Setup completion rate | > 90% complete setup wizard | Post-purchase survey / telemetry |
| Agent Key engagement | Users check Agent Keys > 10x/day | Telemetry (key press events) |
| Reasoning dial usage | Users adjust reasoning > 3x/session | Telemetry (dial events) |
| Push-to-talk adoption | > 40% of users use PTT at least weekly | Telemetry (Mic key events) |
| Layer 2–6 adoption | > 20% of users configure additional layers | Work Louder Input telemetry |

### Developer Workflow Impact

| Metric | Target | Measurement |
|---|---|---|
| Context switches per session | 50% reduction vs. no device | Telemetry comparison |
| Agent error detection latency | < 10s from error to user awareness | RGB feedback latency measurement |
| Reasoning effort adjustments per task | > 1 per task (vs. ~0 with dropdown) | Dial event count |
| User satisfaction (NPS) | > 40 | Post-purchase survey |

---

## 23. Risks & Constraints

### Technical Risks

| Risk | Impact | Mitigation |
|---|---|---|
| ChatGPT desktop app crash/disconnect | Agent Keys go dark; device becomes generic macropad | Automatic reconnection on app restart; standard HID keys still work |
| Bluetooth instability | Intermittent Agent Key status lag | USB-C fallback; 3 BT channels for interference avoidance |
| macOS Input Monitoring revocation | Keys stop working in ChatGPT | Settings > Codex Micro shows status; prompts re-grant |
| Firmware bugs | Incorrect LED states, key misfires | Work Louder Input for firmware updates; OTA patches |

### Market Risks

| Risk | Impact | Mitigation |
|---|---|---|
| Multi-agent workflows don't become mainstream | Core value proposition narrows | Device works as general macropad; 5 custom layers |
| ChatGPT desktop app adoption stalls | Agent Key feature unusable for non-desktop users | Standard HID keys work without the app; Work Louder Input + VIA for full customization |
| Price criticism ($230 for 13 keys) | Negative press; "overpriced" reviews | Positioning as limited-run collectible + niche productivity tool, not mass-market peripheral |
| DIY alternatives cannibalize demand | 10+ GitHub projects emulate Codex Micro for $46–60 | Genuine hardware quality, official support, warranty, collectibility |
| Separate from Jony Ive device | Confusion about which OpenAI hardware this is | Clear messaging: "developer accessory, not consumer device" |

### Constraints

| Constraint | Detail |
|---|---|
| Agent Keys require ChatGPT desktop | No workaround — desktop app is the JSON-RPC bridge |
| No microphone in device | Uses computer's mic; not a standalone voice interface |
| No display | No LCD screen; feedback is RGB only |
| No Linux support (official) | Community driver exists but unsupported |
| Limited run | No announced restock; availability while supplies last |
| ChatGPT Work merger | Users must have post-July 9, 2026 ChatGPT desktop app for integration |

---

## 24. Open Questions

| # | Question | Status |
|---|---|---|
| 1 | Will there be a restock or second production run? | Unanswered — sold out within 48 hours; OpenAI has not commented |
| 2 | Will Agent Key RGB feedback be extended to CLI, IDE extensions, or browser? | Unanswered — currently desktop-only |
| 3 | What is the battery life in Bluetooth mode? | Not officially specified |
| 4 | What is the warranty period and terms? | Listed as "included per Supply Co. listing" — details TBD |
| 5 | Will the firmware be open-sourced? | No announcement; community projects reverse-engineer the protocol |
| 6 | Is there a roadmap for additional Codex-specific features beyond launch? | No public roadmap |
| 7 | Will Linux support be officially added? | No announcement; community driver exists |
| 8 | What is the exact dimensions and weight of the device? | Not officially published |
| 9 | Will there be a Codex Micro 2.0 with display/microphone? | No announcement; this is clearly a v1 limited experiment |
| 10 | How does the device handle >6 simultaneous agents? | Only 6 Agent Keys; additional agents not tracked on hardware |

---

## 25. References

### Official Sources

| Source | URL |
|---|---|
| ChatGPT Learn — Codex Micro docs | https://learn.chatgpt.com/docs/features/codex-micro |
| Work Louder — Codex Micro product page | https://worklouder.cc/codex-micro |
| OpenAI Supply Co. — Product page | https://openai.com/supply/co-lab/work-louder/ |
| OpenAI Codex — Features overview | https://learn.chatgpt.com/codex/features |
| OpenAI Codex — App Server docs | https://learn.chatgpt.com/codex/app-server |
| Work Louder — Creator Micro 2 setup | https://worklouder.cc/micro-setup |
| OpenAI — Launch video (YouTube) | https://www.youtube.com/watch?v=m8uUUUsMD3Y |

### Reviews & Analysis

| Source | URL |
|---|---|
| Product Wiki — Full spec sheet | https://product-wiki.com/what-is-the-openai-codex-micro-and-how-does-it-work/ |
| TechTimes — Agent Keys require desktop app | https://www.techtimes.com/articles/320670/20260716/openai-codex-micro-ships-today-agent-keys-only-work-chatgpt-desktop.htm |
| Sean Kim — Inside the $230 Macropad | https://blog.imseankim.com/openai-codex-micro-230-keyboard-work-louder-agent-keys-reasoning-dial/ |
| Mervin Praison — Agent Macro Pad analysis | https://mer.vin/2026/07/codex-micro-openai-and-work-louder-agent-macro-pad-for-codex-desktop/ |
| Byteiota — $230 Macro Pad Review | https://byteiota.com/openai-codex-micro-review-230-macro-pad-for-ai-agent-developers/ |
| Roo's Newsletter — Deep spec analysis | https://roo.beehiiv.com/p/openai-codex-micro-review-specs-price |
| Gadget Review — $230 Macro Pad | https://www.gadgetreview.com/openais-codex-micro-a-230-macro-pad-built-for-ai-developers |
| Geeky Gadgets — Specifications | https://www.geeky-gadgets.com/openai-work-louder-codex-micro/ |
| DualMedia — Sold out analysis | https://www.dualmedia.com/codex-micro-keyboard/ |
| NGXPTech — Price, features, specs | https://ngxptech.com/openai-codex-micro-price-features-specifications/ |
| TechRadar — What is Codex Micro? | https://www.techradar.com/ai-platforms-assistants/openai/what-is-the-codex-micro-openais-first-hardware-gadget-explained |
| Happy Mag — Glorified desk toy or AI revolution? | https://happymag.tv/codex-micro/ |

### Community / Open-Source Projects

| Project | URL | Description |
|---|---|---|
| codex-micro-4-core2 | https://github.com/imliubo/codex-micro-4-core2 | M5Stack Core2 BLE firmware emulator |
| Open Codex Micro | https://github.com/QusaiALBahri/open-codex-micro | RP2040/Raspberry Pi Pico DIY |
| codex-midi | https://github.com/scf4/codex-midi | Emulate with MIDI controllers |
| codex-pico | https://github.com/aaronpearce/codex-pico | Pico 2 W + Stream Deck plugin |
| FreeMicro | https://github.com/eliBenven/freemicro | Drive real hardware from Claude Code |
| codex-micro-device | https://github.com/Nishkalkashyap/codex-micro-device | ESP32-S3 DIY 3D-printed |
| OpenMicro | https://github.com/Solonix-Chu/OpenMicro | Gaming controller emulation |
| codex-micro-app | https://github.com/maxxspotter/codex-micro-app | Phone-based emulator |
| work-louder-oai | https://github.com/boopdotpng/work-louder-oai | Native Linux driver |
| codex-micro-fpga-controller | https://github.com/sya-23/codex-micro-fpga-controller | FPGA implementation |

### Social Discussion

| Source | URL |
|---|---|
| Hacker News (262 points, 224 comments) | https://news.ycombinator.com/item?id=48923079 |
| Reddit r/singularity (540 points) | https://www.reddit.com/comments/1uxbwiv/openai-reveals-codex-micro/ |

---

## Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | July 26, 2026 | Research compilation | Initial PRD from public sources, official docs, reviews, and community research |

---

*This PRD is a research-driven document compiled from official OpenAI/ChatGPT documentation, Work Louder product pages, independent reviews, and community open-source projects. It documents the shipped product as of July 2026 and is not an internal OpenAI document.*