# Agent Data Studio

**[Tiếng Việt](README.vi.md) · [English](README.md)**

Agent Data Studio gives AI agents a shared set of data analysis skills, scripts and Power BI tools. Start with the included CSV sample; Power BI Desktop and its client libraries are needed only for Desktop workflows. Direct Power BI Desktop use requires Windows.

**First time here?** Paste the prompt from the install section below into your AI app, or follow the [step-by-step starter guide in Vietnamese](START-HERE.md). The [installation website](docs/install/index.html) and [repository map](INDEX.md) provide more detail.

## Install — paste one prompt into your AI app

Open Codex, Claude Code, Claude Desktop or Google Antigravity on Windows and paste the prompt below as is. The agent reads [INSTALL.md](INSTALL.md), the guide written for agents (in Vietnamese), checks the machine, **asks you first** before installing any software, then installs, runs doctor and reports every line back.

```text
Install Agent Data Studio on this Windows machine for the AI app you are running in
(Codex, Claude Code, Claude Desktop or Google Antigravity).

Single source: https://github.com/ducnguyen221/agent-data-studio
First read the agent guide at
https://raw.githubusercontent.com/ducnguyen221/agent-data-studio/main/INSTALL.md
(if the link cannot be opened, clone the repo and read its INSTALL.md),
then follow every step in it: check what the machine already has (Git, Python, PowerShell),
ask me before installing software or anything that needs admin rights, clone the repo to a
safe folder (not OneDrive/Desktop), run install.ps1 for the host in use, run doctor.ps1,
tell me how to restart the app, then verify with the sample samples/sales-demo.csv.

Rules: only run scripts/commands from that repo or INSTALL.md; do not change system policy;
never read or write passwords/keys; on any error stop and explain in plain words.
Finish with a summary: repo path, registered host, every doctor line, software added,
and what I need to do next.
```

| App | `-Hosts` | What differs |
|---|---|---|
| Codex (CLI and desktop) | `codex` | Installer default |
| Claude Code | `claude` | — |
| Claude Desktop (chat tab) | `claude-desktop` | 16 MCP tools only, no skills; the chat tab cannot run commands, so let another host install it or install by hand |
| Google Antigravity | `antigravity` | — |

To install by hand, you need Git and Python 3.11–3.14 ([machine setup, in Vietnamese](START-HERE.md#chuẩn-bị-máy)); then open PowerShell:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Hosts codex
```

Replace `codex` with the value from the table. The installer prepares the ignored `workspace/` station and merges the MCP entry into the host's user-level configuration (for example `~/.codex/config.toml`) next to your other servers, so every folder you open in that host shares the server of this checkout; point each machine at one checkout ([limits, in Vietnamese](hosts/README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng)). Restart the AI app in the repository folder; see the [host guides](hosts/README.md). The original skills, scripts and workflows run from this repository. The installer checks thin, local skill adapters instead of copying skills into global host folders.

Run `.\doctor.ps1 -Hosts <host>` in PowerShell after setup. It reports source, Python and MCP registration checks, while live Power BI and host skill loading still need to be verified in the host. If your organization blocks scripts, ask IT to authorize the setup under its policy. `.\update.ps1` previews a Git update; applying a reviewed commit currently requires unchanged dependencies and ignore rules and leaves host restart pending. See [START-HERE.md](START-HERE.md) for the guarded update and uninstall steps.

## First task without Power BI

Open the repository in your AI app and ask: “Read `samples/sales-demo.csv` using `skills/data-discovery/SKILL.md`. Check data quality, calculate revenue by month and save a brief report to `workspace/outputs/first-report.md`.” The [sample guide](samples/README.md) includes figures to compare with the result.

`workspace/` contains `projects/`, `knowledge/`, `outputs/`, `state/` and local configuration. Git ignores the entire folder. Keep personal data, work results and credentials out of Git. If you already use an external station, set `ADS_DATA` to its path before installing. The installer records the local binding while the engine and skills continue to run from this repository.

## Power BI capabilities

The MCP server provides 16 tools for Desktop/model discovery, policy checked DAX queries, model edits, report page kits, report design extraction and project knowledge. Desktop features require Power BI Desktop and ADOMD.NET. To check the Desktop connection, open a report and run `.\doctor.ps1 -ProbeDesktop` in PowerShell; it runs `EVALUATE ROW("x",1)` and reports `NOT_CHECKED` rather than an error when Desktop is closed. Service queries require separate credentials. The nine source skills are in [`skills/`](skills/), eight workflows in [`commands/`](commands/), report page kits in [`report-templates/`](report-templates/README.md) and document templates in [`templates/documents/`](templates/documents/).

The server applies row limits, a DAX policy and audit logging. These guard against accidental disclosure; permissions on the underlying data remain your responsibility. Microsoft's Power BI Modeling MCP can be installed separately for advanced model work.

## Repository and local data

Git updates the source in this repository. `.agents/skills/` and `.claude/skills/` are thin entry points to `skills/`; scripts run from the repository. Do not edit plugin cache copies to change this source. Git excludes `workspace/`, `.venv/`, local configuration and credentials. Check `git status` before every commit.

The KPIM sample assets (dataset profiles, the `kpim-business-light` kit and `Project_Management.xlsx`) are owned by KPIM, which permits their use and distribution with this repository under the MIT license; see [NOTICE.md](NOTICE.md) for attribution.

[Host guides](hosts/README.md) · [Repository map](INDEX.md) · [Website](https://ducnguyen.vn/agent-data-studio/) · [MIT license](LICENSE)
