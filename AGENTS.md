# AGENTS.md — Agent Data Studio

> File hướng dẫn CHUẨN cho mọi AI agent (Claude Code · Codex CLI · Google Antigravity · bất kỳ
> tool nào đọc AGENTS.md). `CLAUDE.md` và `GEMINI.md` chỉ là con trỏ về file này — sửa Ở ĐÂY.

## 0. Ranh giới source và dữ liệu

**Engine, script, skill, workflow và template public chạy từ repo này. Dữ liệu riêng
nằm ở trạm:** `workspace/` ngay trong repo cho chế độ basic (Git bỏ qua toàn bộ), hoặc
thư mục ngoài repo qua `ADS_DATA` cho trạm riêng. Không chép engine/skill sang trạm.

`workspace/` là dữ liệu riêng dù nằm trong checkout: không commit, đóng gói hay chia sẻ cả
folder này. `.gitignore` không ngăn được `git add -f` hoặc file đã track; trước khi phát hành
phải kiểm Git index và artifact. Không đưa tên khách hàng, schema thật, credential, policy
hoặc log truy vấn vào phần source được Git theo dõi.

**Agent chỉ được GHI vào phần source được Git theo dõi đúng 3 loại:**

| Được ghi | Ví dụ |
|---|---|
| 1. **Template ĐÃ sanitize** | kit mới vào `report-templates/` — bắt buộc `sanitize=True` + user duyệt |
| 2. **Tri thức NỀN TẢNG** | best-practice DAX/M/SQL, cách làm chung — **không tên khách, không số liệu dự án** |
| 3. **Sửa code / docs / test** của chính repo | bug fix, tài liệu, CI |

**Mọi thứ khác đi vào trạm dữ liệu** (`POWERBI_PROJECT_DIR` trong `config.env` của trạm): tài liệu dự án, báo cáo,
model schema đã distill, kit chưa sanitize, log truy vấn, blocklist PII.

Chưa biết trạm hoặc dự án ở đâu → gọi `knowledge_status`; nếu chưa setup thì dùng
`workspace/` mặc định hoặc hỏi người dùng chọn trạm ngoài. Không tự ghi vào source track.

> Máy kiểm luật này, không phải mắt: `tests/test_no_leak.py` chặn tên nghiệp vụ trong kit,
> file riêng tư bị track, đường dẫn home thật, và file lạ ở thư mục gốc.

## 1. Repo này là gì

**Agent Data Studio** = MCP server (16 tool) + 9 skill + 8 lệnh /pbi-* giúp AI Agent làm phân tích dữ liệu
**end-to-end trên Power BI**: truy vấn DAX qua chính sách an toàn dữ liệu, khám phá/ghi model,
dựng trang báo cáo theo template kit, quy trình dự án chuẩn hóa, và Knowledge OS (§4b).

Repo sắp theo **4 trụ cột giá trị** — nhãn ▸ dưới đây cho biết mỗi nhánh phục vụ trụ nào:

```
agent-data-studio/
├─ powerbi_agent/                ▸1  package MCP server (Python) — query · policy · TOM · PBIR · distill
├─ mcp_server_powerbi.py         ▸1  entrypoint host đăng ký (shim — ĐỪNG đổi tên/di chuyển)
├─ hosts/{claude,codex,antigravity}/ ▸1  hướng dẫn đăng ký RIÊNG từng host
├─ policy.example.json           ▸1  mẫu blocklist PII → tạo bản riêng trong station
│
├─ skills/                       ▸2  9 skill dùng chung mọi host (nguồn DUY NHẤT — sửa ở đây)
│  ├─ data-discovery/                pha NGHIỆP VỤ: khảo sát → tài liệu hóa → kế hoạch
│  │  └─ scripts/                       generator mindmap / xlsx (đọc mẫu từ templates/documents/)
│  ├─ data-mockup/                   dữ liệu mẫu (mockup/sample data)
│  ├─ pbi-model/                     Power Query/M · star schema · relationship · DAX measure (TMDL) (+references/kpim/)
│  ├─ pbi-analysis/                  hướng dẫn dùng 16 tool + luật an toàn dữ liệu
│  ├─ pbi-design/                    thiết kế trang báo cáo / Design Brief trước khi ghi PBIR
│  ├─ pbi-build/                     pha KỸ THUẬT: 9 khâu Power Query → model → DAX → report (+references/)
│  ├─ pbi-review/                    review độc lập SQL · DAX · model · trang báo cáo
│  ├─ pbi-publish/                   publish lên Fabric / Power BI Service
│  └─ pbi-knowledge/                 Knowledge OS: dự án · tri thức 4 trục · timeline
├─ commands/                     ▸2  8 lệnh /pbi-* dùng trực tiếp từ repo
├─ agents/                       ▸2  pbi-knowledge-curator (đóng gói tri thức)
├─ templates/documents/          ▸4  mẫu tài liệu: md + xlsx + theme.json + mindmaps
├─ upstream/ · LICENSES/ · THIRD_PARTY_NOTICES.md   vendored upstream · giấy phép bên thứ ba
│
├─ report-templates/             ▸3  kit VISUAL trang báo cáo (PBIR) cho apply_template
│  └─ kpim-business-light/           kit mẫu, 12 block đã sanitize
│
├─ .agents/skills/ · .claude/skills/  adapter mỏng trỏ về skills/ gốc trong repo
├─ .claude-plugin/ · .codex-plugin/  manifest plugin tùy chọn
├─ workspace/                        trạm basic, toàn bộ bị Git bỏ qua
├─ install.ps1 · uninstall.ps1       cài/gỡ kết nối host; mặc định chỉ Codex
├─ scripts/                          tiện ích dev: cli.py (debug DAX không cần MCP) · test_mcp_local.py
├─ tests/ · .github/workflows/       pytest + ruff, CI windows-latest
└─ docs/                             website Pages công khai
```

**Bản đồ chi tiết từng file + từ điển thuật ngữ:** [`INDEX.md`](INDEX.md).

## 2. Cài đặt và làm việc đầu tiên

Theo [`START-HERE.md`](START-HERE.md) và [`README.vi.md`](README.vi.md). Bộ cài chạy tại
checkout, tạo trạm basic `workspace/` và đăng ký **host được chọn**; mặc định chỉ Codex.
Trạm riêng phải chọn tường minh qua `ADS_DATA` trước cài. Đọc skill từ `skills/` qua adapter
project-local, không lấy bản copy/cache làm nguồn thực thi. Sau khi cài, mở phiên host mới,
kiểm đường source/trạm, rồi thực hành `samples/sales-demo.csv` trước khi dùng Power BI Desktop.

MCP Microsoft là tích hợp tùy chọn độc lập; quyền và policy của nó không tự kế thừa policy
của Agent Data Studio. Hướng dẫn riêng từng host ở `hosts/<tên host>/README.md`.

## 3. Cách agent làm việc với Power BI (luật CỨNG)

1. **Thứ tự skill:** dự án mới → `data-discovery` (nghiệp vụ) → `pbi-build` (9 khâu kỹ thuật);
   câu hỏi lẻ → tool trực tiếp theo `pbi-analysis`.
2. **Dữ liệu thô ở lại engine** — policy aggregate-only đang enforce ở server: viết DAX tổng hợp
   (SUMMARIZECOLUMNS/TOPN/measure), KHÔNG `EVALUATE 'Bảng'`. Đầu dự án hỏi user cột PII → ghi
   `policy.json`.
3. **PBIP-first** — bảo user Save As `.pbip` ngay đầu dự án (model = TMDL, report = PBIR, git được).
4. **Ghi model lúc nào cũng được (engine live); ghi REPORT chỉ khi file .pbip ĐÓNG** — mở +
   Ctrl+S phiên cũ sẽ đè mất trang agent vừa tạo.
5. **Không bao giờ tự dựng layout trang từ đầu** — `list_templates` → `apply_template`
   (clone-and-rebind). Trang đẹp user duyệt → `distill_template` thành kit.
6. **Mỗi khâu có cổng kiểm chạy được** — không verify = chưa xong. Nghiệm thu MẮT trang báo cáo
   là của user (agent không thấy render).
7. **Phân vai 2 MCP:** modeling hàng loạt/TMDL/validate → `powerbi-modeling` (Microsoft);
   query + policy + report layer + distill → `agent-data-studio` (repo này).

## 4. Điều phối NHIỀU agent cùng lúc (multi-agent)

Repo này thiết kế để Claude Code + Codex + Antigravity làm việc **song song trên cùng 1 dự án
Power BI**. Luật phối hợp:

### 4.1 Single-writer — quy tắc số 1
- **MODEL** (measure/relationship/TOM/TMDL): tại một thời điểm chỉ **1 agent GHI**. Ghi xong
  (SaveChanges) mới bàn giao. Không interleave write giữa 2 MCP server hoặc 2 agent.
- **REPORT** (`*.Report/` PBIR): 1 agent **sở hữu trọn** thư mục này trong 1 lượt làm việc,
  và chỉ khi file .pbip đóng.
- **Lock convention** (tool-agnostic): trước khi GHI model/report, tạo file
  `<thư mục dự án>/.powerbi-write-lock` nội dung `<tên agent> | <việc> | <timestamp>`; xóa khi xong.
  Agent khác thấy lock → CHỈ ĐỌC (query/analyze), không ghi, không xóa lock của agent khác.

### 4.2 Phân vai gợi ý (điều chỉnh theo dự án)
| Vai | Agent gợi ý | Làm gì |
|---|---|---|
| **Orchestrator / Builder** | Claude Code | Chạy data-discovery + pbi-build, GHI model & report, giữ lock |
| **Reviewer / Second-opinion** | Codex | CHỈ ĐỌC: verify measure (`execute_dax_local` đối chiếu số), soi ERD từ `distill_model_schema`, review DAX/page_spec trước khi Builder ghi |
| **Analyst / Documenter** | Antigravity | Pha data-discovery (tài liệu nghiệp vụ, mindmap, kế hoạch), soạn `page_spec` JSON, viết artifact bàn giao |

Mọi vai đều đọc được an toàn đồng thời — tool ĐỌC (list/describe/execute_dax/distill) không cần lock.

### 4.3 Kênh giao tiếp chung giữa các agent
- **Artifact files trong thư mục dự án** (nguồn sự thật, agent nào cũng đọc/ghi nối tiếp):
  `PLAN.md` → `CHANGESET.md` → `VERIFICATION.md` → `HANDOFF.md` (+ tài liệu data-discovery).
  Bàn giao giữa 2 agent = ghi rõ trạng thái vào artifact, KHÔNG dựa vào trí nhớ phiên chat.
- **Audit log** `<thư mục dự án>/audit/*.jsonl` = sổ cái chung mọi truy vấn (agent nào, chặn gì)
  — Reviewer dùng làm bằng chứng kiểm tra.
- **Blueprint từ `distill_model_schema`** = "bản đồ model" chung: Builder tạo sau mỗi đợt ghi
  model; các agent khác đọc thay vì tự query lại schema.

### 4.4 Checklist khi nhận bàn giao (agent nào cũng vậy)
1. Đọc `AGENTS.md` này + artifact mới nhất trong thư mục dự án.
2. `list_local_reports` xác nhận trạng thái Desktop; kiểm tra `.powerbi-write-lock`.
3. Làm phần việc của vai mình; cập nhật artifact; xóa lock nếu mình tạo.

## 4b. Knowledge OS — dự án, tri thức, timeline (luồng /pbi-*)

Tri thức làm việc sống trong trạm: `workspace/` cho basic hoặc `ADS_DATA` ngoài repo.
Con trỏ dự án là `POWERBI_PROJECT_DIR` trong `config.env` của trạm; credential không nằm
trong file này. `knowledge.config.json` đời cũ chỉ được đọc để migrate, không ghi mới.
Cơ chế đầy đủ: skill `pbi-knowledge`.

| Lệnh (Claude) / luồng (host khác) | Làm gì |
|---|---|
| `/pbi-help` | Liệt kê lệnh/skill/16 tool + **bảng định tuyến** "user nói gì thì chạy gì" |
| `/pbi-setup` | Dùng trạm basic mặc định hoặc nơi user đã chọn → `setup_knowledge` |
| `/pbi-new <tên>` | `init_project` + đọc kinh nghiệm cũ + chạy data-discovery → pbi-build |
| `/pbi-scan <path>` | `distill_report_design` — hồ sơ thiết kế trọn báo cáo vào projects/<slug>/design/ |
| `/pbi-kit <path>` | Chưng cất 1 file .pbip thành **BỘ** kit tái dùng (nhiều trang + theme chung) |
| `/pbi-done` | Checklist đóng dự án + distill + `log_timeline` + pack |
| `/pbi-pack` | Agent `pbi-knowledge-curator` đóng gói bài học 4 trục (dedup, Why/How-to-apply) |
| `/pbi-recall <từ khóa>` | Tra INDEX/TIMELINE/knowledge — "đã từng làm gì tương tự" |

Luật: (1) gọi `knowledge_status` TRƯỚC mọi quy trình tri thức; chưa setup thì thiết lập
basic hoặc hỏi user nơi ngoài repo; (2) mọi file dự án ghi vào `projects/<slug>/` trong trạm;
(3) dữ liệu trạm KHÔNG BAO GIỜ commit;
đường duy nhất ra repo public = user ra lệnh + sanitize + review.

## 5. Quy ước phát triển repo (khi agent sửa CODE repo này)

- Python 3.11+, ruff (line 120), pytest — chạy `pytest tests -m "not integration"` + ruff trước commit.
- `mcp_server_powerbi.py` là shim back-compat: host đăng ký file này — GIỮ bề mặt import.
- Skill là nguồn duy nhất ở `skills/`; adapter `.agents/skills/` và `.claude/skills/`
  chỉ dẫn host đọc nguồn này. Không sửa bản cache/plugin thay nguồn.
- `.ps1` phải UTF-8 **có BOM** (PowerShell 5.1 + tiếng Việt); JSON PBIR ghi UTF-8 **không BOM**.
- KHÔNG commit: `workspace/`, `.ads-binding.json`, `.env*`, `config.env`, `policy.json`, `.venv/`, kit chứa binding nghiệp vụ thật (sanitize trước),
  schema model khách (distill ghi ra NGOÀI repo), tham chiếu máy cá nhân.
- Docs công khai (README/INSTALL/docs/) phải machine-agnostic — không đường dẫn/tên máy riêng, không tên khách hàng (dùng ví dụ generic như "KPIM Mart").
- **Plugin manifest:** `plugin.json` CHỈ khai `skills` — KHÔNG khai `commands`/`agents` (Claude từ chối field `agents`; auto-discover theo convention `commands/` + `agents/`). marketplace.json dùng chung cho Claude + Codex.
- **Song ngữ:** `README.md` = English (canonical). Sửa README.md thì **mirror sang `README.vi.md` TRONG CÙNG commit**. Các doc khác (AGENTS/ROADMAP/skills) hiện **chỉ có tiếng Việt** — KHÔNG tạo bản `-VN` song song (tránh drift). Website `docs/`: toggle ngôn ngữ mới phủ heading/hero/footer; thân bài và `docs/INSTALL.html` còn VI-only. Đừng hứa EN nhiều hơn thực tế trong docs công khai.

## 6. File nào host nào đọc

| Host | File hướng dẫn | Skills | MCP config |
|---|---|---|---|
| Claude Code | `CLAUDE.md` → trỏ về đây | `.claude/skills/` → `skills/` | cấu hình Claude của host |
| Codex CLI/desktop | `AGENTS.md` (file này, native) | `.agents/skills/` → `skills/` | cấu hình Codex của host |
| Antigravity | `GEMINI.md` → trỏ về đây | `.agents/skills/` → `skills/` | cấu hình Antigravity của host |

## 7. Ghi cấu hình host

Config của host (`config.toml`, `.claude.json`, `mcp_config.json`) là file **NHIỀU CHỦ CÙNG GHI**:
host tự ghi, `install.ps1` của ta ghi, tool khác cũng ghi. Ghi sai = **host không khởi động nổi**,
và triệu chứng nổ ra ở nơi hoàn toàn khác — rất khó lần ra.

1. **Theo cấu trúc của host.** Giữ định dạng TOML/JSON mà host đang dùng; Codex dùng sub-table
   cho môi trường MCP. Không tạo khóa trùng qua hai kiểu khai báo.
2. **Replace phải xóa cả block cha LẪN mọi sub-table** `[x.y.*]`. Regex chỉ khớp block cha sẽ để
   sub-table mồ côi — trong TOML, sub-table mồ côi vẫn *ngầm tạo* bảng cha → server không có
   `command` → host lỗi kiểu khác.
3. **Xác định ranh giới block đúng.** Dòng mở đầu một table mới mới kết thúc block hiện hành;
   ký tự `[` nằm trong giá trị mảng không phải điểm cắt.
4. **Validate parse NGAY sau khi ghi** bằng parser tương ứng.
   Config hỏng = host chết; không được fail im lặng. Hỏng → báo khôi phục `.bak`.
5. **Test = chạy installer 2 LẦN LIÊN TIẾP trên fixture lỗi.** Phải *heal* được file hỏng và
   *idempotent* (lần 2 giống hệt lần 1). Chạy 1 lần trên file sạch không chứng minh được gì.
6. **Không ghi credential vào host config.** Cấu hình không mật khẩu sống trong
   `station/config.env`; secret cho Power BI Service chỉ nạp khi cần từ kho secret do user
   chỉ định. Host config chỉ giữ entry MCP và đường source cần để chạy; không in nội dung bí mật.
