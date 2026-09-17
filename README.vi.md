# powerbi-agent

**🌐 Ngôn ngữ:** **Tiếng Việt** · [English](README.md)

> ⚠️ **Chỉ chạy trên Windows.** Power BI Desktop chỉ phát hành cho Windows, nên các tool làm việc
> trực tiếp với Desktop **yêu cầu Windows 10/11**. Không có bản macOS/Linux.

**MCP server + bộ skill biến AI Agent thành chuyên gia phân tích làm việc TRỰC TIẾP trên Power BI.**
Không chỉ là cầu nối: repo đóng gói sẵn cả quy trình phân tích, bộ mẫu tài liệu và kho mẫu thiết kế
báo cáo mà một chuyên gia lâu năm sẽ mang theo khi vào dự án.

Hỗ trợ **Power BI Desktop (local)** · **Power BI Service (cloud)** · **file dự án PBIP/PBIR**.
Host: **Claude Code · Codex CLI · Google Antigravity** và mọi MCP client stdio.

> 🌐 [ducnguyen.vn/powerbi-agent](https://ducnguyen.vn/powerbi-agent/) · 📘 [Cài đặt chi tiết](docs/INSTALL.html) ·
> 🗺️ [**INDEX.md** — bản đồ toàn repo](INDEX.md) · 🤖 [AGENTS.md](AGENTS.md) · [Lộ trình](ROADMAP.md) · [Kết quả UAT](docs/UAT-REPORT.md)

## 🏛️ Do KPIM xây dựng — chia sẻ miễn phí cho cộng đồng

Quy trình phân tích và bộ template được xây dựng bởi **[KPIM](https://kpim.vn)** — công ty tư vấn &
triển khai giải pháp **Dữ liệu, Business Intelligence** và **đào tạo chuyên sâu Data & AI**. Các quy
trình cùng mẫu báo cáo ở đây được **nhiều chuyên gia KPIM phối hợp đúc kết** từ dự án thực chiến và
**chia sẻ MIỄN PHÍ** cho cộng đồng, học viên, người làm nghề dữ liệu.

---

## Bạn nhận được gì — bốn trụ cột

| | Trụ cột | Nghĩa là gì trong thực tế |
|---|---|---|
| **1** | **MCP Server** | 16 tool để agent tự truy vấn DAX, sửa model, ghi trang báo cáo — mọi câu truy vấn đều đi qua **policy an toàn dữ liệu ở phía server**, không phải lời nhắc trong prompt. |
| **2** | **Chuyên môn đã số hóa** | 9 skill · 8 lệnh · 1 agent curator · Knowledge OS. Agent làm theo quy trình thật của chuyên gia thay vì tự ứng biến. |
| **3** | **Kho mẫu thiết kế báo cáo** | Nhân bản trang đã đẹp rồi bind field mới — style giữ nguyên 100%. Layout AI tự vẽ luôn nhìn sai lệch; đây là cách chữa. |
| **4** | **Bộ mẫu tài liệu** | 7 file markdown bàn giao + Excel 6 sheet + theme Power BI + 6 mindmap trong [`templates/documents/`](templates/documents/), điền là dùng được cho dự án mới. |

**→ Từng thư mục nằm đâu, chứa gì: [INDEX.md](INDEX.md).**

## Cài đặt

Dán câu này vào agent của bạn (Claude Code / Codex / Antigravity):

```
Clone https://github.com/ducnguyen221/powerbi-agent vào ~/.mcp/powerbi-mcp rồi chạy install.ps1 trong đó (đọc script trước khi chạy), sau đó restart MCP host.
```

Hoặc tự chạy:

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

Installer dựng `.venv`, dò ADOMD.NET/TOM, đăng ký MCP server vào cả 3 host, rồi cài 9 skill + 8 lệnh từ `skills/` và `commands/` của repo
cho từng host (agent curator lấy từ `agents/`, chỉ Claude Code có thư mục `agents/` chuẩn — host khác
vẫn có năng lực đó qua skill `pbi-knowledge`). Idempotent — chạy lại nhiều lần an toàn — và tự dọn skill/lệnh tên cũ do các bản trước sinh ra. Chỉ muốn cập nhật phần
quy trình: `.\install.ps1 -Only plugin`.

**Yêu cầu:** Windows · Python 3.11+ · ADOMD.NET (có sẵn khi cài SSMS, hoặc
[Analysis Services client libraries](https://learn.microsoft.com/en-us/analysis-services/client-libraries)).

### Hoặc cài dạng plugin

Cùng một `.claude-plugin/marketplace.json` chạy cho **cả Claude Code lẫn Codex** — cài skill, lệnh và
agent, **chưa gồm** 16 tool MCP (muốn đủ tool thì chạy `install.ps1`).

```bash
claude plugin marketplace add ducnguyen221/powerbi-agent && claude plugin install powerbi-agent@powerbi-agent
codex  plugin marketplace add https://github.com/ducnguyen221/powerbi-agent && codex plugin add powerbi-agent@powerbi-agent
```

Chi tiết từng host: [`hosts/`](hosts/).

## 10 phút đầu tiên

```
1.  restart AI host của bạn        →  host nạp MCP server
2.  /pbi-help                      →  agent tự liệt kê năng lực và định tuyến yêu cầu của bạn
3.  /pbi-setup                     →  chỉ định thư mục dự án (folder NGOÀI repo). Làm 1 lần.
4.  /pbi-new "Báo cáo doanh thu"   →  agent đọc kinh nghiệm cũ, khảo sát, tài liệu hóa, rồi dựng
```

Đã có sẵn file `.pbip` ưng ý? `/pbi-scan <path>` giải thích thiết kế của nó;
`/pbi-kit <path>` biến nó thành bộ kit tái dùng.

## Tính năng chính

### 8 lệnh

| Lệnh | Làm gì |
|---|---|
| `/pbi-help` | Liệt kê mọi năng lực + định tuyến yêu cầu của bạn tới đúng quy trình |
| `/pbi-setup` | Khai báo thư mục dự án — nơi lưu toàn bộ tri thức, ngoài repo (làm 1 lần) |
| `/pbi-new <tên>` | Mở dự án: folder riêng + đọc kinh nghiệm cũ + chạy quy trình phân tích |
| `/pbi-scan <path.pbip>` | Quét thiết kế 1 báo cáo: mọi trang + theme + DESIGN.md + catalog |
| `/pbi-kit <path.pbip>` | Chưng cất báo cáo thành **bộ** kit trang báo cáo tái dùng |
| `/pbi-done` | Đóng dự án: checklist bàn giao + distill + timeline + đóng gói tri thức |
| `/pbi-pack [dự án]` | Đóng gói bài học theo 4 trục: tech-stack · industry · business-domain · powerbi |
| `/pbi-recall <từ khóa>` | "Đã từng làm gì tương tự chưa?" |

### 16 tool, chia 6 nhóm

| Nhóm | Tool |
|---|---|
| **Khám phá** | `list_local_reports` · `list_tables` · `describe_table` |
| **Truy vấn** 🛡️ | `execute_dax_local` · `execute_dax_service` — luôn đi qua policy |
| **Ghi model** | `add_measure_local` · `add_relationship_local` |
| **Template** 🎨 | `list_templates` · `apply_template` · `distill_template` |
| **Distill** | `distill_model_schema` · `distill_report_design` |
| **Knowledge OS** 🧠 | `knowledge_status` · `setup_knowledge` · `init_project` · `log_timeline` |

Bảng đầy đủ kèm mô tả: [INDEX.md](INDEX.md).

### 9 skill

Tất cả nằm trong [`skills/`](skills/):
`data-discovery` (pha nghiệp vụ: khảo sát → tài liệu hóa → kế hoạch) · `data-mockup` (dữ liệu mẫu/mockup) ·
`pbi-model` (Power Query/M, star schema, measure DAX trong TMDL) · `pbi-analysis` (sổ tay tra cứu tool) ·
`pbi-design` (thiết kế trang báo cáo / Design Brief trước PBIR) · `pbi-build` (9 khâu kỹ thuật) ·
`pbi-review` (review SQL, DAX, model, trang báo cáo) · `pbi-publish` (publish lên Fabric / Power BI Service) ·
`pbi-knowledge` (Knowledge OS).

## 🛡️ An toàn dữ liệu

**Dữ liệu thô ở lại trong engine Power BI — chỉ kết quả đã tổng hợp mới tới LLM.**

- **aggregate-only, BẬT mặc định** — `EVALUATE '<table>'` và `EVALUATE ALL(...)` bị từ chối kèm gợi ý
  viết lại bằng `SUMMARIZECOLUMNS`/`TOPN`. Tắt bằng `POWERBI_AGGREGATE_ONLY=0`.
- **Blocklist PII + nhật ký audit** — copy `policy.example.json` → `policy.json` rồi liệt kê cột cần
  chặn; mọi truy vấn được ghi vào `<thư mục dự án>/audit/*.jsonl` kèm phán quyết và số dòng.
- **Nói thật về giới hạn** — đây là lớp chắn rò rỉ do sơ suất. Bảo mật thật vẫn là RLS trên model +
  service principal quyền tối thiểu.

Tri thức dự án sống trong **thư mục dự án bạn chỉ định, ngoài repo**. Không ai nhận tri thức của ai
qua git. Đường duy nhất đi ra: bạn chủ động yêu cầu + `sanitize=True` + review.

## Chạy song song microsoft/powerbi-modeling-mcp

powerbi-agent không dựng lại phần modeling — nó giao việc:

```bash
claude mcp add powerbi-modeling -s user -- npx -y "@microsoft/powerbi-modeling-mcp@latest" --start
```

| Việc | Server |
|---|---|
| DAX + policy, khám phá schema, tầng report/PBIR, distill | **powerbi-agent** |
| Sửa bảng/cột/measure/quan hệ hàng loạt, transaction, TMDL, DAX validate | **powerbi-modeling** (Microsoft) |

## Đi tiếp

| | |
|---|---|
| 🗺️ [**INDEX.md**](INDEX.md) | Bản đồ toàn repo: 4 trụ cột, từng thư mục, từ điển, luồng end-to-end |
| 🤖 [AGENTS.md](AGENTS.md) | Luật làm việc cho agent + giao thức đa-agent (§4) |
| 🧩 [plugins/README.md](plugins/README.md) | Phần chuyên môn đã số hóa: skill, lệnh, agent |
| 🎨 [report-templates/](report-templates/README.md) | Kit báo cáo hoạt động thế nào |
| 🗓️ [ROADMAP.md](ROADMAP.md) | Định vị, kiến trúc, cột mốc |

Gỡ cài: `.\uninstall.ps1` (giữ file) · `.\uninstall.ps1 -RemoveVenv`.

**Đã có skill trùng tên?** Trình cài không bao giờ xoá skill không phải do nó tạo. Gặp skill có
`name:` trùng nhưng thiếu dấu sở hữu của chúng tôi, nó **dời** bản đó ra cạnh thư mục skills
(`powerbi-agent-backup-<dấu-thời-gian>\`) rồi cài bản của mình. Muốn giữ bản của bạn: đặt một file
rỗng tên `.powerbi-agent-keep` trong thư mục đó — cả cài lẫn gỡ đều để yên, chạy bao nhiêu lần
cũng vậy.

## Tác giả & ghi công

**Quy trình phân tích KPIM, bộ công cụ, template và kỹ thuật** trong repo được xây dựng bởi
**[KPIM](https://kpim.vn)** (nhiều chuyên gia phối hợp), dẫn dắt kỹ thuật & phát triển bởi
**Nguyễn Quang Đức ([ducnguyen221](https://github.com/ducnguyen221))** — để AI Agent **làm phân tích
dữ liệu như một chuyên gia**. Chia sẻ miễn phí cho cộng đồng và học viên.

Nếu bạn tái sử dụng quy trình / template / công cụ, xin **giữ ghi công KPIM & Đức Nguyễn**.

## Giấy phép

**MIT** — © 2026 KPIM ([kpim.vn](https://kpim.vn)) & Đức Nguyễn. Xem [`LICENSE`](LICENSE).
