# INDEX — repo map

Two views of the same repo. **§1 answers "I want to do X — where do I go?"**
**§2 answers "I see folder Y — what is it?"** Everything else hangs off those two.

| I am… | Read |
|---|---|
| New here, want to install and try it | [`README.md`](README.md) |
| An AI agent about to work in this repo | [`AGENTS.md`](AGENTS.md) — working rules, multi-agent protocol |
| Looking for a specific folder / file / tool | this file |
| Wondering where the project is heading | [`ROADMAP.md`](ROADMAP.md) |

---

## §1 — Axis A: the four pillars

| # | Pillar | What you get | Lives in | Commands & tools |
|---|---|---|---|---|
| **1** | **MCP Server** — the agent works directly on Power BI | 16 tools behind a server-side data-safety policy | [`powerbi_agent/`](powerbi_agent/) · [`hosts/`](hosts/) · `install.ps1` · `policy.example.json` | all 16 tools |
| **2** | **Digitized expertise** — your workflow, skills, knowledge | 4 skills · 8 commands · 1 agent · Knowledge OS | [`plugins/powerbi-agent/`](plugins/README.md) | `/powerbi-*` |
| **3** | **Report design kits** — build reports like a designer | Clone-and-rebind kits; style preserved 100% | [`report-templates/`](report-templates/README.md) | `list_templates` · `apply_template` · `distill_template` · `/powerbi-kit` |
| **4** | **Document templates** — create & manage analysis docs | 7 markdown docs + Excel (6 sheets) + theme + 5 mindmaps | [`plugins/powerbi-agent/skills/kpim-analysis/document-templates/`](plugins/powerbi-agent/skills/kpim-analysis/document-templates/) | skill `kpim-analysis` |

### 1.1 Pillar 1 — MCP Server

The bridge. Everything else is worthless without it.

| File | Why it matters |
|---|---|
| [`powerbi_agent/app.py`](powerbi_agent/app.py) | Boots the server, registers all 16 tools |
| [`powerbi_agent/policy.py`](powerbi_agent/policy.py) | **The safety layer** — aggregate-only, PII blocklist, audit log, row cap |
| [`powerbi_agent/tools_query.py`](powerbi_agent/tools_query.py) | Discover + query (Desktop via ADOMD, Service via REST) |
| [`powerbi_agent/adomd.py`](powerbi_agent/adomd.py) · [`discovery.py`](powerbi_agent/discovery.py) | Find the ADOMD.NET DLLs · find the Desktop port |
| [`install.ps1`](install.ps1) | One command: venv → probe → register 3 hosts → install workflows |
| [`policy.example.json`](policy.example.json) | Copy to `policy.json` and list the columns to block |

**Flow:** `install.ps1` → restart host → `/powerbi-help` → the agent sees the tools.

#### The 16 tools

| Group | Tool | What it does |
|---|---|---|
| **Discover** | `list_local_reports` | Reports open in Desktop (port + model ID) |
| | `list_tables` | Tables in the model (system tables filtered out) |
| | `describe_table` | One table's columns + data types + measures |
| **Query** 🛡️ | `execute_dax_local` | DAX against Desktop — through the data-safety policy |
| | `execute_dax_service` | DAX against Service (MSAL, token cache) — through the policy |
| **Write model** | `add_measure_local` | Create/update a measure via TOM |
| | `add_relationship_local` | Create a Many-to-One relationship via TOM |
| **Templates** 🎨 | `list_templates` | Available report kits |
| | `apply_template` | Build a NEW page from a kit — clone-and-rebind, style preserved |
| | `distill_template` | Distill a polished page into a reusable kit (sanitizable) |
| **Distill** | `distill_model_schema` | Model → Markdown blueprint + Mermaid ERD |
| | `distill_report_design` | Scan a whole report: every page + theme + DESIGN + CATALOG |
| **Knowledge OS** 🧠 | `knowledge_status` | Is the Knowledge Dir set up + current state |
| | `setup_knowledge` | Set up the user-designated Knowledge Dir (outside the repo) |
| | `init_project` | Create `projects/<slug>/` + register in INDEX + TIMELINE |
| | `log_timeline` | Log an event/lesson to TIMELINE.md (append-only) |

> ⚠️ Report writes (`apply_template`, `distill_template`) act on PBIR files on disk — **close the
> `.pbip` in Power BI Desktop first**, or Desktop will overwrite what the tool just wrote.

### 1.2 Pillar 2 — Digitized expertise

The biggest and most valuable part of the repo — 30+ files that turn a generic agent into
someone who works the way an experienced Power BI consultant works.

| Skill | Use it when | Key contents |
|---|---|---|
| [`kpim-analysis`](plugins/powerbi-agent/skills/kpim-analysis/SKILL.md) | Project start — data in, before touching the model | `document-templates/` (pillar 4) · `scripts/` (generators) |
| [`powerbi-pipeline`](plugins/powerbi-agent/skills/powerbi-pipeline/SKILL.md) | Building — the 9 technical steps | `references/` — DAX · Power Query M · SQL best practices · gotchas · knowledge map |
| | | |

**The KPIM analysis process (skill `kpim-analysis`), 5 phases:** Research (read the data, ask back) →
Key Information (Requirements · Analytics Questions · Data · Metrics & Dimensions · Result & Delivery)
→ Planning (2-level Excel tasks) → Implementation (hand off to `powerbi-pipeline`) → Monitoring.

**The 9-step pipeline (skill `powerbi-pipeline`):** 1 Connect data (Power Query, M parameters) →
2 Transform M (explicit data types) → 3 Star-schema modelling + relationships → 4 DAX measures
(verify each) → 5 Aggregated queries (policy-guarded) → 6+7 Visuals & report pages from kits →
8 Advanced (tooltips, drill-through, parameters) → 9 Artifacts + knowledge distillation.

**Knowledge Dir layout** (auto-created by `setup_knowledge`): `projects/<slug>/` ·
`knowledge/{tech-stack, industry, business-domain, powerbi}/` · `templates/` (your private kits) ·
`INDEX.md` · `TIMELINE.md`.
| [`powerbi-mcp`](plugins/powerbi-agent/skills/powerbi-mcp/SKILL.md) | Unsure which tool to call | Tool reference + policy rules + split with `powerbi-modeling` |
| [`powerbi-knowledge`](plugins/powerbi-agent/skills/powerbi-knowledge/SKILL.md) | Handling project knowledge | Knowledge OS mechanics, 4-axis packaging, privacy rules |

**8 commands** in [`plugins/powerbi-agent/commands/`](plugins/powerbi-agent/commands/):
`/powerbi-help` · `/powerbi-setup` · `/powerbi-new` · `/powerbi-scan` · `/powerbi-kit` ·
`/powerbi-done` · `/powerbi-pack` · `/powerbi-recall`.
**1 agent**: [`powerbi-knowledge-curator`](plugins/powerbi-agent/agents/powerbi-knowledge-curator.md) — packages lessons at project close.

> Installed to all three hosts. Antigravity has no slash-command mechanism, so its copy of the
> commands lands inside the `powerbi-knowledge` skill — call them by name instead.

### 1.3 Pillar 3 — Report design kits

The hard-won rule: **a layout an AI builds from scratch always looks off; clone a proven page and
rebind the fields and it looks right.** `apply_template` is that rule as code — it keeps
`visualContainerObjects` (the style) untouched and changes only name/position/fields/type/title.

A kit is a plain text folder, git-friendly:

```
report-templates/kpim-business-light/
  kit.json          # meta: canvas, blocks, roles
  blueprint.md      # source page map: 30 visuals, positions, bindings
  blocks/*.json     # verbatim visual.json per type (KPI card, combo chart, pivot, slicer, map…)
  _page.json        # page settings + background
```

**Loop:** a page you like → `/powerbi-kit` or `distill_template` → later projects `apply_template` it back.
Kits carrying real business bindings stay on your machine (`POWERBI_TEMPLATES_DIR`); to publish → `sanitize=True`.

### 1.4 Pillar 4 — Document templates

Fill-in-ready deliverables so the agent documents a project the way a consultant would,
**before** any report gets built. Ships inside the `kpim-analysis` skill, so the installer
carries it to every host.

| File | Contents |
|---|---|
| `PROJECT.md` | Key Information summary (5 tables + mindmap) |
| `RESEARCH_NOTES.md` | Input notes + the questions to ask the client back |
| `DATA_DICTIONARY.md` | Tables / sources / fields |
| `METRICS_CALCULATION.md` | DAX measures, grouped |
| `DOMAIN_DIMENSION.md` | Analysis dimensions + business reasoning |
| `REPORTS.md` | Report Group → Report → Page → visuals |
| `DESIGN.md` + `theme.json` | Design rationale + an importable Power BI theme |
| `Project_Management.xlsx` | 6 sheets incl. 2-level task planning |
| `mindmaps/*.png` | Objectives · Questions · Data · Analysis · Report |
| `../scripts/` | Generators for the mindmaps and the xlsx |

---

## §2 — Axis B: folder map

```
powerbi-agent/
├─ README.md · README.vi.md      Start here: what it does · how to install · main features
├─ INDEX.md                      ← you are here
├─ AGENTS.md                     Rules for AI agents (canonical). CLAUDE.md/GEMINI.md point at it
├─ ROADMAP.md · LICENSE
├─ install.ps1 · uninstall.ps1 · pack.ps1
├─ mcp_server_powerbi.py         MCP entrypoint (a shim — do not rename or move)
├─ policy.example.json · .env.example · pyproject.toml · requirements*.txt
│
├─ powerbi_agent/          ▸ PILLAR 1   14 modules — the MCP server itself
├─ hosts/                  ▸ PILLAR 1   per-host setup: claude · codex · antigravity
│
├─ plugins/                ▸ PILLAR 2   the digitized expertise
│  └─ powerbi-agent/
│     ├─ skills/                         kpim-analysis · powerbi-pipeline
│     │  │                               powerbi-mcp · powerbi-knowledge
│     │  └─ kpim-analysis/
│     │     ├─ document-templates/  ▸ PILLAR 4   doc templates + xlsx + theme + mindmaps
│     │     └─ scripts/                          generators
│     ├─ commands/                       8 × /powerbi-*
│     └─ agents/                         powerbi-knowledge-curator
│
├─ report-templates/       ▸ PILLAR 3   report-page kits for apply_template
│  └─ kpim-business-light/                12 sanitized blocks
│
├─ scripts/                             dev utilities (not shipped to users)
├─ tests/ · .github/                    unit + installer tests, CI
└─ docs/                                GitHub Pages site + plans/
```

| Folder | What it is, in one sentence | Most important files | Pillar | Who opens it |
|---|---|---|---|---|
| [`powerbi_agent/`](powerbi_agent/) | The MCP server: 14 Python modules providing 16 tools | `app.py` · `policy.py` · `tools_query.py` | 1 | Developers |
| [`hosts/`](hosts/) | How to register the server in each AI host | `claude/` · `codex/` · `antigravity/` | 1 | Installers |
| [`plugins/`](plugins/README.md) | Packaging shell for the expertise — the doorway to pillar 2 | `README.md` · `powerbi-agent/.claude-plugin/plugin.json` | 2 | Everyone |
| `plugins/…/skills/` | The 4 expert processes, single source; installer copies them to hosts | 4 × `SKILL.md` | 2 | Agents |
| `plugins/…/commands/` | 8 slash commands that trigger those processes | `powerbi-help.md` · `powerbi-setup.md` | 2 | Users |
| `plugins/…/agents/` | Sub-agent that packages lessons at project close | `powerbi-knowledge-curator.md` | 2 | Agents |
| `…/kpim-analysis/document-templates/` | Fill-in-ready analysis deliverables | `PROJECT.md` · `Project_Management.xlsx` | 4 | Users |
| [`report-templates/`](report-templates/README.md) | Report-page kits, sanitized and public | `kpim-business-light/kit.json` | 3 | Users |
| [`scripts/`](scripts/) | Dev-only utilities, never shipped to users | `cli.py` · `build_template_gallery.py` | — | Developers |
| [`tests/`](tests/) | Unit tests + a fake-profile installer harness | `test_unit.py` · `installer/installer.tests.ps1` | — | Developers |
| [`docs/`](docs/) | The public website + internal plans | `index.html` · `INSTALL.html` · `plans/` | — | Anyone |
| [`.claude-plugin/`](.claude-plugin/marketplace.json) | Marketplace catalog so hosts can install this as a plugin | `marketplace.json` | 2 | Hosts |

---

## §3 — Glossary

The repo's own history proves this section is needed: two folders were once both called
`templates/`, and the docs had to write "≠" five times to explain the difference. Names now
carry a qualifier instead.

### "template" means four different things

| Path | Contains | Owner | Public? |
|---|---|---|---|
| `report-templates/` | Report-**page** kits (PBIR), sanitized | Repo | ✅ |
| `…/kpim-analysis/document-templates/` | **Document** templates (md/xlsx/theme/mindmaps) | Repo, ships with the skill | ✅ |
| `docs/template/` | The website gallery **route** | Repo (stable URL) | ✅ |
| `<Knowledge Dir>/templates/` | Your **private** kits, not sanitized | **You**, outside the repo | ❌ never |

### Four names for what feels like one thing

Deliberately not unified — renaming any of them would break every existing install for
approximately zero benefit.

| Name | What it actually is |
|---|---|
| `powerbi-agent` | The GitHub repo and the plugin |
| `powerbi_agent` | The Python package (underscore — it is an import name) |
| `powerbi-mcp-bridge` | The MCP server ID hosts register. **Never rename** — it lives in every user's config |
| `~/.mcp/powerbi-mcp` | The conventional clone location, nothing more |

### Other terms

| Term | Meaning |
|---|---|
| **kit** | One report page distilled into text, replayable by `apply_template` |
| **skill** | A process the agent reads and follows (`SKILL.md` + supporting files) |
| **command** | A `/powerbi-*` shortcut that kicks off a process |
| **tool** | An MCP function the agent calls (16 of them) |
| **Knowledge Dir** | A folder **you** designate outside the repo, where all project knowledge lives |
| **host** | The AI app running the agent: Claude Code, Codex CLI, Antigravity |
| **policy** | Server-side data-safety enforcement — not a prompt hint |
| **PBIP / PBIR** | Power BI's project / enhanced-report file formats (Microsoft names) |

---

## §4 — End-to-end flow

```
  data + docs                                                       reusable assets
       │                                                                    ▲
       ▼                                                                    │
 /powerbi-new ──▶ skill kpim-analysis ──▶ skill powerbi-pipeline ──▶ /powerbi-done
                  BUSINESS phase          TECHNICAL phase              close-out
                  survey · ask back       9 steps: Power Query →       handoff checklist
                  document · plan         model → DAX → pages          distill · timeline
                       ▲                        │                            │
                       │                        ▼                            ▼
                       │                 16 MCP tools               agent powerbi-knowledge-curator
                       │                 + policy 🛡️                packages lessons on 4 axes
                       │                 + kits 🎨                          │
                       └──── /powerbi-recall ◀── INDEX + TIMELINE ◀─────────┘
                                                 (in YOUR Knowledge Dir)

  Side paths:  /powerbi-scan <.pbip>  understand an existing report
               /powerbi-kit  <.pbip>  turn it into reusable kits
               /powerbi-help          "what can this thing do?"
```

---

## §5 — What is NOT in this repo

Clone it and these will be missing. That is intentional, not a broken checkout.

| Missing | Where it lives | Why |
|---|---|---|
| **Knowledge Dir** | A folder you designate, outside the repo | It holds real client data. `knowledge.config.json` is gitignored so nobody receives anyone else's knowledge through git |
| `.env` | Your machine | Service-principal secrets. Created from `.env.example`, never committed |
| `policy.json` | Your machine | Lists the actual PII column names of your data |
| `.venv/` | Your machine | Built by `install.ps1` |
| `docs/internal/` | Your machine | Internal notes with client context |

The only path from private knowledge into the public repo: you ask for it explicitly,
`sanitize=True` runs, and you review the result.
