---
name: pbi-publish
description: "Publish Power BI work to Microsoft Fabric / Power BI Service: deploy a local .pbip (semantic model plus report) to a workspace, create or update report and semantic model items through the Fabric REST API with az rest, handle long-running operations, and rebind the report to the target semantic model. Status unverified: no test workspace yet, confirm every step with the user. Use when: publish or upload a report to Fabric, deploy a PBIP, update a report definition in a workspace, list or download workspace reports. Not: editing pages or visuals -> pbi-build; editing measures or TMDL locally -> pbi-model; review before publishing -> pbi-review; closing the project and packing knowledge -> pbi-knowledge."
---

# pbi-publish — adapter nguồn

Đọc toàn bộ [SKILL.md](../../../skills/pbi-publish/SKILL.md) gốc trong repo trước khi làm. Mọi script, reference, workflow và template phải mở trực tiếp từ repo này; không dùng bản copy trong cache hoặc trạm dữ liệu. Nếu không mở được file gốc, báo thiếu source và dừng tác vụ này.
