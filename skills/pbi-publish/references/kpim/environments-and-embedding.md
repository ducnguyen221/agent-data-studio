---
title: Môi trường DEV/UAT/PROD, pipeline, nhúng báo cáo và Fabric
status: unverified
updated: 2026-10-26
---

# Môi trường, pipeline, nhúng báo cáo, Fabric

> **status: unverified** — viết từ hiểu biết chung, chưa chạy thử trên workspace thật của studio. Sản phẩm, SKU, giá và điều kiện cấp phép của Microsoft đổi nhanh: **kiểm Microsoft hiện hành** trước khi tư vấn hoặc thao tác, và không nêu giá hay điều kiện cũ. Agent đọc khi người dùng hỏi về môi trường triển khai, quy trình đưa báo cáo qua các giai đoạn, nhúng vào ứng dụng, hoặc các thành phần Fabric đi kèm. Thao tác đưa lên Service vẫn theo quy trình xác nhận từng bước của `pbi-publish`.

## 1. Ba môi trường: DEV → UAT → PROD

| Môi trường | Dùng để | Ai thấy | Cổng để sang bước sau |
|---|---|---|---|
| DEV | Dựng và thử; hỏng cũng được | nhóm làm báo cáo | số khớp nguồn (tie-out) trong `pbi-review` |
| **UAT** | Người dùng nghiệp vụ nghiệm thu trên dữ liệu gần thật | nhóm nghiệm thu | người dùng nghiệp vụ xác nhận số và **kiểm RLS bằng tài khoản đại diện** |
| PROD | Phục vụ người dùng cuối | người dùng cuối | — |

- **Không đưa thẳng lên PROD mà bỏ qua UAT.** Lỗi ngữ nghĩa và lỗi RLS thường chỉ lộ khi người nghiệp vụ thật mở báo cáo.
- Mỗi môi trường một workspace; tên có hậu tố môi trường (quy ước cụ thể do tổ chức chọn). Dataset dùng chung nhiều báo cáo có thể đặt ở workspace dữ liệu riêng; báo cáo nối vào đó.
- Thông tin riêng của khách (tên workspace thật, tài khoản) ghi trong hồ sơ dự án, không ghi vào tri thức nền.

## 2. Pipeline giữa các môi trường
- Dùng **deployment pipelines** của Fabric/Power BI để chuyển nội dung DEV → UAT → PROD theo từng giai đoạn thay vì đăng lại tay.
- **Quy tắc theo giai đoạn** (deployment rules / tham số): đổi nguồn dữ liệu và tham số theo môi trường; nguồn không được gõ cứng trong model (đường dẫn là M parameter — xem `pbi-model`).
- **Làm mới tăng dần** (incremental refresh) khai báo trong model, nhưng phân vùng chỉ hình thành khi làm mới trên Service: thử một lần làm mới ở UAT trước khi lên PROD.
- **RLS**: kiểm vai trò và thành viên ở UAT, rồi mới sang PROD.
- Sau mỗi lần chuyển, mở báo cáo ở môi trường đích: không lỗi visual, số khớp. Binding báo cáo ↔ model đích xem bước 6 của `pbi-publish`.

## 3. Nhúng báo cáo vào ứng dụng
- **Ứng dụng sở hữu dữ liệu (app owns data)**: ứng dụng tự xác thực với Power BI thay người xem — dùng khi người xem không có tài khoản Power BI (khách hàng, đối tác).
- **Người dùng sở hữu dữ liệu (user owns data)**: người xem đăng nhập bằng tài khoản của chính họ và dùng quyền của họ.
- **Service principal**: ứng dụng gọi API bằng danh tính ứng dụng, không dùng tài khoản người; cấp quyền tối thiểu, thông tin xác thực nằm trong kho bí mật, agent không đọc.
- **Embed token**: cấp theo phiên, kèm **danh tính RLS** của người xem để mỗi người chỉ thấy phần của mình.
- **Dung lượng**: các lựa chọn (giấy phép theo người dùng, dung lượng Fabric, dung lượng dành cho nhúng) khác nhau về điều kiện và giá, và đổi theo thời gian → **kiểm Microsoft hiện hành**; đừng chốt phương án chỉ dựa trên tài liệu này.

## 4. Thành phần Fabric thường đi cùng

| Thành phần | Dùng khi | Ghi chú |
|---|---|---|
| Lakehouse | Dữ liệu dạng tệp/bảng trong OneLake làm nguồn | Nguồn của chế độ Direct Lake — xem `direct-lake-guidelines.md` ở `pbi-model`, không lặp ở đây |
| Warehouse | Báo cáo có cấu trúc, cần điểm truy cập SQL | cùng câu hỏi chọn kiến trúc ở `consulting-method.md` của `data-discovery` |
| Dataflows Gen2 | Chuẩn bị/làm sạch dữ liệu dạng low-code | thay thế một phần Power Query tại model; chọn một chỗ, đừng làm trùng |
| Notebook | Biến đổi phức tạp bằng mã | có chi phí vận hành mã; cân nhắc có thật sự cần |
| Ứng dụng Capacity Metrics | Theo dõi mức tiêu thụ dung lượng (đơn vị CU) | xem để phát hiện báo cáo/làm mới tốn dung lượng |

## 5. Câu hỏi cần kiểm trước khi chốt
- Có cần UAT riêng không, ai nghiệm thu, nghiệm thu bằng tiêu chí nào?
- Nguồn dữ liệu mỗi môi trường là gì, và khác nhau ở đâu?
- Người xem là ai (trong/ngoài tổ chức), có RLS không, phương án phân phối và dung lượng hiện hành có hỗ trợ không?
- Ai sở hữu quá trình lên PROD, và có cách quay lại bản trước nếu lỗi?

## Nguồn
- https://learn.microsoft.com/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines
- https://learn.microsoft.com/power-bi/developer/embedded/embedded-analytics-power-bi
- https://learn.microsoft.com/power-bi/developer/embedded/embed-service-principal
- https://learn.microsoft.com/fabric/enterprise/metrics-app
- https://learn.microsoft.com/fabric/fundamentals/direct-lake-overview
- Đường dẫn trên chưa được mở lại trong lượt viết (không dùng mạng); trạng thái `unverified` giữ cho tới khi kiểm.
