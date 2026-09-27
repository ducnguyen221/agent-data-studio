---
name: pbi-design
description: "Design Power BI report pages before PBIR changes: start from a user-approved page or licensed kit, then record layout, visuals, bindings and style in a Design Brief. Without a usable sample, propose an archetype for approval. Use when: planning or redesigning a page, chart, layout, color, typography or theme. Not: PBIR writing and render checks -> pbi-build; model changes -> pbi-model; data queries -> pbi-analysis; independent review -> pbi-review."
metadata:
  group: powerbi
  chain_position: 4
  status: stable
  sources:
    - "agent-data-studio: report design practice"
    - "microsoft: plugins/powerbi-authoring/skills/powerbi-report-design/{references/**,assets/base.json}@v0.3.16 (verbatim, not yet distilled)"
---

# pbi-design — ý tưởng & nội dung thiết kế trang

## Mục đích
Chốt **trang sẽ trông thế nào và vì sao** trước khi đụng PBIR: ưu tiên clone trang đã duyệt; không có mẫu
thì chọn archetype Microsoft phù hợp và đề xuất lưới/theme trong **Design Brief** để người dùng duyệt trước khi `pbi-build` dựng.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`pbi-analysis`](../pbi-analysis/SKILL.md) | Số đã soát, biết measure/dimension có thật |
| Sau | [`pbi-build`](../pbi-build/SKILL.md) | Design Brief đã được user duyệt |
| Liên quan | [`pbi-review`](../pbi-review/SKILL.md) · [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | Soát thiết kế · kit/thiết kế cũ (`/pbi-recall`, `/pbi-scan`) |

## Bắt buộc / Ưu tiên / Tránh
- **Bắt buộc** — **clone-from-approved-page**: không bao giờ tự nghĩ toạ độ, `objects`, màu, font từ số 0.
- **Bắt buộc** — bám trang, kit hoặc quy chuẩn thương hiệu mà người dùng đã duyệt. Không tự áp lưới/màu của một tổ chức cho dự án khác.
- **Bắt buộc** — chỉ visual hiện đại (`cardVisual`, `pivotTable`, `tableEx`, `azureMap` + chart chuẩn của kit).
- **Bắt buộc** — card KPI có nhãn đối chiếu và màu điều kiện theo **ý nghĩa chỉ số** và theme đã duyệt (chi phí/tỉ lệ rời bỏ: cao là xấu).
- **Bắt buộc** — mọi binding trong Brief là field **có thật** trong model (đã `describe_table`).
- **Ưu tiên** — một câu hỏi phân tích chính mỗi trang; archetype rõ ràng (executive summary, operational monitor…).
- **Ưu tiên** — measure của trang gom bảng `Công Thức`, `displayFolder` = tên trang.
- **Ưu tiên** — matrix đặt trên `shape` panel có `z` thấp hơn; style container theo kit/theme được duyệt, không tự gán token thương hiệu khác.
- **Tránh** — bỏ theme / panel / bookmark "cho gọn"; dùng visual đời cũ cho trang mới.
- **Tránh** — thiết kế khi chưa có số đã soát (dễ thiết kế cho measure không tồn tại).

## Quy trình

| # | Bước | Đọc | Cổng kiểm |
|---|---|---|---|
| 1 | **Tìm mẫu được phép dùng**: trang trong chính báo cáo → kit riêng của người dùng → kit công khai đã xác nhận quyền phân phối | [clone-not-generate](references/kpim/clone-not-generate.md) | Có nguồn clone được duyệt, hoặc ghi rõ "không có mẫu" |
| 2 | **Hiện trạng** (redesign): `distill_report_design` / `/pbi-scan` | MS [brownfield](references/microsoft/brownfield.md) | Biết trang/visual/theme hiện có |
| 3 | **Không có mẫu** → chọn tone, signature, archetype cho từng trang | MS [tone-catalog](references/microsoft/tone-catalog.md) · [signatures](references/microsoft/signatures.md) · [archetype-composition](references/microsoft/archetype-composition.md) · `archetypes/*` | Mỗi trang 1 archetype + 1 câu hỏi chính |
| 4 | **Bố cục theo Brief hoặc kit được duyệt**: đặt vùng header/KPI/chart/detail, chọn chart | [design-standard](references/kpim/design-standard.md) chỉ khi người dùng chọn mẫu đó · MS [layout](references/microsoft/layout.md) · [chart-selection](references/microsoft/chart-selection.md) | Toạ độ khớp lưới đã duyệt; mỗi chart có lý do chọn |
| 5 | **Màu, chữ, tương tác, khả năng tiếp cận** | [design-standard](references/kpim/design-standard.md) chỉ khi áp mẫu đó · MS [color](references/microsoft/color.md) · [typography](references/microsoft/typography.md) · [interactivity](references/microsoft/interactivity.md) · [accessibility](references/microsoft/accessibility.md) | Màu điều kiện đúng chiều ý nghĩa; tương phản đạt |
| 6 | **Viết Design Brief có cấu trúc** → user duyệt | MS [design-brief](references/microsoft/design-brief.md) · [pre-flight-checklist](references/microsoft/pre-flight-checklist.md) | Brief có: trang · archetype · visual + vị trí + binding thật · measure cần thêm · nguồn clone; user "ok" |
| 7 | Bàn giao [`pbi-build`](../pbi-build/SKILL.md); measure còn thiếu → [`pbi-model`](../pbi-model/SKILL.md) | — | Không còn câu hỏi mở trong Brief |

Nếu tài liệu tham khảo mâu thuẫn, Brief/kit người dùng đã duyệt quyết định hình thức; tài liệu Microsoft quyết định cú pháp và cơ chế PBIR. Không dùng kit chưa được xác nhận quyền phân phối.

Với Brief nhiều visual hoặc nhiều trang, dùng contract có `generated_by: powerbi-report-design` (định danh định dạng của tài liệu Microsoft), `contract_version: 1` và `pages[].layout_contract`. Mỗi trang ghi kích thước canvas, các vùng lưới và vị trí từng visual; mô tả tự do chỉ giải thích thêm, không thay toạ độ bàn giao cho `pbi-build`. Nếu chỉ đổi một thuộc tính của một visual, Brief ngắn có thể đủ. Giữ nguyên tên key kỹ thuật để công cụ đọc được.

## Tài liệu tham khảo

### KPIM — `references/kpim/`
| File | Đọc khi |
|---|---|
| [clone-not-generate.md](references/kpim/clone-not-generate.md) | Bước 1 — luật sắt, nguồn clone, 4 thứ được đổi |
| [design-standard.md](references/kpim/design-standard.md) | Bước 4–5 — ví dụ một lưới/theme cụ thể, chỉ dùng khi người dùng chọn và có quyền |

### Microsoft (nguyên văn, v0.3.16) — `references/microsoft/`
| File | Đọc khi |
|---|---|
| [tone-catalog.md](references/microsoft/tone-catalog.md) · [signatures.md](references/microsoft/signatures.md) | Chọn giọng/dấu ấn thiết kế |
| [archetype-composition.md](references/microsoft/archetype-composition.md) + `archetypes/` ([executive-summary](references/microsoft/archetypes/executive-summary.md) · [operational-monitor](references/microsoft/archetypes/operational-monitor.md) · [analytical-canvas](references/microsoft/archetypes/analytical-canvas.md) · [comparative-benchmark](references/microsoft/archetypes/comparative-benchmark.md) · [narrative-story](references/microsoft/archetypes/narrative-story.md)) | Chọn/ghép archetype trang |
| [layout.md](references/microsoft/layout.md) · [chart-selection.md](references/microsoft/chart-selection.md) · [visual-cookbook.md](references/microsoft/visual-cookbook.md) | Bố cục, chọn chart, công thức visual |
| [color.md](references/microsoft/color.md) · [typography.md](references/microsoft/typography.md) · [assets/base.json](references/microsoft/assets/base.json) | Màu, chữ, theme gốc |
| [interactivity.md](references/microsoft/interactivity.md) · [accessibility.md](references/microsoft/accessibility.md) | Tương tác, accessibility |
| [brownfield.md](references/microsoft/brownfield.md) | Redesign báo cáo có sẵn |
| [design-brief.md](references/microsoft/design-brief.md) · [pre-flight-checklist.md](references/microsoft/pre-flight-checklist.md) · [anti-patterns.md](references/microsoft/anti-patterns.md) | Viết Brief, soát trước khi dựng |
| [SOURCE.lock.json](references/microsoft/SOURCE.lock.json) | Kiểm file nguyên văn (sha256) |

## Đổi tên skill Microsoft → studio

| Tên trong reference Microsoft | Skill studio |
|---|---|
| `powerbi-report-design` | `pbi-design` (skill này) |
| `powerbi-report-authoring` | [`pbi-build`](../pbi-build/SKILL.md) |
| `powerbi-report-planning` | [`data-discovery`](../data-discovery/SKILL.md) (yêu cầu) · [`pbi-build`](../pbi-build/SKILL.md) (điều phối) |
| `semantic-model-authoring` | [`pbi-model`](../pbi-model/SKILL.md) |
| `powerbi-report-management` | [`pbi-publish`](../pbi-publish/SKILL.md) |

Link tương đối bên trong file Microsoft (`../SKILL.md`…) theo cây upstream, có thể không mở được — tra bảng trên.

---
*Nguồn: KPIM practice + microsoft/skills-for-fabric v0.3.16 (MIT, tham chiếu nguyên văn; chưa distill vào SKILL.md).*
