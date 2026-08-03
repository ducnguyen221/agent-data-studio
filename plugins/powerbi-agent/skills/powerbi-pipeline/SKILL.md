---
name: powerbi-pipeline
x-generated-by: powerbi-agent
description: >
  Quy trình chuẩn 9 khâu để AI Agent làm phân tích dữ liệu end-to-end trên Power BI —
  từ kết nối Power Query, transform M, mô hình hóa, DAX, đến trang báo cáo hoàn thiện
  theo template và chưng cất tri thức. Kích hoạt khi người dùng yêu cầu: "phân tích dữ
  liệu với Power BI", "dựng báo cáo Power BI từ đầu", "làm dashboard từ dữ liệu X",
  "xây model + báo cáo", hoặc bất kỳ dự án Power BI trọn gói nào (không chỉ 1 truy vấn lẻ).
---

# powerbi-pipeline — Agent làm Power BI end-to-end đúng chuẩn

Điều phối 2 MCP server theo phân vai (đừng lẫn):
- **powerbi-agent** (bridge): query DAX có policy, schema discovery, template/PBIR, distill.
- **powerbi-modeling** (Microsoft): tạo/sửa table/column/measure/relationship, bulk, TMDL, validate DAX.

**Tư thế làm việc: PBIP-first.** Đầu dự án, bảo user Save As `.pbip` (bật Preview "Power BI Project
(.pbip) save option" + PBIR). Được thế thì model = TMDL text, report = PBIR JSON — mọi khâu đều
git-diff được và agent thao tác an toàn khi file đóng.

## 9 khâu chuẩn (làm theo THỨ TỰ, mỗi khâu có cổng kiểm)

### Khâu 1 — Kết nối dữ liệu (Power Query)
- Nguồn vào qua Power Query: sửa partition M expression trong TMDL
  (`*.SemanticModel/definition/tables/*.tmdl`) qua **powerbi-modeling**, hoặc hướng dẫn user
  thao tác Get Data trên Desktop khi nguồn cần credential UI.
- Quy ước: nguồn/đường dẫn tham số hóa bằng **M parameter** (KHÔNG hardcode path máy cá nhân);
  credential KHÔNG bao giờ nằm trong M code.
- ✅ Cổng kiểm: refresh thành công, row count từng bảng nguồn khớp kỳ vọng
  (`EVALUATE ROW("n", COUNTROWS('Bảng'))`).

### Khâu 2 — Transform M
- Staging query tách khỏi query cuối; tên bước rõ nghĩa; kiểu dữ liệu ép TƯỜNG MINH ở cuối
  (nhất là Date — bẫy kinh điển: ngày Excel thành số serial 45292).
- ✅ Cổng kiểm: `describe_table` từng bảng — kiểu cột đúng (Date là DateTime, số là Int64/Decimal).

### Khâu 3 — Mô hình hóa & relationship
- Star schema: Fact ở giữa, Dim xung quanh; date table riêng (`DM_Date`) phủ TOÀN BỘ phạm vi dữ liệu.
- Tạo relationship qua **powerbi-modeling** (bulk, transaction); lẻ 1-2 cái có thể
  `add_relationship_local` (bridge). Many→One từ Fact vào Dim.
- Bẫy đã trả giá: cột khóa có blank → "blank member" hiện ở mọi slicer; snapshot fact nối date
  qua cột cuối-tháng là đủ.
- ✅ Cổng kiểm: `distill_model_schema` → soi Mermaid ERD đúng hình sao, không quan hệ thừa/ngược chiều.

### Khâu 4 — Measure & calculated column (DAX)
- Measure gom vào bảng riêng (vd `Công thức`), đặt DisplayFolder + FormatString (`#,0` tiền, `0.0%` phần trăm).
- Viết qua **powerbi-modeling** (validate được DAX); lẻ thì `add_measure_local`.
- Bẫy đã trả giá: cột STOCK (tồn/số dư cuối kỳ) KHÔNG SUM qua tháng — dùng `CLOSINGBALANCEMONTH`;
  time-intel phải lọc qua date table, không qua cột năm của Fact.
- ✅ Cổng kiểm: mỗi measure chạy thử `EVALUATE ROW("kq", [Measure])` + đối chiếu 1 con số biết trước.

### Khâu 5 — Tổng hợp & truy vấn (DAX Queries)
- Chỉ qua `execute_dax_local`/`_service` của bridge — policy aggregate-only đang gác:
  KHÔNG `EVALUATE 'Bảng'`; dùng SUMMARIZECOLUMNS/TOPN/measure. Cột PII cấm project
  (policy.json per dự án — hỏi user cột nào nhạy cảm NGAY đầu dự án, ghi vào policy.json).
- ✅ Cổng kiểm: audit log không có verdict blocked bất thường.

### Khâu 6+7 — Visual & trang báo cáo (PBIR, file ĐÓNG)
- **KHÔNG BAO GIỜ dựng layout từ đầu** — `list_templates` → chọn kit → `apply_template`
  (clone-and-rebind, giữ `visualContainerObjects`). Field bind phải tồn tại (check bằng
  `describe_table` trước).
- Trang theo cấu trúc chuẩn: header band + card KPI hàng trên + chart giữa + bảng chi tiết/slicer.
- ✅ Cổng kiểm: JSON hợp lệ + user mở Desktop nghiệm thu MẮT (bắt buộc — agent không thấy render).

### Khâu 8 — Tính năng nâng cao
- Làm được bằng code: page tooltip (page.json `pageBinding` type Tooltip) · drill-through
  (`pageBinding` type Drillthrough + filter đích) · field parameters/what-if (calc table qua
  powerbi-modeling) · hierarchy cho drill-down.
- **Bookmark: ĐỂ TAY** — clone bookmark từng vỡ báo cáo (explorationState snapshot). Dựng stacked
  visuals + hướng dẫn user bấm tạo bookmark trong Desktop.
- ✅ Cổng kiểm: từng tính năng demo được trên Desktop.

### Khâu 9 — Đóng dự án: artifact + tri thức
Mỗi dự án sinh đủ 4 artifact (chuẩn OpcOS): **PLAN** (khâu 0 — trước khi làm) · **CHANGESET**
(model/report đổi gì) · **VERIFICATION** (cổng kiểm từng khâu + audit log) · **HANDOFF**
(cách refresh/publish + việc tay còn lại).
Chưng cất tri thức:
- `distill_model_schema` + `distill_report_design` → blueprint model + hồ sơ thiết kế vào `projects/<slug>/design/` (Knowledge Dir — cơ chế: [`../powerbi-knowledge/SKILL.md`](../powerbi-knowledge/SKILL.md)); `log_timeline` ghi mốc; cuối dự án chạy luồng /powerbi-done + /powerbi-pack.
- Trang báo cáo đẹp được user duyệt → `distill_template` thành kit tái dùng cho dự án sau.
- Bài học quy trình (bẫy mới, root-cause) → memory của agent.

## Nguyên tắc xuyên suốt

1. **Thứ tự là bắt buộc** — đừng viết measure khi model chưa chốt; đừng dựng trang khi measure chưa verify.
2. **Mỗi khâu một cổng kiểm chạy được** — không có verify = khâu chưa xong.
3. **Ghi model khi nào cũng được (engine live); ghi REPORT chỉ khi file đóng.**
4. **Không interleave write 2 MCP cùng lúc** — modeling xong SaveChanges rồi mới quay lại query/report.
5. **Dữ liệu thô ở lại engine** — mọi con số vào chat đều là kết quả tổng hợp (policy đang enforce).
6. **Hỏi PII đầu dự án** — cột nào nhạy cảm → policy.json trước khi chạm dữ liệu.

## 📚 Tài liệu kỹ thuật tham chiếu (references/)
Đọc khi cần chi tiết kỹ thuật (nguồn Microsoft Learn + kinh nghiệm KPIM):
- `references/dax-best-practices.md` — VAR, DIVIDE, date table, calculation groups, time-intelligence, measure family.
- `references/powerquery-m-best-practices.md` — query folding, Value.NativeQuery (EnableFolding), connector, kiểu dữ liệu, incremental.
- `references/sql-best-practices.md` — SARGable, index/covering index, no SELEC*, pre-aggregate View/SP, DW staging, SCD.
- `references/gotchas.md` — bẫy Date serial, blank member, STOCK không SUM, bookmark để tay, policy, ghi REPORT khi file đóng.
- `references/powerbi-knowledge-map.md` — bản đồ kiến thức Power BI tổng (chủ đề → reference nào/khâu nào).

## 🔗 Skill liên quan (cùng bộ, thư mục anh em)
- Pha NGHIỆP VỤ trước pipeline này: [`../kpim-analysis/SKILL.md`](../kpim-analysis/SKILL.md) — khảo sát, tài liệu hóa, kế hoạch.
- Hướng dẫn 16 tool + policy an toàn dữ liệu: [`../powerbi-mcp/SKILL.md`](../powerbi-mcp/SKILL.md).
