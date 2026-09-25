---
title: "DESIGN — KPIM Mart (Tư duy thiết kế & Theme Power BI)"
type: design_spec
category: "30_PROJECTS/35_TEMPLATES/PBI_Project_Delivery_Kit"
created: 2026-07-13
updated: 2026-07-13
status: active
tags: [design, theme, power-bi, kpim-mart, ui]
---

# 🎨 DESIGN — KPIM Mart

> Bộ tư duy thiết kế báo cáo + sinh `theme.json` để import vào Power BI. Nếu user cung cấp logo/màu thương hiệu → cập nhật lại bảng màu & theme.

## 1. Nguyên tắc thiết kế (design thinking)
- **Business-light:** nền sáng (#F5F7FA), chữ đậm dễ đọc, accent màu thương hiệu.
- **Phân cấp thị giác:** Header band trên cùng (tiêu đề + logo + slicer) → hàng **card KPI** (số lớn) → **chart chính** → **chi tiết** (bảng/bản đồ).
- **Nhất quán:** dùng 1 bảng màu; đèn giao thông cho đạt/không đạt (xanh ≥100%, vàng 85–<100%, cam 70–<85%, đỏ <70%).
- **Tối giản:** bỏ đường lưới thừa, bo góc nhẹ, khoảng trắng hợp lý; canvas 1280×720.
- **Tương tác:** slicer đồng bộ, bookmark toggle, drill-through, tooltip trang.

## 2. Bảng màu (color palette)
| Vai trò | Mã màu | Dùng cho |
|---|---|---|
| Primary (teal) | `#0F9D8F` | Nhấn chính, card KPI, tiêu đề |
| Primary dark | `#12776E` | Header band, nhóm chỉ số |
| Secondary (blue) | `#2B6FD6` | Chart chính, doanh thu |
| Accent (orange) | `#E8730C` | Cảnh báo/nổi bật, khuyến mãi |
| Positive (green) | `#3A8A2B` | Đạt chỉ tiêu / tăng trưởng |
| Negative (red) | `#D64545` | Không đạt / suy giảm |
| Neutral | `#6B7A90` | Chữ phụ, trục |
| Background | `#F5F7FA` | Nền trang |
| Card bg | `#FFFFFF` | Nền card/visual |

## 3. Icon & nút (buttons)
- Bộ icon phẳng (flat, line) cho: bộ lọc, làm mới, quay lại, drill-through, xuất file.
- Nút bookmark cho toggle (Tháng↔Năm, Bản đồ↔Bảng).
- KPI card kèm ▲▼ (mũi tên tăng/giảm) + màu positive/negative.

## 4. Typography
- Font: **Segoe UI** (mặc định Power BI, hỗ trợ tiếng Việt) — tiêu đề 16–20pt bold, body 10–12pt.

## 5. Áp dụng
1. Import `theme.json` (View → Themes → Browse for themes).
2. Đặt logo vào header band (block `image`), tiêu đề vào `textbox`.
3. Nếu có mẫu báo cáo của khách → distill thành kit riêng (`distill_template` MCP) và cập nhật theme.

> File theme: `theme.json` (cùng thư mục). Chuẩn dựng báo cáo: `27.06_PowerBI_Report_Design_Standard`.
