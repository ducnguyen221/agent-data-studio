# powerbi-agent

**🌐 Ngôn ngữ:** **Tiếng Việt** · [English](README.md)

> ⚠️ **Chỉ chạy trên Windows.** Power BI Desktop chỉ phát hành cho Windows, nên các công cụ
> làm việc trực tiếp với Desktop trong powerbi-agent **yêu cầu Windows 10/11**. Không có bản macOS/Linux.

**MCP server + bộ skill biến AI Agent thành chuyên gia phân tích làm việc TRỰC TIẾP trên Power BI** —
từ truy vấn DAX có chính sách an toàn dữ liệu, đến dựng trang báo cáo đẹp theo template,
đến **quy trình phân tích KPIM** tài liệu hóa & chuẩn hóa dữ liệu, và pipeline thực thi end-to-end 9 khâu.

## 🏛️ Do KPIM xây dựng — chia sẻ miễn phí cho cộng đồng

Quy trình phân tích và bộ template trong powerbi-agent được xây dựng bởi **[KPIM](https://kpim.vn)** —
công ty tư vấn & triển khai giải pháp **Dữ liệu, Business Intelligence** và **đào tạo chuyên sâu về
Data & AI**. Các quy trình (KPIM workflow) cùng mẫu báo cáo ở đây được **nhiều chuyên gia KPIM phối hợp
đúc kết** từ dự án thực chiến, và **chia sẻ MIỄN PHÍ** cho cộng đồng, học viên và người làm nghề dữ liệu.
Tìm hiểu thêm: **[kpim.vn](https://kpim.vn)**.

Không chỉ là "cầu nối MCP + bảo mật dữ liệu" — repo còn đóng gói sẵn:
- 🧠 **Quy trình phân tích KPIM** (skill `kpim-analysis`): Research → Key Information (5 mindmap + tài liệu chuẩn) → Planning → Implementation → Monitoring.
- 📄 **Bộ mẫu tài liệu hóa dữ liệu & phân tích báo cáo**: `PROJECT.md`, `DATA_DICTIONARY.md`, `METRICS_CALCULATION.md`, `DOMAIN_DIMENSION.md`, `REPORTS.md`, `DESIGN.md` + `theme.json`, `Project_Management.xlsx` (6 sheet), 5 mindmap PNG — nhân bản cho dự án mới.
- 📚 **Tài liệu kỹ thuật** DAX / Power Query (M) / SQL best-practices (nguồn Microsoft Learn) trong `plugins/powerbi-agent/skills/pbi-pipeline/references/`.

Hỗ trợ **Power BI Desktop (local)** · **Power BI Service (cloud)** · **PBIP/PBIR (project files)**.
Host: **Claude Code · Codex CLI · Google Antigravity** và mọi MCP client stdio.

> 🌐 Website: **[ducnguyen.vn/powerbi-agent](https://ducnguyen.vn/powerbi-agent/)** · 📘 Cài đặt chi tiết: **[docs/INSTALL.html](docs/INSTALL.html)** ([bản web](https://ducnguyen.vn/powerbi-agent/INSTALL.html)) · Lộ trình: **[ROADMAP.md](ROADMAP.md)** · Kết quả UAT: **[docs/UAT-REPORT.md](docs/UAT-REPORT.md)**

## Cài bằng AI Agent (khuyến nghị — 1 câu lệnh)

Dán vào agent của bạn (Claude Code / Codex / Antigravity):

```
Clone https://github.com/ducnguyen221/powerbi-agent vào ~/.mcp/powerbi-mcp rồi chạy install.ps1 trong đó (đọc script trước khi chạy), sau đó restart MCP host.
```

Agent sẽ: clone → dựng `.venv` → dò ADOMD.NET/TOM (mọi bản SSMS/standalone/GAC) → đăng ký MCP
vào cả 3 host → copy **4 skill** (`powerbi-mcp`, `pbi-pipeline`, `kpim-analysis`, `pbi-knowledge`) kèm references + templates + 6 lệnh /pbi-*. Cài tay: xem [docs/INSTALL.html](docs/INSTALL.html).

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Yêu cầu: Windows (Power BI Desktop chỉ có trên Windows) · Python 3.11+ · ADOMD.NET
(có sẵn nếu cài SSMS; hoặc [Analysis Services client libraries](https://learn.microsoft.com/en-us/analysis-services/client-libraries)).

### Hoặc cài dạng plugin (hiện trong trình quản lý plugin của app)

Cùng một `.claude-plugin/marketplace.json` chạy cho **cả Claude Code lẫn Codex** — cài 4 skill +
6 lệnh `/pbi-*` + agent curator dạng plugin (chưa gồm MCP server; chạy install.ps1 để có 16 tool).
Antigravity không có plugin store — skill nạp từ thư mục skills.

```bash
# Claude Code
claude plugin marketplace add ducnguyen221/powerbi-agent && claude plugin install powerbi-agent@powerbi-agent
# Codex CLI
codex plugin marketplace add https://github.com/ducnguyen221/powerbi-agent && codex plugin add powerbi-agent@powerbi-agent
```

Chi tiết từng host: [`hosts/`](hosts/) (claude · codex · antigravity).

## 🧭 Bắt đầu thế nào — 3 bước

1. **Cài** (lệnh ở trên) → restart host → agent có 16 tool + 4 skill + 6 lệnh.
2. **`/pbi-setup`** — agent hỏi bạn chỉ định **Knowledge Dir** (folder NGOÀI repo — ưu tiên
   knowledge base/Brain có sẵn của bạn) để lưu tri thức dự án. Làm 1 lần.
3. **`/pbi-new <tên dự án>`** — bắt đầu: agent tự đọc kinh nghiệm cũ → khảo sát → tài liệu hóa →
   dựng model + báo cáo → `/pbi-done` đóng dự án là tri thức tự đóng gói cho lần sau.

## ⚡ 6 lệnh (Claude Code; Codex/Antigravity dùng skill `pbi-knowledge` cùng luồng)

| Lệnh | Làm gì |
|---|---|
| `/pbi-setup` | Khai báo Knowledge Dir (lần đầu) — nơi lưu TOÀN BỘ tri thức, ngoài repo |
| `/pbi-new <tên>` | Mở dự án mới: folder riêng + đọc kinh nghiệm cũ + chạy quy trình phân tích |
| `/pbi-scan <path.pbip>` | Quét TRỌN thiết kế 1 báo cáo: mọi trang + theme + DESIGN.md + catalog |
| `/pbi-done` | Đóng dự án: checklist bàn giao + distill + timeline + đóng gói tri thức |
| `/pbi-pack [dự án]` | Đóng gói bài học vào 4 trục: tech-stack · industry · business-domain · powerbi |
| `/pbi-recall <từ khóa>` | "Đã từng làm gì tương tự?" — tra dự án cũ, bài học, kit tái dùng |

## 🔄 Luồng skill & agent (ai làm gì, khi nào)

```
 /pbi-new ──▶ skill kpim-analysis ──▶ skill pbi-pipeline ──▶ /pbi-done ──▶ agent pbi-knowledge-curator
             (NGHIỆP VỤ: khảo sát,     (KỸ THUẬT: 9 khâu       (checklist     (đóng gói bài học 4 trục,
              hỏi ngược, tài liệu       Power Query→model→      + distill      dedup, INDEX, TIMELINE)
              KPIM, kế hoạch)           DAX→trang báo cáo)      + timeline)
                    ▲                          │
                    └── đọc knowledge/ cũ      └── tool MCP (16) + policy 🛡️ + template kit 🎨
 /pbi-recall ◀── INDEX + TIMELINE + knowledge/ ◀────────────────┘  (skill pbi-knowledge = cơ chế chung)
```

- **Skill `powerbi-mcp`** = sổ tay tra cứu 16 tool + luật policy (agent tự tra khi cần).
- **Điều phối NHIỀU agent cùng lúc** (Claude build · Codex review · Antigravity tài liệu): [AGENTS.md](AGENTS.md) §4.

## 🔐 Cơ chế Knowledge Dir (riêng tư mặc định)

- Tri thức dự án (tài liệu, kinh nghiệm, kit thô) sống ở **folder BẠN chỉ định, ngoài repo** —
  `knowledge.config.json` gitignored, mỗi máy tự khai báo, không ai nhận tri thức của ai qua git.
- Cấu trúc tự dựng: `projects/<dự án>/` · `knowledge/{4 trục}/` · `templates/` (kit riêng) ·
  `INDEX.md` · `TIMELINE.md`.
- Đường duy nhất đưa tri thức riêng → repo public: bạn chủ động ra lệnh + `sanitize=True` + review.

## 16 tool

| Nhóm | Tool | Chức năng |
|---|---|---|
| **Khám phá** | `list_local_reports` | Báo cáo Desktop đang mở (port + model ID) |
| | `list_tables` | Bảng trong model (lọc bảng hệ thống) |
| | `describe_table` | Cột + kiểu dữ liệu + measure của 1 bảng |
| **Truy vấn** 🛡️ | `execute_dax_local` | DAX lên Desktop — qua policy an toàn dữ liệu |
| | `execute_dax_service` | DAX lên Service (MSAL, token cache) — qua policy |
| **Ghi model** | `add_measure_local` | Tạo/sửa measure qua TOM |
| | `add_relationship_local` | Tạo relationship Many-to-One qua TOM |
| **Template** 🎨 | `list_templates` | Kit báo cáo có sẵn |
| | `apply_template` | Dựng TRANG MỚI từ kit — clone-and-rebind, style giữ nguyên |
| | `distill_template` | Chưng cất trang đẹp thành kit tái dùng (sanitize được) |
| **Distill** | `distill_model_schema` | Model → Markdown blueprint + Mermaid ERD |
| | `distill_report_design` | Quét TRỌN báo cáo: mọi trang + theme + DESIGN + CATALOG |
| **Knowledge OS** 🧠 | `knowledge_status` | Knowledge Dir đã setup chưa + tóm tắt hiện trạng |
| | `setup_knowledge` | Thiết lập Knowledge Dir user chỉ định (ngoài repo) |
| | `init_project` | Tạo folder dự án `projects/<slug>/` + INDEX + TIMELINE |
| | `log_timeline` | Ghi sự kiện/bài học vào TIMELINE.md (append-only) |

## 🛡️ Chính sách an toàn dữ liệu (enforce ở server, không phải lời nhắc)

Nguyên tắc: **dữ liệu thô ở lại trong engine Power BI — chỉ kết quả tổng hợp vào context LLM.**

- **aggregate-only (mặc định BẬT):** `EVALUATE 'Bảng'` / `EVALUATE ALL(...)` bị từ chối kèm hướng
  dẫn viết lại bằng `SUMMARIZECOLUMNS`/`TOPN`/measure. Tắt: `POWERBI_AGGREGATE_ONLY=0`.
- **PII blocklist:** copy `policy.example.json` → `policy.json`, liệt kê cột cấm project
  (SĐT, CMND, email…). Cột bị chặn ở MỌI truy vấn.
- **Audit log:** mọi truy vấn ghi `~/.powerbi-agent/audit/*.jsonl` (verdict + số dòng) —
  bằng chứng kiểm toán "không dump dữ liệu thô".
- **Trần dimension:** kết quả có cột chữ bị siết 200 dòng (thuần measure không giới hạn).
- *Trung thực về giới hạn:* đây là guard chống rò rỉ **sơ ý** — bảo mật cứng vẫn là RLS trên
  model + service principal quyền tối thiểu.

## 🎨 Template kit — báo cáo đẹp tái tạo được

Bài học đắt giá: **layout agent tự dựng từ đầu luôn xấu; clone trang đã chứng minh + đổi binding thì đẹp.**
`apply_template` biến luật đó thành code: giữ nguyên `visualContainerObjects` (style), chỉ đổi
name/position/fields/visualType/title.

Kit = thư mục text git-được:

```
report-templates/kpim-business-light/   # kit mẫu đi kèm (đã sanitize)
  kit.json          # meta: canvas, blocks, roles
  blueprint.md      # bản đồ trang mẫu: 30 visual, vị trí, binding
  blocks/*.json     # visual.json VERBATIM mỗi loại (card KPI, combo chart, pivot, slicer, map…)
  _page.json        # page settings + nền
```

Vòng tri thức: trang nào user khen đẹp → `distill_template` thành kit → dự án sau `apply_template` tái tạo.
Kit chứa binding nghiệp vụ thật thì để NGOÀI repo (env `POWERBI_TEMPLATES_DIR`); muốn chia sẻ → `sanitize=True`.

## 🤝 Chạy song song microsoft/powerbi-modeling-mcp (khuyến nghị)

powerbi-agent **không xây lại modeling** — delegate cho MCP chính chủ Microsoft:

```bash
claude mcp add powerbi-modeling -s user -- npx -y "@microsoft/powerbi-modeling-mcp@latest" --start
```

| Việc | Server |
|---|---|
| Query DAX + policy, schema discovery, template/PBIR report layer, distill | **powerbi-agent** |
| Tạo/sửa table/column/measure/relationship, bulk + transaction, TMDL, DAX validate | **powerbi-modeling** (Microsoft) |

## 📐 Quy trình 9 khâu (skill `pbi-pipeline`)

Agent làm dự án Power BI trọn gói theo thứ tự chuẩn, mỗi khâu có cổng kiểm:

1. Kết nối dữ liệu (Power Query, M parameter) → 2. Transform M (kiểu dữ liệu tường minh)
→ 3. Mô hình hóa star schema + relationship → 4. Measure/calc column DAX (verify từng cái)
→ 5. Truy vấn tổng hợp (policy gác) → 6+7. Visual & trang báo cáo từ template
→ 8. Nâng cao (tooltip, drill-through, parameters; bookmark để tay) → 9. Artifact + chưng cất tri thức.

Chi tiết: `plugins/powerbi-agent/skills/pbi-pipeline/SKILL.md` (tự cài vào host khi chạy install.ps1).
Kèm **tài liệu kỹ thuật** (nguồn Microsoft Learn): `plugins/powerbi-agent/skills/pbi-pipeline/references/` — `dax-best-practices.md`, `powerquery-m-best-practices.md`, `sql-best-practices.md`, `gotchas.md`.

## 📋 Quy trình phân tích KPIM (skill `kpim-analysis`) — tài liệu hóa & chuẩn hóa dữ liệu

Ngoài lớp kỹ thuật, repo đóng gói sẵn **quy trình phân tích KPIM** để agent nhận **một bộ dữ liệu + tài liệu** → tự khảo sát, hỏi ngược người dùng, và sinh ra **bộ tài liệu nghiệp vụ chuẩn hóa** trước khi dựng báo cáo. 5 pha:

**Research** (đọc data + hỏi ngược) → **Key Information** (5 thành phần: Requirements · Analytics Questions · Data · Metrics & Dimensions · Result & Delivery) → **Planning** (Excel task 2 cấp) → **Implementation** (bàn giao `pbi-pipeline`) → **Monitoring**.

Đầu ra chuẩn (thư mục `plugins/powerbi-agent/skills/kpim-analysis/document-templates/`, kèm worked-example "KPIM Mart"):

```
PROJECT.md              # tổng hợp Key Information (5 bảng + mindmap)
RESEARCH_NOTES.md       # ghi chú input + bộ câu hỏi ngược cho user
DATA_DICTIONARY.md      # bảng/nguồn/trường dữ liệu
METRICS_CALCULATION.md  # danh sách measure DAX theo nhóm
DOMAIN_DIMENSION.md     # chiều phân tích + tư duy nghiệp vụ
REPORTS.md              # danh sách báo cáo (Report Group → Report → Page) + visual
DESIGN.md + theme.json  # tư duy thiết kế + theme Power BI import chạy ngay
Project_Management.xlsx # 6 sheet: KEY INFORMATION, PLANNING, DATA DICTIONARY, METRICS_CALCULATION, DOMAIN_DIMENSION, REPORT
mindmaps/*.png          # Key Objectives / Questions / Data / Analysis / Report
scripts/                # generate_mindmaps.py, generate_project_management_xlsx.py, ...
```

Chi tiết: `plugins/powerbi-agent/skills/kpim-analysis/SKILL.md`.

## 📁 INDEX repo — từng folder & file quan trọng

> Mọi đường dẫn dưới đây tính từ **gốc repo** — clone về đâu cũng đúng. Agent đọc
> [`AGENTS.md`](AGENTS.md) trước khi làm việc; người mới đọc bảng này để định vị.

### Gốc repo — hướng dẫn & cài đặt

| File | Vai trò |
|---|---|
| [`AGENTS.md`](AGENTS.md) | **Hướng dẫn CHUẨN cho mọi agent** — bản đồ repo, luật làm việc với Power BI, giao thức điều phối multi-agent (§4). Codex đọc native. |
| [`CLAUDE.md`](CLAUDE.md) · [`GEMINI.md`](GEMINI.md) | Con trỏ về AGENTS.md cho Claude Code / Antigravity — sửa nội dung Ở AGENTS.md. |
| `README.md` | File này — giới thiệu sản phẩm + INDEX. |
| [`ROADMAP.md`](ROADMAP.md) | Định vị, kiến trúc 4 tầng, milestone (M0–M3 ✅, M4 kế hoạch). |
| [`install.ps1`](install.ps1) | **Bộ cài in-place** — venv + dò ADOMD/TOM + đăng ký MCP cả 3 host + copy skills. Idempotent. |
| [`uninstall.ps1`](uninstall.ps1) · [`pack.ps1`](pack.ps1) | Gỡ cài / đóng zip sạch mang sang máy khác. |
| `mcp_server_powerbi.py` | **Entrypoint MCP** — host đăng ký file này (shim, KHÔNG đổi tên/di chuyển). |
| `pyproject.toml` · `requirements*.txt` | Packaging + dependencies (pin & loose). |
| [`policy.example.json`](policy.example.json) | Mẫu PII blocklist → copy thành `policy.json` (gitignored) theo dự án. |
| `.env.example` | Mẫu cấu hình Power BI Service (service principal) → `.env` (gitignored). |
| `LICENSE` | MIT + attribution quy trình/công cụ: Duc Nguyen. |

### `powerbi_agent/` — package MCP server (code chính)

| File | Vai trò |
|---|---|
| `app.py` | Khởi tạo server: nạp ADOMD/TOM → FastMCP → đăng ký 11 tool. |
| `tools_query.py` | Khám phá + truy vấn: `list_local_reports` · `list_tables` · `describe_table` · `execute_dax_local/_service` (đi qua policy). |
| `policy.py` | **Tầng an toàn dữ liệu**: aggregate-only (mặc định BẬT) · PII blocklist · audit JSONL · trần dòng dimension. |
| `tools_tom.py` | Ghi model qua TOM: `add_measure_local` · `add_relationship_local` (fallback đơn lẻ — bulk dùng modeling-mcp). |
| `pbir.py` + `tools_template.py` | **Report layer**: đọc/ghi PBIR, `list_templates` · `apply_template` (clone-and-rebind) · `distill_template` (+ deep-sanitize). |
| `tools_distill.py` | `distill_model_schema` — model → Markdown blueprint + Mermaid ERD. |
| `adomd.py` · `discovery.py` · `util.py` | Dò DLL đa phiên bản SSMS · dò port Desktop · tiện ích chung. |

### `plugins/powerbi-agent/skills/` — 3 skill (NGUỒN DUY NHẤT, installer copy đi các host)

| Skill | Dùng khi | File quan trọng |
|---|---|---|
| [`kpim-analysis`](plugins/powerbi-agent/skills/kpim-analysis/SKILL.md) | **Đầu dự án** — nhận dữ liệu → khảo sát, hỏi ngược, tài liệu hóa, kế hoạch | `document-templates/` (8 mẫu tài liệu + xlsx + theme.json + 5 mindmap) · `scripts/` (generator mindmap/xlsx) |
| [`pbi-pipeline`](plugins/powerbi-agent/skills/pbi-pipeline/SKILL.md) | **Thực thi kỹ thuật** — 9 khâu Power Query → model → DAX → report | `references/` — dax / powerquery-m / sql best-practices · gotchas · powerbi-knowledge-map |
| [`powerbi-mcp`](plugins/powerbi-agent/skills/powerbi-mcp/SKILL.md) | **Tra cứu tool** — cách dùng 16 tool + luật policy + phân vai với modeling-mcp | (1 file) |
| [`pbi-knowledge`](plugins/powerbi-agent/skills/pbi-knowledge/SKILL.md) | **Knowledge OS** — luồng /pbi-* : dự án, đóng gói tri thức 4 trục, timeline, luật riêng tư | (1 file) |

Plugin còn có [`commands/`](plugins/powerbi-agent/commands/) (6 lệnh /pbi-*) và [`agents/`](plugins/powerbi-agent/agents/) (pbi-knowledge-curator). Các skill link chéo nhau bằng đường dẫn tương đối anh–em (`../<skill>/SKILL.md`) — đúng cả trong repo lẫn sau khi cài vào host.

### Các folder còn lại

| Folder | Vai trò |
|---|---|
| [`.claude-plugin/`](.claude-plugin/marketplace.json) | Marketplace manifest — cài skills dạng plugin: `claude plugin marketplace add ducnguyen221/powerbi-agent` → `claude plugin install powerbi-agent@powerbi-agent` (chỉ skills, không venv/MCP). |
| [`hosts/`](hosts/) | Hướng dẫn đăng ký RIÊNG từng host: [`claude/`](hosts/claude/README.md) · [`codex/`](hosts/codex/README.md) · [`antigravity/`](hosts/antigravity/README.md) (kèm snippet config tay). |
| [`report-templates/`](report-templates/kpim-business-light/README.md) | **Kit visual trang báo cáo** cho `apply_template` — `kpim-business-light` (12 block sanitized). |
| [`scripts/`](scripts/) | Tiện ích dev: `cli.py` (debug DAX không cần MCP: `list`/`tables`/`query`) · `test_mcp_local.py` (smoke test kết nối). |
| [`docs/`](docs/) | Website GitHub Pages: `index.html` (landing) · [`INSTALL.html`](docs/INSTALL.html) (hướng dẫn cài chi tiết — [bản web](https://ducnguyen.vn/powerbi-agent/INSTALL.html)) · [`UAT-REPORT.md`](docs/UAT-REPORT.md) (17 ca UAT trên dashboard thật). |
| `tests/` + `.github/workflows/` | Unit tests + CI (ruff + pytest, windows-latest). |

Điều phối nhiều agent cùng lúc (Claude build · Codex review · Antigravity tài liệu hóa):
xem **[AGENTS.md](AGENTS.md) §4** — single-writer, lock convention, artifact bàn giao chung.

## Bảo mật & vận hành

- `.env` (service principal cloud) không bao giờ bị ghi đè/commit — chỉ tạo từ `.env.example`.
- Tool GHI model nhắc rõ trong docstring; ghi REPORT chỉ khi file .pbip đóng (tool tự cảnh báo).
- Gỡ: `.\uninstall.ps1` (giữ file) · `.\uninstall.ps1 -RemoveVenv`.

## Tác giả & Credit

**Quy trình phân tích KPIM, bộ công cụ (MCP server + tools), template và kỹ thuật** trong repo này
được xây dựng bởi **[KPIM](https://kpim.vn)** (nhiều chuyên gia phối hợp), chủ biên & phát triển kỹ
thuật: **Duc Nguyen (Nguyễn Quang Đức — [ducnguyen221](https://github.com/ducnguyen221))** — để AI
Agent có thể **làm việc phân tích dữ liệu như một chuyên gia**. Chia sẻ miễn phí cho cộng đồng & học viên.

Nếu bạn dùng lại quy trình / template / công cụ này, vui lòng **giữ credit tới KPIM & Duc Nguyen**.

## License

**MIT** — © 2026 KPIM ([kpim.vn](https://kpim.vn)) & Duc Nguyen ([ducnguyen221](https://github.com/ducnguyen221)). Xem `LICENSE`.
Tự do dùng/sửa/phân phối theo MIT; đề nghị ghi nhận credit KPIM & tác giả quy trình.
