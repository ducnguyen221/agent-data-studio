---
description: Quét 1 file Power BI (.pbip) → chưng cất thành BỘ template kit tái dùng (mọi trang đáng tái dùng, không chỉ 1 trang)
---

Dựng bộ template kit từ báo cáo Power BI: $ARGUMENTS

> Khác quy trình `pbi-scan` (chỉ **ghi hồ sơ thiết kế** để đọc) — quy trình này **tạo ra tài sản tái dùng**:
> từ 1 file .pbip ra một **bộ kit** mà `apply_template` (skill `pbi-build`) dùng lại được cho dự án sau.
> Khác `distill_template` (tool, làm **1 trang → 1 kit**) — lệnh này điều phối cho **cả báo cáo**.

## Luồng

1. `knowledge_status` — chưa thiết lập thì theo `commands/pbi-setup.md` trong repo. Trạm đang dùng là `workspace/` hoặc `ADS_DATA`.

2. Xác định `report_path` từ tham số: file `.pbip` hoặc folder `*.Report`.
   File `.pbix` → **KHÔNG** quét được: bảo user `Save As` sang `.pbip` (Power BI Desktop →
   File → Save as → Power BI project). Xem skill `pbi-model`, mục PBIP-first.

3. `distill_report_design(report_path, project=<tên dự án hoặc tên báo cáo>)`
   → `REPORT_CATALOG.md` + `DESIGN.md` + theme. Đây là **bản đồ** để biết có bao nhiêu trang
   và trang nào đáng tái dùng.

4. **Chọn trang** — không distill bừa cả báo cáo. Trình cho user danh sách trang kèm số visual
   và đề xuất giữ lại trang nào, theo tiêu chí:
   - trang có **hệ thiết kế rõ** (layout nhất quán, dùng theme, nhiều loại visual khác nhau)
   - trang **lặp lại được** ở dự án khác (tổng quan KPI, phân tích theo chiều, chi tiết giao dịch)
   - **bỏ** trang nháp, trang chỉ có 1–2 visual, trang phụ thuộc dữ liệu quá đặc thù,
     và trang **mồ côi** (có thư mục nhưng không có trong `pages.json`)
   Chờ user chốt danh sách trước khi chạy bước 5.

5. Với **mỗi** trang đã chốt → `distill_template(report_path, page=<tên trang>,
   out_dir=<kho-bộ>/<slug-vai-trò>, kit_name=<slug-vai-trò>)`.

   ⚠️ **`out_dir` phải KHÁC NHAU cho từng trang.** `distill_template` ghi `kit.json`,
   `blueprint.md`, `_page.json` và `blocks/` **thẳng vào `out_dir`** — đưa cùng một `out_dir`
   cho nhiều trang thì trang sau **đè mất** trang trước, và cuối cùng chỉ còn đúng 1 kit.
   `kit_name` chỉ đổi metadata, không đổi nơi ghi.

   Cấu trúc đúng:
   ```
   <kho-bộ>/
     tong-quan/        kit.json · blueprint.md · _page.json · blocks/
     phan-tich-chieu/  kit.json · blueprint.md · _page.json · blocks/
     chi-tiet/         …
   ```

   `sanitize` **mặc định đã là True** — đừng tắt trừ khi user nói rõ kit chỉ dùng nội bộ.

   Sau mỗi lần gọi, **kiểm** `<kho-bộ>/<slug>/kit.json` tồn tại rồi mới sang trang kế —
   phát hiện ngay nếu lỡ ghi đè, thay vì đến cuối mới thấy thiếu kit.

6. **Gom thành bộ** — viết `README.md` ở thư mục cha của các kit, mô tả:
   - nguồn chưng cất đã khử thông tin riêng, ngày tạo và số kit
   - **hệ thiết kế chung**: palette, font, canvas size, quy ước đặt visual (lấy từ `DESIGN.md` bước 3;
     đối chiếu skill `pbi-design`)
   - bảng: kit | vai trò | loại block | dùng khi nào
   - `theme.json` dùng chung (copy từ output bước 3) để dự án sau import thẳng vào Power BI

7. **Nơi ghi** — mặc định `templates/` trong trạm dữ liệu đang dùng (kho riêng, chưa công khai).
   Muốn đưa vào repo công khai (`report-templates/` của studio): phải đủ 4 điều kiện, thiếu 1 thì DỪNG và hỏi:
   - đã `sanitize=True`
   - user **duyệt rõ ràng** từng kit
   - agent tự đọc lại `kit.json` + `blocks/*.json` xác nhận không còn tên bảng/cột/khách hàng thật
   - có quyền phân phối công khai cho từng tài sản của kit (kể cả ảnh, font, theme và thành phần lấy từ báo cáo nguồn); khử thông tin riêng không thay thế quyền này
   Sau khi thêm vào repo, cập nhật chỉ mục mẫu theo quy trình hiện có và kiểm lại nội dung công khai.

8. `log_timeline(project, event="Chưng cất bộ kit từ <báo cáo>", link=<đường dẫn kho kit>)`.

## Báo cáo lại cho user

Bao nhiêu trang đã quét · bao nhiêu kit tạo ra (và **vì sao bỏ những trang còn lại**) ·
kho kit nằm ở đâu · câu lệnh mẫu để dùng lại: *"apply_template với kit `<đường dẫn>` dựng trang
mới trên model hiện tại, bind field phù hợp."*
