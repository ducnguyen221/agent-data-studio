# Bộ dữ liệu thực hành đầu tiên

`sales-demo.csv` là dữ liệu tổng hợp tự tạo cho bài hướng dẫn, không lấy từ khách hàng hay báo cáo thật. Đơn vị doanh thu: VND; mỗi dòng là một tháng × vùng × nhóm hàng. Toàn bộ mẫu thuộc giấy phép MIT của repo.

Trong folder repo, nhờ AI Agent: “Đọc `samples/sales-demo.csv` bằng skill `data-discovery` gốc trong repo. Kiểm chất lượng dữ liệu, tính tổng doanh thu theo tháng và lưu báo cáo ngắn vào `workspace/outputs/first-report.md`. Không cần Power BI Desktop.”

Kết quả kiểm tay: 12 dòng, không ô trống, tổng 182 đơn hàng, doanh thu 20.350.000 VND. Agent cần tính từ CSV và đối chiếu con số này trước khi bàn giao.

| Tháng | Số đơn | Doanh thu (VND) |
|---|---:|---:|
| 2026-01 | 55 | 6.050.000 |
| 2026-02 | 61 | 6.800.000 |
| 2026-03 | 66 | 7.500.000 |
| **Tổng** | **182** | **20.350.000** |

Mỗi tổ hợp tháng × vùng × nhóm hàng xuất hiện đúng một lần (12 tổ hợp). Nếu báo cáo của agent khác bảng trên, nhờ agent chỉ ra các dòng CSV và phép cộng đã dùng trước khi tin kết quả.
