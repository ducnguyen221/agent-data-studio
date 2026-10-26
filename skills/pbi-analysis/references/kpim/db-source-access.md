# Đọc cơ sở dữ liệu nguồn an toàn (ngoài model Power BI)

> Nguồn: thực hành của studio về truy cập CSDL nguồn (PostgreSQL, MySQL, SQL Server, BigQuery và tương tự), đối chiếu `sql-best-practices.md` của `pbi-model` và chính sách an toàn của `pbi-analysis`. File này là **nguyên tắc và tiền đề**, không phải script mẫu. Agent đọc khi người dùng muốn kết nối CSDL nguồn, liệt kê bảng, hoặc phân tích metadata nguồn — việc mà engine DAX của studio không làm.

## 1. Phạm vi
- Engine studio truy vấn **model Power BI** bằng DAX. Đọc thẳng **CSDL nguồn** là việc khác: mặc định chỉ để *hiểu nguồn* (bảng nào, cột nào, khóa nào, cỡ bao nhiêu) trước khi dựng Power Query hoặc kiểm tie-out.
- Không dùng đường này để kéo dữ liệu thô về cho agent xử lý. Cần số tổng hợp thì để CSDL tính (mục 5).
- Đường này **đi vòng engine** của studio nên **không có** chặn PII, aggregate-only hay audit như `pbi-analysis` (xem *Chính sách an toàn dữ liệu* trong `mcp-tools.md` cùng thư mục); người làm phải tự giữ các rào đó theo mục 5b.

## 2. Kết nối an toàn
1. **Không mở IP public** cho instance CSDL để agent kết nối vào.
2. Đi qua **proxy xác thực của nhà cung cấp cloud** (đúng loại dành cho dịch vụ CSDL đang dùng) hoặc **SSH tunnel**; đầu cục bộ chỉ lắng nghe trên địa chỉ loopback.
3. **Không lưu mật khẩu rõ.** Chuỗi kết nối lấy lúc chạy từ kho bí mật của tổ chức (secret manager). Agent **không mở file bí mật**; chương trình đọc nó, agent chỉ nhận kết quả (khớp `pbi-analysis` và mục Bảo mật của `sql-best-practices.md`). Không đặt bí mật ở đối số dòng lệnh (lộ trong danh sách tiến trình); không in hay ghi log chuỗi kết nối; thông báo lỗi phải che phần xác thực (exception của driver thường chứa URL kết nối).
4. Tên instance, tên bí mật, cổng, tài khoản của một dự án cụ thể thuộc **hồ sơ dự án** trong trạm dữ liệu, không ghi vào tri thức nền của repo.

## 3. Chỉ đọc — bằng cơ chế, không bằng lời dặn
- Dùng **tài khoản chỉ-đọc ở phía CSDL** (vai trò chỉ có quyền `SELECT`, hoặc bản sao đọc). Chỉ tin quyền do CSDL cưỡng chế; một câu "chỉ chạy SELECT" trong prompt hay trong script không phải rào chắn.
- Agent **không** ghi, sửa, xóa hay đổi cấu trúc trên CSDL nguồn. Gặp yêu cầu kiểu "xóa bản ghi trùng giúp", "sửa giá trị sai": từ chối phần ghi; thay bằng truy vấn đọc **liệt kê** bản ghi trùng/sai kèm khóa, rồi giao danh sách cho người chủ hệ thống xử lý qua kênh vận hành của họ.
- Nếu tài khoản đang dùng có quyền ghi: nói rõ với người dùng và đề nghị đổi sang tài khoản chỉ-đọc trước khi tiếp tục.

## 4. Kiểm tiền đề trước khi truy vấn
Kiểm từng thứ; thiếu thì báo thiếu gì rồi dừng, đừng đoán:
- Công cụ dòng lệnh đăng nhập của nhà cung cấp cloud đã có và đã đăng nhập (người dùng tự đăng nhập).
- Proxy hoặc tunnel đang chạy và cổng cục bộ sẵn sàng.
- Driver/thư viện của ngôn ngữ đang dùng đã cài.
- Có tài khoản chỉ-đọc (mục 3) và nơi lấy chuỗi kết nối (mục 2).

## 5. Truy vấn tiết kiệm context
- **Luôn giới hạn dòng** khi khám phá: `LIMIT` (hoặc `TOP`) với số nhỏ, để kết quả không tràn context của agent; mẫu dòng chỉ lấy theo điều kiện ở mục 5b.
- **BigQuery**: `LIMIT` **không** giảm lượng dữ liệu bị quét hay phí. Ước lượng trước bằng dry-run, đặt trần byte tính phí (`maximum_bytes_billed`), chỉ chọn cột cần dùng và lọc theo cột phân vùng (partition); kiểm với tài liệu Google hiện hành.
- **Đẩy tính toán về CSDL**: `COUNT`, `SUM`, `GROUP BY` ở phía nguồn thay vì tải bản ghi thô rồi xử lý lại (xem mục *Viết query cho BI* trong `sql-best-practices.md` của `pbi-model`).
- **Metadata ưu tiên dùng bản đã trích sẵn** (blueprint schema đã lưu trong hồ sơ dự án) thay vì hỏi `information_schema` liên tục.
- Chú ý **dialect**: hàm JSON của PostgreSQL, Standard SQL của BigQuery, `TOP` của T-SQL... không dùng lẫn.

## 5b. Dữ liệu cá nhân và dấu vết (đường này không có audit của engine)
- **Trước khi chạm dữ liệu**: hỏi người dùng cột nhạy cảm (PII) nếu dự án chưa có `policy.json` (như bước 3 của `pbi-analysis`); chưa rõ thì coi mọi cột định danh cá nhân (tên, liên hệ, giấy tờ, địa chỉ, số tài khoản) là nhạy cảm.
- Khám phá ưu tiên **metadata và số tổng hợp** (đếm, min/max, phân bố) hơn dòng thô.
- Chỉ lấy **mẫu dòng nhỏ** khi thật cần để hiểu định dạng, chọn rõ tên cột không nhạy cảm; không `SELECT *` trên bảng có hoặc có thể có PII.
- **Ghi lại** các câu truy vấn đã chạy (câu lệnh, thời điểm, số dòng trả về; không ghi dữ liệu) vào hồ sơ dự án, vì engine không ghi audit cho đường này.

## 6. Nếu buộc phải viết script nối CSDL
- Thư viện thuần Python cho PostgreSQL: `pg8000` (không cần thư viện C) hoặc `psycopg2`; nguồn khác dùng driver chính thức tương ứng.
- Chạy tiến trình proxy bằng `subprocess` với **đối số dạng danh sách**, không chạy qua shell.
- **Không chờ cố định** (không `sleep` một con số): thăm dò cổng cục bộ đã sẵn sàng, có **hạn chờ**; quá hạn thì báo lỗi.
- Trong khối `finally`: **đóng kết nối và dừng tiến trình proxy** — cả hai, dù truy vấn lỗi hay không.
- Chỉ gửi câu lệnh đọc đã soát; không nhận chuỗi SQL tùy ý từ người dùng rồi thực thi nguyên văn. Giá trị từ người dùng đi qua **tham số ràng buộc** của driver, không ghép chuỗi.
- Đặt **timeout câu lệnh** phía CSDL hoặc phiên để truy vấn chậm không treo cả luồng.

## 7. Trình bày kết quả
- Bảng Markdown (như `pbi-analysis`), giữ Unicode tiếng Việt; nói rõ khi kết quả bị cắt theo giới hạn dòng.
- Giải nghĩa cột theo **từ điển dữ liệu của dự án** (`DATA_DICTIONARY`), không đoán nghĩa từ tên cột.
- Số tổng hợp lấy từ nguồn dùng để **tie-out** với model (mục A của `pbi-review`).

## Nguồn
- `skills/pbi-model/references/kpim/sql-best-practices.md` (pre-aggregate, bảo mật)
- `skills/pbi-analysis/SKILL.md` (read-only mặc định, agent không mở file bí mật)
- https://learn.microsoft.com/sql/relational-databases/sql-server-index-design-guide (khi cần soi truy vấn chậm ở nguồn SQL Server)
