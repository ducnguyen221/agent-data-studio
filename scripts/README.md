# scripts/ — Tiện ích dev của REPO (không phải một phần của skill)

| File | Dùng khi |
|---|---|
| `cli.py` | Debug DAX **không cần MCP host**: `.venv\Scripts\python.exe scripts\cli.py list \| tables \| query <port> <model> "<dax>"` — hữu ích khi host chưa restart hoặc cần kiểm tra kết nối nhanh. |
| `test_mcp_local.py` | Smoke test kết nối ADOMD → Power BI Desktop đang mở. Công cụ dev chẩn đoán thủ công: import `pyadomd` trực tiếp, không qua gate `ADOMD_LOADED` như `cli.py`/MCP, nên máy thiếu DLL có thể thấy banner của pyadomd. Người dùng kiểm kết nối bằng `doctor.ps1 -ProbeDesktop`. |
| `build_host_adapters.py` | Tạo hoặc kiểm tra các adapter skill, lệnh và agent của Codex/Claude/Antigravity từ nguồn trong repo. Dùng `--check` để kiểm tra mà không ghi file. |
| `build_template_gallery.py` | Tạo metadata gallery dạng chữ **chỉ khi** truyền `--approval-manifest` ở ngoài repo. Manifest phải duyệt chủ sở hữu, giấy phép, trạng thái đã khử thông tin riêng và SHA-256 của từng file kit; mặc định script từ chối và không đổi gallery. Script không sao chép ảnh. |
| `update_release.py` | Helper nội bộ do `update.ps1 -Apply` gọi sau khi user/Codex duyệt SHA. Kiểm candidate trong worktree tạm, chỉ áp khi dependency không đổi, ghi nhật ký ở trạm và thử rollback nếu hậu kiểm lỗi; không chạy độc lập cho người mới. |

> `skills/data-discovery/scripts/` là generator của skill. Cả hai nhóm script đều
> chạy trực tiếp từ repo; installer không tạo bản copy trong thư mục host hay trạm.

Gallery chỉ được tạo sau khi người phụ trách đã kiểm quyền phân phối và nội dung từng kit. `sanitized=true` trong `kit.json` là điều kiện kỹ thuật, không thay thế việc kiểm nội dung hoặc giấy phép. Không đưa manifest duyệt hay tài liệu chứng minh quyền vào repo public.
