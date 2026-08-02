# powerbi-agent

**🌐 Language:** **English** · [Tiếng Việt](README.vi.md)

> ⚠️ **Windows only.** Power BI Desktop ships for Windows only, so powerbi-agent's tools that
> talk to Desktop **require Windows 10/11**. There is no macOS/Linux build.

**An MCP server + skill pack that turns any AI Agent into a data analyst working DIRECTLY on Power BI** —
from DAX queries behind a data-safety policy, to building polished report pages from templates,
to the **KPIM analysis process** for documenting & standardizing data, plus an end-to-end 9-step pipeline.

More than "an MCP bridge + data safety" — the repo also ships:
- 🧠 **KPIM analysis process** (skill `kpim-analysis`): Research → Key Information (5 mindmaps + standard docs) → Planning → Implementation → Monitoring.
- 📄 **Ready-to-use documentation templates**: `PROJECT.md`, `DATA_DICTIONARY.md`, `METRICS_CALCULATION.md`, `DOMAIN_DIMENSION.md`, `REPORTS.md`, `DESIGN.md` + `theme.json`, `Project_Management.xlsx` (6 sheets), 5 mindmap PNGs — clone them for a new project.
- 📚 **Technical references** for DAX / Power Query (M) / SQL best practices (sourced from Microsoft Learn) in `plugins/powerbi-agent/skills/powerbi-pipeline/references/`.

Supports **Power BI Desktop (local)** · **Power BI Service (cloud)** · **PBIP/PBIR (project files)**.
Hosts: **Claude Code · Codex CLI · Google Antigravity** and any stdio MCP client.

> 🌐 Website: **[ducnguyen.vn/powerbi-agent](https://ducnguyen.vn/powerbi-agent/)** · 📘 Full install guide: **[docs/INSTALL.html](docs/INSTALL.html)** ([web](https://ducnguyen.vn/powerbi-agent/INSTALL.html)) · Roadmap: **[ROADMAP.md](ROADMAP.md)** · UAT results: **[docs/UAT-REPORT.md](docs/UAT-REPORT.md)**

## 🏛️ Built by KPIM — shared free with the community

The analysis process and report templates in powerbi-agent were built by **[KPIM](https://kpim.vn)** —
a consultancy that delivers **Data & Business Intelligence** solutions and provides **in-depth Data & AI
training**. The workflows (the "KPIM workflow") and report templates here are **distilled by many KPIM
experts** from real-world engagements and shared **FREE** with the community, students and data
practitioners. Learn more: **[kpim.vn](https://kpim.vn)**.

## Install with your AI Agent (recommended — one line)

Paste into your agent (Claude Code / Codex / Antigravity):

```
Clone https://github.com/ducnguyen221/powerbi-agent into ~/.mcp/powerbi-mcp, then run install.ps1 there (read the script first), and restart the MCP host.
```

The agent will: clone → build `.venv` → probe ADOMD.NET/TOM (any SSMS/standalone/GAC) → register the MCP
across all 3 hosts → copy **4 skills** (`powerbi-mcp`, `powerbi-pipeline`, `kpim-analysis`, `powerbi-knowledge`)
plus references, templates and the 6 `/powerbi-*` commands. Manual install: see [docs/INSTALL.html](docs/INSTALL.html).

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Requirements: Windows (Power BI Desktop is Windows-only) · Python 3.11+ · ADOMD.NET
(bundled with SSMS; or install the [Analysis Services client libraries](https://learn.microsoft.com/en-us/analysis-services/client-libraries)).

### Or install as a plugin (shows in the app's plugin manager)

The same `.claude-plugin/marketplace.json` works for **both Claude Code and Codex** — installs the
4 skills + 6 `/powerbi-*` commands + the curator agent as a managed plugin (no MCP server; run
install.ps1 for the 16 tools). Antigravity has no plugin store — its skills load from the skills folder.

```bash
# Claude Code
claude plugin marketplace add ducnguyen221/powerbi-agent && claude plugin install powerbi-agent@powerbi-agent
# Codex CLI
codex plugin marketplace add https://github.com/ducnguyen221/powerbi-agent && codex plugin add powerbi-agent@powerbi-agent
```

Per-host details: [`hosts/`](hosts/) (claude · codex · antigravity).

## 🧭 Getting started — 3 steps

1. **Install** (command above) → restart the host → the agent gains 16 tools + 4 skills + 6 commands.
2. **`/powerbi-setup`** — the agent asks you to designate a **Knowledge Dir** (a folder OUTSIDE the repo —
   ideally your existing knowledge base / brain) to store project knowledge. One-time.
3. **`/powerbi-new <project name>`** — start: the agent reads prior lessons → surveys → documents → builds
   model + report → `/powerbi-done` closes the project and its knowledge is packaged for next time.

## ⚡ 6 commands (Claude Code; Codex/Antigravity use skill `powerbi-knowledge` for the same flow)

| Command | What it does |
|---|---|
| `/powerbi-setup` | Declare the Knowledge Dir (once) — where ALL knowledge lives, outside the repo |
| `/powerbi-new <name>` | Open a project: its own folder + read prior lessons + run the analysis process |
| `/powerbi-scan <path.pbip>` | Scan a whole report's design: every page + theme + DESIGN.md + catalog |
| `/powerbi-done` | Close a project: handoff checklist + distill + timeline + knowledge packaging |
| `/powerbi-pack [project]` | Package lessons into 4 axes: tech-stack · industry · business-domain · powerbi |
| `/powerbi-recall <keyword>` | "Have we done something like this?" — look up past projects, lessons, reusable kits |

## 🔄 Skill & agent flow (who does what, when)

```
 /powerbi-new ──▶ skill kpim-analysis ──▶ skill powerbi-pipeline ──▶ /powerbi-done ──▶ agent powerbi-knowledge-curator
             (BUSINESS: survey,        (TECHNICAL: 9 steps    (checklist    (package lessons on 4 axes,
              question, KPIM docs,      Power Query→model→     + distill     dedup, INDEX, TIMELINE)
              planning)                 DAX→report pages)      + timeline)
                    ▲                          │
                    └── reads prior knowledge/ └── MCP tools (16) + policy 🛡️ + template kit 🎨
 /powerbi-recall ◀── INDEX + TIMELINE + knowledge/ ◀──────────────┘  (skill powerbi-knowledge = the mechanism)
```

- **Skill `powerbi-mcp`** = a reference for the 16 tools + policy rules (the agent consults it as needed).
- **Coordinating MANY agents at once** (Claude builds · Codex reviews · Antigravity documents): [AGENTS.md](AGENTS.md) §4.

## 🔐 The Knowledge Dir mechanism (private by default)

- Project knowledge (docs, lessons, raw kits) lives in **a folder YOU designate, outside the repo** —
  `knowledge.config.json` is gitignored, each machine declares its own, and nobody receives anyone
  else's knowledge through git.
- Auto-created structure: `projects/<project>/` · `knowledge/{4 axes}/` · `templates/` (private kits) ·
  `INDEX.md` · `TIMELINE.md`.
- The only path from private knowledge → the public repo: you explicitly ask + `sanitize=True` + review.

## 16 tools

| Group | Tool | What it does |
|---|---|---|
| **Discover** | `list_local_reports` | Reports open in Desktop (port + model ID) |
| | `list_tables` | Tables in the model (system tables filtered out) |
| | `describe_table` | One table's columns + data types + measures |
| **Query** 🛡️ | `execute_dax_local` | DAX against Desktop — through the data-safety policy |
| | `execute_dax_service` | DAX against Service (MSAL, token cache) — through the policy |
| **Write model** | `add_measure_local` | Create/update a measure via TOM |
| | `add_relationship_local` | Create a Many-to-One relationship via TOM |
| **Template** 🎨 | `list_templates` | Available report kits |
| | `apply_template` | Build a NEW page from a kit — clone-and-rebind, style preserved |
| | `distill_template` | Distill a polished page into a reusable kit (sanitizable) |
| **Distill** | `distill_model_schema` | Model → Markdown blueprint + Mermaid ERD |
| | `distill_report_design` | Scan a whole report: every page + theme + DESIGN + CATALOG |
| **Knowledge OS** 🧠 | `knowledge_status` | Is the Knowledge Dir set up + current state |
| | `setup_knowledge` | Set up the user-designated Knowledge Dir (outside the repo) |
| | `init_project` | Create a project folder `projects/<slug>/` + INDEX + TIMELINE |
| | `log_timeline` | Log an event/lesson to TIMELINE.md (append-only) |

## 🛡️ Data-safety policy (enforced server-side, not just a prompt hint)

Principle: **raw data stays inside the Power BI engine — only aggregated results reach the LLM context.**

- **aggregate-only (ON by default):** `EVALUATE '<table>'` / `EVALUATE ALL(...)` are refused with a
  rewrite hint toward `SUMMARIZECOLUMNS`/`TOPN`/measures. Turn off: `POWERBI_AGGREGATE_ONLY=0`.
- **PII blocklist:** copy `policy.example.json` → `policy.json`, list columns to block from projection
  (phone, national ID, email…). Blocked in every query.
- **Audit log:** every query is written to `~/.powerbi-agent/audit/*.jsonl` (verdict + row count) —
  an audit trail proving "no raw data dumped".
- **Dimension cap:** results with a text column are capped at 200 rows (measure-only is unlimited).
- *Honest about limits:* this is a guard against accidental leaks — real hard security is still RLS on
  the model + a least-privilege service principal.

## 🎨 Template kit — beautiful reports, reproducible

A hard-won lesson: **layouts an AI builds from scratch always look off; clone a proven page + rebind the
fields and it looks great.** `apply_template` turns that rule into code: it keeps `visualContainerObjects`
(the style) intact and only changes name/position/fields/visualType/title.

A kit is a git-friendly text folder:

```
report-templates/kpim-business-light/   # bundled sample kit (sanitized)
  kit.json          # meta: canvas, blocks, roles
  blueprint.md      # source page map: 30 visuals, positions, bindings
  blocks/*.json     # verbatim visual.json per type (KPI card, combo chart, pivot, slicer, map…)
  _page.json        # page settings + background
```

Knowledge loop: a page you like → `distill_template` into a kit → later projects `apply_template` to reproduce it.
A kit with real business bindings stays on your machine (env `POWERBI_TEMPLATES_DIR`); to share publicly → `sanitize=True`.

## 🤝 Runs alongside microsoft/powerbi-modeling-mcp (recommended)

powerbi-agent **doesn't rebuild modeling** — it delegates to Microsoft's official MCP:

```bash
claude mcp add powerbi-modeling -s user -- npx -y "@microsoft/powerbi-modeling-mcp@latest" --start
```

| Task | Server |
|---|---|
| DAX query + policy, schema discovery, template/PBIR report layer, distill | **powerbi-agent** |
| Create/update tables/columns/measures/relationships, bulk + transactions, TMDL, DAX validate | **powerbi-modeling** (Microsoft) |

## 📐 The 9-step pipeline (skill `powerbi-pipeline`)

The agent runs a full Power BI project in a standard order, each step with a runnable check:

1. Connect data (Power Query, M parameters) → 2. Transform M (explicit data types)
→ 3. Star-schema modeling + relationships → 4. DAX measures/calc columns (verify each)
→ 5. Aggregated queries (policy-guarded) → 6+7. Visuals & report pages from templates
→ 8. Advanced (tooltips, drill-through, parameters; bookmarks by hand) → 9. Artifacts + knowledge distillation.

Details: `plugins/powerbi-agent/skills/powerbi-pipeline/SKILL.md` (installed to the host by install.ps1).
Includes **technical references** (from Microsoft Learn): `plugins/powerbi-agent/skills/powerbi-pipeline/references/` — `dax-best-practices.md`, `powerquery-m-best-practices.md`, `sql-best-practices.md`, `gotchas.md`.

## 📋 The KPIM analysis process (skill `kpim-analysis`) — document & standardize data

Beyond the technical layer, the repo ships the **KPIM analysis process** so the agent can take **a dataset +
docs** → survey it, ask you clarifying questions, and produce a **standardized business-documentation set**
before building any report. 5 phases:

**Research** (read data + ask back) → **Key Information** (5 parts: Requirements · Analytics Questions · Data ·
Metrics & Dimensions · Result & Delivery) → **Planning** (2-level Excel tasks) → **Implementation** (hand off to
`powerbi-pipeline`) → **Monitoring**.

Standard output (folder `plugins/powerbi-agent/skills/kpim-analysis/document-templates/`, with a worked "KPIM Mart" example):

```
PROJECT.md              # Key Information summary (5 tables + mindmap)
RESEARCH_NOTES.md       # input notes + clarifying questions for the user
DATA_DICTIONARY.md      # tables/sources/fields
METRICS_CALCULATION.md  # DAX measures grouped
DOMAIN_DIMENSION.md     # analysis dimensions + business reasoning
REPORTS.md              # report list (Report Group → Report → Page) + visuals
DESIGN.md + theme.json  # design thinking + an importable Power BI theme
Project_Management.xlsx # 6 sheets: KEY INFORMATION, PLANNING, DATA DICTIONARY, METRICS_CALCULATION, DOMAIN_DIMENSION, REPORT
mindmaps/*.png          # Key Objectives / Questions / Data / Analysis / Report
scripts/                # generate_mindmaps.py, generate_project_management_xlsx.py, ...
```

Details: `plugins/powerbi-agent/skills/kpim-analysis/SKILL.md`.

## 📁 Repo INDEX — key folders & files

> All paths are relative to the **repo root** — correct wherever you clone. Agents read
> [`AGENTS.md`](AGENTS.md) before working; newcomers use this table to orient.

### Root — guides & install

| File | Role |
|---|---|
| [`AGENTS.md`](AGENTS.md) | **The canonical guide for every agent** — repo map, Power BI working rules, multi-agent protocol (§4). Codex reads it natively. |
| [`CLAUDE.md`](CLAUDE.md) · [`GEMINI.md`](GEMINI.md) | Pointers to AGENTS.md for Claude Code / Antigravity — edit content IN AGENTS.md. |
| `README.md` / [`README.vi.md`](README.vi.md) | This file (English, canonical) / Vietnamese version. |
| [`ROADMAP.md`](ROADMAP.md) | Positioning, 4-layer architecture, milestones (M0–M3 ✅, M4+ planned). |
| [`install.ps1`](install.ps1) | **In-place installer** — venv + ADOMD/TOM probe + register MCP on 3 hosts + copy skills. Idempotent. |
| [`uninstall.ps1`](uninstall.ps1) · [`pack.ps1`](pack.ps1) | Uninstall / pack a clean zip for another machine. |
| `mcp_server_powerbi.py` | **MCP entrypoint** — hosts register this file (a shim, don't rename/move). |
| `pyproject.toml` · `requirements*.txt` | Packaging + dependencies (pinned & loose). |
| [`policy.example.json`](policy.example.json) | PII blocklist sample → copy to `policy.json` (gitignored) per project. |
| `.env.example` | Power BI Service (service principal) config sample → `.env` (gitignored). |
| `LICENSE` | MIT + attribution to KPIM & the author. |

### `powerbi_agent/` — the MCP server package (core code)

| File | Role |
|---|---|
| `app.py` | Boots the server: load ADOMD/TOM → FastMCP → register the 16 tools. |
| `tools_query.py` | Discover + query: `list_local_reports` · `list_tables` · `describe_table` · `execute_dax_local/_service` (through policy). |
| `policy.py` | **Data-safety layer**: aggregate-only (ON by default) · PII blocklist · JSONL audit · dimension row cap. |
| `tools_tom.py` | Model writes via TOM: `add_measure_local` · `add_relationship_local` (single-shot fallback — bulk goes to modeling-mcp). |
| `pbir.py` + `tools_template.py` | **Report layer**: read/write PBIR, `list_templates` · `apply_template` (clone-and-rebind) · `distill_template` (+ deep-sanitize). |
| `tools_distill.py` · `tools_design.py` | `distill_model_schema` (model → blueprint + ERD) · `distill_report_design` (whole-report design scan). |
| `knowledge.py` · `tools_knowledge.py` | Knowledge OS: Knowledge Dir resolution + `setup_knowledge`/`init_project`/`log_timeline`. |
| `adomd.py` · `discovery.py` · `util.py` | Multi-version SSMS DLL probe · Desktop port discovery · shared utilities. |

### `plugins/powerbi-agent/skills/` — 4 skills (SINGLE SOURCE, copied to hosts by the installer)

| Skill | Use when | Key files |
|---|---|---|
| [`kpim-analysis`](plugins/powerbi-agent/skills/kpim-analysis/SKILL.md) | **Project start** — data in → survey, ask, document, plan | `document-templates/` (8 doc templates + xlsx + theme.json + 5 mindmaps) · `scripts/` (mindmap/xlsx generators) |
| [`powerbi-pipeline`](plugins/powerbi-agent/skills/powerbi-pipeline/SKILL.md) | **Technical execution** — 9 steps Power Query → model → DAX → report | `references/` — dax / powerquery-m / sql best-practices · gotchas · powerbi-knowledge-map |
| [`powerbi-mcp`](plugins/powerbi-agent/skills/powerbi-mcp/SKILL.md) | **Tool reference** — how to use the 16 tools + policy rules + role split with modeling-mcp | (1 file) |
| [`powerbi-knowledge`](plugins/powerbi-agent/skills/powerbi-knowledge/SKILL.md) | **Knowledge OS** — the /powerbi-* flow: projects, 4-axis packaging, timeline, privacy rules | (1 file) |

The plugin also has [`commands/`](plugins/powerbi-agent/commands/) (6 `/powerbi-*` commands) and [`agents/`](plugins/powerbi-agent/agents/) (powerbi-knowledge-curator). Skills cross-link via sibling relative paths (`../<skill>/SKILL.md`) — valid both in-repo and once installed on a host.

### Remaining folders

| Folder | Role |
|---|---|
| [`.claude-plugin/`](.claude-plugin/marketplace.json) | Marketplace manifest — install skills as a plugin: `claude plugin marketplace add ducnguyen221/powerbi-agent` → `claude plugin install powerbi-agent@powerbi-agent` (skills only, no venv/MCP). |
| [`hosts/`](hosts/) | Per-host registration guides: [`claude/`](hosts/claude/README.md) · [`codex/`](hosts/codex/README.md) · [`antigravity/`](hosts/antigravity/README.md) (with manual config snippets). |
| [`report-templates/`](report-templates/kpim-business-light/README.md) | **Visual report-page kits** for `apply_template` — `kpim-business-light` (12 sanitized blocks). |
| [`scripts/`](scripts/) | Dev utilities: `cli.py` (debug DAX without the MCP: `list`/`tables`/`query`) · `test_mcp_local.py` (connection smoke test) · `build_template_gallery.py`. |
| [`docs/`](docs/) | GitHub Pages site: `index.html` (landing) + `feature/` `instruction/` `template/` `install/` · [`INSTALL.html`](docs/INSTALL.html) · [`UAT-REPORT.md`](docs/UAT-REPORT.md). |
| `tests/` + `.github/workflows/` | Unit + installer tests + CI (ruff + pytest, windows-latest). |

Coordinating many agents at once (Claude builds · Codex reviews · Antigravity documents):
see **[AGENTS.md](AGENTS.md) §4** — single-writer, lock convention, shared handoff artifacts.

## Security & operations

- `.env` (cloud service principal) is never overwritten/committed — created only from `.env.example`.
- Model-write tools warn in their docstrings; REPORT writes only when the .pbip is closed (the tool warns).
- Uninstall: `.\uninstall.ps1` (keeps files) · `.\uninstall.ps1 -RemoveVenv`.

## Authors & credit

The **KPIM analysis process, tooling (MCP server + tools), templates and techniques** in this repo were
built by **[KPIM](https://kpim.vn)** (many experts collaborating), technical lead & development by
**Duc Nguyen (Nguyễn Quang Đức — [ducnguyen221](https://github.com/ducnguyen221))** — so an AI Agent can
**do data analysis like an expert**. Shared free with the community and students.

If you reuse the process / templates / tools, please **keep the credit to KPIM & Duc Nguyen**.

## License

**MIT** — © 2026 KPIM ([kpim.vn](https://kpim.vn)) & Duc Nguyen ([ducnguyen221](https://github.com/ducnguyen221)). See `LICENSE`.
Free to use/modify/distribute under MIT; attribution to KPIM & the process author is appreciated.
