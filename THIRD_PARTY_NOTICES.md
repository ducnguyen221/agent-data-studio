# Third-party notices

Repo `agent-data-studio` (MIT, Duc Nguyen) kèm và tham chiếu các thành phần bên thứ ba dưới đây.

## 1. microsoft/skills-for-fabric — chép nguyên văn

| | |
|---|---|
| Nguồn | https://github.com/microsoft/skills-for-fabric |
| Tag | `v0.3.16` |
| Commit | `24cc0d296e5e8523cc6a92e1342bc1791d7deb85` |
| Giấy phép | MIT — văn bản nguyên văn: [`LICENSES/microsoft-skills-for-fabric.txt`](LICENSES/microsoft-skills-for-fabric.txt) |
| Cách dùng | Chép **nguyên văn, không sửa byte nào**; mỗi skill giữ `references/microsoft/SOURCE.lock.json` (sha256 + bytes từng file). Bản đồ đường upstream → đường studio: [`upstream/microsoft-skills-for-fabric.yaml`](upstream/microsoft-skills-for-fabric.yaml) |

File đang dùng (58 file, đường upstream gốc `plugins/powerbi-authoring/`):

| Skill studio | Thư mục trong repo | Đường upstream |
|---|---|---|
| `pbi-model` | `skills/pbi-model/references/microsoft/` (12) | `skills/semantic-model-authoring/references/*.md` |
| `pbi-design` | `skills/pbi-design/references/microsoft/` (20) | `skills/powerbi-report-design/references/*.md` (14) · `references/archetypes/*.md` (5) · `assets/base.json` |
| `pbi-build` | `skills/pbi-build/references/microsoft/` (23) | `skills/powerbi-report-authoring/references/*.md` |
| `pbi-publish` | `skills/pbi-publish/references/microsoft/common/` (3) | `common/COMMON-CLI.md` · `common/COMMON-CORE.md` · `common/ITEM-DEFINITIONS-CORE.md` |

Copyright (c) 2026 Microsoft Corporation. Permission is hereby granted under the MIT License —
xem văn bản đầy đủ trong `LICENSES/microsoft-skills-for-fabric.txt`.

## 2. Công cụ Microsoft — KHÔNG kèm trong repo, chỉ hướng dẫn cài

| Gói npm | Giấy phép | Cách dùng |
|---|---|---|
| `@microsoft/powerbi-desktop-bridge-cli` | MIT | Người dùng tự `npm install -g` (ghim phiên bản); repo không phân phối |
| `@microsoft/powerbi-report-authoring-cli` | MIT | Người dùng tự `npm install -g` (ghim phiên bản); repo không phân phối |
| `@microsoft/powerbi-modeling-mcp` | EULA preview của Microsoft (không phải MIT) | **Không phân phối, không vendor.** Repo chỉ hướng dẫn cài/bật theo nhu cầu; người dùng chịu điều khoản của Microsoft |
