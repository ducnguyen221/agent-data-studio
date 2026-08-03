# UAT Report — powerbi-agent v0.2.0

> Ngày: 2026-07-12 · Môi trường: Windows 11, Power BI Desktop (Store 2.155), SSMS 21 ADOMD/TOM,
> Python 3.12 venv. Dữ liệu UAT: một báo cáo Power BI nội bộ (.pbip PBIR nhiều trang, model
> nhiều bảng và measure) + template kit đã kiểm chứng. **Mọi số liệu nhận dạng model và tên
> bảng/cột/measure đã được gỡ khỏi báo cáo này** — chỉ giữ lại kết quả kỹ thuật.
>
> Nguyên tắc UAT: KHÔNG sửa file gốc — apply chạy trên BẢN COPY; phiên Desktop chỉ chạy tool ĐỌC, đóng không lưu.

## Tổng kết

| Hạng mục | Kết quả |
|---|---|
| Ca UAT | **17 PASS / 0 FAIL** (sau sửa lỗi; 4 defect phát hiện & sửa trong UAT) |
| Unit tests | 32 pass (policy, PBIR, sanitize, back-compat, distill path) |
| Lint | ruff sạch |
| Live health | `claude mcp list` ✔ Connected (shim không đổi) |

## UAT-01 — distill_template (trang thật → kit, sanitize)

| Ca | Kết quả |
|---|---|
| Distill trang mẫu 30 visual → kit 12 block + blueprint + _page + kit.json | ✅ PASS |
| Re-scan kit: KHÔNG còn tên bảng/cột/measure trong blocks + kit.json + blueprint | ✅ PASS (sau defect #1, xem defect #5) |

**Defect #1 (phát hiện & sửa):** sanitize v1 chỉ thay projections trong `queryState` — field refs thật còn
sót trong `visualContainerObjects` (conditional color), `objects`, `sortDefinition` và text của textbox.
Fix: `deep_sanitize` walk toàn cây JSON + gom map tên trên toàn trang + thay textbox text = TEMPLATE_TEXT
+ bỏ `filterConfig` mức visual. Unit test cover (`test_deep_sanitize_covers_style_refs`).

## UAT-02 — apply_template (kit → trang mới, trên BẢN COPY .Report)

Spec: 5 visual (shape nền + cardVisual 3 measure + combo chart Category/Y/Y2 + pivotTable + slicer),
bind field thật của model (1 measure từ bảng công thức, 1 cột phân nhóm từ bảng fact).

| Kiểm tra | Kết quả |
|---|---|
| pages.json đăng ký GUID trang mới | ✅ |
| page.json schema 2.1.0, canvas 1280×720, nền #DFE7F6 kế thừa kit | ✅ |
| Không mang theo filter/interaction của trang nguồn | ✅ |
| Đủ 5 visual, JSON hợp lệ, UTF-8 KHÔNG BOM | ✅ |
| cardVisual rebind đúng 3 measure thật, `visualContainerObjects` (style) giữ nguyên | ✅ |
| KHÔNG sót placeholder TEMPLATE_* trong query các visual đã bind | ✅ (sau defect #2) |

**Defect #2 (phát hiện & sửa):** `sortDefinition` trong `query` của block còn trỏ field cũ sau rebind
→ rebind giờ bỏ `sortDefinition` (Desktop dùng sort mặc định; sort tùy chỉnh đặt lại trong Desktop).

## UAT-03 — Policy an toàn dữ liệu (unit, 10 ca)

| Ca | Kết quả |
|---|---|
| Mặc định BẬT: `EVALUATE 'Sales'` / `EVALUATE Bảng` / `ALL()` bị chặn kèm hint viết lại | ✅ |
| SUMMARIZECOLUMNS / TOPN / ROW / FILTER-wrapped được phép | ✅ |
| PII blocklist (policy.json): cột cấm bị chặn, cột khác đi qua, audit ghi `blocked_pii` | ✅ |
| Opt-out `POWERBI_AGGREGATE_ONLY=0` | ✅ |
| Dimension row cap 200 (kết quả có cột chữ), thuần số không siết | ✅ |
| Audit không bao giờ làm hỏng truy vấn (đường ghi hỏng vẫn chạy) | ✅ |

## UAT-05 — Live Power BI Desktop (file .pbix thật, chỉ ĐỌC)

| Ca | Kết quả |
|---|---|
| a. `list_local_reports` → port 56600 + catalog GUID | ✅ |
| b. `list_tables` → đủ số bảng của model, lọc bảng hệ thống | ✅ |
| c. `describe_table` bảng công thức → cột + toàn bộ measure kèm expression | ✅ (sau defect #3) |
| d. `execute_dax_local` SUMMARIZECOLUMNS → 3 dòng dữ liệu tổng hợp thật | ✅ |
| e. `execute_dax_local` `EVALUATE '<bảng fact>'` (dump thô) → **BỊ CHẶN** bởi policy (mặc định) | ✅ |
| f. `distill_model_schema` → blueprint 10 bảng/174 measure + Mermaid ERD, ghi đúng POWERBI_DISTILL_DIR | ✅ (sau defect #3) |
| g. Audit JSONL: verdict `allowed` (rows=3) + `blocked_raw_dump` đúng thứ tự | ✅ |

**Defect #3 (phát hiện & sửa):** DMV `TMSCHEMA_COLUMNS` không có cột `[DataType]` — tên đúng là
`[ExplicitDataType]`. Lỗi tồn tại từ bản single-file trước khi hợp nhất → chứng tỏ tool distill
bản cũ **chưa từng chạy live thành công**. Đã sửa cả describe_table + distill.

**Defect #4 (phát hiện & sửa):** map enum kiểu dữ liệu sai (bằng chứng: RowNumber — luôn Int64 —
hiện "Decimal/Currency"). Sửa theo TOM DataType enum thật (String=2, Int64=6, Decimal=10…);
lọc thêm cột nội bộ `RowNumber-*`.

## Phạm vi chưa UAT (ghi nhận trung thực)

- `execute_dax_service` (cloud): cần dataset publish + service principal — smoke test đường auth
  qua unit (thiếu env → lỗi rõ ràng); chưa chạy live trong đợt này.
- `add_measure_local` / `add_relationship_local` (TOM write): KHÔNG chạy trên file thật
  trong đợt UAT (tránh dirty model). Cơ chế TOM đã được chứng minh trước đó trên chính dashboard
  này (đợt tạo measures hàng loạt + 1 trang báo cáo 15 visual).
- Mở lại `.pbip` UAT copy trong Desktop để nghiệm thu MẮT trang mới — bước bắt buộc của quy trình,
  do người dùng thực hiện (agent không nhìn thấy trang render).

## Defect #5 (phát hiện 2026-08-03, sau UAT)

`blueprint.md` của kit `kpim-business-light` còn sót **2 tên measure thật** (`TEMPLATE_TABLE.<tên measure>`) trong khi các file `blocks/*.json` đã sạch. Nguyên nhân: blueprint là artifact sinh ra **trước** khi `deep_sanitize` được vá ở defect #1, và không được sinh lại sau đó.

Đã xử lý: gỡ 2 tên đó, và thêm **test quét rò rỉ toàn repo** (`tests/test_no_leak.py`) để lỗi cùng loại không thể lọt lần nữa — kiểm bằng máy thay vì bằng mắt.
