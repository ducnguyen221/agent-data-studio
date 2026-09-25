---
name: pbi-design
description: "Design Power BI report pages before any PBIR is written: clone-from-approved-page first; with no approved page, pick Microsoft archetypes and the KPIM page standard (1280x720 grid, KPI/chart/detail rows, modern visuals, conditional colors) and write a Design Brief with tone, page plan, visuals and bindings. Use when: plan or redesign a report page or dashboard, choose chart types, layout, color, typography or theme, apply the KPIM brand, critique a page design, pick a template kit to clone. Not: writing PBIR files, validate/reload/screenshot loop -> pbi-build; measures or model changes -> pbi-model; querying data -> pbi-analysis; independent review of a finished page -> pbi-review."
metadata:
  group: powerbi
  chain_position: 4
  status: stable
  sources:
    - "kpim: OpcOS kpim-skills powerbi-report-design (clone-and-rebind, tokens)"
    - "kpim: page standard measured 2026-09-16; feedback clone-not-generate"
    - "microsoft: plugins/powerbi-authoring/skills/powerbi-report-design/{references/**,assets/base.json}@v0.3.16 (verbatim, not yet distilled)"
---

# pbi-design — ý tưởng & nội dung thiết kế trang

## Mục đích
Chốt **trang sẽ trông thế nào và vì sao** trước khi đụng PBIR: ưu tiên clone trang đã duyệt; không có mẫu
thì archetype Microsoft + chuẩn KPIM → **Design Brief** để `pbi-build` dựng đúng một lần.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`pbi-analysis`](../pbi-analysis/SKILL.md) | Số đã soát, biết measure/dimension có thật |
| Sau | [`pbi-build`](../pbi-build/SKILL.md) | Design Brief đã được user duyệt |
| Liên quan | [`pbi-review`](../pbi-review/SKILL.md) · [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | Soát thiết kế · kit/thiết kế cũ (`/pbi-recall`, `/pbi-scan`) |

## Must / Prefer / Avoid
- **Must** — **clone-from-approved-page**: không bao giờ tự nghĩ toạ độ, `objects`, màu, font từ số 0.
- **Must** — bám chuẩn KPIM: canvas 1280×720, lề 30, gutter 20, header 80, KPI y100 h110, chart y225 h235, detail y475 h230.
- **Must** — chỉ visual hiện đại (`cardVisual`, `pivotTable`, `tableEx`, `azureMap` + chart chuẩn của kit).
- **Must** — card KPI có reference label + màu điều kiện `#42A19F` / `#D64554` **theo ý nghĩa chỉ số** (chi phí/tỉ lệ rời bỏ: cao là xấu).
- **Must** — mọi binding trong Brief là field **có thật** trong model (đã `describe_table`).
- **Prefer** — một câu hỏi phân tích chính mỗi trang; archetype rõ ràng (executive summary, operational monitor…).
- **Prefer** — measure của trang gom bảng `Công Thức`, `displayFolder` = tên trang.
- **Prefer** — matrix đặt trên `shape` panel có `z` thấp hơn; style container: nền trắng, bo 5, viền ThemeDataColor 0 −10 %, padding 15, title 12 pt bold ColorId 2.
- **Avoid** — bỏ theme / panel / bookmark "cho gọn"; dùng visual đời cũ cho trang mới.
- **Avoid** — thiết kế khi chưa có số đã soát (dễ thiết kế cho measure không tồn tại).

## Quy trình

| # | Bước | Đọc | Cổng kiểm |
|---|---|---|---|
| 1 | **Tìm mẫu đã duyệt**: trang trong chính báo cáo → kit Knowledge Dir → `report-templates/kpim-business-light/` (gốc repo) | [clone-not-generate](references/kpim/clone-not-generate.md) | Có nguồn clone, hoặc ghi rõ "không có mẫu" |
| 2 | **Hiện trạng** (redesign): `distill_report_design` / `/pbi-scan` | MS [brownfield](references/microsoft/brownfield.md) | Biết trang/visual/theme hiện có |
| 3 | **Không có mẫu** → chọn tone, signature, archetype cho từng trang | MS [tone-catalog](references/microsoft/tone-catalog.md) · [signatures](references/microsoft/signatures.md) · [archetype-composition](references/microsoft/archetype-composition.md) · `archetypes/*` | Mỗi trang 1 archetype + 1 câu hỏi chính |
| 4 | **Bố cục theo chuẩn KPIM**: đặt vùng header/KPI/chart/detail, chọn chart | [design-standard](references/kpim/design-standard.md) · MS [layout](references/microsoft/layout.md) · [chart-selection](references/microsoft/chart-selection.md) | Toạ độ khớp lưới; mỗi chart có lý do chọn |
| 5 | **Màu, chữ, tương tác, accessibility** | [design-standard](references/kpim/design-standard.md) §3–6 · MS [color](references/microsoft/color.md) · [typography](references/microsoft/typography.md) · [interactivity](references/microsoft/interactivity.md) · [accessibility](references/microsoft/accessibility.md) | Màu điều kiện đúng chiều ý nghĩa; tương phản đạt |
| 6 | **Viết Design Brief** → user duyệt | MS [design-brief](references/microsoft/design-brief.md) · [pre-flight-checklist](references/microsoft/pre-flight-checklist.md) | Brief có: trang · archetype · visual + vị trí + binding thật · measure cần thêm · nguồn clone; user "ok" |
| 7 | Bàn giao [`pbi-build`](../pbi-build/SKILL.md); measure còn thiếu → [`pbi-model`](../pbi-model/SKILL.md) | — | Không còn câu hỏi mở trong Brief |

KPIM ↔ Microsoft mâu thuẫn: **chuẩn thương hiệu/lưới KPIM thắng** về hình thức; Microsoft thắng về cơ chế PBIR.

## References

### KPIM — `references/kpim/`
| File | Đọc khi |
|---|---|
| [clone-not-generate.md](references/kpim/clone-not-generate.md) | Bước 1 — luật sắt, nguồn clone, 4 thứ được đổi |
| [design-standard.md](references/kpim/design-standard.md) | Bước 4–5 — số đo lưới, visual, style, màu điều kiện, 5 pattern |

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
