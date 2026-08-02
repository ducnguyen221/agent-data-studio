# powerbi-agent

**🌐 Language:** **English** · [Tiếng Việt](README.vi.md)

> ⚠️ **Windows only.** Power BI Desktop ships for Windows only, so the tools that talk to Desktop
> **require Windows 10/11**. There is no macOS/Linux build.

**An MCP server + skill pack that turns any AI Agent into a data analyst working DIRECTLY on Power BI.**
Not just a bridge: it also ships the analysis process, the documentation templates and the report
design kits that a senior consultant would bring to the job.

Supports **Power BI Desktop (local)** · **Power BI Service (cloud)** · **PBIP/PBIR project files**.
Hosts: **Claude Code · Codex CLI · Google Antigravity** and any stdio MCP client.

> 🌐 [ducnguyen.vn/powerbi-agent](https://ducnguyen.vn/powerbi-agent/) · 📘 [Full install guide](docs/INSTALL.html) ·
> 🗺️ [**INDEX.md** — the complete repo map](INDEX.md) · 🤖 [AGENTS.md](AGENTS.md) · [Roadmap](ROADMAP.md) · [UAT results](docs/UAT-REPORT.md)

## 🏛️ Built by KPIM — shared free with the community

The analysis process and report templates were built by **[KPIM](https://kpim.vn)** — a consultancy
delivering **Data & Business Intelligence** solutions and **in-depth Data & AI training**. The
workflows and templates here are **distilled by many KPIM experts** from real engagements and shared
**FREE** with the community, students and data practitioners.

---

## What you get — four pillars

| | Pillar | What it means in practice |
|---|---|---|
| **1** | **MCP Server** | 16 tools so the agent queries DAX, edits the model and writes report pages itself — every query passing a **server-side data-safety policy**, not a prompt hint. |
| **2** | **Digitized expertise** | 4 skills · 8 commands · 1 curator agent · a Knowledge OS. The agent follows a real consultant's process instead of improvising. |
| **3** | **Report design kits** | Clone a proven page and rebind the fields — style preserved 100%. Layouts an AI draws from scratch always look off; this fixes that. |
| **4** | **Document templates** | 7 markdown deliverables + a 6-sheet Excel + a Power BI theme + 5 mindmaps, ready to fill in for a new project. |

**→ Where everything lives, folder by folder: [INDEX.md](INDEX.md).**

## Install

Paste this into your agent (Claude Code / Codex / Antigravity):

```
Clone https://github.com/ducnguyen221/powerbi-agent into ~/.mcp/powerbi-mcp, then run install.ps1 there (read the script first), and restart the MCP host.
```

Or run it yourself:

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

The installer builds a `.venv`, probes for ADOMD.NET/TOM, registers the MCP server on all three
hosts, then installs the 4 skills + 8 commands + the curator agent **on each host**. It is
idempotent — safe to re-run. To refresh only the workflows: `.\install.ps1 -Only plugin`.

**Requirements:** Windows · Python 3.11+ · ADOMD.NET (bundled with SSMS, or the
[Analysis Services client libraries](https://learn.microsoft.com/en-us/analysis-services/client-libraries)).

### Or install as a plugin

The same `.claude-plugin/marketplace.json` works for **both Claude Code and Codex** — it ships the
skills, commands and agent, but **not** the 16 MCP tools (run `install.ps1` for those).

```bash
claude plugin marketplace add ducnguyen221/powerbi-agent && claude plugin install powerbi-agent@powerbi-agent
codex  plugin marketplace add https://github.com/ducnguyen221/powerbi-agent && codex plugin add powerbi-agent@powerbi-agent
```

Per-host details: [`hosts/`](hosts/).

## Your first 10 minutes

```
1.  restart your AI host          →  it picks up the MCP server
2.  /powerbi-help                 →  the agent lists what it can do and routes your request
3.  /powerbi-setup                →  designate a Knowledge Dir (a folder OUTSIDE the repo). Once.
4.  /powerbi-new "Revenue report" →  it reads past lessons, surveys the data, documents, then builds
```

Already have a `.pbip` you like? `/powerbi-scan <path>` explains its design;
`/powerbi-kit <path>` turns it into reusable kits.

## Main features

### 8 commands

| Command | What it does |
|---|---|
| `/powerbi-help` | List every capability + route your request to the right process |
| `/powerbi-setup` | Declare the Knowledge Dir — where all knowledge lives, outside the repo (once) |
| `/powerbi-new <name>` | Open a project: its own folder + prior lessons + the analysis process |
| `/powerbi-scan <path.pbip>` | Scan a report's design: every page + theme + DESIGN.md + catalog |
| `/powerbi-kit <path.pbip>` | Distill a report into a **set** of reusable report-page kits |
| `/powerbi-done` | Close a project: handoff checklist + distill + timeline + knowledge packaging |
| `/powerbi-pack [project]` | Package lessons on 4 axes: tech-stack · industry · business-domain · powerbi |
| `/powerbi-recall <keyword>` | "Have we done something like this before?" |

### 16 tools, in 5 groups

| Group | Tools |
|---|---|
| **Discover** | `list_local_reports` · `list_tables` · `describe_table` |
| **Query** 🛡️ | `execute_dax_local` · `execute_dax_service` — always through the policy |
| **Write model** | `add_measure_local` · `add_relationship_local` |
| **Templates** 🎨 | `list_templates` · `apply_template` · `distill_template` |
| **Distill** | `distill_model_schema` · `distill_report_design` |
| **Knowledge OS** 🧠 | `knowledge_status` · `setup_knowledge` · `init_project` · `log_timeline` |

Full table with descriptions: [INDEX.md](INDEX.md).

### 4 skills

`kpim-analysis` (business phase: survey → document → plan) · `powerbi-pipeline` (9 technical steps) ·
`powerbi-mcp` (tool reference) · `powerbi-knowledge` (Knowledge OS).

## 🛡️ Data safety

**Raw data stays inside the Power BI engine — only aggregated results reach the LLM.**

- **aggregate-only, ON by default** — `EVALUATE '<table>'` and `EVALUATE ALL(...)` are refused with a
  rewrite hint toward `SUMMARIZECOLUMNS`/`TOPN`. Disable with `POWERBI_AGGREGATE_ONLY=0`.
- **PII blocklist + audit log** — copy `policy.example.json` → `policy.json` and list the columns to
  block; every query is recorded to `~/.powerbi-agent/audit/*.jsonl` with its verdict and row count.
- **Honest about limits** — this guards against accidental leaks. Real security is still RLS on the
  model plus a least-privilege service principal.

Your project knowledge lives in a **Knowledge Dir you designate, outside the repo**. Nobody receives
anyone else's knowledge through git. The only path out is you asking, `sanitize=True`, and a review.

## Runs alongside microsoft/powerbi-modeling-mcp

powerbi-agent doesn't rebuild modeling — it delegates:

```bash
claude mcp add powerbi-modeling -s user -- npx -y "@microsoft/powerbi-modeling-mcp@latest" --start
```

| Task | Server |
|---|---|
| DAX + policy, schema discovery, report/PBIR layer, distill | **powerbi-agent** |
| Bulk table/column/measure/relationship edits, transactions, TMDL, DAX validate | **powerbi-modeling** (Microsoft) |

## Where to go next

| | |
|---|---|
| 🗺️ [**INDEX.md**](INDEX.md) | Complete repo map: four pillars, every folder, glossary, end-to-end flow |
| 🤖 [AGENTS.md](AGENTS.md) | Working rules for agents + the multi-agent protocol (§4) |
| 🧩 [plugins/README.md](plugins/README.md) | The digitized expertise: skills, commands, agent |
| 🎨 [report-templates/](report-templates/README.md) | How report kits work |
| 🗓️ [ROADMAP.md](ROADMAP.md) | Positioning, architecture, milestones |

Uninstall: `.\uninstall.ps1` (keeps files) · `.\uninstall.ps1 -RemoveVenv`.

## Authors & credit

The **KPIM analysis process, tooling, templates and techniques** here were built by
**[KPIM](https://kpim.vn)** (many experts collaborating), technical lead & development by
**Duc Nguyen (Nguyễn Quang Đức — [ducnguyen221](https://github.com/ducnguyen221))** — so an AI Agent
can **do data analysis like an expert**. Shared free with the community and students.

If you reuse the process / templates / tools, please **keep the credit to KPIM & Duc Nguyen**.

## License

**MIT** — © 2026 KPIM ([kpim.vn](https://kpim.vn)) & Duc Nguyen. See [`LICENSE`](LICENSE).
