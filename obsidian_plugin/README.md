# Hive.AGI Obsidian Plugin — Project Hive.AGI P2 (part 2)

Capture human-perspective triggers inside Obsidian, then trigger the Python
LLM Wiki Engine (P1) to process them into structured wiki entries.

**Architecture**: file-system handoff. Plugin writes JSON to `00_Inbox/`,
then shell-calls `python -m llm_wiki_engine` to process it. No HTTP server,
no token management — the heavy lifting stays in tested Python code.

---

## Commands

| Command | What it does |
|---|---|
| **Capture current note → 00_Inbox/** | Reads active note + frontmatter → writes a `RawData`-shaped JSON to `<vault>/00_Inbox/`. Prompts for `trigger_type` / `domain` if not in frontmatter. |
| **Process inbox (run LLM Wiki Engine)** | Shell-calls `python -m llm_wiki_engine process --inbox … --entries … [--mock]`. Uses repo root + python path from settings. |
| **Open Hive.AGI settings** | Opens the settings tab (repo root path, python binary, mock mode, vault subdirs). |

---

## Install (for use)

1. Build the plugin (see [Development](#development)) — you need `main.js` + `manifest.json`.
2. In your Obsidian vault, create a folder:
   `<vault>/.obsidian/plugins/hiveagi/`
3. Copy `main.js` and `manifest.json` into it.
4. Obsidian → Settings → Community plugins → enable "Hive.AGI".
5. Open the plugin settings, set **Repo root path** to your `gg-hiveagi` checkout.

## Development

Prerequisites: Node.js 18+.

```bash
cd obsidian_plugin
npm install
npm run dev      # watch mode (auto-rebuild on save)
# or
npm run build    # production build → main.js
```

For live development, symlink the built `main.js` + `manifest.json` into your
vault's plugin folder, then reload Obsidian (Cmd/Ctrl+R) after each rebuild.

---

## The bridge: TS → Python

```
Obsidian note
    │
    │ (Capture command)
    ▼
<vault>/00_Inbox/2026-07-25_1930_<slug>.json   ← RawData schema
    │
    │ (Process command: shell)
    ▼
python -m llm_wiki_engine process
    --inbox      <vault>/00_Inbox
    --entries    <vault>/01_Entries
    --quarantine <vault>/99_Archive/quarantine
    [--mock]
    │
    ▼
<vault>/01_Entries/*.md   (P1 output, validated by P0)
```

The JSON written by **Capture** satisfies P1's pydantic `RawData` model:
- `timestamp` (ISO 8601)
- `gps: {lat, lng}` (nested — matches P1 contract)
- `trigger_type` / `domain` (enum, validated)
- `human_description`, `human_label?`, `tags`

See [`src/types.ts`](./src/types.ts) for the TypeScript mirror of the schema.

---

## Settings

| Setting | Default | Purpose |
|---|---|---|
| Repo root path | (empty) | Absolute path to `gg-hiveagi` — where `llm_wiki_engine/` lives |
| Python binary | `python3` | Interpreter to run the engine |
| Mock mode | ON | Run engine without MiniMax/DeepSeek keys (turn off after `.env` setup) |
| Inbox subdir | `00_Inbox` | Vault-relative |
| Entries subdir | `01_Entries` | Vault-relative |
| Quarantine subdir | `99_Archive/quarantine` | Vault-relative |

---

## ⚠️ Testing status (honest)

- ✅ **Build verified**: `npm run build` produces `main.js` with no TS errors.
- ✅ **Cross-compat verified**: a JSON in the exact Capture format parses cleanly through P1's `RawData` pydantic model and produces a valid entry.
- ❌ **Not click-tested inside Obsidian**: no Obsidian install in the build environment. You should do a real smoke test:
  1. Install the plugin in a vault
  2. Open a note → run "Capture current note"
  3. Confirm JSON appears in `00_Inbox/`
  4. Run "Process inbox" → confirm entries appear in `01_Entries/`

If anything misbehaves, report via GitHub Issues with the console output
(`Process inbox` logs stdout/stderr to the dev console on failure).

---

## License

AGPL-3.0 (consistent with the Project Hive.AGI main repo).
