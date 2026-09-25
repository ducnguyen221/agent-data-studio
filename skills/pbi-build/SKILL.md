---
name: pbi-build
description: "Build and finish Power BI reports from an approved Design Brief: clone and fully rebind approved pages or template kits, write PBIR only while the .pbip is closed, run the Edit -> Validate -> Reload -> Screenshot -> Review loop with the Microsoft powerbi-report-author and powerbi-desktop CLIs, add tooltips and drill-through, and orchestrate an end-to-end Power BI project across the 9-step pipeline. Use when: build or edit a report page, add or format visuals, apply a template kit, validate PBIR, reload Desktop and screenshot, deliver a whole Power BI report end to end. Not: deciding what the page should look like -> pbi-design; measures, relationships, Power Query -> pbi-model; ad-hoc data questions -> pbi-analysis; independent review -> pbi-review; publishing to Fabric -> pbi-publish."
metadata:
  group: powerbi
  chain_position: 5
  status: stable
  sources:
    - "kpim: repo skill powerbi-pipeline + OpcOS kpim-skills pbi-project-delivery (pipeline-execution, knowledge map)"
    - "kpim: clone/rebind lessons 2026-09-16/17 (rebind sites, object edits, orphan pages, TOM not dirty)"
    - "microsoft: plugins/powerbi-authoring/skills/powerbi-report-authoring/references/*@v0.3.16 (verbatim, not yet distilled)"
---

# pbi-build — dựng & hoàn thiện báo cáo

## Mục đích
Biến Design Brief đã duyệt thành trang PBIR **chạy được, nhìn đúng**, qua vòng kiểm có screenshot; khi làm trọn
gói thì điều phối 9 khâu, giao đúng skill chủ ở từng khâu.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`pbi-design`](../pbi-design/SKILL.md) | Có Design Brief (nguồn clone, visual, vị trí, binding thật) |
| Sau | [`pbi-review`](../pbi-review/SKILL.md) | Trang qua vòng kiểm → review độc lập |
| Liên quan | [`pbi-model`](../pbi-model/SKILL.md) · [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | Thiếu measure · distill kit/timeline |

Làm trọn gói: `workflows/data-to-report.md` (gốc repo) + [pipeline-execution](references/kpim/pipeline-execution.md).
Agent review screenshot độc lập: `agents/pbi-render-reviewer.md` (gốc repo).

## Must / Prefer / Avoid
- **Must** — không dựng layout từ số 0: clone trang đã duyệt / kit, đổi `name`, `position`, binding, `visualType`; giữ `objects` + `visualContainerObjects`.
- **Must** — rebind **toàn diện**: `queryState` + `selector.metadata` + `referenceLabel` + `Conditional` + `expansionStates` + `sortDefinition` + `filterConfig` + `image`; grep tên cũ = 0.
- **Must** — sửa JSON **trên object** (parse → sửa node → ghi), không thay chuỗi thô.
- **Must** — ghi PBIR/TMDL chỉ khi `.pbip` **đóng**; tìm trang theo `pages.json` (tránh trang mồ côi).
- **Must** — không báo xong khi chưa qua **Validate → Reload → Screenshot → Review** sạch và user nghiệm thu mắt.
- **Prefer** — CLI Microsoft (T0) cho validate/reload/screenshot; MCP studio cho template/distill.
- **Prefer** — một thay đổi có render → một vòng kiểm; gom sửa nhỏ cùng trang vào một vòng.
- **Avoid** — clone bookmark (để user tạo tay); sửa theme mà không đổi tên file khi reload không nhận.
- **Avoid** — reload khi Desktop báo `hasUnsavedChanges: true` — hỏi user lưu/bỏ trước.
- **Avoid** — đường tạm dài > 260 ký tự khi copy thư mục trang.

## Quy trình dựng một trang

| # | Bước | Đọc | Cổng kiểm |
|---|---|---|---|
| 1 | Nạp Brief; kiểm field bind tồn tại (`describe_table`); measure thiếu → `pbi-model` | [rebind-and-pitfalls](references/kpim/rebind-and-pitfalls.md) §4 | Mọi binding có thật |
| 2 | `powerbi-desktop status` → chọn PID; user **đóng** file nếu cần ghi | MS [powerbi-desktop](references/microsoft/powerbi-desktop.md) | Biết PID; file đóng khi ghi |
| 3 | **Clone + rebind** (trang đã duyệt hoặc `apply_template` từ kit), đăng ký `pages.json` | [rebind-and-pitfalls](references/kpim/rebind-and-pitfalls.md) · MS [authoring](references/microsoft/authoring.md) | Grep tên bảng/cột cũ trong trang mới = 0 |
| 4 | Định dạng theo Brief & chuẩn KPIM (card, table, cartesian, shape, textbox…) | MS [formatting-overview](references/microsoft/formatting-overview.md) · [card](references/microsoft/card.md) · [table](references/microsoft/table.md) · [conditional-formatting](references/microsoft/conditional-formatting.md) | Toạ độ/khung/màu khớp Brief |
| 5 | **Validate**: `powerbi-report-author validate <Tên>.Report` | MS [powerbi-report-author-cli](references/microsoft/powerbi-report-author-cli.md) | 0 lỗi |
| 6 | **Reload**: `powerbi-desktop reload --pid <pid>` | MS [powerbi-desktop](references/microsoft/powerbi-desktop.md) | Reload không lỗi |
| 7 | **Screenshot + review** (tự review hoặc agent `pbi-render-reviewer`) | MS [screenshot-review](references/microsoft/screenshot-review.md) | Không còn lỗi hiển thị; có lỗi → quay lại bước 3/4 |
| 8 | Tính năng nâng cao nếu Brief có (tooltip, drill-through, slicer, filter) | MS [slicers](references/microsoft/slicers.md) · [filters](references/microsoft/filters.md) · [filter-pane](references/microsoft/filter-pane.md) · [pipeline-execution](references/kpim/pipeline-execution.md) §8 | Demo được trên Desktop |
| 9 | User nghiệm thu mắt → [`pbi-review`](../pbi-review/SKILL.md); trang đẹp → `/pbi-kit` | — | User "ok"; ghi CHANGESET/VERIFICATION |

## References

### KPIM — `references/kpim/`
| File | Đọc khi |
|---|---|
| [pipeline-execution.md](references/kpim/pipeline-execution.md) | Làm trọn gói — 9 khâu, skill chủ, cổng kiểm, artifact |
| [rebind-and-pitfalls.md](references/kpim/rebind-and-pitfalls.md) | Bước 1–3 — mọi vị trí binding, sửa trên object, bẫy đã trả giá, PBIR tối thiểu |
| [knowledge-map.md](references/kpim/knowledge-map.md) | Định vị nhanh khái niệm Power BI (8 cụm) → reference nào |

### Microsoft (nguyên văn, v0.3.16) — `references/microsoft/`
| File | Đọc khi |
|---|---|
| [authoring.md](references/microsoft/authoring.md) · [version-control.md](references/microsoft/version-control.md) | Cấu trúc PBIR, quy tắc sửa file, git |
| [powerbi-report-author-cli.md](references/microsoft/powerbi-report-author-cli.md) · [powerbi-desktop.md](references/microsoft/powerbi-desktop.md) | Validate, catalog, reload, screenshot |
| [screenshot-review.md](references/microsoft/screenshot-review.md) | Review ảnh render |
| [card.md](references/microsoft/card.md) · [table.md](references/microsoft/table.md) · [cartesian.md](references/microsoft/cartesian.md) · [map.md](references/microsoft/map.md) · [shape.md](references/microsoft/shape.md) · [textbox.md](references/microsoft/textbox.md) · [image.md](references/microsoft/image.md) | Schema + định dạng từng loại visual |
| [slicers.md](references/microsoft/slicers.md) · [filters.md](references/microsoft/filters.md) · [filter-pane.md](references/microsoft/filter-pane.md) | Lọc, slicer |
| [formatting-overview.md](references/microsoft/formatting-overview.md) · [formatting.md](references/microsoft/formatting.md) · [page-formatting.md](references/microsoft/page-formatting.md) · [conditional-formatting.md](references/microsoft/conditional-formatting.md) · [expressions.md](references/microsoft/expressions.md) | Định dạng, màu điều kiện, biểu thức |
| [theming.md](references/microsoft/theming.md) · [re-theming.md](references/microsoft/re-theming.md) · [color-strategy.md](references/microsoft/color-strategy.md) | Theme, đổi theme, chiến lược màu |
| [SOURCE.lock.json](references/microsoft/SOURCE.lock.json) | Kiểm file nguyên văn (sha256) |

## Đổi tên skill Microsoft → studio

| Tên trong reference Microsoft | Skill studio |
|---|---|
| `powerbi-report-authoring` | `pbi-build` (skill này) |
| `powerbi-report-design` | [`pbi-design`](../pbi-design/SKILL.md) |
| `powerbi-report-planning` | [`data-discovery`](../data-discovery/SKILL.md) (yêu cầu) · `pbi-build` (điều phối) |
| `semantic-model-authoring` · Modeling MCP | [`pbi-model`](../pbi-model/SKILL.md) |
| `powerbi-report-management` | [`pbi-publish`](../pbi-publish/SKILL.md) |

Link tương đối bên trong file Microsoft (`../SKILL.md#…`) theo cây upstream, có thể không mở được — tra bảng trên.

---
*Nguồn: KPIM practice + microsoft/skills-for-fabric v0.3.16 (MIT, tham chiếu nguyên văn; chưa distill vào SKILL.md).*
