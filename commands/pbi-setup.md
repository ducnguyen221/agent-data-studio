---
description: Thiết lập nơi lưu tri thức dự án trong trạm dữ liệu
---

Thiết lập tri thức của Agent Data Studio: $ARGUMENTS

1. Gọi `knowledge_status`. Nếu đã có trạm và dự án, báo đường dẫn hiện tại; chỉ đổi nơi lưu khi người dùng yêu cầu.
2. Chưa thiết lập thì dùng `workspace/` của checkout ở chế độ basic. Nếu người dùng đã chọn trạm ngoài, dùng đường dẫn từ `ADS_DATA`. Không tự chuyển dữ liệu giữa hai trạm.
3. Gọi `setup_knowledge(path)` với nơi lưu dự án được chọn; đọc lại `knowledge_status` để xác nhận đường dẫn thực tế.
4. Giới thiệu ngắn `projects/`, `knowledge/`, `templates/`, `INDEX.md` và `TIMELINE.md`, rồi gợi ý bước tiếp theo theo nhu cầu.

Skill và engine luôn đọc từ repo đang chạy; trạm chỉ chứa dữ liệu. Nếu MCP chưa có, vẫn có thể bắt đầu khảo sát hoặc đọc CSV mẫu bằng skill `data-discovery` và `data-mockup`, chưa gọi tool tri thức.
