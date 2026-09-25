---
name: pbi-knowledge
description: "Knowledge OS for data and Power BI projects: the entry and exit of every project. Set up a Knowledge Dir outside the repo, open a project, recall past projects and lessons before asking the user, scan report designs, distill reusable template kits, close a project with a handover checklist and pack reusable lessons into four axes (tech-stack, industry, business-domain, powerbi) with INDEX and TIMELINE. Use when: /pbi-help, /pbi-setup, /pbi-new, /pbi-scan, /pbi-kit, /pbi-done, /pbi-pack, /pbi-recall, save project knowledge, have we done something similar, start or finish a Power BI project. Not: discovery interviews and project documents -> data-discovery; building pages -> pbi-build; running queries -> pbi-analysis."
metadata:
  group: powerbi
  chain_position: 0
  status: stable
  sources:
    - "kpim: repo skill powerbi-knowledge"
    - "kpim: OpcOS data-bi skill pbi-knowledge + commands pbi-*"
---

# pbi-knowledge — Knowledge OS (lối vào & lối ra của mọi dự án)

## Mục đích
Giữ tri thức dự án **ngoài repo**, nạp kinh nghiệm cũ trước khi hỏi user, và đóng gói bài học tái dùng khi
kết thúc — để lần sau làm nhanh và đúng hơn.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Đầu chuỗi (lối vào) | skill này → [`data-discovery`](../data-discovery/SKILL.md) | `/pbi-new`: mở dự án, đọc kinh nghiệm cũ |
| Cuối chuỗi (lối ra) | [`pbi-publish`](../pbi-publish/SKILL.md) / [`pbi-review`](../pbi-review/SKILL.md) → skill này | `/pbi-done`, `/pbi-pack` |
| Xuyên suốt | [`pbi-design`](../pbi-design/SKILL.md) · [`pbi-build`](../pbi-build/SKILL.md) | `/pbi-scan`, `/pbi-kit`, `/pbi-recall` |

Chuỗi đầy đủ: `workflows/data-to-report.md` (gốc repo). Lệnh: `commands/pbi-*.md`. Agent đóng gói: `agents/pbi-knowledge-curator.md`.

## Must / Prefer / Avoid
- **Must** — gọi `knowledge_status` **trước mọi luồng**; chưa setup → dừng, hỏi user chọn folder (`/pbi-setup`).
- **Must** — mọi file dự án ghi vào `projects/<slug>/` của Knowledge Dir; **không bao giờ** vào repo.
- **Must** — `/pbi-new`: đọc `INDEX.md` + `TIMELINE.md` + `knowledge/` khớp domain **trước khi** hỏi user.
- **Must** — kit đưa vào repo công khai chỉ khi `sanitize=True` + user duyệt từng kit + tự đọc lại không còn tên thật.
- **Prefer** — `/pbi-pack` giao agent `pbi-knowledge-curator` (host không có subagent → tự làm đúng quy trình của agent).
- **Prefer** — dedup: cập nhật file tri thức cũ thay vì tạo trùng; mỗi bài học có **Why** + **How to apply**.
- **Avoid** — lưu số liệu cụ thể, chi tiết một lần, thứ tra lại được từ tài liệu dự án.
- **Avoid** — gợi ý commit `.env`, cấu hình Knowledge Dir, schema hay audit.

## Quy trình theo lệnh

| Lệnh | Bước chính | Cổng kiểm |
|---|---|---|
| `/pbi-setup` | `knowledge_status` → hỏi folder NGOÀI repo → `setup_knowledge(path)` → giải thích cấu trúc | `knowledge_status` báo đã setup |
| `/pbi-new <tên>` | `init_project` → recall kinh nghiệm → [`data-discovery`](../data-discovery/SKILL.md) | Có `projects/<slug>/` + tóm tắt kinh nghiệm cũ |
| `/pbi-scan <path>` | `.pbix` → bảo Save As `.pbip`; `distill_report_design` (+ `distill_model_schema`) | `design/` có REPORT_CATALOG + DESIGN + theme |
| `/pbi-kit <path>` | Scan → user chốt trang → `distill_template` từng trang, `out_dir` khác nhau → README bộ + theme | Mỗi `<slug>/kit.json` tồn tại |
| `/pbi-done` | Checklist: 4 artifact (PLAN · CHANGESET · VERIFICATION · HANDOFF), design/, schema, kit → `log_timeline` → `/pbi-pack` | Checklist đủ; báo cáo bàn giao ngắn |
| `/pbi-pack` | Curator: đọc INDEX/TIMELINE/knowledge → đọc dự án → rút bài học → dedup → ghi → cập nhật INDEX + TIMELINE | User xác nhận danh sách bài học |
| `/pbi-recall <từ khoá>` | INDEX → TIMELINE → grep `knowledge/` + `projects/*/PROJECT.md` + `design/DESIGN.md` | Trả lời kèm đường dẫn, hoặc nói thẳng chưa có |
| `/pbi-help` | Trạng thái thật + bản đồ 9 skill (`skills/README.md`) + định tuyến | Đề xuất đúng 1 quy trình khi user đã mô tả việc |

## References — `references/kpim/`

| File | Đọc khi |
|---|---|
| [knowledge-os.md](references/kpim/knowledge-os.md) | Mọi luồng — bảng 8 lệnh, cấu trúc Knowledge Dir, luật riêng tư, chuẩn file tri thức |

---
*Nguồn: KPIM practice (Knowledge OS của engine studio).*
