# Changelog

## 0.7.1 — 2026-09-27 — Cài bằng một prompt cho mọi AI agent

- `INSTALL.md` mới ở gốc repo: hướng dẫn cài dành cho AI agent. Một prompt copy-dán dùng chung
  cho Codex, Claude Code, Claude Desktop và Google Antigravity; agent tự kiểm tra máy, hỏi trước
  khi cài phần mềm hoặc cần quyền admin, cài, chạy doctor, kiểm bằng bài mẫu CSV và báo lại.
- Hỗ trợ Python 3.11–3.14 (`pythonnet` 3.1.0); bộ cài báo rõ khi Python nằm ngoài khoảng này.
- `doctor.ps1 -Preflight` kiểm tiên quyết (PowerShell, ExecutionPolicy, Git, Python, ADOMD.NET,
  Node, Azure CLI) ngay sau khi clone, trước khi cài.
- Claude Desktop (tab chat) được đăng ký bằng `-Hosts claude-desktop`, chỉ có 16 công cụ MCP.
- Bộ cài, doctor và engine dò ADOMD.NET theo cùng một danh sách, tôn trọng `ADOMD_LIB_DIR`.
- Tài liệu và website cài đặt viết chung cho mọi host: bảng "Chuẩn bị máy" với gói `winget`,
  script chạy bằng `-ExecutionPolicy Bypass` theo tiến trình, không đổi chính sách máy.
- Test mới giữ prompt đồng bộ giữa `INSTALL.md`, README, START-HERE và website, và giữ version
  thống nhất giữa các manifest.
- Sửa lỗi: cài lại trên checkout đã có `.venv` từng treo chờ bàn phím; nay chạy thẳng.
- Sửa lỗi: `powershell -File install.ps1 -Hosts a,b` từng không đăng ký host nào mà vẫn báo hoàn
  tất; nay bộ cài tách dấu phẩy và từ chối tên host lạ trước khi ghi. `doctor.ps1` và
  `uninstall.ps1` gọi qua `-File` vẫn nhận mỗi lần một host.
- `doctor.ps1` báo `WARN` ở dòng `driver` khi có module ADOMD cho Python nhưng không thấy DLL
  ADOMD.NET. `ADOMD_LIB_DIR` trong `config.env` viết không bọc nháy kép.
- **Nâng cấp từ 0.7.0:** `requirements.txt` đổi (`pythonnet` 3.1.0) nên `update.ps1 -Apply` sẽ
  từ chối áp tự động. Đóng các host, chạy `git pull`, rồi chạy lại `install.ps1` với `-Hosts` như
  lúc cài; pip tự nâng thư viện trong `.venv`. Muốn thêm Claude Desktop thì thêm `claude-desktop`
  vào `-Hosts`.

## 0.7.0 — 2026-09-27 — Agent Data Studio chạy từ checkout

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
