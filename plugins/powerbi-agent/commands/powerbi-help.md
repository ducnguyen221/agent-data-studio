---
description: Liệt kê toàn bộ năng lực powerbi-agent (lệnh · skill · 16 tool) + quy tắc định tuyến để agent tự chọn đúng quy trình
---

Trình bày năng lực powerbi-agent và định tuyến việc của user: $ARGUMENTS

> Đây là **điểm vào chuẩn** khi vừa cài xong trên máy mới, hoặc khi agent chưa rõ nên dùng gì.
> Nếu user có mô tả việc cần làm trong `$ARGUMENTS` → **bỏ qua phần liệt kê dài, đi thẳng
> mục "Định tuyến"** và đề xuất đúng 1 quy trình + câu lệnh cụ thể.

## Bước 0 — kiểm tra thực tế trước khi nói

Chạy `knowledge_status` và `list_templates`, rồi báo trạng thái thật:
- MCP có trả lời không → nếu tool lỗi: server chưa chạy, bảo user **restart host** (sau `install.ps1`
  bắt buộc restart) hoặc chạy `.venv\Scripts\python.exe scripts\cli.py list` để kiểm.
- Knowledge Dir đã setup chưa → **chưa** thì việc đầu tiên là `/powerbi-setup`.
- Có bao nhiêu kit dùng được.

## 8 lệnh

| Lệnh | Dùng khi | Kết quả |
|---|---|---|
| `/powerbi-help` | Không biết bắt đầu từ đâu | Chính trang này + định tuyến |
| `/powerbi-setup` | **Lần đầu trên máy mới** | Khai báo Knowledge Dir (ngoài repo) — làm 1 lần |
| `/powerbi-new <tên>` | Bắt đầu dự án mới | Folder dự án + đọc kinh nghiệm cũ + chạy quy trình phân tích |
| `/powerbi-scan <path.pbip>` | Muốn **hiểu** một báo cáo có sẵn | Hồ sơ thiết kế: mọi trang + theme + DESIGN.md + catalog |
| `/powerbi-kit <path.pbip>` | Muốn **tái dùng** thiết kế của báo cáo có sẵn | Bộ template kit + theme dùng chung |
| `/powerbi-done` | Kết thúc dự án | Checklist bàn giao + distill + timeline + đóng gói tri thức |
| `/powerbi-pack [dự án]` | Muốn đúc kết bài học | Đóng gói vào 4 trục: tech-stack · industry · business-domain · powerbi |
| `/powerbi-recall <từ khóa>` | "Đã từng làm gì tương tự chưa?" | Tra dự án cũ, bài học, kit tái dùng |

> Host không có cơ chế slash-command (Antigravity) → gọi thẳng tên quy trình:
> *"chạy quy trình powerbi-setup"*. Skill `powerbi-knowledge` mô tả cùng luồng đó.

## 4 skill

| Skill | Vai trò | Đọc khi |
|---|---|---|
| `kpim-analysis` | Pha **NGHIỆP VỤ** — khảo sát, hỏi ngược, tài liệu hóa, lập kế hoạch | Đầu dự án, trước khi đụng vào model |
| `powerbi-pipeline` | Pha **KỸ THUẬT** — 9 khâu Power Query → model → DAX → trang báo cáo | Khi bắt tay dựng |
| `powerbi-mcp` | **Sổ tay tra cứu** 16 tool + luật policy + phân vai với modeling-mcp | Khi không chắc gọi tool nào |
| `powerbi-knowledge` | **Cơ chế Knowledge OS** — dự án, đóng gói 4 trục, timeline, luật riêng tư | Khi thao tác với tri thức |

## 16 tool MCP

| Nhóm | Tool | Chức năng |
|---|---|---|
| **Khám phá** | `list_local_reports` · `list_tables` · `describe_table` | Báo cáo đang mở · bảng trong model · cột + kiểu + measure |
| **Truy vấn** 🛡️ | `execute_dax_local` · `execute_dax_service` | DAX lên Desktop / Service — **luôn qua policy an toàn dữ liệu** |
| **Ghi model** | `add_measure_local` · `add_relationship_local` | Tạo/sửa measure · quan hệ Many-to-One (qua TOM) |
| **Template** 🎨 | `list_templates` · `apply_template` · `distill_template` | Kit có sẵn · dựng trang mới từ kit · chưng cất trang đẹp thành kit |
| **Distill** | `distill_model_schema` · `distill_report_design` | Model → blueprint + ERD · quét trọn thiết kế báo cáo |
| **Knowledge OS** 🧠 | `knowledge_status` · `setup_knowledge` · `init_project` · `log_timeline` | Trạng thái · thiết lập · mở dự án · ghi dòng thời gian |

## Định tuyến — user nói gì thì chạy gì

| User nói đại ý | Chạy |
|---|---|
| "vừa cài xong", "bắt đầu thế nào" | `/powerbi-setup` (nếu chưa) → rồi `/powerbi-new` |
| "phân tích bộ dữ liệu này", "làm báo cáo cho…" | `/powerbi-new <tên>` → skill `kpim-analysis` |
| "báo cáo này đang làm gì vậy", "giải thích thiết kế" | `/powerbi-scan <path.pbip>` |
| "làm cho tôi cái giống báo cáo này", "lấy mẫu này dùng lại" | `/powerbi-kit <path.pbip>` → sau đó `apply_template` |
| "dựng trang mới đẹp như mẫu" | `list_templates` → `apply_template` (**không** để agent tự vẽ layout) |
| "thêm measure", "sửa quan hệ" | `add_measure_local` / `add_relationship_local`; **bulk/TMDL → giao `powerbi-modeling` của Microsoft** |
| "chạy câu DAX này", "cho tôi số…" | `execute_dax_local` — nhớ policy chặn `EVALUATE '<table>'`, viết `SUMMARIZECOLUMNS`/`TOPN` |
| "xong rồi", "bàn giao" | `/powerbi-done` |
| "trước đây làm cái này chưa" | `/powerbi-recall <từ khóa>` |

## Hai luật không được quên

1. **Không tự vẽ layout từ đầu** — luôn `apply_template` từ kit đã chứng minh. Layout AI dựng
   từ số 0 nhìn luôn sai lệch; clone trang đã đẹp rồi rebind field thì đúng ngay.
2. **Dữ liệu thô không rời engine** — policy chặn dump cả bảng ở phía server, không phải gợi ý
   trong prompt. Muốn tắt: `POWERBI_AGGREGATE_ONLY=0` (và tự chịu trách nhiệm).

Chi tiết đầy đủ: [INDEX.md](https://github.com/ducnguyen221/powerbi-agent/blob/main/INDEX.md) ·
luật làm việc: [AGENTS.md](https://github.com/ducnguyen221/powerbi-agent/blob/main/AGENTS.md).
*(URL tuyệt đối có chủ đích — file này được copy sang `~/.claude/commands/`, `~/.codex/prompts/`…
nên link tương đối sẽ trỏ vào thư mục lung tung của người dùng.)*
