---
title: "METRICS_CALCULATION — KPIM Mart (DAX Measures)"
type: metrics_calculation
category: "30_PROJECTS/35_TEMPLATES/PBI_Project_Delivery_Kit"
created: 2026-07-13
updated: 2026-07-13
status: active
tags: [dax, measures, kpim-mart, power-bi]
---

# 🧮 METRICS_CALCULATION — KPIM Mart

> Danh sách hàm tính (DAX Measure) theo **Key Analysis Mindmap**. Lưu trong bảng `Measure`, chia **DisplayFolder** theo 6 nhóm. Ảnh: `mindmaps/key_analysis.png`.

## Quy tắc đặt tên & tổ chức
- Bảng riêng `Measure` (chỉ chứa measure). Folder con = 6 nhóm chỉ số.
- FormatString: `#,0` (tiền/số), `0.0%` (tỷ lệ). Time-intelligence lọc qua `Dim_Date`.
- Base measure → biến thể lũy kế/cùng kỳ (dùng calculation group nếu bùng nổ).

## 1. Nhóm DOANH THU (`/Doanh Thu`)
| Measure | Công thức (mô tả) | DAX gợi ý |
|---|---|---|
| Doanh Thu | Tổng doanh thu | `SUM(Fact_DonHang[Tổng doanh thu])` |
| Doanh Thu LK Năm | Lũy kế năm (YTD) | `TOTALYTD([Doanh Thu], Dim_Date[Date])` |
| Tăng trưởng vs Tháng trước | %DT vs tháng trước | `DIVIDE([Doanh Thu]-CALCULATE([Doanh Thu],PREVIOUSMONTH(Dim_Date[Date])), ...)` |
| Tăng trưởng vs Cùng kỳ năm ngoái | %DT YoY | `VAR ly=CALCULATE([Doanh Thu],SAMEPERIODLASTYEAR(Dim_Date[Date])) RETURN DIVIDE([Doanh Thu]-ly, ly)` |

## 2. Nhóm LỢI NHUẬN GỘP (`/Lợi Nhuận Gộp`)
| Measure | Mô tả | DAX gợi ý |
|---|---|---|
| Lợi Nhuận Gộp | Tổng lợi nhuận gộp | `SUM(Fact_DonHang[Lợi nhuận gộp])` |
| Giá Vốn Hàng Bán | Tổng giá vốn | `SUM(Fact_DonHang[Giá vốn hàng bán])` |
| Biên Lợi Nhuận Gộp | LNG / Doanh thu | `DIVIDE([Lợi Nhuận Gộp],[Doanh Thu])` |

## 3. Nhóm TỔNG KHUYẾN MÃI (`/Khuyến Mãi`)
| Measure | Mô tả | DAX gợi ý |
|---|---|---|
| Tổng Khuyến Mãi | Tổng giảm giá | `SUM(Fact_DonHang[Tổng giảm giá])` |
| Tỷ Lệ Khuyến Mãi | Giảm giá / Tổng giá tiền | `DIVIDE([Tổng Khuyến Mãi], SUM(Fact_DonHang[Tổng giá tiền]))` |
| Số SP Chạy Khuyến Mãi | SP có khuyến mãi | `CALCULATE(DISTINCTCOUNT(Fact_DonHang[Sản phẩm]), Fact_DonHang[Khuyến mãi]<>"Không")` |

## 4. Nhóm SỐ SẢN PHẨM BÁN (`/Sản Phẩm`)
| Measure | Mô tả | DAX gợi ý |
|---|---|---|
| Số Sản Phẩm Bán | Tổng số lượng | `SUM(Fact_DonHang[Số lượng])` |
| Lợi Nhuận Trên 1 SP | LNG / số lượng | `DIVIDE([Lợi Nhuận Gộp],[Số Sản Phẩm Bán])` |
| Giá Bán TB 1 SP | Doanh thu / số lượng | `DIVIDE([Doanh Thu],[Số Sản Phẩm Bán])` |

## 5. Nhóm SỐ KHÁCH MUA HÀNG (`/Khách Hàng`)
| Measure | Mô tả | DAX gợi ý |
|---|---|---|
| Số Khách Mua Hàng | Số khách distinct | `DISTINCTCOUNT(Fact_DonHang[Số điện thoại])` |
| Tần Suất Mua TB 1 Khách | Số đơn / số khách | `DIVIDE([Số Đơn Hàng],[Số Khách Mua Hàng])` |
| Bình Quân Giá Trị Mua 1 Khách | Doanh thu / số khách | `DIVIDE([Doanh Thu],[Số Khách Mua Hàng])` |

## 6. Nhóm SỐ ĐƠN HÀNG (`/Đơn Hàng`)
| Measure | Mô tả | DAX gợi ý |
|---|---|---|
| Số Đơn Hàng | Số giao dịch distinct | `DISTINCTCOUNT(Fact_DonHang[Mã giao dịch])` |
| Giá Trị TB 1 Đơn | Doanh thu / số đơn | `DIVIDE([Doanh Thu],[Số Đơn Hàng])` |
| Số SP Mua TB 1 Đơn | Số lượng / số đơn | `DIVIDE([Số Sản Phẩm Bán],[Số Đơn Hàng])` |

## 7. Nhóm KẾ HOẠCH & SO SÁNH (`/Kế Hoạch`)
| Measure | Mô tả |
|---|---|
| Doanh Thu Kế Hoạch | `SUM(Fact_KeHoach[Doanh thu KH])` |
| % Hoàn Thành KH | `DIVIDE([Doanh Thu],[Doanh Thu Kế Hoạch])` |
| Chênh Lệch vs KH | `[Doanh Thu]-[Doanh Thu Kế Hoạch]` |

> **Đối chiếu:** kiểm tra lại Analysis Mindmap + dữ liệu đã nạp → tạo đủ measure, đặt tên chuẩn. Cập nhật sheet **METRICS_CALCULATION** của `Project_Management.xlsx`.
