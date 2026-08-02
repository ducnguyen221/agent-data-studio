---
title: "REPORTS — KPIM Mart (Danh sách & đặc tả báo cáo)"
type: reports_spec
category: "30_PROJECTS/35_TEMPLATES/PBI_Project_Delivery_Kit"
created: 2026-07-13
updated: 2026-07-13
status: active
tags: [reports, power-bi, kpim-mart, report-spec]
---

# 📑 REPORTS — KPIM Mart

> Danh sách & đặc tả báo cáo theo **Key Report Mindmap**, phân **3 cấp: Report Group → Report → Report Page**. Mỗi trang liệt kê **visual** map đúng loại block trong kit `kpim-business-light` (xem `27.06_PowerBI_Report_Design_Standard`). Ảnh: `mindmaps/key_report.png`.

## Cấu trúc phân cấp
- **Report Group:** `KPIM Mart — Bán Hàng` (1 nhóm).
- **Report (file .pbix):** 6 báo cáo dưới đây.
- **Report Page:** các trang trong từng file.

## Bố cục trang chuẩn (mọi trang bám kit)
`Header band (shape + logo image + textbox tiêu đề) → hàng slicer (Thời gian/Khu vực/Sản phẩm) + bookmarkNavigator → hàng cardVisual KPI → chart chính (combo/line) + chart phụ (donut/bar) → pivotTable/azureMap chi tiết`. Canvas 1280×720.

---

## R1 — Báo cáo Tổng Quan  *(3 trang)*
| Trang | Mục tiêu | Visual (block) |
|---|---|---|
| 1. Tổng quan chỉ số | DT/LNG/số SP/số đơn tổng | `cardVisual` (4 card KPI) · `lineClusteredColumnComboChart` (xu hướng) · `slicer` |
| 2. So sánh theo Quận/Cửa hàng | So chỉ số theo địa lý | `azureMap` (DT theo quận) · `clusteredBarChart` (top cửa hàng) · `pivotTable` |
| 3. So sánh theo Tháng/Năm & Ngành hàng/SP | So chỉ số theo thời gian & sản phẩm | `lineClusteredColumnComboChart` · `donutChart` (cơ cấu ngành) · `pivotTable` |

## R2 — Báo cáo Phân Tích Doanh Thu  *(3 trang)*
| Trang | Mục tiêu | Visual |
|---|---|---|
| 1. DT vs Kế hoạch & Tăng trưởng | Doanh số / kế hoạch / %YoY | `cardVisual` · `lineClusteredColumnComboChart` (TH vs cùng kỳ) · `slicer` |
| 2. Xu hướng 12 tháng (năm nay vs năm ngoái) | So xu hướng | `lineClusteredColumnComboChart` · `cardVisual` |
| 3. DT theo Quận/Cửa hàng + Lũy kế năm vs Chỉ tiêu | Giám sát tăng trưởng & lũy kế | `pivotTable` (matrix % tăng trưởng) · `clusteredBarChart` · `azureMap` |

## R3 — Báo cáo Phân Tích Tái Mua Hàng  *(2 trang)*
| Trang | Mục tiêu | Visual |
|---|---|---|
| 1. KH mới/cũ/duy trì vs tháng trước | Cấu trúc khách theo trạng thái | `cardVisual` · `lineClusteredColumnComboChart` · `donutChart` |
| 2. Tỷ trọng KH quay lại (quý/nửa năm/năm) | Retention/cohort | `clusteredBarChart` · `pivotTable` |

## R4 — Báo cáo Kết Quả Bán Hàng theo Khu Vực  *(3 trang)*
| Trang | Mục tiêu | Visual |
|---|---|---|
| 1. Cửa hàng đạt/không đạt KH vs năm ngoái | Xếp hạng đạt chỉ tiêu | `cardVisual` · `clusteredBarChart` · `pivotTable` (đèn giao thông) |
| 2. % tiến độ DT đạt chỉ tiêu từng cửa hàng | Bullet/gauge tiến độ | `clusteredBarChart` (bullet-style) · `pivotTable` |
| 3. % tăng trưởng so cùng kỳ từng cửa hàng | So sánh YoY theo cửa hàng | `azureMap` · `clusteredBarChart` |

## R5 — Báo cáo Phân Khúc Khách Hàng  *(3 trang)*
| Trang | Mục tiêu | Visual |
|---|---|---|
| 1. Giá trị đơn TB / khách | Chỉ số theo khách | `cardVisual` · `scatterChart` |
| 2. Số KH theo phân loại (quan trọng/thường xuyên/ít mua) | RFM/segment | `donutChart` · `clusteredBarChart` · `pivotTable` |
| 3. DT theo nhóm KH (tuổi/nghề/giới tính) | Chân dung khách | `clusteredBarChart` · `pivotTable` |

## R6 — Báo cáo Giám Sát Biên Lợi Nhuận Gộp  *(3 trang)*
| Trang | Mục tiêu | Visual |
|---|---|---|
| 1. Tổng quan DS/giá vốn/LNG/biên LNG | KPI lợi nhuận | `cardVisual` · `lineClusteredColumnComboChart` |
| 2. LNG theo từng cửa hàng | So sánh cửa hàng | `clusteredBarChart` · `pivotTable` |
| 3. Giá bán/giá mua/LN & biên LN từng SP | Chi tiết sản phẩm | `scatterChart` · `pivotTable` |

---
## Asset cần user cung cấp (GĐ5.1)
- Logo (PNG nền trong), background/nền trang, bộ màu thương hiệu, font.
- (Tùy chọn) 1 file báo cáo Power BI mẫu để lấy ý tưởng layout → cập nhật `theme.json`.

## Tính năng BI áp dụng
Drill-through (tổng quan → chi tiết cửa hàng/sản phẩm), page tooltip, bookmark toggle (tháng↔năm, bản đồ↔bảng), slicer sync, RLS theo Quản lý/Cửa hàng.

> Cập nhật sheet **REPORT** của `Project_Management.xlsx`. Thiết kế: `DESIGN.md` + `theme.json`.
