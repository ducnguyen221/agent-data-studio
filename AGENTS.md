# AGENTS.md — powerbi-agent

> File hướng dẫn CHUẨN cho mọi AI agent (Claude Code · Codex CLI · Google Antigravity · bất kỳ
> tool nào đọc AGENTS.md). `CLAUDE.md` và `GEMINI.md` chỉ là con trỏ về file này — sửa Ở ĐÂY.

## 0. LUẬT SỐ 0 — repo này KHÔNG phải nơi làm việc

**Repo giữ thứ đến từ GitHub. MỌI sản phẩm tạo ra đi về thư mục dữ liệu ngoài repo.**

Repo là **git working tree công khai**. Một lệnh `git add -A` là tài liệu khách hàng bị commit —
và chuyện đó đã xảy ra thật: kit `kpim-business-light` từng mang tên measure thật của khách hàng
suốt nhiều tháng trước khi bị test tự động phát hiện.

**Agent chỉ được GHI vào repo đúng 3 loại:**

| Được ghi | Ví dụ |
|---|---|
| 1. **Template ĐÃ sanitize** | kit mới vào `report-templates/` — bắt buộc `sanitize=True` + user duyệt |
| 2. **Tri thức NỀN TẢNG** | best-practice DAX/M/SQL, cách làm chung — **không tên khách, không số liệu dự án** |
| 3. **Sửa code / docs / test** của chính repo | bug fix, tài liệu, CI |

**Mọi thứ khác đi ra thư mục dữ liệu** (`POWERBI_PROJECT_DIR`): tài liệu dự án, báo cáo,
model schema đã distill, kit chưa sanitize, log truy vấn, blocklist PII.

Chưa biết thư mục dữ liệu ở đâu → gọi `knowledge_status`; chưa setup thì **DỪNG và hỏi user**,
không được tiện tay ghi vào repo.

> Máy kiểm luật này, không phải mắt: `tests/test_no_leak.py` chặn tên nghiệp vụ trong kit,
> file riêng tư bị track, đường dẫn home thật, và file lạ ở thư mục gốc.

## 1. Repo này là gì

**powerbi-agent** = MCP server (16 tool) + 4 skill + 8 lệnh /powerbi-* giúp AI Agent làm phân tích dữ liệu
**end-to-end trên Power BI**: truy vấn DAX qua chính sách an toàn dữ liệu, khám phá/ghi model,
dựng trang báo cáo theo template kit, quy trình dự án chuẩn hóa, và Knowledge OS (§4b).

Repo sắp theo **4 trụ cột giá trị** — nhãn ▸ dưới đây cho biết mỗi nhánh phục vụ trụ nào:

```
powerbi-agent/
├─ powerbi_agent/                ▸1  package MCP server (Python) — query · policy · TOM · PBIR · distill
├─ mcp_server_powerbi.py         ▸1  entrypoint host đăng ký (shim — ĐỪNG đổi tên/di chuyển)
├─ hosts/{claude,codex,antigravity}/ ▸1  hướng dẫn đăng ký RIÊNG từng host
├─ policy.example.json           ▸1  mẫu blocklist PII → copy thành policy.json
│
├─ plugins/                      ▸2  chuyên môn đã số hóa (cửa vào: plugins/README.md)
│  └─ powerbi-agent/
│     ├─ .claude-plugin/plugin.json   manifest plugin (≠ marketplace.json ở gốc — 2 tầng chuẩn)
│     ├─ skills/                      4 skill dùng chung mọi host (nguồn DUY NHẤT — sửa ở đây)
│     │  ├─ kpim-analysis/            pha NGHIỆP VỤ: khảo sát → tài liệu hóa → kế hoạch
│     │  │  ├─ document-templates/ ▸4    mẫu tài liệu: md + xlsx + theme.json + mindmaps
│     │  │  └─ scripts/                  generator mindmap / xlsx
│     │  ├─ powerbi-pipeline/         pha KỸ THUẬT: 9 khâu Power Query → model → DAX → report (+references/)
│     │  ├─ powerbi-mcp/              hướng dẫn dùng 16 tool + luật an toàn dữ liệu
│     │  └─ powerbi-knowledge/        Knowledge OS: dự án · tri thức 4 trục · timeline
│     ├─ commands/                    8 lệnh /powerbi-* (installer copy sang CẢ 3 host)
│     └─ agents/                      powerbi-knowledge-curator (đóng gói tri thức)
│
├─ report-templates/             ▸3  kit VISUAL trang báo cáo (PBIR) cho apply_template
│  └─ kpim-business-light/           kit mẫu, 12 block đã sanitize
│
├─ .claude-plugin/marketplace.json    DANH MỤC chợ plugin (khai báo repo phân phối plugin nào)
├─ install.ps1 · uninstall.ps1       cài/gỡ in-place: venv + ADOMD/TOM + 3 host + skill/lệnh/agent
├─ scripts/                          tiện ích dev: cli.py (debug DAX không cần MCP) · test_mcp_local.py
├─ tests/ · .github/workflows/       pytest + ruff, CI windows-latest
└─ docs/                             website Pages + docs/plans/ (artifact kế hoạch)
```

**Bản đồ chi tiết từng file + từ điển thuật ngữ:** [`INDEX.md`](INDEX.md).

## 2. Cài đặt (agent thực hiện được toàn bộ)

```powershell
git clone https://github.com/ducnguyen221/powerbi-agent "$env:USERPROFILE\.mcp\powerbi-mcp"
cd "$env:USERPROFILE\.mcp\powerbi-mcp"
powershell -ExecutionPolicy Bypass -File .\install.ps1   # venv + ADOMD + đăng ký 3 host + skill
```

- Sau cài: **restart MCP host** rồi verify (`claude mcp list` → `powerbi-mcp-bridge ✔ Connected`).
- Chỉ cần SKILLS (không MCP): `claude plugin marketplace add ducnguyen221/powerbi-agent`
  → `claude plugin install powerbi-agent@powerbi-agent` (Codex tương tự). Lưu ý: plugin
  KHÔNG dựng venv/MCP — đầy đủ phải chạy `install.ps1`.
- Khuyến nghị cài kèm modeling chính chủ Microsoft:
  `claude mcp add powerbi-modeling -s user -- npx -y "@microsoft/powerbi-modeling-mcp@latest" --start`
- Chi tiết từng host: `hosts/<tên host>/README.md`.

## 3. Cách agent làm việc với Power BI (luật CỨNG)

1. **Thứ tự skill:** dự án mới → `kpim-analysis` (nghiệp vụ) → `powerbi-pipeline` (9 khâu kỹ thuật);
   câu hỏi lẻ → tool trực tiếp theo `powerbi-mcp`.
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
   query + policy + report layer + distill → `powerbi-agent` (repo này).

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
| **Orchestrator / Builder** | Claude Code | Chạy kpim-analysis + powerbi-pipeline, GHI model & report, giữ lock |
| **Reviewer / Second-opinion** | Codex | CHỈ ĐỌC: verify measure (`execute_dax_local` đối chiếu số), soi ERD từ `distill_model_schema`, review DAX/page_spec trước khi Builder ghi |
| **Analyst / Documenter** | Antigravity | Pha kpim-analysis (tài liệu nghiệp vụ, mindmap, kế hoạch), soạn `page_spec` JSON, viết artifact bàn giao |

Mọi vai đều đọc được an toàn đồng thời — tool ĐỌC (list/describe/execute_dax/distill) không cần lock.

### 4.3 Kênh giao tiếp chung giữa các agent
- **Artifact files trong thư mục dự án** (nguồn sự thật, agent nào cũng đọc/ghi nối tiếp):
  `PLAN.md` → `CHANGESET.md` → `VERIFICATION.md` → `HANDOFF.md` (+ tài liệu kpim-analysis).
  Bàn giao giữa 2 agent = ghi rõ trạng thái vào artifact, KHÔNG dựa vào trí nhớ phiên chat.
- **Audit log** `<thư mục dự án>/audit/*.jsonl` = sổ cái chung mọi truy vấn (agent nào, chặn gì)
  — Reviewer dùng làm bằng chứng kiểm tra.
- **Blueprint từ `distill_model_schema`** = "bản đồ model" chung: Builder tạo sau mỗi đợt ghi
  model; các agent khác đọc thay vì tự query lại schema.

### 4.4 Checklist khi nhận bàn giao (agent nào cũng vậy)
1. Đọc `AGENTS.md` này + artifact mới nhất trong thư mục dự án.
2. `list_local_reports` xác nhận trạng thái Desktop; kiểm tra `.powerbi-write-lock`.
3. Làm phần việc của vai mình; cập nhật artifact; xóa lock nếu mình tạo.

## 4b. Knowledge OS — dự án, tri thức, timeline (luồng /powerbi-*)

Tri thức làm việc sống ở **Knowledge Dir do USER chỉ định NGOÀI repo** — con trỏ là MỘT dòng `POWERBI_PROJECT_DIR` trong `.env` (gitignored, mỗi máy tự khai).
`knowledge.config.json` chỉ còn là legacy CHỈ-ĐỌC để migrate bản cũ. Thư mục user chỏn CHÍNH LÀ root
— không đẻ thêm cấp con. Cơ chế đầy đủ: skill `powerbi-knowledge`.

| Lệnh (Claude) / luồng (host khác) | Làm gì |
|---|---|
| `/powerbi-help` | Liệt kê lệnh/skill/16 tool + **bảng định tuyến** "user nói gì thì chạy gì" |
| `/powerbi-setup` | Hỏi user chọn nơi lưu tài liệu dự án (mặc định ~/powerbi-project) → `setup_knowledge` |
| `/powerbi-new <tên>` | `init_project` + đọc kinh nghiệm cũ + chạy kpim-analysis → powerbi-pipeline |
| `/powerbi-scan <path>` | `distill_report_design` — hồ sơ thiết kế trọn báo cáo vào projects/<slug>/design/ |
| `/powerbi-kit <path>` | Chưng cất 1 file .pbip thành **BỘ** kit tái dùng (nhiều trang + theme chung) |
| `/powerbi-done` | Checklist đóng dự án + distill + `log_timeline` + pack |
| `/powerbi-pack` | Agent `powerbi-knowledge-curator` đóng gói bài học 4 trục (dedup, Why/How-to-apply) |
| `/powerbi-recall <từ khóa>` | Tra INDEX/TIMELINE/knowledge — "đã từng làm gì tương tự" |

Luật: (1) gọi `knowledge_status` TRƯỚC mọi quy trình tri thức — chưa setup thì DỪNG hỏi user;
(2) mọi file dự án ghi vào `projects/<slug>/`; (3) Knowledge Dir KHÔNG BAO GIỜ commit;
đường duy nhất ra repo public = user ra lệnh + sanitize + review.

## 5. Quy ước phát triển repo (khi agent sửa CODE repo này)

- Python 3.11+, ruff (line 120), pytest — chạy `pytest tests -m "not integration"` + ruff trước commit.
- `mcp_server_powerbi.py` là shim back-compat: host đăng ký file này — GIỮ bề mặt import.
- Skill là nguồn duy nhất ở `plugins/powerbi-agent/skills/` — installer copy đi các host,
  ĐỪNG sửa bản copy trong `~/.claude/skills/...`.
- `.ps1` phải UTF-8 **có BOM** (PowerShell 5.1 + tiếng Việt); JSON PBIR ghi UTF-8 **không BOM**.
- KHÔNG commit: `.env`, `policy.json`, `.venv/`, kit chứa binding nghiệp vụ thật (sanitize trước),
  schema model khách (distill ghi ra NGOÀI repo), tham chiếu máy cá nhân.
- Docs công khai (README/INSTALL/docs/) phải machine-agnostic — không đường dẫn/tên máy riêng, không tên khách hàng (dùng ví dụ generic như "KPIM Mart").
- **Plugin manifest:** `plugin.json` CHỈ khai `skills` — KHÔNG khai `commands`/`agents` (Claude từ chối field `agents`; auto-discover theo convention `commands/` + `agents/`). marketplace.json dùng chung cho Claude + Codex.
- **Song ngữ:** `README.md` = English (canonical). Sửa README.md thì **mirror sang `README.vi.md` TRONG CÙNG commit**. Các doc khác (AGENTS/ROADMAP/skills) hiện **chỉ có tiếng Việt** — KHÔNG tạo bản `-VN` song song (tránh drift). Website `docs/`: toggle ngôn ngữ mới phủ heading/hero/footer; thân bài và `docs/INSTALL.html` còn VI-only. Đừng hứa EN nhiều hơn thực tế trong docs công khai.

## 6. File nào host nào đọc

| Host | File hướng dẫn | Skills | MCP config |
|---|---|---|---|
| Claude Code | `CLAUDE.md` → trỏ về đây | `~/.claude/skills/` (installer copy) hoặc plugin | `~/.claude.json` |
| Codex CLI | `AGENTS.md` (file này, native) | `~/.codex/skills/` hoặc plugin | `~/.codex/config.toml` |
| Antigravity | `GEMINI.md` → trỏ về đây | `~/.gemini/antigravity/skills/` | `~/.gemini/antigravity/mcp_config.json` |

## 7. GHI VÀO CONFIG CỦA HOST — luật CỨNG (đã trả giá 2026-07-15)

Config của host (`config.toml`, `.claude.json`, `mcp_config.json`) là file **NHIỀU CHỦ CÙNG GHI**:
host tự ghi, `install.ps1` của ta ghi, tool khác cũng ghi. Ghi sai = **host không khởi động nổi**,
và triệu chứng nổ ra ở nơi hoàn toàn khác — rất khó lần ra.

**Sự cố thật:** installer ghi `env = { PYTHONUNBUFFERED = "1" }` dạng *inline*, trong khi Codex tự
ghi dạng *sub-table* `[mcp_servers.<name>.env]`. Hai dạng cùng tồn tại → TOML **duplicate key** →
Codex không parse nổi config → app chết ở `windowsSandbox/setupStart`, hiện màn onboarding
"Finish Windows setup" **và không bao giờ xin UAC** (chết trước khi kịp xin). Người dùng tưởng
dính malware.

1. **Theo convention của HOST, không theo cái mình thấy tiện.** Mở config xem entry do chính host
   sinh ra (vd `[mcp_servers.node_repl.env]` của Codex) rồi bắt chước y hệt. Codex = sub-table.
2. **Replace phải xóa cả block cha LẪN mọi sub-table** `[x.y.*]`. Regex chỉ khớp block cha sẽ để
   sub-table mồ côi — trong TOML, sub-table mồ côi vẫn *ngầm tạo* bảng cha → server không có
   `command` → host lỗi kiểu khác.
3. **Kết thúc match bằng lookahead `^\[` (ngoặc ĐẦU DÒNG).** KHÔNG dùng `[^\[]*`: giá trị
   `args = ["-u", ...]` có `[` giữa dòng sẽ cắt cụt block và làm hỏng file. Bẫy này đã cắn 1 lần
   ngay trong lúc vá.
4. **Validate parse NGAY sau khi ghi** (`python -c "import tomllib; tomllib.load(...)"` / `ConvertFrom-Json`).
   Config hỏng = host chết; không được fail im lặng. Hỏng → báo khôi phục `.bak`.
5. **Test = chạy installer 2 LẦN LIÊN TIẾP trên file hỏng thật.** Phải *heal* được file hỏng và
   *idempotent* (lần 2 giống hệt lần 1). Chạy 1 lần trên file sạch không chứng minh được gì.
6. **Host config chỉ chứa `PYTHONUNBUFFERED=1`.** MỌI tinh chỉnh theo máy (đường dẫn, policy,
   secret) đặt ở `.env` — server tự `load_dotenv()` trong `powerbi_agent/app.py`. Đừng bao giờ
   nhét đường dẫn máy cá nhân hay secret vào config host (nó nằm ngoài repo, không ai review được).
