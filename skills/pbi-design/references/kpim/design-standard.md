---
title: Chuẩn trang báo cáo KPIM — số đo được (canvas, lưới, visual, màu, style)
measured_on: 2026-09-16 · Power BI Desktop 2.157 · PBIR · theme KPIM_Business_Light
source: KPIM practice — đo trên trang mẫu đã được duyệt; gộp token cũ của skill powerbi-report-design (KPIM)
---

# Chuẩn trang KPIM (đo 16/09/2026)

Đây là **số đo**, không phải gợi ý thẩm mỹ. Dựng trang mới thì bám số này; lệch số phải có lý do ghi vào Design Brief.

## 1. Canvas & lưới

| Thông số | Giá trị |
|---|---|
| Canvas | **1280 × 720**, `displayOption` FitToPage |
| Lề trái/phải | **30** |
| Gutter giữa hai cột | **20** → hai cột bằng nhau rộng 600 (30 + 600 + 20 + 600 + 30 = 1280) |
| Header band | y 0, cao **80**, full width |
| Hàng KPI (card) | **y 100, cao 110** |
| Hàng chart | **y 225, cao 235** |
| Hàng chi tiết (bảng/matrix) | **y 475, cao 230** |
| Nền trang | `#DFE7F6` (token KPIM_Business_Light) |

Khoảng trắng dọc giữa các hàng là hệ quả của toạ độ trên — đừng "căn cho đều" bằng mắt.

## 2. Visual được phép

Chỉ **visual hiện đại**: `cardVisual` (card mới, có reference label) · `pivotTable` (matrix) · `tableEx` (table) ·
`azureMap`. Chart chuẩn (`lineClusteredColumnComboChart`, `clusteredBarChart`, `donutChart`, `scatterChart`),
`slicer`, `shape`, `textbox`, `image`, `bookmarkNavigator` dùng theo block của kit.
**Không dùng** visual đời cũ (`card` cũ, `multiRowCard`, `map` cũ) cho trang mới.

## 3. Style container (mọi visual có khung)

| Thuộc tính | Giá trị |
|---|---|
| Nền | trắng |
| Bo góc | **5** |
| Viền | `ThemeDataColor` ColorId 0, Percent **−10 %** |
| Padding | **15** |
| Tiêu đề | **12 pt, bold**, màu `ThemeDataColor` ColorId **2** |

Matrix/bảng chi tiết **đặt trên một `shape` làm panel** có `z` **thấp hơn** matrix (panel ở dưới, matrix ở trên).

## 4. Card KPI — `cardVisual` + reference label + màu điều kiện

- Mỗi card có **reference label** (so kế hoạch / cùng kỳ / kỳ trước).
- Màu điều kiện theo **ý nghĩa chỉ số**, không theo dấu số học:
  - tốt → `#42A19F` · xấu → `#D64554`;
  - chỉ số "càng cao càng tốt" (doanh thu, tỉ lệ đạt): ≥ ngưỡng là tốt;
  - chỉ số "càng thấp càng tốt" (chi phí, tỉ lệ rời bỏ, nợ xấu): ≥ ngưỡng là **xấu**.
- Cơ chế PBIR: entry `referenceLabelDetail` có `selector.data` (wildcard) + `detailFontColor` / `detailBackgroundColor`
  = biểu thức `Conditional.Cases[]` với `Comparison` (`ComparisonKind` 2 là ≥, 3 là <) so measure với `Literal` `"<n>D"`.
- Token màu nền đo trước đây (vẫn hợp lệ khi cần tô nền): đỏ chữ `#D64554` / nền `#efb5bb`; xanh chữ `#327977` / nền `#b3d9d9`.

## 5. Measure phục vụ trang

- Measure nằm trong bảng **`Công Thức`**, `displayFolder` **theo tên trang** báo cáo (mỗi trang một thư mục).
- `formatString` tường minh; phần trăm `0.0%`, tiền `#,0`.
- Ghi measure bền bằng TMDL khi file đóng — skill `pbi-model`.

## 6. Theme & palette KPIM_Business_Light

Palette dữ liệu: `#4874C5` `#E67D29` `#42A19F` `#FEBA02` `#A6A6A6` `#D64554`. Theme chạy ngay:
`templates/documents/theme.json` ở gốc repo. Import qua *View → Themes → Browse*; file JSON UTF-8 không BOM.

## 7. Năm pattern tái dùng (đừng đơn giản hoá bỏ đi)

1. Header band + tab điều hướng bằng `bookmarkNavigator`.
2. Visual xếp chồng theo lớp bookmark (cùng vị trí, bật/tắt bằng bookmark).
3. `cardVisual` reference label + màu điều kiện (mục 4).
4. Page tooltip (`pageBinding` type Tooltip).
5. `shape` panel nền dưới nhóm visual + theme custom.

Kit mẫu đã sanitize mang đủ 5 pattern: `report-templates/kpim-business-light/` ở gốc repo
(`blueprint.md` · `blocks/*.json` · `_page.json` · `kit.json`).
