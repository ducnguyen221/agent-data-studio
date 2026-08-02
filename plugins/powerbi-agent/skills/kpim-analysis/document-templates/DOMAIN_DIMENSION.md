---
title: "DOMAIN_DIMENSION — KPIM Mart (Chiều phân tích & tư duy nghiệp vụ)"
type: domain_dimension
category: "30_PROJECTS/35_TEMPLATES/PBI_Project_Delivery_Kit"
created: 2026-07-13
updated: 2026-07-13
status: active
tags: [dimensions, business-thinking, kpim-mart, power-bi]
---

# 🧭 DOMAIN_DIMENSION — KPIM Mart

> Các cột chiều phân tích chính + tư duy nghiệp vụ đi kèm. Ảnh: `mindmaps/key_analysis.png` (nhánh trái).

## 1. Thời gian (`Dim_Date`)
| Cột chiều | Cấp | Tư duy nghiệp vụ |
|---|---|---|
| Ngày / Tháng / Quý / Năm | Hierarchy | Theo dõi xu hướng; nền cho time-intelligence (YTD, cùng kỳ, tháng trước) |

## 2. Khách hàng (`Dim_KhachHang`)
| Cột chiều | Tư duy nghiệp vụ |
|---|---|
| Phân khúc | Nhóm KH quan trọng/thường xuyên/ít mua → chiến lược chăm sóc & khuyến mãi |
| Hạng thẻ | Loyalty tier → ưu đãi & giữ chân |
| Nhóm tuổi | Chân dung KH → chọn sản phẩm/kênh phù hợp |
| Giới tính | Phân tích hành vi mua theo giới |

## 3. Sản phẩm (`Dim_SanPham`)
| Cột chiều | Tư duy nghiệp vụ |
|---|---|
| Ngành hàng | Cơ cấu doanh thu theo ngành → tập trung đầu tư |
| Nhóm sản phẩm | Phân tích hiệu quả nhóm; cross-sell |
| Phân loại | So sánh biên lợi nhuận theo loại |
| Nguồn gốc | Đánh giá nhà cung cấp/xuất xứ |
| Hãng, thương hiệu | Hiệu quả brand; đàm phán rebate |

## 4. Khu vực bán hàng (`Dim_KhuVuc`)
| Cột chiều | Tư duy nghiệp vụ |
|---|---|
| Quận | Phân bố địa lý (bản đồ); độ phủ thị trường |
| Cửa hàng | Đơn vị đánh giá hiệu suất, đạt/không đạt chỉ tiêu |
| Quản lý | Trách nhiệm & KPI theo người quản lý |

## 5. Kịch bản (Scenario)
| Giá trị | Ý nghĩa |
|---|---|
| Thực hiện (Actual) | Số liệu thật từ đơn hàng |
| Kế hoạch (Plan) | Từ Excel kế hoạch tháng |
| (Chỉ tiêu / Target) | Nếu có — so sánh % hoàn thành |

## Nguyên tắc dùng chiều
- Mỗi báo cáo chọn **1 chiều chính** + slicer các chiều phụ.
- Cửa hàng/Quản lý là chiều "đơn vị" để xếp hạng & RLS (mỗi quản lý xem cửa hàng của mình).
- Thời gian luôn kèm góc so sánh (cùng kỳ / tháng trước / kế hoạch).

> Cập nhật sheet **DOMAIN_DIMENSION** của `Project_Management.xlsx`.
