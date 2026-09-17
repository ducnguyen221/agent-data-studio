---
title: Pipeline thi công 9 khâu — Power BI end-to-end (điều phối trọn gói)
source: KPIM practice — gộp skill powerbi-pipeline (repo) và pbi-project-delivery/references/pipeline-execution.md (OpcOS); tên skill đổi sang studio
updated: 2026-09-17
---

# Pipeline 9 khâu — ai làm khâu nào

`pbi-build` giữ vai **điều phối** khi làm trọn gói: mỗi khâu giao đúng skill chủ, khâu nào cũng có cổng kiểm
chạy được. Bản chuỗi skill ở `workflows/data-to-report.md` (gốc repo).

**Tư thế: PBIP-first.** Đầu dự án bảo user *Save As* `.pbip` (bật preview "Power BI Project (.pbip) save option"
+ PBIR). Model = TMDL text, report = PBIR JSON — git-diff được, agent thao tác an toàn khi file đóng.

| Khâu | Việc | Skill chủ | Cổng kiểm |
|---|---|---|---|
| 0 | Khảo sát → tài liệu → kế hoạch (PROJECT.md, dictionary, Project_Management.xlsx) | `data-discovery` | User duyệt PROJECT.md + PLANNING |
| 1 | Kết nối dữ liệu (Power Query, M parameter, không credential trong M) | `pbi-model` | Refresh OK; row count từng bảng khớp kỳ vọng |
| 2 | Transform M (staging, ép kiểu tường minh) | `pbi-model` | `describe_table`: kiểu cột đúng |
| 3 | Mô hình hoá & quan hệ (star schema, date table phủ đủ) | `pbi-model` | `distill_model_schema` → ERD hình sao |
| 4 | Measure & cột tính (thử TOM, lưu TMDL) | `pbi-model` | `EVALUATE ROW("kq", [M])` + 1 số biết trước; mở lại file vẫn còn |
| 5 | Tổng hợp & truy vấn (policy aggregate-only, PII) | `pbi-analysis` | Audit không có `blocked` bất thường |
| 6 | Thiết kế trang (clone-from-approved-page, Design Brief) | `pbi-design` | User duyệt Brief |
| 7 | Dựng trang PBIR (clone + rebind toàn diện, file ĐÓNG) + vòng Edit→Validate→Reload→Screenshot→Review | `pbi-build` | `validate` sạch · reload không lỗi · screenshot được review · user nghiệm thu mắt |
| 8 | Tính năng nâng cao (tooltip, drill-through, field parameter, hierarchy; **bookmark để tay**) | `pbi-build` (+ `pbi-model` cho bảng tính) | Từng tính năng demo được trên Desktop |
| 9 | Review → publish → đóng dự án & tri thức | `pbi-review` → `pbi-publish` → `pbi-knowledge` | Review không còn Blocker; artifact đủ 4; `/pbi-done` |

## Khâu 7 chi tiết — dựng trang
- **Không bao giờ dựng layout từ đầu.** Nguồn clone: trang đã duyệt → kit (`list_templates` → `apply_template`) → Brief.
- Field bind phải **tồn tại** (kiểm bằng `describe_table` trước).
- Rebind phủ **mọi** vị trí binding, sửa trên **object JSON** — danh sách ở `rebind-and-pitfalls.md`.
- Trang mới đăng ký trong `pages.json` (`pageOrder`); trang không có trong `pages.json` là trang mồ côi.

## Khâu 8 chi tiết
- Làm được bằng file: page tooltip (`page.json` `pageBinding` type Tooltip) · drill-through (`pageBinding` type
  Drillthrough + filter đích) · field parameter / what-if (bảng tính, qua `pbi-model`) · hierarchy cho drill-down.
- **Bookmark: để tay.** Clone bookmark từng vỡ báo cáo (snapshot `explorationState`). Dựng các visual xếp chồng,
  hướng dẫn user bấm tạo bookmark trong Desktop.

## Khâu 9 — artifact & tri thức
Mỗi dự án đủ 4 artifact: **PLAN** (trước khi làm) · **CHANGESET** (model/report đổi gì) · **VERIFICATION** (cổng
kiểm từng khâu + audit) · **HANDOFF** (cách refresh/publish + việc tay còn lại).
- `distill_model_schema` + `distill_report_design` → `projects/<slug>/design/` trong Knowledge Dir; `log_timeline`.
- Trang đẹp được duyệt → `distill_template` (hoặc `/pbi-kit`) thành kit tái dùng.
- Bài học tái dùng → `/pbi-pack` (agent `pbi-knowledge-curator`).

## Nguyên tắc xuyên suốt
1. **Thứ tự là bắt buộc** — không viết measure khi model chưa chốt; không dựng trang khi measure chưa kiểm.
2. **Mỗi khâu một cổng kiểm chạy được** — không có bằng chứng = khâu chưa xong.
3. **Ghi PBIR và TMDL chỉ khi file `.pbip` ĐÓNG**; TOM chỉ để thử (không làm file dirty).
4. **Không interleave ghi từ hai MCP** — xong `SaveChanges` bên này mới quay lại bên kia.
5. **Dữ liệu thô ở lại engine** — số vào chat là kết quả tổng hợp.
6. **Hỏi PII đầu dự án** — cột nhạy cảm → `policy.json` trước khi chạm dữ liệu.
