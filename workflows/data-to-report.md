---
name: data-to-report
description: End-to-end chain from raw data and business documents to a reviewed, published Power BI report, with the skill, files to read and gate for every step.
skills: [pbi-knowledge, data-discovery, data-mockup, pbi-model, pbi-analysis, pbi-design, pbi-build, pbi-review, pbi-publish]
gates: [project-opened, discovery-approved, model-verified, numbers-checked, brief-approved, page-validated, review-clean, published, project-closed]
---

# Workflow: dữ liệu → báo cáo (trọn gói)

Đọc **một bước một lần**: mở SKILL.md của bước đang làm, chỉ mở reference khi bảng dưới chỉ tới. Mỗi bước có
**cổng kiểm** — chưa qua cổng thì không sang bước sau. Đường dẫn tính từ gốc repo.

```
pbi-knowledge ─► data-discovery ─┬─► pbi-model ─► pbi-analysis ─► pbi-design ─► pbi-build ─► pbi-review ─► pbi-publish ─► pbi-knowledge
  (mở dự án)                     └─► data-mockup ─┘ (chưa có dữ liệu)              ▲    │ vòng Edit→Validate→Reload→Screenshot→Review
                                                                                     └────┘
```

| # | Bước | Skill | File đọc | Cổng kiểm | Lệnh |
|---|---|---|---|---|---|
| 0 | Mở dự án, nạp kinh nghiệm cũ | `pbi-knowledge` | `skills/pbi-knowledge/SKILL.md` · `references/kpim/knowledge-os.md` | **project-opened** — có `projects/<slug>/`; đã tóm tắt kinh nghiệm cũ | `/pbi-setup` (lần đầu) · `/pbi-new <tên>` · `/pbi-recall` |
| 1 | Khảo sát, hỏi ngược, tài liệu hoá, kế hoạch | `data-discovery` | `skills/data-discovery/SKILL.md` · `references/kpim/discovery-process.md` · mẫu `templates/documents/` | **discovery-approved** — PROJECT.md đủ 5 bảng + 6 mindmap; Project_Management.xlsx có PLANNING; câu hỏi PII đã hỏi; user duyệt | — |
| 1′ | (Nhánh) Chưa có dữ liệu → bộ mẫu | `data-mockup` | `skills/data-mockup/SKILL.md` · `references/kpim/mockup-*-playbook.md` · `templates/documents/dataset/` | Verify 0 FAIL (ngoài `intentional_fail`); Excel có Data Dictionary | — |
| 2 | Kết nối, transform, mô hình hoá, measure | `pbi-model` | `skills/pbi-model/SKILL.md` · `references/kpim/{m,dax,sql}-best-practices.md` · `tom-tmdl-write.md` · MS `modeling-guidelines.md`, `tmdl-guidelines.md` | **model-verified** — row count khớp; kiểu cột đúng; ERD hình sao; mỗi measure `EVALUATE ROW` khớp số biết trước; mở lại file vẫn còn measure (TMDL) | — |
| 3 | Truy vấn an toàn, soát số | `pbi-analysis` | `skills/pbi-analysis/SKILL.md` · `references/kpim/mcp-tools.md` · `operations.md` | **numbers-checked** — `policy.json` đã khai PII; 1–2 con số đối chiếu `METRICS_CALCULATION` khớp; audit sạch | — |
| 4 | Thiết kế trang → Design Brief | `pbi-design` | `skills/pbi-design/SKILL.md` · `references/kpim/clone-not-generate.md` · `design-standard.md` · MS `design-brief.md`, archetypes | **brief-approved** — có nguồn clone hoặc archetype; toạ độ theo lưới KPIM; binding là field thật; user duyệt Brief | `/pbi-scan` (redesign) · `/pbi-recall` (kit cũ) |
| 5 | Dựng trang + vòng kiểm | `pbi-build` | `skills/pbi-build/SKILL.md` · `references/kpim/rebind-and-pitfalls.md` · MS `powerbi-report-author-cli.md`, `powerbi-desktop.md`, `screenshot-review.md` | **page-validated** — grep tên cũ = 0; `validate` 0 lỗi; reload OK; screenshot được `agents/pbi-render-reviewer.md` chấm ĐẠT; user nghiệm thu mắt | — |
| 6 | Review độc lập | `pbi-review` | `skills/pbi-review/SKILL.md` · `references/kpim/review-checklist.md` | **review-clean** — không Blocker/Major; tie-out khớp; RLS/PII ổn | — |
| 7 | Publish (khi user yêu cầu) | `pbi-publish` *(unverified)* | `skills/pbi-publish/SKILL.md` · `references/microsoft/common/*` | **published** — workspace đúng; LRO Succeeded; binding report ↔ model đích khớp; HANDOFF ghi refresh/quyền | — |
| 8 | Đóng dự án, đóng gói tri thức | `pbi-knowledge` | `skills/pbi-knowledge/SKILL.md` · `agents/pbi-knowledge-curator.md` | **project-closed** — 4 artifact (PLAN · CHANGESET · VERIFICATION · HANDOFF); design/ + schema distill; bài học đã pack; TIMELINE có mốc | `/pbi-done` · `/pbi-kit` · `/pbi-pack` |

## Quay lui

| Phát hiện ở | Quay về |
|---|---|
| Số không khớp (bước 3, 6) | `pbi-model` (measure/model) hoặc `data-discovery` (định nghĩa chỉ số sai) |
| Thiếu measure khi thiết kế/dựng (bước 4, 5) | `pbi-model` |
| Visual trống / rebind sót (bước 5) | `pbi-build` bước clone + rebind |
| Thiết kế không đạt (bước 5, 6) | `pbi-design` sửa Brief |

## Luật xuyên suốt
- Dữ liệu dự án chỉ ở Knowledge Dir / thư mục dữ liệu máy, **không bao giờ** trong repo.
- PBIR/TMDL chỉ ghi khi `.pbip` đóng; TOM chỉ để thử.
- Không tự dựng layout từ số 0; dữ liệu thô không rời engine.
- Mỗi bước để lại bằng chứng cổng kiểm trong `projects/<slug>/artifacts/VERIFICATION`.
