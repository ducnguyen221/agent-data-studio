# Changelog

## 0.7.0 — 2026-09-26 — Agent Data Studio chạy từ checkout

- Sản phẩm mang tên Agent Data Studio. Chạy thẳng từ checkout; dữ liệu, cấu hình và tri thức
  nằm ở trạm dữ liệu: `workspace/` trong repo (basic) hoặc thư mục riêng qua `ADS_DATA`.
- Bộ cài, `doctor.ps1`, `update.ps1` và `uninstall.ps1` mới. `doctor.ps1 -ProbeDesktop` kiểm
  kết nối Power BI Desktop; `update.ps1` chỉ áp bản mới khi khớp SHA đầy đủ (`-ExpectedCommit`).
- Adapter skill cho Claude Code, Codex và Antigravity, sinh từ `skills/` gốc của repo.
- MCP đăng ký ở cấu hình người dùng của host: mỗi máy trỏ một checkout, dùng chung một server.
- `ADOMD_LIB_DIR` là nguồn ADOMD.NET duy nhất khi được đặt; thiếu ADOMD.NET thì công cụ báo rõ.
- Asset mẫu của KPIM chia sẻ cho cộng đồng tham khảo, ghi nguồn trong `NOTICE.md`; website mới.

## 2026-09-26 — Hướng dẫn làm việc theo source và trạm dữ liệu

Hướng dẫn agent của repo được cập nhật cho chế độ basic `workspace/` và trạm riêng qua
`ADS_DATA`. Skill, script và engine lấy từ source repo; cấu hình host chỉ kết nối tới
source được chọn. Bản sửa đồng bộ với [hướng dẫn bắt đầu](https://github.com/ducnguyen221/agent-data-studio/blob/main/START-HERE.md) và chưa
phải thông báo phát hành hay xác nhận hỗ trợ mọi host.
