---
title: "RESEARCH_NOTES — KPIM Mart (Pha 0)"
type: research_notes
category: "30_PROJECTS/35_TEMPLATES/PBI_Project_Delivery_Kit"
created: 2026-07-13
updated: 2026-07-13
status: active
tags: [research, discovery, kpim-mart]
---

# 🔎 RESEARCH_NOTES — KPIM Mart (Pha 0: Đọc – Hiểu – Hỏi ngược)

## 1. Tổng quan tài liệu & dữ liệu đầu vào
- **Bộ dữ liệu:** đơn hàng bán bán lẻ (KPIM Mart) — 1 bảng Fact 15 trường + danh mục SP/KH/khu vực (SQL Server) + kế hoạch tháng (Excel).
- **Domain:** bán lẻ (retail POS), nghiệp vụ Bán hàng; đối tượng xem: Ban giám đốc & quản lý.
- **Đặc điểm dữ liệu:** granularity dòng đơn hàng; có additive (Số lượng) & non-additive (Giá bán/Giá mua); có PII (SĐT).

## 2. Suy luận & research bổ sung
- Bài toán điển hình bán lẻ: theo dõi doanh thu/lợi nhuận, đạt chỉ tiêu, tăng trưởng, tái mua, phân khúc khách, biên lợi nhuận.
- KPI ngành (tham chiếu `27.04_Domain_Business_Playbooks` — bán lẻ): DT & số đơn (vs cùng kỳ), top cửa hàng, cơ cấu mặt hàng, độ phủ, tồn kho (nếu có), RFM khách.
- Rủi ro: mã SP/khu vực không đồng nhất giữa SharePoint & SQL Server; Excel kế hoạch nhiều sheet cần append; SĐT cần che (PII).

## 3. Bộ câu hỏi ngược cho user (chốt điểm mấu chốt)
1. **Nguồn & kết nối:** SQL Server/SharePoint/Excel có cho kết nối trực tiếp (gateway/API) không? Mã SP-KH-khu vực có đồng nhất giữa nguồn?
2. **Chỉ tiêu:** có bảng chỉ tiêu (target) riêng ngoài kế hoạch không? Chỉ tiêu theo cửa hàng/quản lý/tháng?
3. **Phân quyền:** cần RLS theo Quản lý/Cửa hàng? Bao nhiêu user, dùng Service/Report Server/Embedded?
4. **Cảnh báo:** cần cảnh báo (đạt/không đạt, giảm YoY) qua Teams/Email không?
5. **Thiết kế:** có logo/bộ màu/thương hiệu & mẫu báo cáo Power BI mong muốn?
6. **Tính năng:** drill-through/tooltip/bookmark/dashboard tổng hợp/scorecard?
7. **Phạm vi:** 6 báo cáo đề xuất đã đủ chưa, hay thêm Tồn kho/Marketing?

> Sau khi user trả lời → sang Pha 1 (Key Information) hoàn thiện `PROJECT.md`.
