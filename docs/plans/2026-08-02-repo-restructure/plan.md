# PLAN — Tái cấu trúc & điều hướng repo powerbi-agent

Đi kèm [`spec.md`](./spec.md) · **FINAL v2** (2026-08-02) · Đã áp quyết định Q1–Q4 + 15 finding từ review Codex.
**Chưa thực thi — chờ duyệt một lượt.**

---

## A. Nguyên tắc thiết kế

**A1. Chữa điều hướng trước, đổi tên sau, di chuyển gần như không.**
109 file đều đúng chỗ kỹ thuật. Cảm giác "tạp nham" đến từ *thiếu bản đồ* + *từ ngữ đa nghĩa*,
không phải *sai vị trí*.

**A2. "Non-tech" chỉ áp cho folder người dùng thật sự ghé.**
Họ mở: kho mẫu báo cáo, kho mẫu tài liệu, skill, docs. Họ **không bao giờ** mở `powerbi_agent/`,
`tests/`, `.github/`, `scripts/`. Bắt các folder đó "dễ hiểu với non-tech" là churn thuần.
*(Chính nguyên tắc này loại bỏ đề xuất `scripts/ → dev-tools/` ở bản v1 — xem §F.)*

**A3. Tên folder chứa cùng từ khóa với tool nó phục vụ.**
Tool `apply_template` / `list_templates`, env `POWERBI_TEMPLATES_DIR` ⇒ giữ chữ "template" trong tên,
thêm định ngữ để phân biệt. Đây là lý do `*-templates/` thắng `*-kits/`.

**A4. Trùng tên chữa bằng định ngữ đối xứng, không chữa bằng chú thích.**
`report-templates/` ↔ `document-templates/`: đọc là hiểu, không cần dòng "≠" nào.

---

## B. Kết quả chấm điểm & tên đã chốt

Tiêu chí: dễ hiểu non-tech **30** · hết trùng nghĩa **25** · đúng kỹ thuật & khớp tool **20** ·
khớp cách chủ repo mô tả trụ cột **15** · chi phí đổi tên **10**.

### B1 — Trụ 3 (hiện `templates/`)

| Ứng viên | C1 | C2 | C3 | C4 | C5 | Tổng |
|---|---|---|---|---|---|---|
| `dashboard-templates/` | 29 | 22 | 15 | 15 | 7 | 88 |
| ✅ **`report-templates/`** | 27 | 22 | **19** | 11 | 7 | **86** ← **CHỐT** |
| `dashboard-kits/` | 22 | 25 | 16 | 13 | 7 | 83 |
| `report-kits/` | 20 | 25 | 19 | 10 | 7 | 81 |
| `design-kits/` | 19 | 24 | 12 | 12 | 7 | 74 |
| `templates/` (giữ) | 18 | **5** | 14 | 8 | 10 | 55 |

Chủ repo chọn `report-templates/` — ưu tiên chuẩn thuật ngữ hơn câu chuyện marketing.
Review độc lập củng cố lựa chọn này: repo **đã** dùng sẵn từ vựng "report page", "report layer",
"Visual report kits" (`README.md:266`) ⇒ C3 đúng là điểm mạnh thật, không phải lý thuyết.
Về kỹ thuật đây cũng là tên **chính xác**: mỗi kit = một **report page (PBIR)**, không phải
Dashboard của Power BI Service.

### B2 — Trụ 4 (hiện `skills/kpim-analysis/templates/`)

| Ứng viên | C1 | C2 | C3 | C4 | C5 | Tổng |
|---|---|---|---|---|---|---|
| ✅ **`document-templates/`** | 29 | 24 | 19 | 15 | 8 | **95** ← **CHỐT** |
| `doc-templates/` | 25 | 24 | 18 | 13 | 8 | 88 |
| `deliverables/` | 14 | 22 | 15 | 8 | 8 | 67 |
| `report-docs/` | 16 | 18 | 12 | 7 | 8 | 61 |
| `templates/` (giữ) | 18 | **5** | 14 | 8 | 10 | 55 |

Phương án thay thế được cân nhắc và **loại**: `kpim-analysis/assets/document-templates/`
(theo gợi ý dùng `assets/` của spec skill) — thêm một tầng lồng, churn nhiều hơn giá trị.

### B3 — Tên **không** đổi

| Folder | Lý do |
|---|---|
| `powerbi_agent/` | Python package name = import name. Đổi = phá mọi import, `pyproject.toml`, config host. A2: non-tech không mở |
| `plugins/` | Convention hệ sinh thái plugin; `marketplace.json` trỏ `./plugins/powerbi-agent`. Chữa bằng viết lại `plugins/README.md` |
| `scripts/` | A2 — dev-facing thuần. Xem §F |
| `hosts/`, `tests/`, `.github/`, `docs/`, `docs/template/` | Convention chuẩn / URL công khai |
| `<Knowledge Dir>/templates/` | Ngoài repo, thuộc user, đã tự phân biệt bằng ngữ cảnh |

**4 nghĩa của "template" sau khi xong** — sẽ được ghi rõ trong `INDEX.md §3`:

| Đường dẫn | Là gì | Ai sở hữu |
|---|---|---|
| `report-templates/` | Kit trang báo cáo PBIR đã sanitize, public | Repo |
| `…/kpim-analysis/document-templates/` | Mẫu tài liệu phân tích (md/xlsx/theme/mindmap) | Repo (ship theo skill) |
| `docs/template/` | Route website gallery | Repo (URL cố định) |
| `<Knowledge Dir>/templates/` | Kit riêng CHƯA sanitize | **User**, ngoài repo |

---

## C. Cấu trúc đích

```
powerbi-agent/
├─ README.md · README.vi.md      ← cửa vào: làm gì · cài sao · tính năng chính  (rút còn ≤150 dòng)
├─ INDEX.md                      ← 🆕 bản đồ 2 trục (EN-only, theo Q3)
├─ AGENTS.md · CLAUDE.md · GEMINI.md · ROADMAP.md · LICENSE
├─ install.ps1 · uninstall.ps1 · pack.ps1 · mcp_server_powerbi.py · pyproject.toml …
│
│  ── TRỤ 1: MCP Server ────────────────────────────────
├─ powerbi_agent/                 (giữ)
├─ hosts/                         (giữ)
├─ policy.example.json            (giữ)
│
│  ── TRỤ 2: Chuyên môn số hóa ──────────────────────────
├─ plugins/
│  ├─ README.md                   ← ✏️ viết lại thành "cửa vào trụ 2"
│  └─ powerbi-agent/
│     ├─ .claude-plugin/plugin.json   ← 🔢 bump version
│     ├─ skills/                  (giữ nguyên vị trí — L1)
│     │  ├─ kpim-analysis/
│     │  │  ├─ document-templates/    ← 🔤 ĐỔI TÊN (trụ 4)
│     │  │  └─ scripts/               (giữ)
│     │  ├─ pbi-pipeline/ · powerbi-mcp/ · pbi-knowledge/
│     ├─ commands/ · agents/
│
│  ── TRỤ 3: Mẫu thiết kế báo cáo ───────────────────────
├─ report-templates/              ← 🔤 ĐỔI TÊN từ templates/
│  └─ kpim-business-light/
│
├─ scripts/ · tests/ · .github/ · docs/     (giữ)
└─ docs/plans/2026-08-02-repo-restructure/  ← kế hoạch này
```

**Tổng: 2 lần đổi tên · 0 lần di chuyển folder · 1 file tài liệu mới · 3 file viết lại · 1 bump version.**

---

## D. Bảng tác động chi tiết (đã sửa theo review)

### D1 — `templates/` → `report-templates/`

**PHẢI SỬA:**

| File | Dòng | Ghi chú |
|---|---|---|
| `powerbi_agent/tools_template.py` | **20** | `os.path.join(_REPO_ROOT, "templates")` — **dòng code duy nhất ràng buộc runtime** |
| `powerbi_agent/tools_template.py` | 45, 199 | docstring |
| `scripts/build_template_gallery.py` | 3, **19**, 41, 72 | `SRC`, message, URL GitHub |
| `templates/README.md` | 1, 7, 10 + **xóa 13** | đi theo folder khi `git mv` |
| `README.md` | 153, **266** | xóa chú thích "≠" ở 266 |
| `README.vi.md` | 151, **259** | xóa chú thích "≠" |
| `AGENTS.md` | **25** | xóa chú thích "≠" |
| `ROADMAP.md` | 82, 83 | |
| `ROADMAP.md` | **146 — CHỈ nửa đầu câu** | ⚠️ *phát hiện bởi review*: `…sanitize → \`templates/\` repo, còn full project + kit thô → Knowledge Dir`. Nửa đầu = repo (đổi), nửa sau = Knowledge Dir (giữ) |
| `.env.example` | **28 (KHÔNG đụng 29)** | dòng 28 nói "templates/ trong repo"; dòng 29 là ví dụ `POWERBI_TEMPLATES_DIR` ngoài repo |
| `docs/INSTALL.html` | 164 | |
| `docs/template/index.html` | 90, 138 | giữ nguyên **route** `docs/template/` |
| `plugins/…/skills/powerbi-mcp/SKILL.md` | 38 | |
| `plugins/…/skills/pbi-pipeline/references/powerbi-knowledge-map.md` | 10 | |
| `docs/template/templates.json` | 30 | **sinh lại bằng script**, không sửa tay |

**TUYỆT ĐỐI KHÔNG ĐỔI** (đều là `<Knowledge Dir>/templates/` — folder của user, ngoài repo):

`powerbi_agent/knowledge.py:59,76,77` · `powerbi_agent/tools_knowledge.py:52,72,73` ·
`plugins/…/skills/pbi-knowledge/SKILL.md:25,39` · `commands/pbi-done.md:12` · `commands/pbi-scan.md:11` ·
`commands/pbi-setup.md:10` · `ROADMAP.md:111,126` · `ROADMAP.md:146` *(nửa sau)* ·
`README.md:105` · `README.vi.md:103` · `.env.example:29` ·
**`docs/feature/index.html:149`** ⚠️ *sửa từ bản v1*: dòng 143 ngay trên nó ghi
"📁 Knowledge Dir (của BẠN, ngoài repo)" ⇒ cây thư mục 145–150 là Knowledge Dir, **không phải repo**.

> **Luật thi hành:** phân loại **theo từng occurrence, không theo file**. Cấm `sed`/replace-all toàn repo.

### D2 — `skills/kpim-analysis/templates/` → `document-templates/`

Không code Python nào chạm → rủi ro runtime bằng 0. `templates/` không phải tên dành riêng
trong spec skill Claude/Codex (L9 — đã giải quyết, không còn là giả định).

| File | Dòng |
|---|---|
| `plugins/…/skills/kpim-analysis/SKILL.md` | 34 (`templates/mindmaps/`), 51 (tiêu đề mục) |
| `install.ps1` | 288 — **chỉ comment** (copy là whole-folder). Sửa phải **giữ BOM** (L8) |
| `hosts/antigravity/README.md` | 32 |
| `docs/INSTALL.html` | 99, 172 |
| `README.md` | 198, 253 |
| `README.vi.md` | 192, 246 |
| `AGENTS.md` | 16 |

Đối chiếu độc lập (Claude + Codex): `kit.json`, `blueprint.md`, 12 file block, nội dung `.xlsx`,
`tests/`, `.github/`, `pack.ps1`, `uninstall.ps1`, `agents/` — **không** chứa đường dẫn nào cần sửa.

### D3 — Bump version (bắt buộc, thiếu ở bản v1)

`plugin.json:3` và `marketplace.json:14` đang cùng ghim `0.3.0`. Version được ghim là điều kiện để
người dùng marketplace **nhận được** layout skill mới; không bump = họ giữ bản cũ dù repo đã đổi.
→ **cả hai lên `0.5.0`** (v3 mở rộng phạm vi: đổi tên lệnh + skill mới + installer mới ⇒ minor bump lớn hơn).

### D5 — `pbi-*` → `powerbi-*` (yêu cầu bổ sung #1)

**Phạm vi: 158 occurrence / 40 file.** Phân loại bắt buộc — có 2 nhóm chữ "pbi" **KHÔNG được đụng**:

| Đổi | Không đổi (và vì sao) |
|---|---|
| skill `pbi-pipeline/` → `powerbi-pipeline/` | `.pbip`, `.pbix` — **đuôi file của Microsoft** |
| skill `pbi-knowledge/` → `powerbi-knowledge/` | `pbir` / `powerbi_agent/pbir.py` — **PBIR là tên format chính thức** (Power BI Enhanced Report) |
| 6 lệnh `pbi-*.md` → `powerbi-*.md` | keyword `"pbir"` trong `plugin.json:13` |
| agent `pbi-knowledge-curator.md` → `powerbi-knowledge-curator.md` | |
| `.pbi-write-lock` → `.powerbi-write-lock` (AGENTS.md §4) | |
| `install.ps1:204` `.pbi-tmp` · `:212` `pbi-merge-mcp.py` (tên tạm nội bộ) | |
| skill `powerbi-mcp/`, `kpim-analysis/` — **đã đúng**, không đụng | |

⚠️ **Breaking change có chủ đích:** người đang dùng `/pbi-new` sẽ phải gõ `/powerbi-new`.
Chủ repo yêu cầu trực tiếp; repo chưa 1.0 nên chấp nhận. **Bắt buộc kèm bước dọn:**
`install.ps1:314` hiện chỉ xóa `pbi-*.md` ở thư mục đích — phải xóa **cả `pbi-*.md` lẫn
`powerbi-*.md`**, nếu không người nâng cấp sẽ có **12 lệnh** (6 cũ mồ côi + 6 mới).
`uninstall.ps1` cũng phải gỡ được cả hai họ tên.

---

## L. Yêu cầu bổ sung v3 — khảo sát hiện trạng & thiết kế

### L1 (#2) — Cây thư mục trực quan trong tài liệu và website

**Hiện trạng:** repo **chưa** có sơ đồ cây nào mô tả chính nó. `docs/feature/index.html:143–151`
đã có sẵn pattern cây bằng `<div class="mono">` — nhưng cây đó vẽ **Knowledge Dir**, không phải repo.

**Thiết kế:** một cây duy nhất, canonical, xuất hiện ở 4 nơi bằng cùng nội dung:
`INDEX.md §2` (nguồn gốc) · `README.md §2` (bản rút gọn 4 trụ) · `AGENTS.md §1` (bản cho agent) ·
`docs/index.html` (khối `.mono` mới, tái dùng đúng CSS đang có — **không** thêm asset ngoài).
Mỗi nhánh gắn nhãn trụ cột để nhìn phát ra ngay 4 trụ.

### L2 (#3a) — Skill: quét 1 project Power BI → **bộ** template kit

**Khoảng trống được xác nhận.** Hiện có `distill_template(report_path, page, out_dir)` —
**1 trang → 1 kit**. `/pbi-scan:11` chỉ *gợi ý* người dùng tự chạy. Không có đường nào từ
**1 file .pbip → bộ kit tái dùng** như `kpim-business-light`.

**Thiết kế — lệnh mới `/powerbi-kit <path .pbip>`:**
1. `distill_report_design` → biết có bao nhiêu trang, trang nào đặc trưng
2. Với **mỗi** trang đáng tái dùng → `distill_template(..., sanitize=True)`
3. Gom thành **một kho kit** có `kit.json` chung + `blueprint.md` mô tả hệ thiết kế + preview
4. Mặc định ghi vào Knowledge Dir; muốn vào repo public → hỏi duyệt + kiểm sanitize
Không cần tool MCP mới — chỉ điều phối 3 tool sẵn có. ⇒ đây là **command + bổ sung skill**,
không phải code Python mới.

### L3 (#3b) — Lệnh liệt kê năng lực cho agent

**Khoảng trống được xác nhận.** Không có gì để agent tự hỏi "tôi làm được gì với repo này".

**Thiết kế — lệnh mới `/powerbi-help`:** in ra 3 bảng (lệnh · skill · 16 tool) kèm cột
"khi nào dùng", và **quy tắc định tuyến** để agent tự chọn quy trình đúng thay vì hỏi lại người dùng.
Đây cũng là câu trả lời cho yêu cầu #6.

### L4 (#4) — Chuẩn hóa cài plugin cho Codex & Antigravity

**Hiện trạng:**
- Claude: có `.claude-plugin/marketplace.json` + `plugin.json`, **nhưng `install.ps1` KHÔNG dùng
  đường plugin** — nó copy tay skill vào `~/.claude/skills` và lệnh vào `~/.claude/commands`.
  ⇒ tồn tại **2 đường phân phối song song**, dễ nạp trùng.
- Codex: `hosts/codex/README.md:26–39` đã ghi `codex plugin marketplace add` — nhưng **thủ công**,
  installer không làm, và README tự cảnh báo "đừng chạy cả hai".
- Antigravity: **không có** trình quản lý plugin (`hosts/antigravity/README.md:5–7`) ⇒ chỉ có đường skill-dir.

**Thiết kế:** installer thêm tham số `-Mode plugin|copy|auto` (mặc định `auto`):
`auto` → host nào có CLI plugin (`claude`, `codex`) thì **dùng đường plugin**; host nào không
(Antigravity) thì copy skill-dir. Chống nạp trùng: chọn plugin thì **gỡ** bản copy tay, và ngược lại.

### L5 (#5) — Tách bước cài plugin/agent thành step riêng

**Hiện trạng:** installer 3 bước (venv → deps → đăng ký host). Lệnh `/pbi-*` **chỉ được copy cho
Claude** (`install.ps1:307–318`) ⇒ Codex và Antigravity **không có lệnh nào**.

**Thiết kế:** thêm **Step 4 — "Cài plugin & agent"** tách bạch, chạy được độc lập
(`install.ps1 -Only plugin`), và **cấp lệnh cho cả 3 host** (Codex: `~/.codex/prompts/`;
Antigravity: nhúng bảng lệnh vào skill `powerbi-knowledge` vì host không có cơ chế lệnh riêng).

### L6 (#6) — Cài ở máy khác là agent làm việc được ngay

**Hiện trạng:** sau `install.ps1` agent có tool + skill, nhưng **không có gì bảo nó bắt đầu từ đâu**;
Knowledge Dir chưa setup; Codex/Antigravity thiếu lệnh.

**Thiết kế — "bootstrap" khép kín:**
1. Step 4 cấp lệnh cho cả 3 host (L5)
2. `/powerbi-help` là điểm vào chuẩn (L3)
3. Cuối installer in **3 dòng việc-cần-làm-tiếp** thay vì chỉ "HOÀN TẤT"
4. Thêm **smoke test end-to-end**: gọi thử `knowledge_status` + `list_templates` qua chính venv,
   báo rõ "MCP sẵn sàng / chưa setup Knowledge Dir"

### D4 — `.gitignore:18`

`skill/*/scripts/out/` trỏ layout `skill/` đã bỏ. **Không phải bug**: dòng 17 `out/` đã ignore mọi
thư mục tên `out` ở mọi độ sâu (`git check-ignore` phân giải về dòng 17). ⇒ **xóa dòng 18** như dọn
chữ chết, không thay bằng đường dẫn mới.

---

## E. LỘ TRÌNH TỔNG QUAN — từ đầu đến cuối, duyệt một lượt

Hai commit, thực thi liền mạch. Cột "Cổng" đánh dấu chỗ dừng bắt buộc.

| # | Bước | Chạm vào | Cổng |
|---|---|---|---|
| **COMMIT 1 — Đổi tên + hồi quy** | | | |
| S1 | `git mv templates report-templates` | 17 file kit | |
| S2 | Sửa 2 file code theo D1 (`tools_template.py`, `build_template_gallery.py`) | 2 file | |
| S3 | Sửa 12 file docs/HTML theo D1 — **theo occurrence**, đối chiếu bảng loại trừ | 12 file | |
| S4 | `git mv plugins/powerbi-agent/skills/kpim-analysis/templates …/document-templates` | 20 file mẫu | |
| S5 | Sửa 7 file theo D2 (giữ BOM `install.ps1`) | 7 file | |
| S6 | Bump `plugin.json` + `marketplace.json` → `0.5.0` (D3) | 2 file | |
| S7 | Xóa `.gitignore:18` (D4) | 1 dòng | |
| S8 | **Thêm test hồi quy** (xem §G) — kit discovery, gallery URL, installer copy | `tests/test_unit.py`, `tests/installer/installer.tests.ps1` | |
| S9 | Mở rộng ruff trong `ci.yml:21` phủ cả `scripts/` (hiện chỉ lint `scripts/cli.py`) | 1 dòng | |
| S10 | Chạy toàn bộ nghiệm thu V1–V7 (§G) | — | |
| S11 | **Trình diff + kết quả test → chờ duyệt → commit 1** | — | 🚦 **Gate 2** |
| **COMMIT 2 — Lớp điều hướng** | | | |
| S12 | Viết `INDEX.md` (EN-only) theo khung §H | 1 file mới | |
| S13 | Rút gọn `README.md` ≤150 dòng theo khung §I + mirror `README.vi.md` **cùng commit** (L7) | 2 file | |
| S14 | Viết lại `plugins/README.md` thành cửa vào trụ 2 | 1 file | |
| S15 | Cập nhật bản đồ repo ở `AGENTS.md §1` khớp tên mới | 1 file | |
| S16 | Kiểm nghiệm thu #2, #3 (§6 spec): ≤2 click từ trụ cột tới file | — | |
| S17 | **Trình diff → chờ duyệt → commit 2** | — | 🚦 **Gate 2** |
| **COMMIT 3 — `pbi-*` → `powerbi-*`** (yêu cầu #1, xem D5) | | | |
| S18 | `git mv` 2 skill · 6 lệnh · 1 agent sang tên `powerbi-*` | 9 đường dẫn | |
| S19 | Sửa 158 occurrence theo D5 — **loại trừ** `.pbip`/`.pbix`/`pbir` | ~40 file | |
| S20 | `install.ps1` dọn **cả** `pbi-*.md` lẫn `powerbi-*.md` khi mirror lệnh; `uninstall.ps1` gỡ cả hai họ | 2 file | |
| S21 | Chạy V1–V7 + kiểm không còn `\bpbi[-_]` ngoài danh sách loại trừ | — | 🚦 **Gate 2** |
| **COMMIT 4 — Năng lực mới** (yêu cầu #3, #4, #5, #6) | | | |
| S22 | Lệnh mới `/powerbi-kit` — 1 file .pbip → **bộ** kit (L2) | 1 file mới | |
| S23 | Lệnh mới `/powerbi-help` — bảng lệnh/skill/tool + quy tắc định tuyến (L3) | 1 file mới | |
| S24 | `install.ps1` **Step 4 "Cài plugin & agent"** + `-Mode plugin\|copy\|auto` + `-Only` (L4, L5) | `install.ps1` | |
| S25 | Cấp lệnh cho **cả 3 host**: Codex `~/.codex/prompts/`, Antigravity nhúng vào skill (L5) | `install.ps1` | |
| S26 | Smoke test end-to-end + 3 dòng "việc cần làm tiếp" cuối installer (L6) | `install.ps1` | |
| S27 | Cập nhật `hosts/{claude,codex,antigravity}/README.md` theo đường cài mới | 3 file | |
| S28 | Test installer mới trên fake profile (cả 3 mode) | `tests/installer/` | |
| S29 | Chạy toàn bộ nghiệm thu | — | 🚦 **Gate 2** |
| **COMMIT 5 — Cây thư mục trực quan** (yêu cầu #2, L1) | | | |
| S30 | Cây canonical vào `INDEX.md §2` · `README.md` (rút gọn) · `AGENTS.md §1` | 4 file | |
| S31 | Khối `.mono` cây repo vào `docs/index.html` (tái dùng CSS sẵn có, không thêm asset) | 1 file | |
| S32 | Kiểm hiển thị + 🚦 duyệt | — | 🚦 **Gate 2** |
| **SAU ĐÓ (task riêng)** | | | |
| S33 | Sửa rò rỉ `pack.ps1` — đóng gói theo allowlist `git ls-files` | `pack.ps1` | 🚦 quyết riêng |

**Vì sao commit 1 trước commit 2:** không phải để "khỏi sửa docs 2 lần" — commit 1 *có* chạm README
(sửa chuỗi đường dẫn), commit 2 viết lại chúng. Lý do thật: **commit 1 là thay đổi có thể verify bằng
máy** (test/CI), commit 2 thuần văn bản. Tách ra để nếu hồi quy hỏng thì revert đúng một commit
có phạm vi rõ, không kéo theo bản viết lại tài liệu.

**Rollback:** `git revert` commit 2 → rồi commit 1. Chỉ cần cài lại (`install.ps1`) nếu đã thật sự
chạy installer lên máy thật ở bước UAT tùy chọn; nghiệm thu bắt buộc chạy trên fake profile nên
không đụng trạng thái máy.

---

## F. Những thứ bản v1 đề xuất và nay **BỎ**

| Bỏ | Lý do |
|---|---|
| `scripts/` → `dev-tools/` | Mâu thuẫn nguyên tắc A2 của chính kế hoạch. Thêm nữa bảng impact v1 còn sót `mcp_server_powerbi.py:4,5,15`. Lợi ích duy nhất là xóa dòng "≠" trong một README chỉ dev đọc |
| Đổi tên `<Knowledge Dir>/templates/` | Folder của user, ngoài repo. `_template_dirs()` (`tools_template.py:21`) nhận **bất kỳ chuỗi nào** trong `POWERBI_TEMPLATES_DIR` — không đảm bảo là đường tuyệt đối, nên lập luận "người dùng cũ không gãy" ở v1 **không có cơ sở**. Logic "giữ tên cũ nếu đã có" tạo 2 schema vĩnh viễn |
| `INDEX.vi.md` | Q3 — chỉ tiếng Anh. Kéo theo: **không** sửa `AGENTS.md:133` |
| Thay `.gitignore:18` bằng đường dẫn mới | Dòng 17 đã phủ. Chỉ xóa |
| Nghiệm thu "grep ≠ phải rỗng" | Sai từ gốc: `AGENTS.md:22`, `plugins/README.md:6` dùng "≠" cho `marketplace.json` vs `plugin.json`; `dax-best-practices.md:17` dùng "≠ 0" toán học. Thay bằng assertion có mục tiêu (§G/V6) |
| Chạy `install.ps1` 2 lần lên máy thật làm bước nghiệm thu bắt buộc | `install.ps1:296` **xóa** skill đã cài rồi copy đè và ghi lại config host. Đã có harness fake-profile ở `tests/installer/installer.tests.ps1:21` — dùng cái đó. Cài lên máy thật hạ xuống mức **UAT tùy chọn, có duyệt riêng** |

---

## G. Nghiệm thu (đã sửa)

| # | Kiểm tra | Kỳ vọng |
|---|---|---|
| V1 | `pytest tests -m "not integration"` | xanh |
| V2 | `ruff check` (đã mở rộng phủ `scripts/`) | xanh |
| V3 | `.venv\Scripts\python.exe scripts\build_template_gallery.py` | `docs/template/templates.json` diff **chỉ** đổi `readme_url` |
| V4 | Test mới: `_template_dirs()` trỏ `report-templates/`; `list_templates()` trả về `kpim-business-light`; tồn tại `report-templates/kpim-business-light/kit.json` | xanh |
| V5 | Test installer trên **fake profile**: skill cài ra có `kpim-analysis/document-templates/` đủ file; **không** còn `kpim-analysis/templates/` | xanh |
| V6 | Assertion có mục tiêu: repo không còn chuỗi `templates/kpim-business-light` và `kpim-analysis/templates`; đã xóa 4 chú thích "≠" về folder (`templates/README.md:13`, `README.md:266`, `README.vi.md:259`, `AGENTS.md:25`) — **giữ** "≠" ở `AGENTS.md:22`, `plugins/README.md:6`, `dax-best-practices.md:17` | đạt |
| V7 | `plugin.json` · `marketplace.json` · `pyproject.toml` · `powerbi_agent/__init__.py` cùng `0.5.0`; plugin validate không lỗi | đạt |
| UAT | *(tùy chọn, duyệt riêng)* chạy `install.ps1` lên máy thật rồi kiểm `~/.claude/skills/kpim-analysis/document-templates/` | đạt |

**Vì sao cần V4/V5 mới:** `tests/test_unit.py:189` hiện chỉ kiểm một tập con tool đã đăng ký,
**không** có test nào cho `list_templates` / `_template_dirs` / kit discovery / gallery.
`tests/installer/installer.tests.ps1:138` chỉ **đếm 4 thư mục skill**, không kiểm nội dung.
⇒ Không có 2 test này thì CI vẫn xanh trong khi cả hai tính năng vừa đổi tên đều đã hỏng.

---

## H. Khung `INDEX.md` (EN-only, ~180 dòng)

```
§0  Start here                 3 dòng định tuyến: người dùng mới → README · agent → AGENTS.md · tra cứu → đây

§1  AXIS A — The four pillars  [trụ cột → tính năng → tài liệu]
    Bảng tổng: Pillar | What you get | Key folder/file | Commands & tools | Read more
    §1.1 Pillar 1 — MCP Server: 5 file quan trọng nhất · luồng cài → chạy → hỏi
    §1.2 Pillar 2 — Digitized expertise: 4 skill · 6 lệnh · 1 agent · Knowledge OS
    §1.3 Pillar 3 — Report design kits: kit là gì · apply_template · distill_template · sanitize
    §1.4 Pillar 4 — Document templates: 8 mẫu md · xlsx 6 sheet · theme.json · 5 mindmap · generator

§2  AXIS B — Folder map A→Z    [folder → là gì + file chính]
    Bảng: Folder | What it is (1 câu) | Most important files (tối đa 3) | Pillar | Who opens it

§3  Glossary                   template · kit · skill · command · tool · Knowledge Dir · host · policy
                               + **bảng 4 nghĩa của "template"** (§B3 ở trên)
                               + giải thích 4 cái tên: repo powerbi-agent · package powerbi_agent
                                 · MCP server powerbi-mcp-bridge · plugin powerbi-agent

§4  End-to-end flow            1 sơ đồ: dữ liệu vào → /pbi-new → kpim-analysis → pbi-pipeline
                               → apply_template → /pbi-done → kit + tài liệu ra

§5  What is NOT in this repo   Knowledge Dir · .env · policy.json · .venv — vì sao clone về không thấy
```

§1 trả lời *"tôi muốn làm X thì đi đâu"*; §2 trả lời *"tôi thấy folder Y, nó là gì"* — hai chiều ngược
nhau của cùng một bản đồ, không trùng nội dung. §3 là thứ trực tiếp chữa gốc rễ, vì gốc rễ là **từ ngữ**.

---

## I. Khung `README.md` (≤150 dòng)

| § | Nội dung | ~Dòng | Nguồn |
|---|---|---|---|
| 1 | Một câu repo là gì + banner "Windows only" | 8 | giữ |
| 2 | **Bạn nhận được gì — 4 trụ cột**, mỗi trụ 2 dòng + link vào `INDEX.md` | 20 | **mới** |
| 3 | Cài đặt: lệnh 1 dòng + 3 bước | 25 | giữ |
| 4 | **10 phút đầu tiên** — 3 câu lệnh gõ thử ngay | 15 | **mới** |
| 5 | Tính năng chính: bảng 6 lệnh `/pbi-*` + 16 tool **gom thành 5 nhóm** | 30 | rút gọn |
| 6 | An toàn dữ liệu — 3 gạch đầu dòng | 12 | rút gọn |
| 7 | Đi tiếp: `INDEX.md` · `AGENTS.md` · `ROADMAP.md` · website · license | 12 | mới |

**Chuyển sang `INDEX.md`** (không xóa): bảng 16 tool đầy đủ · mục "Repo INDEX — key folders & files" ·
chi tiết pipeline 9 bước · chi tiết quy trình KPIM · mục cùng tồn tại với `powerbi-modeling-mcp` ·
chi tiết cơ chế Knowledge Dir. Giữ bản 5-nhóm-tool trong README để không mất từ khóa khám phá.

---

## J. Rủi ro & giảm thiểu

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| Replace mù chữ "templates" phá logic Knowledge Dir | **Cao nếu ẩu** | Bảng loại trừ D1 liệt kê đích danh 14 vị trí; phân loại **theo occurrence**; cấm sed toàn repo; `ROADMAP.md:146` là câu **trộn cả hai nghĩa** — sửa nửa đầu, giữ nửa sau |
| CI xanh trong khi tính năng đã hỏng | **Cao trước khi có S8** | V4 + V5 là test hồi quy bắt buộc, không phải tùy chọn |
| Người dùng marketplace không nhận layout mới | Trung bình | S6 bump `0.4.0` ở **cả hai** manifest |
| Nghiệm thu làm hỏng trạng thái máy thật | Trung bình | Dùng harness fake-profile; cài máy thật hạ xuống UAT tùy chọn |
| Sửa `install.ps1` mất BOM | Trung bình | L8; kiểm byte đầu `EF BB BF` sau khi sửa |
| Link ngoài trỏ `…/tree/main/templates/` gãy | Thấp | GitHub không redirect thư mục. Chấp nhận; README mới + `templates.json` sinh lại đều trỏ đường đúng |
| README rút gọn mất từ khóa khám phá | Thấp | Không xóa — **chuyển** sang `INDEX.md`, giữ bản 5 nhóm tool ở README |

---

## K. Xác nhận cần trước khi thực thi

Kế hoạch đã khép kín: Q1–Q4 đã chốt, 15 finding review đã xử lý, không còn quyết định mở.
Duyệt là chạy thẳng S1 → S17, dừng ở hai Gate 2 để trình diff.

**Một việc cần chủ repo quyết riêng:** S18 — rò rỉ `pack.ps1` (`spec.md §8`).
Làm ngay sau, hay để sau nữa?
