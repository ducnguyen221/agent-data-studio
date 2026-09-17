# skills/ — 9 skill phẳng, tiền tố = nhóm

- `data-*` — **không cần Power BI** (khảo sát, dữ liệu mẫu).
- `pbi-*` — cần Power BI Desktop / PBIP (hoặc Fabric cho `pbi-publish`).

Loại: **G** gộp KPIM + Microsoft · **K** chỉ KPIM (có thể trỏ reference Microsoft của skill khác) · **M** chỉ Microsoft.
Reference Microsoft hiện là **bản chép nguyên văn** (v0.3.16, khoá sha256) — chưa distill vào SKILL.md.

| Skill | Nhóm | Vị trí chuỗi | Loại | Vai | References |
|---|---|---|---|---|---|
| [`pbi-knowledge`](pbi-knowledge/SKILL.md) | powerbi | 0 — lối vào / lối ra (xuyên suốt) | K | Knowledge OS: mở dự án, recall, scan, kit, đóng dự án, pack tri thức | kpim 1 |
| [`data-discovery`](data-discovery/SKILL.md) | data | 1 — khảo sát | G¹ | Khảo sát, hỏi ngược, PROJECT.md + 6 mindmap + dictionary, kế hoạch Excel | kpim 1 · scripts 2 · mẫu `templates/documents/` |
| [`data-mockup`](data-mockup/SKILL.md) | data | 1′ — nhánh khi chưa có dữ liệu | K | Spec MD+YAML → generator seed cố định → verify → Excel + Data Dictionary | kpim 8 (2 playbook + 6 hồ sơ bộ dữ liệu) · scripts 5 · mẫu `templates/documents/dataset/` |
| [`pbi-model`](pbi-model/SKILL.md) | powerbi | 2 | G | Power Query/M + star schema + TMDL/DAX, ghi measure an toàn | kpim 5 · microsoft 12 |
| [`pbi-analysis`](pbi-analysis/SKILL.md) | powerbi | 3 | K | Truy vấn & khai thác an toàn, tầng T0–T3, policy aggregate/PII/audit | kpim 2 (trỏ MS của `pbi-model`) |
| [`pbi-design`](pbi-design/SKILL.md) | powerbi | 4 | G | Clone-from-approved-page → archetype + chuẩn KPIM → Design Brief | kpim 2 · microsoft 20 (14 + archetypes 5 + `assets/base.json`) |
| [`pbi-build`](pbi-build/SKILL.md) | powerbi | 5 | G | Dựng & hoàn thiện, vòng Edit→Validate→Reload→Screenshot→Review, điều phối trọn gói | kpim 3 · microsoft 23 |
| [`pbi-review`](pbi-review/SKILL.md) | powerbi | 6 | K | Review độc lập SQL/DAX/model/trang | kpim 1 (trỏ MS của `pbi-design`, `pbi-build`, `pbi-model`) |
| [`pbi-publish`](pbi-publish/SKILL.md) | powerbi | 7 — **unverified** | M | Đưa lên Fabric/Service | microsoft 3 (`common/`) |

¹ `data-discovery` là G theo kế hoạch (thêm phần requirements của Microsoft `powerbi-report-planning`); hiện chỉ có nội dung KPIM.

## Chuỗi

`pbi-knowledge` → `data-discovery` → (`data-mockup` khi chưa có dữ liệu) → `pbi-model` → `pbi-analysis` →
`pbi-design` → `pbi-build` → `pbi-review` → `pbi-publish` → `pbi-knowledge` (đóng gói).
Chi tiết từng bước (skill · file đọc · cổng kiểm): [`../workflows/data-to-report.md`](../workflows/data-to-report.md).

## Đổi tên skill Microsoft → studio

| Microsoft (skills-for-fabric v0.3.16) | Studio |
|---|---|
| `semantic-model-authoring` | `pbi-model` |
| `powerbi-report-design` | `pbi-design` |
| `powerbi-report-authoring` | `pbi-build` |
| `powerbi-report-planning` | `data-discovery` (yêu cầu) · `pbi-build` (điều phối) — chưa chép |
| `powerbi-report-management` · `common/` | `pbi-publish` |

## Khuôn một skill
`SKILL.md` ≤ 150 dòng · frontmatter tiếng Anh (`name` = tên thư mục, `description` kiểu router *Use when / Not* ≤ 1024
ký tự, `metadata.group` ∈ {data, powerbi}, `chain_position`, `sources`, `status`) · thân tiếng Việt · reference theo
skill sở hữu: `references/kpim/` (đã khử tên khách) và `references/microsoft/` (nguyên văn + `SOURCE.lock.json`).
Kiểm tự động: `tests/test_skills_lint.py`. Lệnh: [`../commands/`](../commands/) · agent: [`../agents/`](../agents/).
