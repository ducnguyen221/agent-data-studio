---
title: "DATASET SPEC — <Tên bộ dữ liệu>"
type: dataset_spec
spec_yaml: dataset.yaml        # nguồn sự thật máy đọc — cặp với file này
status: draft
created: <YYYY-MM-DD>
updated: <YYYY-MM-DD>
---

# DATASET SPEC — <Tên bộ dữ liệu>

> **Cặp file.** Tài liệu này là bản người đọc. Nguồn sự thật máy đọc là [`dataset.yaml`](dataset.yaml).
> Mục §1 viết tay. Các mục §2–§6 **được sinh tự động** từ YAML bằng
> `python mockpack.py dict dataset.yaml -o DATASET_SPEC.md` — sửa tay ở đó sẽ bị ghi đè.
> Đổi cấu trúc dữ liệu ⇒ sửa `dataset.yaml` rồi chạy lại lệnh trên, đừng sửa ở đây.

---

## §1. Brief nghiệp vụ  *(viết tay — phần này không bị ghi đè)*

### 1.1 Bối cảnh
<Ngành, tổ chức giả lập, quy mô, phạm vi mô phỏng là phòng ban nào hay cả doanh nghiệp, hệ thống nguồn giả lập.>

### 1.2 Mục đích sử dụng
<Dạy học / demo BI / test hệ thống / POC — và hệ quả kèm theo: cần lỗi cài cắm không, cần độ dài thời gian bao nhiêu.>

### 1.3 Quy trình nghiệp vụ được mô phỏng
<Kể quy trình từ đầu đến cuối theo dòng thời gian: ai làm gì, sự kiện nào phát sinh theo thứ tự nào. Đây là căn cứ để chọn bảng fact và grain — viết đủ để người mới đọc hiểu được nghiệp vụ mà không cần hỏi thêm.>

### 1.4 Quy tắc nghiệp vụ
<Liệt kê dạng câu, mỗi dòng một quy tắc. Ví dụ: "đơn huỷ không tính vào doanh thu"; "một khách chỉ có một hạng thẻ tại một thời điểm"; "giảm giá không vượt quá giá trị hàng". Mỗi quy tắc kiểm được bằng máy nên có một rule tương ứng trong `rules:` của YAML.>

### 1.5 Câu hỏi phân tích bộ dữ liệu phải trả lời được
<Liệt kê 5–15 câu. Mỗi câu phải chỉ ra được cột nào + phép tính nào trả lời; câu nào không chỉ ra được là thiết kế còn thiếu bảng hoặc cột.>

### 1.6 Giả định & giới hạn
<Những gì cố tình đơn giản hoá so với thực tế; những gì bộ dữ liệu này KHÔNG mô phỏng, để người dùng không suy diễn sai.>

### 1.7 Lỗi cài cắm có chủ đích  *(chỉ khi mục đích là dạy học)*
<Nêu ngắn gọn từng lỗi và ý đồ giảng dạy. Danh sách kỹ thuật nằm ở `intentional_issues:` trong YAML và được in lại ở §6.>

---

<!-- BEGIN GENERATED — mọi thứ dưới đây do `mockpack.py dict` sinh ra từ dataset.yaml. ĐỪNG SỬA TAY. -->

*(Chạy `python mockpack.py dict dataset.yaml -o DATASET_SPEC.md` để sinh §2–§6: thông tin bộ dữ liệu, danh sách bảng, từ điển dữ liệu chi tiết, quan hệ, chỉ số KPI, và danh sách rule kiểm tra.)*

<!-- END GENERATED -->

---

## §7. Nhật ký thay đổi  *(viết tay)*

| Ngày | Phiên bản | Thay đổi | Người sửa |
|---|---|---|---|
| <YYYY-MM-DD> | 1.0 | Bản đầu tiên | <tên> |
