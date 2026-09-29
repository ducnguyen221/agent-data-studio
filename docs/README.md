# docs/ — Website Agent Data Studio

Thư mục này là source của website GitHub Pages tại [ducnguyen.vn/agent-data-studio](https://ducnguyen.vn/agent-data-studio/). Nội dung đang sửa trong repo chỉ xuất hiện trên website sau khi được phát hành.

| Đường dẫn | Vai trò |
|---|---|
| `index.html` | Trang chủ và lối vào cài đặt |
| `about/index.html` | **Giới thiệu** (menu 1): Agent Data Studio là gì, Data Agent là gì, mục tiêu, định vị với Microsoft, con số đếm từ mã nguồn, tác giả, trạng thái |
| `instruction/index.html` | **Hướng dẫn** (menu 2): cách vận hành cho người không chuyên — ẩn dụ, 5 chặng, ba ví dụ, 8 lệnh, hỏi đáp, từ điển |
| `architecture/index.html` | **Thiết kế** (menu 3): kiến trúc kỹ thuật — MCP server, policy, skill, host, trạm dữ liệu, Knowledge OS, template kit, multi-agent, vòng đời |
| `install/index.html` | **Cài đặt** (menu 4): prompt chung cho mọi AI agent (chép từ `INSTALL.md` ở gốc repo, có test đồng bộ) và phần cài tay |
| `feature/index.html` | Chuyển hướng sang `about/`, giữ fragment URL (liên kết cũ "Power Agent") |
| `template/index.html` | Chuyển hướng sang `architecture/#template-kit`, giữ fragment URL nếu có |
| `template/templates.json` | Đầu ra của `scripts/build_template_gallery.py` (gallery mẫu đã duyệt); giữ nguyên vị trí |
| `INSTALL.html` | Chuyển liên kết cũ sang `/install/`, giữ fragment URL |
| `assets/site.css`, `assets/site.js` | Style và script dùng chung cho mọi trang, kể cả trang chủ |
| `UAT-REPORT.md` | Hồ sơ thử nghiệm của v0.2.0; không chứng nhận bản hiện tại |

Header và footer là cùng một khối markup chép vào năm trang chính (không có bước build). Menu luôn gồm bốn mục theo thứ tự Giới thiệu · Hướng dẫn · Thiết kế · Cài đặt; `tests/test_site_nav.py` bắt lệch thứ tự, `aria-current` và link hỏng. Sửa header/footer thì sửa đủ năm trang.

Gallery mẫu công khai chỉ được thêm kit sau khi kiểm tra quyền sử dụng, dữ liệu và bản xem trước. Dữ liệu dự án của người dùng nằm ở `workspace/` hoặc trạm ngoài do họ chọn; không được đưa vào `docs/`.
