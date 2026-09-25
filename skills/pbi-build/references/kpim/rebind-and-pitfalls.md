---
title: Rebind toàn diện khi clone trang PBIR + bảng bẫy đã trả giá
measured_on: 2026-09-16 · Power BI Desktop 2.157 · PBIR · clone trang mẫu sang model khác
source: KPIM practice (bài học clone/rebind 16–17/09; ghi PBIR/TMDL)
---

# Rebind toàn diện & bẫy khi dựng trang

## 1. Binding nằm ở NHIỀU chỗ hơn `queryState`

Clone một trang rồi chỉ đổi `query.queryState` là **sót**. Đo trên trang thật (16/09): sau khi chỉ rebind
`queryState`, còn **90** chỗ sót ở `cardVisual`, **27** ở `pivotTable`, **8** ở combo chart — visual vẫn trỏ
tên bảng/cột cũ, Desktop báo lỗi hoặc hiện trống.

| Vị trí binding | Hay gặp ở | Ghi chú |
|---|---|---|
| `visual.query.queryState.<role>.projections[].field` (+ `queryRef`, `nativeQueryRef`) | mọi visual có dữ liệu | Chỗ duy nhất tool cũ rebind |
| `objects.*[].selector.metadata` | `cardVisual`, chart có định dạng theo series | Chuỗi `Bảng.Field` |
| `referenceLabel` / `referenceLabelDetail` (value + detail) | `cardVisual` | Measure so sánh của card |
| Biểu thức `Conditional` (`Cases[].Condition.Comparison.Left`) | màu điều kiện | Measure trong điều kiện |
| `expansionStates[].roles/levels` | `pivotTable` | Trạng thái mở rộng hàng |
| `query.sortDefinition.sort[].field` | chart, matrix | Sắp xếp |
| `filterConfig.filters[].field` | visual/page filter | Bộ lọc |
| `objects.image` / URL động theo field | `image`, table có hình | Nếu dùng field |

**Luật:** duyệt **toàn bộ cây object** tìm mọi node `SourceRef.Entity` / `Property` / chuỗi `Entity.Property`,
map theo bảng đổi tên; cuối cùng grep tên cũ trong thư mục trang mới phải = 0.

## 2. Sửa JSON trên OBJECT, không thay chuỗi
Thay chuỗi thô (`replace("Old", "New")`) đụng cả nhãn hiển thị, tên measure con trùng tiền tố, và làm hỏng JSON
khi tên có ký tự đặc biệt. **Parse JSON → sửa node → ghi lại** (UTF-8 không BOM, giữ thứ tự khoá).

## 3. Bẫy đã trả giá

| Bẫy | Hậu quả | Cách né |
|---|---|---|
| Tìm trang theo tên thư mục → trúng **trang mồ côi** (có trong `pages/` nhưng không có trong `pages.json`) | Sửa nhầm trang không hiển thị | Chỉ tìm trang có trong `pages.json` (`pageOrder`) |
| Ghi PBIR khi `.pbip` đang **mở** | Ctrl+S của user đè mất file vừa ghi | Bảo user đóng file (hoặc đóng không lưu rồi mở lại) trước khi ghi |
| Ghi measure bằng **TOM** rồi bảo user lưu | TOM không làm file dirty → Desktop không ghi → mất measure | Thử bằng TOM, **lưu bằng TMDL khi file đóng** (skill `pbi-model`) |
| Clone bookmark | Vỡ báo cáo (snapshot `explorationState`) | Bookmark để user tạo tay |
| Đường tạm dài (> 260 ký tự) khi copy thư mục trang | Python/Windows gãy giữa chừng | Dùng thư mục tạm ngắn |
| Theme sửa nhưng Desktop không nhận khi reload | Theme cache theo tên file | Đổi tên file theme (xem Microsoft `re-theming.md`) |
| Visual type sinh tay phức tạp (decompositionTree, scatter, textbox, what-if) | Schema sai, Desktop từ chối | Clone block có sẵn; đọc schema từ một `visual.json` thật |
| Tên cột có ký tự vô hình (U+200B) | Binding "đúng tên" vẫn không khớp | Lấy tên từ `describe_table`, không gõ lại |

## 4. Cấu trúc PBIR tối thiểu cần nhớ
- `definition/pages/pages.json` = `{pageOrder[], activePageName}`.
- Trang: `pages/<pid>/page.json` (name, displayName, `displayOption` FitToPage, 1280×720).
- Visual: `pages/<pid>/visuals/<vid>/visual.json` = `{name, position{x,y,z,height,width,tabOrder}, visual{visualType, query{queryState{<Role>:{projections:[…]}}}, objects, visualContainerObjects}}`.
- Field measure: `{field:{Measure:{Expression:{SourceRef:{Entity}},Property}}, queryRef, nativeQueryRef}`; cột: `Column` tương tự.
- Role thường gặp: card/slicer `Values` · line/column `Category` / `Series` / `Y` · matrix `Rows` / `Columns` / `Values`.
Chi tiết schema chuẩn: reference Microsoft `authoring.md`, `card.md`, `table.md`, `cartesian.md` cùng skill.
