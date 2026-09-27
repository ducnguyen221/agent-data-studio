---
name: pbi-knowledge
description: "Knowledge workflow for data and Power BI projects. Use the ignored basic workspace or selected external ADS_DATA station; keep engine and skills in the repository. Use when: setting up project storage, recalling lessons, scanning reports, managing private kits or closing projects with /pbi-* commands. Not: discovery interviews -> data-discovery; report-page editing -> pbi-build; data queries -> pbi-analysis."
metadata:
  group: powerbi
  chain_position: 0
  status: stable
  sources:
    - "agent-data-studio: project knowledge workflow"
---

# pbi-knowledge — Knowledge OS (lối vào & lối ra của mọi dự án)

## Mục đích
Giữ tri thức dự án trong **trạm dữ liệu** (`workspace/` mặc định, hoặc `ADS_DATA` ngoài repo), nạp kinh nghiệm cũ trước khi hỏi người dùng, và đóng gói bài học tái dùng khi
kết thúc — để lần sau làm nhanh và đúng hơn.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Đầu chuỗi (lối vào) | skill này → [`data-discovery`](../data-discovery/SKILL.md) | `/pbi-new`: mở dự án, đọc kinh nghiệm cũ |
| Cuối chuỗi (lối ra) | [`pbi-publish`](../pbi-publish/SKILL.md) / [`pbi-review`](../pbi-review/SKILL.md) → skill này | `/pbi-done`, `/pbi-pack` |
| Xuyên suốt | [`pbi-design`](../pbi-design/SKILL.md) · [`pbi-build`](../pbi-build/SKILL.md) | `/pbi-scan`, `/pbi-kit`, `/pbi-recall` |

Chuỗi đầy đủ: `workflows/data-to-report.md` (gốc repo). Lệnh: `commands/pbi-*.md`. Agent đóng gói: `agents/pbi-knowledge-curator.md`.

## Bắt buộc / Ưu tiên / Tránh
- **Bắt buộc** — gọi `knowledge_status` trước luồng tri thức; nếu chưa có cấu trúc, chạy `setup_knowledge()` tại trạm mặc định. Chỉ hỏi đường dẫn khi người dùng muốn trạm ngoài hoặc cấu hình đang xung đột.
- **Bắt buộc** — mọi file dự án ghi vào `<trạm>/projects/<slug>/`; với basic, `<trạm>` là `workspace/` bị Git bỏ qua. Không ghi dữ liệu vào phần source được Git theo dõi.
- **Bắt buộc** — `/pbi-new`: đọc `INDEX.md` + `TIMELINE.md` + `knowledge/` khớp domain **trước khi** hỏi user.
- **Bắt buộc** — kit đưa vào repo công khai chỉ khi có quyền phân phối từng tài sản, `sanitize=True`, người dùng duyệt và kiểm lại không còn dữ liệu riêng; sanitize không thay thế quyền.
- **Ưu tiên** — `/pbi-pack` giao agent `pbi-knowledge-curator` (host không có subagent → tự làm đúng quy trình của agent).
- **Ưu tiên** — cập nhật file tri thức cũ thay vì tạo trùng; mỗi bài học có **Vì sao** + **Cách áp dụng**.
- **Tránh** — lưu số liệu cụ thể, chi tiết một lần, thứ tra lại được từ tài liệu dự án.
- **Tránh** — gợi ý commit `config.env`, binding trạm, schema hay nhật ký truy vấn.

## Quy trình theo lệnh

| Lệnh | Bước chính | Cổng kiểm |
|---|---|---|
| `/pbi-setup` | `knowledge_status` → basic dùng `setup_knowledge()` tại `workspace/`; trạm riêng dùng `setup_knowledge(path)` sau khi xác nhận đường ngoài repo | `knowledge_status` báo đúng trạm đã chọn |
| `/pbi-new <tên>` | `init_project` → recall kinh nghiệm → [`data-discovery`](../data-discovery/SKILL.md) | Có `projects/<slug>/` + tóm tắt kinh nghiệm cũ |
| `/pbi-scan <path>` | `.pbix` → bảo Save As `.pbip`; `distill_report_design` (+ `distill_model_schema`) | `design/` có REPORT_CATALOG + DESIGN + theme |
| `/pbi-kit <path>` | Scan → user chốt trang → `distill_template` từng trang, `out_dir` khác nhau → README bộ + theme | Mỗi `<slug>/kit.json` tồn tại |
| `/pbi-done` | Checklist: 4 artifact (PLAN · CHANGESET · VERIFICATION · HANDOFF), design/, schema, kit → `log_timeline` → `/pbi-pack` | Checklist đủ; báo cáo bàn giao ngắn |
| `/pbi-pack` | Curator: đọc INDEX/TIMELINE/knowledge → đọc dự án → rút bài học → dedup → ghi → cập nhật INDEX + TIMELINE | User xác nhận danh sách bài học |
| `/pbi-recall <từ khoá>` | INDEX → TIMELINE → grep `knowledge/` + `projects/*/PROJECT.md` + `design/DESIGN.md` | Trả lời kèm đường dẫn, hoặc nói thẳng chưa có |
| `/pbi-help` | Trạng thái thật + bản đồ 9 skill (`skills/README.md`) + định tuyến | Đề xuất đúng 1 quy trình khi user đã mô tả việc |

## Tài liệu tham khảo — `references/kpim/`

| File | Đọc khi |
|---|---|
| [knowledge-os.md](references/kpim/knowledge-os.md) | Mọi luồng — bảng 8 lệnh, cấu trúc Knowledge Dir, luật riêng tư, chuẩn file tri thức |

---
*Nguồn: KPIM practice (Knowledge OS của engine studio).*
