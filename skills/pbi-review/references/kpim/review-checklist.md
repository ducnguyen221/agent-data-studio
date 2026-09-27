---
title: Checklist review độc lập — SQL · DAX · model · trang báo cáo
source: Agent Data Studio practice
updated: 2026-09-17
---

# Checklist review (đánh mức: Blocker / Major / Minor / Nit)

## A. Ngữ nghĩa & đúng số (làm TRƯỚC mọi thứ)
- [ ] Chỉ số tính đúng **định nghĩa nghiệp vụ** trong `METRICS_CALCULATION.md` của dự án? Kiểm ở đúng **grain**.
- [ ] **Tie-out**: tổng khớp nguồn tin cậy (báo cáo gốc, số user cung cấp). Không khớp → **Blocker**, chưa duyệt.
- [ ] Đơn vị tính / tiền tệ / múi giờ / biên ngày nhất quán.

## B. SQL (nguồn, view, stored procedure)
- [ ] Join đúng loại (inner / left / full); null được xử lý; không nhân dòng do join trùng khoá.
- [ ] Predicate SARGable; không `SELECT *`; không ép kiểu ngầm; không cross join vô tình.
- [ ] Index / partition pruning phù hợp khối lượng; có số đo (query plan) chứ không đoán.

## C. DAX
- [ ] `CALCULATE` và ngữ cảnh lọc đúng; `ALL` / `REMOVEFILTERS` / `KEEPFILTERS` có chủ đích.
- [ ] Iterator vs aggregator đúng (`SUMX` vs `SUM`); không lỗi row context.
- [ ] Cột tồn / số dư **không SUM qua kỳ** (`CLOSINGBALANCEMONTH`); time-intel lọc qua **date table**.
- [ ] `VAR` cho biểu thức lặp; `DIVIDE` thay `/`.
- [ ] Measure ưu tiên hơn calculated column; tên, `displayFolder`, `formatString` rõ ràng.
- [ ] Measure âm thầm đổi ngữ cảnh (`ALL` trên fact không chủ đích) → gắn cờ + đề xuất biểu thức thay.

## D. Model
- [ ] Star schema (snowflake phải có lý do); quan hệ Many→One; khoá số nguyên.
- [ ] Không lọc hai chiều khi không cần; không quan hệ thừa/ngược chiều (soi ERD `distill_model_schema`).
- [ ] Date table riêng phủ toàn bộ phạm vi; auto date/time tắt; không "blank member".
- [ ] Import / DirectQuery / Direct Lake / aggregation chọn hợp lý với khối lượng và tần suất refresh.

## E. Bảo mật
- [ ] RLS đúng; model lộ PII mà thiếu RLS → **Blocker**.
- [ ] Cột PII che/không project; `policy.json` đã khai; service principal quyền tối thiểu.

## F. Trang báo cáo (đọc cùng screenshot)
- [ ] Lưới, tỷ lệ và khoảng cách khớp Design Brief hoặc kit đã được người dùng duyệt; chỉ áp số đo KPIM nếu dự án chọn mẫu đó và có quyền dùng.
- [ ] Chỉ visual hiện đại (`cardVisual`, `pivotTable`, `tableEx`, `azureMap` + chart chuẩn).
- [ ] Card có nhãn đối chiếu; màu điều kiện theo theme đã duyệt và **đúng chiều ý nghĩa** chỉ số.
- [ ] Style container, panel và chữ khớp kit/theme đã duyệt; không tự áp token của tổ chức khác.
- [ ] Matrix nằm trên `shape` panel có z thấp hơn; không visual chồng lấn ngoài ý muốn; không chữ bị cắt.
- [ ] Không còn binding tên cũ sau clone (grep = 0); không trang mồ côi ngoài `pages.json`.
- [ ] Accessibility: tương phản, alt text, thứ tự tab (Microsoft `accessibility.md`).

## G. Khả năng bảo trì
- [ ] Đặt tên nhất quán; comment ở chỗ khó; không hằng số ma thuật trong DAX/SQL.

## Điều kiện DỪNG (không duyệt)
- Số không khớp nguồn sự thật nghiệp vụ.
- Model lộ PII không có RLS.
- Measure đổi ngữ cảnh âm thầm trên fact.
- Trang chưa qua validate / reload / screenshot.

## Đầu ra review
Danh sách phát hiện theo mức (Blocker / Major / Minor / Nit) + đề xuất cụ thể; DAX có biểu thức thay thế khi
cần; nếu phát sinh field/grain mới → cập nhật `DATA_DICTIONARY.md` của dự án (trong Knowledge Dir, không phải repo).
