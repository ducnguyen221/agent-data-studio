# powerbi-agent — Kế hoạch triển khai (Implementation Roadmap)

> **powerbi-agent** = MCP server + bộ skill + template kit giúp AI Agent (Claude Code · Codex ·
> Antigravity · mọi MCP client) làm việc **trực tiếp và đúng chuẩn** với Power BI — từ Power Query
> đến trang báo cáo hoàn thiện — với chính sách an toàn dữ liệu enforce ở tầng server.
>
> Trạng thái: v0 (bridge read-only, đang chạy production) → v1.0 theo roadmap dưới đây.

---

## 1. Định vị & ranh giới

**Không xây lại modeling.** [`microsoft/powerbi-modeling-mcp`](https://github.com/microsoft/powerbi-modeling-mcp)
(official, MIT) đã phủ: tạo/sửa table, column, measure, relationship, bulk ops + transaction, TMDL/PBIP,
DAX validate. powerbi-agent **delegate** phần đó và tập trung vào 4 vùng Microsoft chưa/không làm:

| Vùng | Vì sao là khoảng trống |
|---|---|
| **Report layer (PBIR)** — tạo/sửa trang báo cáo, visual | modeling-mcp tuyên bố rõ *không* sửa report pages |
| **Data-safety policy** — chặn dump dữ liệu thô vào context LLM | Chưa server nào enforce; các server hiện tại trả raw rows |
| **Template kit** — dựng báo cáo từ mẫu chuẩn hóa, distill mẫu thành kit | Layout agent tự sinh luôn xấu; clone-and-rebind đã chứng minh |
| **Pipeline 9 khâu** — quy trình chuẩn end-to-end cho agent + artifact | Các server chỉ đưa tool rời, không đưa quy trình |

**Kiến trúc 4 tầng:**

```
T4  WORKFLOW & KNOWLEDGE   skill powerbi-pipeline · template kits · distill · artifacts
T3  POLICY                 aggregate-only · PII blocklist · audit log · row caps
T2  MCP TOOLS (repo này)   query · schema discovery · PBIR read/write · template · TOM fallback
T1  DELEGATE               microsoft/powerbi-modeling-mcp (modeling, bulk, TMDL, DAX validate)
```

## 2. Khả năng tích hợp (integration matrix)

| Đích kết nối | Giao thức | Trạng thái |
|---|---|---|
| **Power BI Desktop** (file .pbix/.pbip đang mở) | ADOMD.NET → `localhost:<port>` (tự dò port msmdsrv) | ✅ v0 |
| **Power BI Service / Fabric** (dataset đã publish) | REST `executeQueries` + MSAL service principal | ✅ v0 |
| **PBIP project files** (file đóng, git-versioned) | Đọc/ghi trực tiếp TMDL (model) + PBIR JSON (report) | 🔜 v1 |
| **MCP host** | stdio — Claude Code, Codex CLI, Antigravity, VS Code, Cursor… | ✅ v0 (installer 3 host, mở rộng được) |
| **microsoft/powerbi-modeling-mcp** | Chạy song song, phân vai qua skill (không trùng tool name) | 🔜 M0 |

Yêu cầu hệ: Windows (Power BI Desktop chỉ có trên Windows) · Python 3.11+ · ADOMD.NET
(SSMS 18–22 / standalone / GAC — tự dò, override `ADOMD_LIB_DIR`).

## 3. Feature spec theo milestone

### v0 — hiện có (production)

| Tool | Mô tả |
|---|---|
| `list_local_reports()` | Liệt kê báo cáo Desktop đang mở (port + model ID) |
| `execute_dax_local(port, model_id, dax, max_rows)` | Chạy DAX lên Desktop |
| `execute_dax_service(dataset_id, dax, max_rows)` | Chạy DAX lên Service |

Kèm: installer in-place 3 host (`install.ps1`), CLI debug (`scripts/cli.py`), skill mô tả cách dùng.

### M0 — Nền sản phẩm

- [x] Tách `mcp_server_powerbi.py` → package `powerbi_agent/` (util · adomd · discovery · tools_query · policy · app); `mcp_server_powerbi.py` giữ làm shim back-compat — host config KHÔNG phải đổi.
- [x] `pyproject.toml` v0.1.0 + entry `powerbi-agent`; `requirements.txt` giữ cho installer.
- [x] Test suite pytest (19 unit: util/adomd-probe/policy/back-compat) + GitHub Actions (windows runner, ruff + pytest, marker `integration` skip trên CI).
- [x] Policy khung sẵn từ M0: `POWERBI_AGGREGATE_ONLY=1` bật chặn dump thô (mặc định tắt — M1 đảo mặc định + PII blocklist + audit).
- [x] Cài `microsoft/powerbi-modeling-mcp` song song (✔ Connected); doc phân vai trong README + SKILL.md.
- [x] Hợp nhất nhánh đóng góp single-file vào package: TOM loader + `add_measure_local` + `add_relationship_local` (`tools_tom.py`, fallback — bulk/TMDL vẫn delegate modeling-mcp) + `distill_model_schema` (`tools_distill.py`, đổi tên từ `distill_report_model`; đích ghi mặc định `~/.powerbi-agent/distilled/` NGOÀI repo, cấu hình qua `POWERBI_DISTILL_DIR`).

### M1 — Policy + Discovery (an toàn dữ liệu) — ✅ XONG 2026-07-12

- [x] `aggregate_only` mặc định BẬT (opt-out `POWERBI_AGGREGATE_ONLY=0`); chặn kèm hint viết lại.
- [x] PII blocklist qua `policy.json` (gitignored; mẫu `policy.example.json`; env `POWERBI_POLICY_FILE`). Heuristic bảo thủ: chặn khi cột xuất hiện bất kỳ đâu trong DAX (tài liệu hóa rõ).
- [x] Row cap dimension 200 (`POWERBI_DIMENSION_ROW_CAP`); thuần measure không siết.
- [x] Audit log JSONL `~/.powerbi-agent/audit/YYYY-MM.jsonl` (ts·tool·verdict·rows·dax) — lỗi ghi audit không phá truy vấn.
- [x] `list_tables` / `describe_table` (DMV; đã sửa bug `[ExplicitDataType]` + lọc `RowNumber-*` + TOM enum map — phát hiện qua UAT live).
- [x] Token cache MSAL (app singleton).

### M2 — Report layer (PBIR) + Template kit — ✅ XONG 2026-07-12

- [x] `pbir.py`: resolve .pbip/.Report/definition · find_page (GUID/displayName) · projection/rebind (bỏ `sortDefinition` cũ) · set_title giữ style · GUID 20-hex · UTF-8 no-BOM · deep_sanitize (walk toàn cây: queryState + objects + conditional color + textbox text + filterConfig).
- [x] `apply_template(report_path, kit_dir, page_spec)` — clone-and-rebind thành code; đăng ký pages.json; bỏ parentGroupName/expansionStates; cảnh báo file-đóng trong output.
- [x] `distill_template(report_path, page, out_dir, sanitize)` — trang → kit (1 block giàu style nhất/loại + blueprint 100% visual + _page.json + kit.json).
- [x] Kit format v1 = `kit.json` + `blueprint.md` + `blocks/*.json` + `_page.json` (JSON thay YAML — zero dep; preview.png để sau).
- [x] Kit đầu tiên `report-templates/kpim-business-light` — distill từ trang chuẩn thật 30 visual, 12 loại block (card refLabel + conditional color, combo chart, pivot, slicer, map…), ĐÃ sanitize.
- [x] `list_templates()` (repo report-templates/ + env `POWERBI_TEMPLATES_DIR`).
- Dời sau: `read_report_structure` (blueprint của distill đã cover nhu cầu đọc), validate field-tồn-tại-trong-model trước khi bind (làm được qua describe_table thủ công trong pipeline).

### M3 — Distill + Pipeline skill — ✅ XONG 2026-07-12

- [x] `distill_model_schema` (đích ghi `POWERBI_DISTILL_DIR`/`~/.powerbi-agent/distilled/`) — live PASS trên model 10 bảng/174 measure + Mermaid ERD.
- [x] Skill **`powerbi-pipeline`** 9 khâu (điều phối 2 MCP, cổng kiểm mỗi khâu, 4 artifact, bookmark-để-tay, hỏi PII đầu dự án) — cài cả 3 host, install.ps1 copy mọi skill.
- [x] Vòng tri thức: distill_model_schema (model→blueprint) + distill_template (trang đẹp→kit) + bài học→memory.

**UAT (docs/UAT-REPORT.md):** 17 ca PASS trên dashboard thật (.pbip 7 trang + model 174 measure + Desktop live) — 4 defect tìm thấy & sửa trong UAT (deep-sanitize leak, sortDefinition leak, DMV ExplicitDataType, TOM enum map).

### M4 — Sản phẩm hóa

- [ ] Docs song ngữ (README EN + VI) · demo GIF/video · ví dụ end-to-end (CSV → model → 2 trang báo cáo theo kit).
- [ ] Versioned release + CHANGELOG.
- [ ] (Cân nhắc) Đăng MCP registry/marketplace cộng đồng.

### M5 — Knowledge OS: dự án, tri thức, timeline — ✅ CORE XONG 2026-07-14 (v0.3.0)

> Mục tiêu: repo public sạch, nhưng mọi tri thức làm việc (dự án, kinh nghiệm, template riêng)
> chảy về **Knowledge Dir do USER CHỈ ĐỊNH ngoài repo** (vd folder Brain có sẵn của user).
> Agent học dần theo từng dự án; người dùng git clone không nhận tri thức của ai khác.

#### 5.0 Kiến trúc 3 tầng lưu trữ (nền của mọi thứ dưới)

| Tầng | Nằm đâu | Chứa gì | Git? |
|---|---|---|---|
| **Repo public** | repo này | code, skills, commands, agents, kit ĐÃ sanitize | ✅ |
| **Knowledge Dir** | user chỉ định NGOÀI repo (env `POWERBI_KNOWLEDGE_DIR` / `knowledge.config.json` gitignored) | projects/ · knowledge/ · templates riêng · TIMELINE | ❌ (thuộc user; user tự quyết sync riêng) |
| **Brain user** | = Knowledge Dir trỏ thẳng vào folder Brain có sẵn | như trên, hòa vào hệ tri thức cá nhân | ❌ |

Cấu trúc Knowledge Dir chuẩn (tool tự dựng):

```
<KNOWLEDGE_DIR>/powerbi-agent/
  INDEX.md                    # mục lục toàn bộ (agent đọc đầu tiên)
  TIMELINE.md                 # dòng thời gian: dự án + bài học theo ngày (quy trình #4)
  projects/<slug>/            # MỖI dự án 1 folder (quy trình #2)
    PROJECT.md + bộ tài liệu KPIM (từ skill kpim-analysis)
    design/                   #   distill model + report design (quy trình #1)
    artifacts/                #   PLAN/CHANGESET/VERIFICATION/HANDOFF
  knowledge/                  # tri thức ĐÃ ĐÓNG GÓI (quy trình #3)
    tech-stack/ · industry/ · business-domain/ · powerbi/
  templates/                  # kit riêng CHƯA sanitize (POWERBI_TEMPLATES_DIR trỏ vào đây)
```

- **Setup bắt buộc lần đầu**: command `/powerbi-setup` hỏi user chỉ định folder (ưu tiên Brain/knowledge
  base có sẵn; không có thì đề xuất tạo `~/powerbi-knowledge/`) → ghi `knowledge.config.json`
  (gitignored) → dựng skeleton + INDEX. Chưa setup mà chạy quy trình tri thức → agent DỪNG và hỏi.
- Mọi file agent tạo trong dự án mặc định lưu vào `projects/<slug>/` — user muốn chuyển đi đâu
  tùy ý, nhưng bản tri thức .md luôn giữ lại đây.

#### 5.1 Quy trình #1 — Quét trọn Power BI project → bộ thiết kế chuẩn

Hiện có: `distill_model_schema` (model) + `distill_template` (1 trang → kit). **Thiếu: quét CẢ báo cáo.**

- [x] Tool MCP `distill_report_design(report_path, out_dir)` — quét toàn bộ `*.Report`:
  mọi trang (blueprint per-page: visual/vị trí/binding), **theme** (StaticResources/SharedResources
  + RegisteredResources → trích `theme.json` dùng lại được), `report.json` settings,
  tổng hợp `DESIGN.md` (palette/font/canvas/pattern nhận diện được) + `REPORT_CATALOG.md`
  (Report → Page → Visual). Kết hợp distill_model_schema = trọn bộ hồ sơ thiết kế 1 project.
- [x] Command `/powerbi-scan <path .pbip>` — chạy trọn: scan design + model → ghi `projects/<slug>/design/`.
- [x] Tư vấn lưu template ĐỒNG BỘ: KHÔNG commit cả .pbip vào repo (nặng + lộ nghiệp vụ);
  chuẩn = kit per-page sanitize → `report-templates/` repo, còn **full project + kit thô → Knowledge Dir**.

#### 5.2 Quy trình #2 — Project Management (`projects/`)

- [x] Command `/powerbi-new` (đổi tên gọn từ /powerbi-project init <tên>` → dựng `projects/<slug>/` theo skeleton + đăng ký INDEX/TIMELINE.
- [x] Skill `powerbi-knowledge` (mới): luật "làm việc qua MCP này = có project folder"; mọi tài liệu
  KPIM (kpim-analysis) ghi thẳng vào đây; cuối dự án bắt buộc HANDOFF + distill.
- [x] `/powerbi-done` (đổi tên gọn từ /powerbi-project close) → checklist đóng dự án: đủ 4 artifact? design/ đã distill? bài học đã
  rút? → đề xuất trang đẹp nào đáng `distill_template` thành kit (sanitize → repo, thô → riêng).
- [x] Reference chéo: PROJECT.md ↔ kit đã sinh ↔ knowledge/ entry ↔ TIMELINE — bằng relative link.

#### 5.3 Quy trình #3 — Đóng gói tri thức theo 4 trục

- [x] Agent **`powerbi-knowledge-curator`** (định nghĩa trong `plugins/powerbi-agent/agents/`):
  đọc projects/ mới hoàn thành hoặc theo chu kỳ → rút bài học TÁI DÙNG → phân loại vào
  `knowledge/{tech-stack, industry, business-domain, powerbi}/` — dedup (cập nhật file cũ
  thay vì tạo trùng), mỗi bài học có **Why + How to apply**, cập nhật INDEX.
- [x] Command `/powerbi-pack` (gọn từ /powerbi-knowledge pack [project]` — kích hoạt curator cho 1 dự án vừa xong hoặc quét tổng.
- [x] Khi làm dự án MỚI: kpim-analysis pha Research đọc `knowledge/` khớp domain trước khi hỏi user
  (agent "có kinh nghiệm" thật).

#### 5.4 Quy trình #4 — Timeline tự học

- [x] `TIMELINE.md` chuẩn append-only: `| ngày | dự án | việc | bài học/kit sinh ra | link |`.
- [ ] Curator tự append khi `pack`; `/powerbi-timeline [từ khóa]` để agent tra "đã từng làm gì tương tự".

#### 5.5 Phân vai agent trong Knowledge OS

| Agent | Vai | Nguồn |
|---|---|---|
| `powerbi-knowledge-curator` | Đóng gói tri thức, dedup, timeline, INDEX | agents/ mới |
| Builder (agent chính) | Làm dự án, ghi vào projects/, gọi distill | skills hiện có |
| Reviewer (Codex) | Đọc knowledge/ + audit khi review | AGENTS.md §4 |

#### 5.6 Riêng tư vs public (luật cứng)

- `knowledge.config.json` + toàn bộ Knowledge Dir: **KHÔNG BAO GIỜ commit** (gitignore + luật trong
  AGENTS.md §5). Máy của tác giả trỏ vào Brain riêng — cấu hình đó là của máy, không phải của repo.
- Đường DUY NHẤT đưa tri thức riêng → repo public: user chủ động ra lệnh + `sanitize=True` + review.

**Ước lượng:** 5.0+5.2 (nền + project) 1 buổi · 5.1 (scan design) 1 buổi · 5.3+5.4 (curator + timeline) 1 buổi · UAT trên dự án thật 1 buổi.

## 4. Definition of Done (v1.0)

1 dự án mẫu chạy trọn 9 khâu: từ CSV nguồn → `.pbip` có model + measures + 2 trang báo cáo
theo kit + tooltip/drill-through — agent tự chạy qua skill `powerbi-pipeline`, **không một dòng dữ liệu
thô nào vào context** (audit log chứng minh), đủ 4 artifact bàn giao.

## 5. Rủi ro đã nhận diện

| Rủi ro | Đối sách |
|---|---|
| modeling-mcp đang Public Preview, API đổi trước GA | Pin version; theo dõi release notes |
| 2 MCP server cùng ghi 1 model | Quy ước trong skill: không interleave write; modeling ops nhường MS server |
| PBIR schema đổi theo Desktop release | Kit lưu schema version; validate khi apply |
| Policy DAX guard là best-effort parse | Tuyên bố rõ giới hạn; RLS mới là bảo mật cứng |
| Bookmark clone dễ vỡ báo cáo | Không tự động hóa bookmark — hướng dẫn thao tác tay |
