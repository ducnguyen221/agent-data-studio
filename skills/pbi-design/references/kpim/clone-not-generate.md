---
title: Clone-from-approved-page — luật sắt khi làm trang PBIR
measured_on: 2026-09-16 · so sánh trực tiếp trang tự dựng vs trang clone trên cùng model, cùng agent
source: KPIM practice (feedback clone-not-generate + skill powerbi-report-design của KPIM)
---

# Clone trang đã duyệt, không tự dựng layout

## Vì sao
Trang PBIR agent **tự dựng từ số 0** nhìn nghiệp dư: spacing lệch, không theme, không panel. Cùng agent,
cùng model, **clone trang chuẩn rồi đổi field** thì được đánh giá tốt. Biến số duy nhất là clone vs generate.

## Luật sắt
Trước khi viết một `visual.json`, bạn phải đang **chép một visual.json có sẵn**. Đang tự nghĩ ra
`x/y/width/height`, `objects`, màu, font → **DỪNG**.

| Ý nghĩ | Thực tế |
|---|---|
| "Trang này đơn giản, tự xếp cũng được" | Đơn giản mà tự xếp vẫn lệch. Clone. |
| "Mẫu không có visual này" | Clone visual gần nhất, đổi `visualType` + role. |
| "Viết JSON mới nhanh hơn" | JSON mới = sai spacing/theme. Clone vừa nhanh vừa đẹp. |
| "Tôi sẽ tự khớp style bằng tay" | Không khớp được. Chép nguyên khối `objects`. |

## Nguồn clone (theo thứ tự ưu tiên)
1. **Trang đã được user duyệt** trong chính báo cáo/dự án (tốt nhất: cùng theme, cùng model).
2. **Kit** trong Knowledge Dir của user (`templates/` — kit riêng chưa sanitize).
3. **Kit đã xác nhận quyền sử dụng và phân phối**; kit nằm trong repo chưa tự động đồng nghĩa với quyền dùng cho mọi dự án. `sanitize=True` chỉ xử lý dữ liệu riêng, không chứng minh quyền tài sản.
4. Không có mẫu phù hợp → archetype Microsoft + lưới/theme đề xuất trong **Design Brief** để người dùng duyệt trước khi dựng.

Clone-source là **text kit** (`blueprint.md` + `blocks/*.json` verbatim) — không cần file `.pbip` mẫu.

## Được đổi gì khi clone một block
Chỉ **4 thứ**: `name` (GUID mới) · `position` (x/y/z/w/h theo blueprint hoặc lưới đã duyệt) ·
binding field (`query.queryState.<role>` **và mọi vị trí binding khác** — danh sách đầy đủ ở skill `pbi-build`
→ `references/kpim/rebind-and-pitfalls.md`) · `visualType` nếu đổi loại chart.
**Giữ nguyên** `visualContainerObjects` và `objects` — đó là thứ làm trang đẹp.

## Dấu hiệu sai — dừng lại và clone
- Toạ độ layout nghĩ ra từ không khí.
- "Trang mới" không bắt đầu bằng một bản sao.
- Sửa PBIR khi file `.pbip` đang **mở** (Ctrl+S của user sẽ đè mất).
- Bỏ theme / panel shape / bookmark "cho gọn".
