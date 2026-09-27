# Ghi nguồn asset KPIM

Agent Data Studio có kèm một số asset do **KPIM ([kpim.vn](https://kpim.vn))** xây dựng. KPIM chia sẻ các asset này để cộng đồng tham khảo khi học và làm dự án dữ liệu.

| Asset | Vị trí trong repo | Hồ sơ nguồn |
|---|---|---|
| Hồ sơ bốn bộ dữ liệu mẫu `Data KPIM Mart`, `Data KPIM Bank`, `Data KPIM HR`, `Data KPIM Marketing` | [`skills/data-mockup/references/kpim/kpim-datasets/`](skills/data-mockup/references/kpim/kpim-datasets/README.md) | [PROVENANCE.md](skills/data-mockup/references/kpim/kpim-datasets/PROVENANCE.md) |
| Kit trang báo cáo Power BI `kpim-business-light` | [`report-templates/kpim-business-light/`](report-templates/kpim-business-light/README.md) | [PROVENANCE.md](report-templates/kpim-business-light/PROVENANCE.md) |
| Workbook kế hoạch mẫu `Project_Management.xlsx` | [`templates/documents/`](templates/documents/) | [PROVENANCE.md](templates/documents/PROVENANCE.md) |

## Khi dùng lại

Vui lòng ghi nguồn, ví dụ: *“Asset của KPIM (kpim.vn), chia sẻ qua Agent Data Studio.”* Nếu bạn sửa asset, hãy ghi rõ phần đã sửa để người sau phân biệt với bản gốc.

## Quan hệ với giấy phép MIT

Bản quyền repo đứng tên Duc Nguyen (dòng copyright trong [`LICENSE`](LICENSE)). Các asset trên thuộc sở hữu của KPIM; KPIM cho phép sử dụng và phân phối chúng cùng repo theo [Giấy phép MIT](LICENSE), điều này được ghi ở phần đầu `LICENSE`. Vì vậy bạn được dùng, sửa và phân phối lại, miễn giữ thông báo bản quyền và nội dung giấy phép. Lời đề nghị ghi nguồn KPIM ở trên là đề nghị, không thêm điều kiện nào ngoài Giấy phép MIT. Tài liệu tham khảo của Microsoft đi kèm repo có giấy phép riêng, xem [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

## Các asset này không chứa gì

- Không kèm dữ liệu gốc: hồ sơ bộ dữ liệu chỉ mô tả cấu trúc bảng, grain, KPI và cạm bẫy thiết kế; bộ dữ liệu dạy học gốc không nằm trong repo.
- Kit báo cáo đã thay mọi tên bảng, cột, measure và nhãn bằng placeholder `TEMPLATE_*`; ảnh trong kit là tên placeholder, không kèm file ảnh.
- Workbook kế hoạch là ví dụ cho bối cảnh bán lẻ mẫu “KPIM Mart”, không chứa bản ghi giao dịch.

Người bảo trì chỉ thêm asset mới vào nhóm này khi thư mục của asset có `PROVENANCE.md`; `pack.ps1` từ chối đóng gói asset KPIM thiếu hồ sơ nguồn.
