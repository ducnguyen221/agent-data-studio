---
name: pbi-review
description: "Independent review of SQL, DAX, Power BI semantic models and finished report pages for correctness, performance, security and the KPIM page standard, with severity-tagged findings and tie-out against business definitions. Use when: review SQL or a DAX measure, audit a Power BI model, numbers do not tie out, is this measure right, optimize a slow query, check a built page or its screenshot before handover or publish. Not: writing or fixing measures and model -> pbi-model; designing a page -> pbi-design; building or editing PBIR -> pbi-build; routine data queries -> pbi-analysis."
metadata:
  group: powerbi
  chain_position: 6
  status: stable
  sources:
    - "kpim: OpcOS data-bi skill sql-pbix-reviewer"
    - "kpim: page standard measured 2026-09-16"
---

# pbi-review — review độc lập SQL / DAX / model / trang

## Mục đích
Một cặp mắt **không phải người dựng**: soát đúng số, hiệu năng, bảo mật và chuẩn trang trước khi bàn giao
hoặc publish. Kết quả là danh sách phát hiện có mức độ, không phải lời khen chung chung.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`pbi-build`](../pbi-build/SKILL.md) | Trang đã qua validate/reload/screenshot |
| Sau | [`pbi-publish`](../pbi-publish/SKILL.md) | Không còn Blocker/Major |
| Quay lại | [`pbi-model`](../pbi-model/SKILL.md) · [`pbi-build`](../pbi-build/SKILL.md) | Sửa theo phát hiện |
| Liên quan | [`pbi-analysis`](../pbi-analysis/SKILL.md) | Chạy truy vấn tie-out an toàn |

Agent đọc screenshot độc lập: `agents/pbi-render-reviewer.md` (gốc repo).

## Must / Prefer / Avoid
- **Must** — kiểm **ngữ nghĩa trước hiệu năng**: chỉ số có tính đúng định nghĩa nghiệp vụ, đúng grain không.
- **Must** — tie-out với nguồn tin cậy; lệch số là **Blocker**.
- **Must** — mọi phát hiện có mức (Blocker / Major / Minor / Nit) + đề xuất sửa cụ thể.
- **Must** — truy vấn kiểm chứng đi qua `execute_dax_*` (policy + audit), không dump dữ liệu.
- **Prefer** — số đo (Performance Analyzer, query plan, thời gian truy vấn) thay cho phán đoán hiệu năng.
- **Prefer** — DAX measure + star schema sạch hơn calculated column "thông minh".
- **Prefer** — review trang dựa trên **screenshot thật** + checklist KPIM, không chỉ đọc JSON.
- **Avoid** — tự sửa trong lúc review (review là độc lập; giao lại skill chủ).
- **Avoid** — duyệt khi thiếu input bắt buộc; nói rõ thiếu gì thay vì bịa.

## Đầu vào
Truy vấn / measure / model / trang (thư mục `.Report` + screenshot) · dialect (T-SQL, PostgreSQL, BigQuery,
Snowflake, Spark, DAX) · định nghĩa nghiệp vụ chỉ số (`METRICS_CALCULATION.md`, `DATA_DICTIONARY.md` của dự án
trong Knowledge Dir) · ước lượng khối lượng (số dòng, tần suất refresh, số người xem).
Thiếu tài liệu dự án → vẫn review theo checklist, ghi rõ phần nào không kiểm được.

## Quy trình

| # | Bước | Đọc | Cổng kiểm |
|---|---|---|---|
| 1 | Ngữ nghĩa & tie-out | [review-checklist](references/kpim/review-checklist.md) §A | Số khớp nguồn, hoặc Blocker đã ghi |
| 2 | Đúng đắn SQL / DAX | [review-checklist](references/kpim/review-checklist.md) §B–C | Mỗi lỗi có vị trí + biểu thức thay |
| 3 | Model & hiệu năng | §D · MS `dax-perf-patterns.md`, `dax-perf-decision-guide.md` (skill [`pbi-model`](../pbi-model/SKILL.md)) | Nhận định hiệu năng có số đo |
| 4 | Bảo mật (RLS, PII, quyền) | §E | Không lộ PII thiếu RLS |
| 5 | Trang báo cáo + screenshot | §F · MS `anti-patterns.md`, `pre-flight-checklist.md`, `accessibility.md` (skill [`pbi-design`](../pbi-design/SKILL.md)) · MS `screenshot-review.md` (skill [`pbi-build`](../pbi-build/SKILL.md)) | Lưới/visual/màu/style đúng chuẩn KPIM |
| 6 | Tổng hợp phát hiện theo mức → giao skill chủ sửa | §G + Đầu ra | Không còn Blocker/Major mới cho sang `pbi-publish` |

## Điều kiện DỪNG
Số không khớp nguồn sự thật · model lộ PII không RLS · measure đổi ngữ cảnh âm thầm (`ALL` trên fact không chủ đích)
· trang chưa qua vòng validate/reload/screenshot.

## References

| File | Đọc khi |
|---|---|
| [references/kpim/review-checklist.md](references/kpim/review-checklist.md) | Mọi lần review — checklist A–G, điều kiện dừng, đầu ra |

Reference Microsoft liên quan nằm ở skill chủ (không chép lần hai):
- [`pbi-design`](../pbi-design/SKILL.md) → `references/microsoft/anti-patterns.md`, `pre-flight-checklist.md`, `accessibility.md`
- [`pbi-build`](../pbi-build/SKILL.md) → `references/microsoft/screenshot-review.md`
- [`pbi-model`](../pbi-model/SKILL.md) → `references/microsoft/dax-perf-patterns.md`, `dax-perf-decision-guide.md`

---
*Nguồn: KPIM practice (quy trình review SQL/DAX/model + chuẩn trang KPIM).*
