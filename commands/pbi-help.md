---
description: Liệt kê toàn bộ năng lực agent-data-studio (9 skill · 8 lệnh · 2 agent · 16 tool) + quy tắc định tuyến để agent tự chọn đúng quy trình
---

Trình bày năng lực agent-data-studio và định tuyến việc của user: $ARGUMENTS

> Đây là **điểm vào chuẩn** khi vừa cài xong trên máy mới, hoặc khi agent chưa rõ nên dùng gì.
> Nếu user có mô tả việc cần làm trong `$ARGUMENTS` → **bỏ qua phần liệt kê dài, đi thẳng
> mục "Định tuyến"** và đề xuất đúng 1 quy trình + câu lệnh cụ thể.

## Bước 0 — kiểm tra thực tế trước khi nói

Chạy `knowledge_status` và `list_templates`, rồi báo trạng thái thật:
- MCP có trả lời không → tool lỗi: server chưa bật hoặc chưa restart host sau khi cài; hướng dẫn user bật MCP của
  studio (on-demand) rồi mở phiên mới. Skill `data-*` vẫn dùng được khi không có MCP/Power BI.
- Knowledge Dir đã setup chưa → **chưa** thì việc đầu tiên là `/pbi-setup`.
- Có bao nhiêu kit dùng được.

## 9 skill — chuỗi từ dữ liệu tới báo cáo

| # | Skill | Nhóm | Vai | Đọc khi |
|---|---|---|---|---|
| 0 | `pbi-knowledge` | powerbi | Knowledge OS — lối vào & lối ra dự án | Đầu/cuối dự án, lưu/tra kinh nghiệm |
| 1 | `data-discovery` | data | Khảo sát, hỏi ngược, PROJECT.md + mindmap + dictionary, kế hoạch (không cần Power BI) | Đầu dự án, trước khi đụng model |
| 1′ | `data-mockup` | data | Bộ dữ liệu mẫu: spec → generator seed cố định → verify → Excel + Data Dictionary | Chưa có dữ liệu thật / lab / demo |
| 2 | `pbi-model` | powerbi | Power Query/M + mô hình hoá TMDL/DAX, ghi measure an toàn | Kết nối nguồn, model, measure |
| 3 | `pbi-analysis` | powerbi | Truy vấn & khai thác an toàn, chọn tầng công cụ, policy | Chạy DAX, soát số, xem metadata |
| 4 | `pbi-design` | powerbi | Clone-from-approved-page → archetype + chuẩn KPIM → Design Brief | Trước khi dựng trang |
| 5 | `pbi-build` | powerbi | Dựng & hoàn thiện trang, vòng Edit→Validate→Reload→Screenshot→Review, điều phối trọn gói | Dựng/sửa trang, làm end-to-end |
| 6 | `pbi-review` | powerbi | Review độc lập SQL/DAX/model/trang | Trước bàn giao/publish, số không khớp |
| 7 | `pbi-publish` | powerbi | Đưa lên Fabric/Service (**unverified**) | Khi user yêu cầu publish rõ ràng |

Trọn gói: `workflows/data-to-report.md` của studio. Bản đồ chi tiết: `skills/README.md`.

## 8 lệnh

| Lệnh | Dùng khi | Kết quả |
|---|---|---|
| `/pbi-help` | Không biết bắt đầu từ đâu | Chính trang này + định tuyến |
| `/pbi-setup` | **Lần đầu trên máy mới** | Khai báo Knowledge Dir (ngoài repo) — làm 1 lần |
| `/pbi-new <tên>` | Bắt đầu dự án mới | Folder dự án + đọc kinh nghiệm cũ + chạy chuỗi skill |
| `/pbi-scan <path.pbip>` | Muốn **hiểu** một báo cáo có sẵn | Hồ sơ thiết kế: mọi trang + theme + DESIGN.md + catalog |
| `/pbi-kit <path.pbip>` | Muốn **tái dùng** thiết kế của báo cáo có sẵn | Bộ template kit + theme dùng chung |
| `/pbi-done` | Kết thúc dự án | Checklist bàn giao + distill + timeline + đóng gói tri thức |
| `/pbi-pack [dự án]` | Muốn đúc kết bài học | Đóng gói vào 4 trục: tech-stack · industry · business-domain · powerbi |
| `/pbi-recall <từ khoá>` | "Đã từng làm gì tương tự chưa?" | Tra dự án cũ, bài học, kit tái dùng |

> Host không có slash-command (Antigravity, Codex) → gọi thẳng tên quy trình: *"chạy quy trình pbi-setup"*.
> Skill `pbi-knowledge` mô tả cùng luồng đó.

## 2 agent

| Agent | Vai |
|---|---|
| `pbi-knowledge-curator` | Thủ thư tri thức — `/pbi-pack`: rút bài học tái dùng, dedup, cập nhật INDEX + TIMELINE |
| `pbi-render-reviewer` | Reviewer độc lập đọc screenshot trang theo chuẩn KPIM (bước Review của `pbi-build`) |

## 16 tool MCP của engine

| Nhóm | Tool | Chức năng |
|---|---|---|
| **Khám phá** | `list_local_reports` · `list_tables` · `describe_table` | Báo cáo đang mở · bảng · cột + kiểu + measure |
| **Truy vấn** 🛡️ | `execute_dax_local` · `execute_dax_service` | DAX lên Desktop / Service — **luôn qua policy an toàn dữ liệu** |
| **Ghi model** | `add_measure_local` · `add_relationship_local` | Thử measure · quan hệ Many-to-One qua TOM (lưu bền: TMDL, skill `pbi-model`) |
| **Template** 🎨 | `list_templates` · `apply_template` · `distill_template` | Kit có sẵn · dựng trang mới từ kit · chưng cất trang đẹp thành kit |
| **Distill** | `distill_model_schema` · `distill_report_design` | Model → blueprint + ERD · quét trọn thiết kế báo cáo |
| **Knowledge OS** 🧠 | `knowledge_status` · `setup_knowledge` · `init_project` · `log_timeline` | Trạng thái · thiết lập · mở dự án · ghi dòng thời gian |

## Định tuyến — user nói gì thì chạy gì

| User nói đại ý | Chạy |
|---|---|
| "vừa cài xong", "bắt đầu thế nào" | `/pbi-setup` (nếu chưa) → `/pbi-new` |
| "phân tích bộ dữ liệu này", "làm báo cáo cho…" | `/pbi-new <tên>` → skill `data-discovery` |
| "chưa có dữ liệu", "tạo data mẫu để thực hành" | skill `data-mockup` |
| "kết nối nguồn", "thêm measure", "sửa quan hệ", "DAX chậm" | skill `pbi-model` (bulk/TMDL → Modeling MCP của Microsoft, bật on-demand) |
| "chạy câu DAX này", "cho tôi số…" | skill `pbi-analysis` — policy chặn `EVALUATE '<table>'`, viết `SUMMARIZECOLUMNS`/`TOPN` |
| "trang này nên trình bày thế nào", "redesign", "chọn chart" | skill `pbi-design` |
| "dựng trang mới đẹp như mẫu", "sửa visual", "validate/screenshot" | skill `pbi-build` (clone/`apply_template`, **không** tự vẽ layout) |
| "báo cáo này đang làm gì vậy", "giải thích thiết kế" | `/pbi-scan <path.pbip>` |
| "làm cho tôi cái giống báo cáo này", "lấy mẫu này dùng lại" | `/pbi-kit <path.pbip>` |
| "review measure/model/trang", "số không khớp" | skill `pbi-review` |
| "đưa lên Service/Fabric" | skill `pbi-publish` (unverified — xác nhận từng bước) |
| "xong rồi", "bàn giao" | `/pbi-done` |
| "trước đây làm cái này chưa" | `/pbi-recall <từ khoá>` |

## Hai luật không được quên

1. **Không tự vẽ layout từ đầu** — clone trang đã duyệt hoặc `apply_template` từ kit. Layout AI dựng từ số 0 luôn
   lệch; clone trang đã đẹp rồi rebind field thì đúng ngay.
2. **Dữ liệu thô không rời engine** — policy chặn dump cả bảng ở phía server, không phải gợi ý trong prompt.
   Muốn tắt: `POWERBI_AGGREGATE_ONLY=0` (và tự chịu trách nhiệm).

Chi tiết: `INDEX.md` và `AGENTS.md` ở gốc repo agent-data-studio. *(Không dùng link tương đối: file này được
copy sang thư mục lệnh của host.)*
