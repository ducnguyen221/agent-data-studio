# BÁO CÁO TRIỂN KHAI — tái cấu trúc powerbi-agent v0.5.0

Nhánh `restructure/v3` · 5 commit · 2026-08-02/03 · **chưa merge vào `main`**

> Chạy tự trị theo uỷ quyền: mỗi phase xong → spawn agent review độc lập → sửa finding → sang phase kế.

---

## 1. Kết quả kiểm thử (số liệu thật, chạy lần cuối sau commit `61c317a`)

| Kiểm thử | Trước | Sau |
|---|---|---|
| `pytest -m "not integration"` | 38 passed | **44 passed** |
| `ruff check` | chỉ phủ `scripts/cli.py` | **phủ cả `scripts/`** — clean |
| Harness installer (fake profile) | 13 ca | **22 ca, 22 True** |
| BOM UTF-8 trên 3 file `.ps1` | — | `EF BB BF` giữ nguyên |
| JSON parse (`plugin.json`, `marketplace.json`, `templates.json`) | — | OK |
| Link tương đối trong INDEX/README/AGENTS/plugins | — | 0 link gãy |

**Cách chạy lại toàn bộ:**

```powershell
cd C:\Users\DucNguyen\.mcp\powerbi-mcp
git checkout restructure/v3
.venv\Scripts\python.exe -m pytest tests -m "not integration" -q
.venv\Scripts\python.exe -m ruff check powerbi_agent tests mcp_server_powerbi.py scripts
powershell -ExecutionPolicy Bypass -File tests\installer\installer.tests.ps1 -PythonExe .venv\Scripts\python.exe
```

Harness chạy trên `USERPROFILE` giả (`tests/installer/fakehome`) — **không đụng cấu hình thật** của máy.

---

## 2. Năm commit

| Commit | Nội dung |
|---|---|
| `7eed750` | `templates/` → `report-templates/` · `skills/kpim-analysis/templates/` → `document-templates/` · bump 0.5.0 · 4 test hồi quy |
| `0f936a4` | `pbi-` → `powerbi-` toàn bộ bề mặt người dùng: 2 skill, 6 lệnh, 1 agent, 223 occurrence / 33 file |
| `096991b` | 2 lệnh mới (`/powerbi-kit`, `/powerbi-help`) · installer bước 4 · lệnh cho **cả 3 host** · sổ ghi thay wildcard |
| `47be6cd` | `INDEX.md` 2 trục · README 293→168 dòng (EN+VI) · `plugins/README.md` thành cửa vào trụ 2 · cây thư mục trên website |
| `61c317a` | Sửa toàn bộ finding của 3 vòng review agent |

---

## 3. Sáu yêu cầu bổ sung

| # | Yêu cầu | Trạng thái |
|---|---|---|
| 1 | `pbi` → `powerbi` | ✅ Trừ `.pbip`/`.pbix`/`pbir` (tên format Microsoft) và `find_active_pbi_ports` (bề mặt back-compat của shim, tài liệu hoá là ổn định) |
| 2 | Cây thư mục trực quan | ✅ `INDEX.md §2` · `AGENTS.md §1` (gắn nhãn ▸ trụ cột) · section mới trên `docs/index.html` dùng CSS sẵn có |
| 3a | Quét .pbip → **bộ** kit | ✅ Lệnh `/powerbi-kit` — điều phối 3 tool sẵn có, không thêm code Python |
| 3b | Lệnh liệt kê năng lực | ✅ Lệnh `/powerbi-help` — có bảng định tuyến "user nói gì thì chạy gì" |
| 4 | Plugin chuẩn cho Codex/Antigravity | ✅ Codex → `~/.codex/prompts/`; Antigravity không có slash-command nên lệnh nằm trong skill `powerbi-knowledge` |
| 5 | Tách bước cài plugin | ✅ Bước 4 riêng + `install.ps1 -Only plugin` |
| 6 | Máy khác dùng được ngay | ✅ Lệnh cho cả 3 host + smoke test kiểm kit/Knowledge Dir + in 3 dòng "việc cần làm tiếp" theo trạng thái thật |

---

## 4. Những gì review agent bắt được (đều là lỗi thật, đã sửa)

Đây là phần đáng đọc nhất — **9 lỗi thật**, trong đó 3 lỗi tự tôi tạo ra ở chính lượt sửa trước:

| # | Lỗi | Hậu quả nếu không bắt |
|---|---|---|
| 0 | **CRITICAL — skill zombie khi nâng cấp.** `Install-Skill` mirror theo skill *có trong nguồn*, nên `pbi-pipeline`/`pbi-knowledge` nằm lại ở host | Người nâng cấp có **6 skill**; bản cũ `pbi-knowledge/SKILL.md` chứa nguyên bảng định tuyến bảo agent chạy `/pbi-setup`, `/pbi-new`… — đúng những lệnh installer vừa xoá. Lỗi chạm **mọi người dùng hiện có** |
| 0b | Harness gọi `install.ps1` trực tiếp mà **không set `USERPROFILE` giả** — chỉ chạy đúng nhờ `Run-Install` đã mutate env tiến trình | Đổi thứ tự ca là test ghi thẳng vào `~/.claude` **thật** của dev |
| 1 | `foreach ($root in ...)` **ghi đè `$Root`** trong `uninstall.ps1` (PowerShell không phân biệt hoa/thường) | Gỡ xong Codex vẫn còn 8 lệnh sống nhăn. Bug tiềm ẩn **có sẵn từ trước**, code mới mới làm lộ |
| 2 | Gỡ không đối xứng với bước 4 | Bỏ quên `~/.codex/prompts` và `~/.claude/agents` |
| 3 | Sổ ghi được tin tuyệt đối | Một dòng `powerbi-*.md` trong sổ ghi → xoá luôn lệnh **riêng của user**; `..\..\x.md` xoá file **ngoài** thư mục; ký tự lạ → giết installer giữa chừng |
| 4 | Bước 4 chạy vô điều kiện | `-SkipHosts` vẫn ghi vào 3 host, trái tài liệu của chính nó |
| 5 | `$Root` nội suy vào literal Python | Đường dẫn có dấu `'` → SyntaxError → installer khuyên **SAI** ("chưa setup Knowledge Dir") cho người đã setup |
| 6 | Antigravity mất bộ lệnh im lặng | Host khó phát hiện nhất vì không có slash-command |
| 7 | 2 test không isolate env | Đỏ trên **chính cấu hình mà repo khuyến nghị**, chỉ xanh trên CI vì CI không có env var |
| 8 | `register_project_in_index` chỉ khớp placeholder mới | Knowledge Dir dựng bởi bản <0.5.0 mãi bảo chạy `/pbi-new` — lệnh installer vừa xoá |
| 9 | README hứa bảng 16 tool ở INDEX nhưng INDEX không có | Nội dung bị **mất**, không phải chuyển chỗ |

Ngoài ra: `ROADMAP.md` bị replace hàng loạt viết lại văn xuôi **lịch sử** thành tên mới, tạo ra
`/powerbi-project` và `/powerbi-timeline` không tồn tại — đã hoàn nguyên.

---

## 5. Còn tồn đọng — cần anh quyết

| # | Việc | Mức |
|---|---|---|
| A | **`pack.ps1` rò rỉ dữ liệu**: `:31` chỉ loại `.venv/.git/__pycache__`, `:36` copy **mọi** entry ở root ⇒ zip phân phối mang theo `policy.json` (tên cột PII thật), `knowledge.config.json` (đường dẫn Brain cá nhân), `docs/internal/`. Chữa: đóng gói theo allowlist `git ls-files`. | **Cao** |
| B | `~/.codex/prompts/` là nơi Codex đọc custom prompt — tôi **chưa kiểm chứng trực tiếp** trên máy này, mới chỉ theo tài liệu. Cần chạy thử Codex thật rồi gõ `/powerbi-help`. | Trung bình |
| C | `plugins/README.md`, `report-templates/README.md`, `hosts/*/README.md` chỉ có tiếng Việt nhưng là đích đến từ README tiếng Anh. | Thấp |
| D | Cây thư mục trên `docs/index.html` chỉ có tiếng Việt (heading/lead thì song ngữ). | Thấp |
| E | Nhánh chưa merge vào `main`, chưa push. | — |

---

## 6. Breaking change cần biết

**`/pbi-*` → `/powerbi-*`.** Người đang dùng phải đổi thói quen gõ lệnh.
Installer tự dọn 6 lệnh cũ (có test `C-legacy-cmd-cleanup` chứng minh còn 0 lệnh cũ + đúng 8 lệnh mới),
`INDEX.md` của Knowledge Dir cũ cũng được migrate placeholder tự động.

---

## 7. Cách anh kiểm tra lại

```powershell
cd C:\Users\DucNguyen\.mcp\powerbi-mcp
git log --oneline main..restructure/v3        # 5 commit
git diff --stat main...restructure/v3          # ~90 file
git diff main...restructure/v3 -- install.ps1  # phần rủi ro nhất
```

Đọc theo thứ tự: `README.md` (bản dễ hiểu) → `INDEX.md` (bản đồ) → `plan.md` (vì sao làm vậy)
→ `REPORT.md` (file này).

Muốn thử thật: `install.ps1 -Only plugin` rồi restart host, gõ `/powerbi-help`.
Muốn quay lại: `git checkout main` — nhánh `restructure/v3` không đụng `main`.
