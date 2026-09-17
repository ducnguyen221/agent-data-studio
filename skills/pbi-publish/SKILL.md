---
name: pbi-publish
description: "Publish Power BI work to Microsoft Fabric / Power BI Service: deploy a local .pbip (semantic model plus report) to a workspace, create or update report and semantic model items through the Fabric REST API with az rest, handle long-running operations, and rebind the report to the target semantic model. Status unverified: no test workspace yet, confirm every step with the user. Use when: publish or upload a report to Fabric, deploy a PBIP, update a report definition in a workspace, list or download workspace reports. Not: editing pages or visuals -> pbi-build; editing measures or TMDL locally -> pbi-model; review before publishing -> pbi-review; closing the project and packing knowledge -> pbi-knowledge."
metadata:
  group: powerbi
  chain_position: 7
  status: unverified
  sources:
    - "microsoft: plugins/powerbi-authoring/common/{COMMON-CLI,COMMON-CORE,ITEM-DEFINITIONS-CORE}.md@v0.3.16 (verbatim)"
    - "microsoft: role summary of plugins/powerbi-authoring/skills/powerbi-report-management/SKILL.md@v0.3.16 (not copied)"
---

# pbi-publish — đưa lên Fabric / Power BI Service

> ⚠️ **status: unverified** — chưa chạy thử trên workspace Fabric thật. Mỗi lệnh ghi lên Service phải được user
> xác nhận; kết quả phải kiểm lại trên giao diện Service.

## Mục đích
Chuyển báo cáo/model đã review từ `.pbip` cục bộ lên workspace, **không làm mất phần định nghĩa nào** và
report trỏ đúng semantic model đích.

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`pbi-review`](../pbi-review/SKILL.md) | Không còn Blocker/Major |
| Sau | [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | Đóng dự án: `/pbi-done`, `/pbi-pack` |
| Liên quan | [`pbi-build`](../pbi-build/SKILL.md) · [`pbi-model`](../pbi-model/SKILL.md) | Sửa nội dung PBIR / TMDL (không sửa ở skill này) |

## Must / Prefer / Avoid
(Tóm vai từ skill Microsoft `powerbi-report-management`; chi tiết lệnh ở `references/microsoft/common/`.)
- **Must** — skill này chỉ **vận chuyển** định nghĩa; mọi nội dung PBIR do [`pbi-build`](../pbi-build/SKILL.md), TMDL do [`pbi-model`](../pbi-model/SKILL.md).
- **Must** — sửa cục bộ **ở lại cục bộ**: chỉ publish khi user nói rõ publish/upload/deploy.
- **Must** — xác nhận workspace đích **một lần** đầu quy trình; hỏi user: publish kèm model cục bộ hay nối model có sẵn trong workspace; tạo mới hay cập nhật report.
- **Must** — `az rest` luôn có `--resource "https://api.fabric.microsoft.com"`; `getDefinition` luôn `?format=PBIR` (PBIR-Legacy → dừng, báo không hỗ trợ).
- **Must** — `updateDefinition` gửi **TẤT CẢ** part (sửa + không sửa), payload base64; API thay cả định nghĩa, thiếu part là mất part.
- **Must** — thao tác dài (202 Accepted) phải poll tới trạng thái cuối; dùng `--verbose` để lấy `x-ms-operation-id`.
- **Must** — sau khi có model đích: so mọi binding PBIR (`Entity`, `queryRef`, `nativeQueryRef`, filter) với tên trong TMDL đích; lệch thì remap qua `pbi-build`, không tương đương thì hỏi user.
- **Prefer** — `definition.pbir` dạng `byConnection` cho API (`byPath` chỉ cho local/git); ID tìm động qua List API.
- **Prefer** — xoá mềm thay vì xoá cứng; dọn file tạm (định nghĩa đã giải mã, payload) sau khi xong.
- **Avoid** — tự viết JSON PBIR từ trí nhớ; gửi chỉ part đã sửa; retry POST tạo mới sau khi đã nhận 202 (sinh bản trùng).
- **Avoid** — đọc secret/token bằng agent: xác thực do `az login` hoặc engine đọc `ADS_SECRETS_FILE`.

## Quy trình (chưa kiểm chứng — xác nhận từng bước với user)

| # | Bước | Đọc | Cổng kiểm |
|---|---|---|---|
| 1 | Kiểm công cụ: `az version`, `az login` (user tự đăng nhập) | [COMMON-CLI](references/microsoft/common/COMMON-CLI.md) | `az` chạy; user đã đăng nhập |
| 2 | Nhận diện nguồn: `.pbip` cục bộ (có `.Report` + `.SemanticModel`) hay report tải từ Fabric | [ITEM-DEFINITIONS-CORE](references/microsoft/common/ITEM-DEFINITIONS-CORE.md) | Biết nhánh quy trình |
| 3 | Xác nhận workspace đích (tìm ID theo tên bằng List + JMESPath) | [COMMON-CLI](references/microsoft/common/COMMON-CLI.md) · [COMMON-CORE](references/microsoft/common/COMMON-CORE.md) | User xác nhận đúng workspace |
| 4 | Semantic model: deploy model cục bộ **hoặc** chọn model có sẵn; tham khảo `semantic-model-rest-api.md`, `connection-binding.md` ở skill [`pbi-model`](../pbi-model/SKILL.md) | [ITEM-DEFINITIONS-CORE](references/microsoft/common/ITEM-DEFINITIONS-CORE.md) | Có `semanticModelId` đích |
| 5 | Report: tạo mới hoặc `updateDefinition` (đủ part, base64, `byConnection`), poll LRO | [COMMON-CLI](references/microsoft/common/COMMON-CLI.md) §LRO | Trạng thái Succeeded |
| 6 | So binding report ↔ model đích; remap nếu cần | — | Mở report trên Service không lỗi visual |
| 7 | Dọn file tạm; ghi HANDOFF (cách refresh, gateway, quyền) → [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | — | HANDOFF có trong `projects/<slug>/artifacts/` |

## References — `references/microsoft/` (nguyên văn, v0.3.16)

| File | Đọc khi |
|---|---|
| [common/COMMON-CLI.md](references/microsoft/common/COMMON-CLI.md) | Lệnh `az rest`, tìm workspace/item, LRO, chọn công cụ |
| [common/COMMON-CORE.md](references/microsoft/common/COMMON-CORE.md) | Khái niệm Fabric REST, xác thực, quy ước chung |
| [common/ITEM-DEFINITIONS-CORE.md](references/microsoft/common/ITEM-DEFINITIONS-CORE.md) | Cấu trúc định nghĩa item (Report, SemanticModel), part, payload |
| [SOURCE.lock.json](references/microsoft/SOURCE.lock.json) | Kiểm file nguyên văn (sha256) |

## Đổi tên skill Microsoft → studio

| Tên trong reference Microsoft | Skill studio |
|---|---|
| `powerbi-report-management` | `pbi-publish` (skill này) |
| `powerbi-report-authoring` | [`pbi-build`](../pbi-build/SKILL.md) |
| `semantic-model-authoring` | [`pbi-model`](../pbi-model/SKILL.md) |
| `powerbi-report-design` | [`pbi-design`](../pbi-design/SKILL.md) |
| `fabriciq` | không có trong studio |

---
*Nguồn: microsoft/skills-for-fabric v0.3.16 (MIT) — `common/` nguyên văn + tóm vai `powerbi-report-management`; chưa distill đầy đủ.*
