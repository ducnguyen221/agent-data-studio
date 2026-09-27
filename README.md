# Agent Data Studio

**[Tiếng Việt](README.vi.md) · [English](README.md)**

Agent Data Studio gives AI agents a shared set of data analysis skills, scripts and Power BI tools. Start with the included CSV sample; Power BI Desktop and its client libraries are needed only for Desktop workflows. Direct Power BI Desktop use requires Windows.

**First time here?** Follow the [step-by-step starter guide in Vietnamese](START-HERE.md). The [installation website](docs/install/index.html) and [repository map](INDEX.md) provide more detail.

## Install for Codex

On Windows, install Git and Python 3.11 or later, then open PowerShell:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
.\install.ps1
```

The installer defaults to **Codex**, registers this repository's MCP server and prepares the ignored `workspace/` station. The MCP entry is merged into the host's user-level configuration (for example `~/.codex/config.toml`) next to your other servers, so every folder you open in that host shares the server of this checkout; point each machine at one checkout ([limits, in Vietnamese](hosts/README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng)). Restart Codex in the repository folder. Use `-Hosts claude` or `-Hosts antigravity` for another host; see the [host guides](hosts/README.md). The original skills, scripts and workflows run from this repository. The installer checks thin, local skill adapters instead of copying skills into global host folders.

Run `.\doctor.ps1 -Hosts codex` in PowerShell after setup. It reports source, Python and MCP registration checks, while live Power BI and host skill loading still need to be verified in the host. If your organization blocks scripts, ask IT to authorize the setup under its policy. `.\update.ps1` previews a Git update; applying a reviewed commit currently requires unchanged dependencies and ignore rules and leaves host restart pending. See [START-HERE.md](START-HERE.md) for the guarded update and uninstall steps.

If you want Codex to handle setup, ask it to clone this repository, read `START-HERE.md`, run `install.ps1`, verify the result and guide you through the sample CSV exercise.

## First task without Power BI

In Codex, open the repository and ask: “Read `samples/sales-demo.csv` using `skills/data-discovery/SKILL.md`. Check data quality, calculate revenue by month and save a brief report to `workspace/outputs/first-report.md`.” The [sample guide](samples/README.md) includes figures to compare with the result.

`workspace/` contains `projects/`, `knowledge/`, `outputs/`, `state/` and local configuration. Git ignores the entire folder. Keep personal data, work results and credentials out of Git. If you already use an external station, set `ADS_DATA` to its path before installing. The installer records the local binding while the engine and skills continue to run from this repository.

## Power BI capabilities

The MCP server provides 16 tools for Desktop/model discovery, policy checked DAX queries, model edits, report page kits, report design extraction and project knowledge. Desktop features require Power BI Desktop and ADOMD.NET. To check the Desktop connection, open a report and run `.\doctor.ps1 -ProbeDesktop` in PowerShell; it runs `EVALUATE ROW("x",1)` and reports `NOT_CHECKED` rather than an error when Desktop is closed. Service queries require separate credentials. The nine source skills are in [`skills/`](skills/), eight workflows in [`commands/`](commands/), report page kits in [`report-templates/`](report-templates/README.md) and document templates in [`templates/documents/`](templates/documents/).

The server applies row limits, a DAX policy and audit logging. These guard against accidental disclosure; permissions on the underlying data remain your responsibility. Microsoft's Power BI Modeling MCP can be installed separately for advanced model work.

## Repository and local data

Git updates the source in this repository. `.agents/skills/` and `.claude/skills/` are thin entry points to `skills/`; scripts run from the repository. Do not edit plugin cache copies to change this source. Git excludes `workspace/`, `.venv/`, local configuration and credentials. Check `git status` before every commit.

The KPIM sample assets (dataset profiles, the `kpim-business-light` kit and `Project_Management.xlsx`) are owned by KPIM, which permits their use and distribution with this repository under the MIT license; see [NOTICE.md](NOTICE.md) for attribution.

[Host guides](hosts/README.md) · [Repository map](INDEX.md) · [Website](https://ducnguyen.vn/agent-data-studio/) · [MIT license](LICENSE)
