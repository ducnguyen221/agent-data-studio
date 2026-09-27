# Power BI — bản đồ kiến thức cho agent

> Dùng tám nhóm chủ đề dưới đây để xác định khái niệm cần tra cứu. Hướng dẫn DAX, Power Query M và SQL nằm ở skill `pbi-model`: `../../../pbi-model/references/kpim/`.

## Tám nhóm khái niệm
1. **Nền tảng** — phân biệt Power BI Desktop, Service và Report Server; tệp PBIX/PBIP/PBIR; báo cáo, dashboard, semantic model, workspace, app và giấy phép Free/Pro/PPU/Premium/Fabric capacity.
2. **Chuẩn bị dữ liệu (Power Query)** — lấy dữ liệu (Get Data), các bước biến đổi bằng M (Applied Steps), chế độ Import/DirectQuery/Direct Lake/kết nối trực tiếp, Reference/Duplicate, Merge/Append, tham số, mức riêng tư, query folding và làm mới tăng dần. → xem `pbi-model` → `m-best-practices.md`.
3. **Mô hình dữ liệu** — bảng fact/dimension, lược đồ sao/bông tuyết/galaxy, hạt dữ liệu (grain), khóa chính/ngoại, bội số và hướng lọc quan hệ, quan hệ hoạt động/không hoạt động (`USERELATIONSHIP`), many-to-many, bảng cầu nối, dimension nhiều vai trò và bảng ngày. → xem `pbi-model` → `dax-best-practices.md` §3.
4. **Tính toán DAX** — measure tường minh/ngầm, cột/bảng tính, ngữ cảnh dòng và lọc, chuyển ngữ cảnh, `CALCULATE`/`CALCULATETABLE`, `FILTER`, `ALL`/`REMOVEFILTERS`/`ALLSELECTED`/`ALLEXCEPT`/`KEEPFILTERS`, tính theo thời gian, nhóm tính toán, biến `VAR` và UDF. → xem `pbi-model` → `dax-best-practices.md`.
5. **Trực quan hóa** — thẻ số, bảng ma trận, bộ lọc, định dạng có điều kiện, tooltip, drill-through/drill-down, bookmark, tham số trường/số, ngăn chọn, đồng bộ slicer, bố cục di động, báo cáo phân trang và biểu đồ waterfall/combo/scatter. → dựng qua kit `report-templates/kpim-business-light` + `apply_template` khi có quyền dùng kit.
6. **Power BI Service** — gateway cho nguồn tại chỗ, lịch/làm mới tăng dần, dataflow, datamart, OneLake, gắn nhãn Promoted/Certified, quy trình triển khai, xuất bản/chia sẻ, quyền Build và nhóm người xem app.
7. **Bảo mật** — RLS tĩnh/động, OLS, vai trò workspace, quyền từng mục, nhãn nhạy cảm, `USERPRINCIPALNAME`/`USERNAME`/`CUSTOMDATA`, Microsoft Entra ID và khách B2B; tài khoản ứng dụng chỉ nên có quyền cần thiết.
8. **Tối ưu hiệu năng** — Performance Analyzer, DAX query view, VertiPaq, giảm cardinality, mô hình kết hợp, bảng tổng hợp, DAX Studio, VertiPaq Analyzer và chế độ columnstore/batch mode.

## Thứ tự học
Power Query và kiểu dữ liệu → mô hình sao, quan hệ và bảng ngày → ngữ cảnh DAX, `CALCULATE` và measure → trang báo cáo → làm mới, RLS và xuất bản trên Service → tối ưu hiệu năng.

## Vận hành (governance) — lưu ý thực chiến
- **Gateway**: cần cho refresh nguồn on-prem từ Service; standard (enterprise, chia sẻ) vs personal.
- **Development lifecycle**: Dev → Test → Prod qua **Deployment pipeline**; PBIP + git để version control.
- **Report Server (on-prem)**: bản Developer free; thiếu Dashboard/Scorecard/Subscription so với Service; RLS 2 lớp.
- **SSRS/paginated**: cho báo cáo in ấn/pixel-perfect; kết hợp Power BI cho tương tác.
- **Power Query vs DAX**: biến đổi/chuẩn hóa dữ liệu → làm ở **Power Query** (fold về nguồn); tính toán theo ngữ cảnh báo cáo → **DAX measure**. Không nhồi logic nghiệp vụ nặng vào DAX nếu Power Query/SQL làm được rẻ hơn.

## Nguồn sâu hơn
skill `pbi-model` (`dax-best-practices.md` · `m-best-practices.md` · `sql-best-practices.md` · `gotchas.md`) · Microsoft Learn (learn.microsoft.com/power-bi, /dax, /power-query).
