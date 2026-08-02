# Kit `kpim-business-light`

Template kit mẫu đi kèm powerbi-agent — distill (đã **sanitize**) từ một trang dashboard
quản trị doanh nghiệp production thật gồm 30 visual: canvas 1280×720, nền `#DFE7F6`,
card KPI reference-label với conditional color, combo chart, pivot table, slicer,
azure map, bookmark navigator…

- Binding trong `blocks/*.json` là placeholder `TEMPLATE_*` — `apply_template` sẽ thay bằng
  field thật của model đích (bắt buộc truyền `fields` cho mọi block có dữ liệu).
- Title trong style là **text ví dụ** — ghi đè bằng `title` trong page_spec.
- Block `image` tham chiếu resource của báo cáo NGUỒN (`StaticResources/RegisteredResources`) —
  dùng sang báo cáo khác cần tự thêm ảnh vào resource của báo cáo đích, hoặc bỏ block này.
- Xem `blueprint.md` để biết layout gốc (vị trí/z-order từng visual) — dùng làm tham chiếu
  khi thiết kế page_spec.
