---
name: pbi-model
description: "Bring data into Power BI and model it: Power Query / M connections and transforms, star schema and date table, relationships, DAX measures and calculated columns in TMDL, naming and performance, and writing measures safely (TMDL when the .pbip is closed, TOM only to try formulas). Use when: connect a source, fix types or query folding, design fact/dimension tables, add or fix a measure, relationship or date table, tune DAX. Not: business discovery or project documents -> data-discovery; querying or exploring data under the safety policy -> pbi-analysis; report pages and visuals -> pbi-design / pbi-build; reviewing an existing model -> pbi-review; deploying to Fabric -> pbi-publish."
metadata:
  group: powerbi
  chain_position: 2
  status: stable
  sources:
    - "kpim: pbi-project-delivery references (dax, m, sql, gotchas) + pipeline steps 1-4"
    - "kpim: measure-writing practice (TOM vs TMDL), measured 2026-09-16"
    - "microsoft: plugins/powerbi-authoring/skills/semantic-model-authoring/references/*@v0.3.16 (verbatim, not yet distilled)"
---

# pbi-model — đưa dữ liệu vào & mô hình hoá

## Mục đích
Biến nguồn dữ liệu thành semantic model đúng và nhanh: Power Query/M → star schema + date table →
measure DAX có tên, định dạng, thư mục. Ghi measure sao cho **không mất khi user lưu file**.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`data-discovery`](../data-discovery/SKILL.md) | Đã có PROJECT.md, DATA_DICTIONARY, METRICS_CALCULATION |
| Trước (nhánh) | [`data-mockup`](../data-mockup/SKILL.md) | Chưa có dữ liệu thật → dùng bộ mẫu |
| Sau | [`pbi-analysis`](../pbi-analysis/SKILL.md) | Model chốt → truy vấn/khai thác, soát số |
| Liên quan | [`pbi-review`](../pbi-review/SKILL.md) · [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | Review model · ghi bài học |

Chuỗi đầy đủ: `workflows/data-to-report.md` ở gốc repo.

## Must / Prefer / Avoid
- **Must** — PBIP-first: đầu dự án bảo user *Save As* `.pbip` (bật preview PBIP + PBIR) để model là TMDL text.
- **Must** — thứ tự: kết nối → transform → model → measure. Không viết measure khi model chưa chốt.
- **Must** — mỗi bước một cổng kiểm **chạy được** (bảng dưới); không có bằng chứng = chưa xong.
- **Must** — lưu measure bền bằng **TMDL khi file đóng**; TOM không làm file dirty → Ctrl+S không cứu.
- **Must** — đường dẫn nguồn là **M parameter**; credential không bao giờ nằm trong M.
- **Prefer** — fold tối đa về nguồn; biến đổi nặng ở Power Query/SQL, tính theo ngữ cảnh báo cáo ở DAX.
- **Prefer** — measure gom một bảng riêng (vd `Công Thức`), `displayFolder` theo trang báo cáo, `formatString` tường minh.
- **Prefer** — `VAR`, `DIVIDE`, time-intelligence lọc qua date table.
- **Avoid** — auto date/time; quan hệ hai chiều không lý do; `SUM` cột tồn/số dư qua nhiều kỳ.
- **Avoid** — interleave ghi từ hai MCP (bridge studio + Modeling MCP Microsoft) lên cùng model.
- **Avoid** — TMSL `createOrReplace` mức từng measure qua ADOMD (Desktop từ chối).

## Quy trình (mỗi bước có cổng)

| # | Bước | Đọc | Cổng kiểm |
|---|---|---|---|
| 1 | **Kết nối** — sửa partition M trong TMDL hoặc hướng dẫn *Get Data* khi nguồn cần credential UI | [m-best-practices](references/kpim/m-best-practices.md) · [sql-best-practices](references/kpim/sql-best-practices.md) · MS [connection-binding](references/microsoft/connection-binding.md) | Refresh thành công; `EVALUATE ROW("n", COUNTROWS('Bảng'))` khớp kỳ vọng |
| 2 | **Transform M** — staging tách query cuối, tên bước rõ nghĩa, ép kiểu tường minh ở cuối (nhất là Date) | [m-best-practices](references/kpim/m-best-practices.md) · [gotchas](references/kpim/gotchas.md) | `describe_table` — Date là DateTime, số là Int64/Decimal |
| 3 | **Mô hình hoá** — star schema, date table phủ toàn bộ phạm vi, Many→One từ fact vào dim | MS [modeling-guidelines](references/microsoft/modeling-guidelines.md) · [naming-conventions](references/microsoft/naming-conventions.md) | `distill_model_schema` → ERD đúng hình sao, không quan hệ thừa/ngược |
| 4 | **Measure & cột tính** — thử bằng TOM, lưu bằng TMDL | [tom-tmdl-write](references/kpim/tom-tmdl-write.md) · [dax-best-practices](references/kpim/dax-best-practices.md) · MS [dax-guidelines](references/microsoft/dax-guidelines.md) · [tmdl-guidelines](references/microsoft/tmdl-guidelines.md) | Mỗi measure `EVALUATE ROW("kq", [M])` + đối chiếu 1 con số biết trước; mở lại file vẫn còn measure |
| 5 | **Hiệu năng** (khi chậm) | MS [dax-perf-decision-guide](references/microsoft/dax-perf-decision-guide.md) · [dax-perf-patterns](references/microsoft/dax-perf-patterns.md) | Thời gian truy vấn trước/sau có số đo |
| 6 | **Bàn giao sang truy vấn** — cập nhật `DATA_DICTIONARY` / `METRICS_CALCULATION` của dự án | — | Tài liệu dự án khớp model; chuyển [`pbi-analysis`](../pbi-analysis/SKILL.md) |

Ghi TMDL: tab-indent, CRLF, UTF-8 không BOM, `lineageTag` UUID mới, chèn trước `partition`.

## References

### KPIM — `references/kpim/`
| File | Đọc khi |
|---|---|
| [m-best-practices.md](references/kpim/m-best-practices.md) | Bước 1–2: query folding, `Value.NativeQuery`, connector, kiểu dữ liệu, incremental |
| [sql-best-practices.md](references/kpim/sql-best-practices.md) | Nguồn SQL/DW: SARGable, index, pre-aggregate, staging, SCD |
| [dax-best-practices.md](references/kpim/dax-best-practices.md) | Viết/tối ưu DAX: VAR, DIVIDE, date table, calculation group, time-intel |
| [gotchas.md](references/kpim/gotchas.md) | Trước mỗi bước — bẫy đã trả giá (serial date, blank member, STOCK) |
| [tom-tmdl-write.md](references/kpim/tom-tmdl-write.md) | Bước 4 — ghi measure/cột tính/quan hệ; TOM vs TMDL |

### Microsoft (nguyên văn, v0.3.16) — `references/microsoft/`
| File | Đọc khi |
|---|---|
| [modeling-guidelines.md](references/microsoft/modeling-guidelines.md) | Thiết kế bảng, quan hệ, star schema |
| [naming-conventions.md](references/microsoft/naming-conventions.md) | Đặt tên bảng/cột/measure |
| [dax-guidelines.md](references/microsoft/dax-guidelines.md) | Quy ước viết DAX |
| [dax-perf-decision-guide.md](references/microsoft/dax-perf-decision-guide.md) · [dax-perf-patterns.md](references/microsoft/dax-perf-patterns.md) | Chẩn đoán và sửa DAX chậm |
| [tmdl-guidelines.md](references/microsoft/tmdl-guidelines.md) · [pbip.md](references/microsoft/pbip.md) | Sửa TMDL, cấu trúc thư mục PBIP |
| [metadata-discovery.md](references/microsoft/metadata-discovery.md) | Đọc metadata model (INFO.*, DMV) |
| [connection-binding.md](references/microsoft/connection-binding.md) | Nguồn/kết nối, binding khi deploy |
| [direct-lake-guidelines.md](references/microsoft/direct-lake-guidelines.md) | Model Direct Lake trên Fabric |
| [semantic-model-ai-readiness.md](references/microsoft/semantic-model-ai-readiness.md) | Chuẩn bị model cho Copilot/AI |
| [semantic-model-rest-api.md](references/microsoft/semantic-model-rest-api.md) | Thao tác model qua REST (xem thêm `pbi-publish`) |
| [SOURCE.lock.json](references/microsoft/SOURCE.lock.json) | Kiểm file nguyên văn chưa bị sửa (sha256) |

Reference Microsoft **không sửa byte nào**; muốn nói khác thì ghi vào `references/kpim/`.
Khi KPIM ↔ Microsoft mâu thuẫn: Microsoft thắng về cơ chế TMDL/PBIR, KPIM thắng về quy trình nghiệp vụ.

## Đổi tên skill Microsoft → studio
Reference nguyên văn nhắc tên skill gốc; đọc theo bảng này.

| Tên trong reference Microsoft | Skill studio |
|---|---|
| `semantic-model-authoring` | `pbi-model` (skill này) |
| `powerbi-report-authoring` | [`pbi-build`](../pbi-build/SKILL.md) |
| `powerbi-report-design` | [`pbi-design`](../pbi-design/SKILL.md) |
| `powerbi-report-planning` | [`data-discovery`](../data-discovery/SKILL.md) (yêu cầu) · [`pbi-build`](../pbi-build/SKILL.md) (điều phối) |
| `powerbi-report-management` · `common/*` | [`pbi-publish`](../pbi-publish/SKILL.md) |
| `fabriciq` | không có trong studio |

Link tương đối bên trong file Microsoft (`../SKILL.md`, `../../../common/…`) trỏ theo cây upstream và có thể không mở được ở đây — tra bảng trên.

---
*Nguồn: KPIM practice + microsoft/skills-for-fabric v0.3.16 (MIT, tham chiếu nguyên văn; chưa distill vào SKILL.md).*
