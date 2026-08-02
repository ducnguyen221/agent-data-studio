---
title: "DATA_DICTIONARY — KPIM Mart"
type: data_dictionary
category: "30_PROJECTS/35_TEMPLATES/PBI_Project_Delivery_Kit"
created: 2026-07-13
updated: 2026-07-13
status: active
tags: [data-dictionary, kpim-mart, power-bi]
---

# 🗃️ DATA DICTIONARY — KPIM Mart

> Mô tả chi tiết các bảng, nguồn và trường dữ liệu. Bảng Fact chính = **Đơn hàng bán** (15 trường). Ảnh: `mindmaps/key_data_dictionary.png`.

## 1. Danh sách nguồn & bảng
| STT | Nguồn | Bảng | Loại | Granularity | Ghi chú |
|---|---|---|---|---|---|
| 1 | SharePoint List | `Fact_DonHang` (Đơn hàng bán) | Fact | 1 dòng / dòng đơn hàng | Form nhập khi phát sinh đơn |
| 2 | SQL Server | `Dim_SanPham` (Sản phẩm) | Dim | 1 dòng / SKU | Ngành hàng, nhóm, phân loại, nguồn gốc, hãng |
| 3 | SQL Server | `Dim_KhachHang` (Khách hàng) | Dim | 1 dòng / khách (SĐT) | Phân khúc, hạng thẻ, nhóm tuổi, giới tính |
| 4 | SQL Server | `Dim_KhuVuc` (Cửa hàng/Khu vực) | Dim | 1 dòng / cửa hàng | Quận, cửa hàng, quản lý |
| 5 | Excel | `Fact_KeHoach` (Kế hoạch tháng) | Fact | 1 dòng / khu vực × tháng | Mỗi sheet 1 năm → cần append |
| 6 | (tạo) | `Dim_Date` (Date Table) | Dim | 1 dòng / ngày | Chuẩn hóa time-intelligence |

## 2. Bảng Fact chính — Đơn hàng bán (15 trường)
| STT | Tên cột | Loại dữ liệu | Định nghĩa |
|---|---|---|---|
| 1 | Mã giao dịch | Text | Mã định danh giao dịch mua bán đơn hàng |
| 2 | Ngày đặt hàng | Date | Ngày phát sinh đơn hàng, đặt bởi khách hàng |
| 3 | Tên cửa hàng | List | Cửa hàng trên hệ thống phát sinh đơn hàng |
| 4 | Sản phẩm | List | Sản phẩm được đặt hàng |
| 5 | Khuyến mãi | List | Chương trình giảm giá áp dụng |
| 6 | Số lượng | Whole Number | Số lượng sản phẩm mua *(Additive)* |
| 7 | Số điện thoại | Text | Số điện thoại định danh khách hàng |
| 8 | Tên khách hàng | Text | Tên của khách hàng trên hệ thống |
| 9 | Giá bán | Decimal Number | Giá bán cho 1 đơn vị sản phẩm *(Non-additive)* |
| 10 | Giá mua | Decimal Number | Giá vốn mua nhập sản phẩm về *(Non-additive)* |
| 11 | Tổng giá tiền | Decimal Number | Số lượng × Giá bán |
| 12 | Tổng giảm giá | Decimal Number | Số lượng × Tỷ lệ giảm giá |
| 13 | Tổng doanh thu | Decimal Number | Tổng giá tiền − Tổng giảm giá |
| 14 | Giá vốn hàng bán | Decimal Number | Số lượng × Giá mua |
| 15 | Lợi nhuận gộp | Decimal Number | Tổng doanh thu − Giá vốn hàng bán |

> **Lưu ý mô hình hóa:** cột 11–15 nên tính ở tầng dữ liệu (calculated column/Power Query) hoặc để measure; số 7 (SĐT) là **PII** → khai báo vào `policy.json` của MCP `powerbi-agent` (aggregate-only). Additive vs Non-additive quyết định cách tổng hợp (Giá bán/Giá mua KHÔNG SUM).

## 3. Quan hệ (relationships)
```
Fact_DonHang[Sản phẩm]     → Dim_SanPham[Sản phẩm]      (Many→One)
Fact_DonHang[Số điện thoại]→ Dim_KhachHang[Số điện thoại](Many→One)
Fact_DonHang[Tên cửa hàng] → Dim_KhuVuc[Cửa hàng]       (Many→One)
Fact_DonHang[Ngày đặt hàng]→ Dim_Date[Date]             (Many→One)
Fact_KeHoach[Khu vực+Tháng]→ Dim_KhuVuc / Dim_Date       (Many→One)
```
→ **Star schema**; Date Table đánh dấu "Mark as Date Table".

## 4. Đề xuất chỉnh sửa dữ liệu (GĐ2.3)
- Append 12 sheet Excel kế hoạch (mỗi năm) thành 1 bảng dài (unpivot nếu cần).
- Chuẩn hóa mã sản phẩm/khu vực đồng nhất giữa SharePoint và SQL Server.
- Ép kiểu `Ngày đặt hàng` = Date (tránh serial 45292).
- Tạo Date Table phủ từ min→max ngày giao dịch.

> Cập nhật vào sheet **DATA DICTIONARY** của `Project_Management.xlsx`.
