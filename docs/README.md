# docs/ — Website Agent Data Studio

Thư mục này là source của website GitHub Pages tại [ducnguyen.vn/agent-data-studio](https://ducnguyen.vn/agent-data-studio/). Nội dung đang sửa trong repo chỉ xuất hiện trên website sau khi được phát hành.

| Đường dẫn | Vai trò |
|---|---|
| `index.html` | **Trang chủ** (menu 1): lối vào, infographic kiến trúc 4 tầng và quy trình 9 khâu, đường đi cho người mới |
| `about/index.html` | **Giới thiệu** (menu 2): Agent Data Studio là gì, Data Agent là gì, mục tiêu, định vị với Microsoft, con số đếm từ mã nguồn, tác giả, trạng thái |
| `instruction/index.html` | **Hướng dẫn** (menu 3): cách vận hành cho người không chuyên — ẩn dụ, 5 chặng, ba ví dụ, 8 lệnh, hỏi đáp, từ điển |
| `architecture/index.html` | **Thiết kế** (menu 4): kiến trúc kỹ thuật — MCP server, policy, skill, host, trạm dữ liệu, Knowledge OS, template kit, multi-agent, vòng đời |
| `install/index.html` | **Cài đặt** (menu 5): prompt chung cho mọi AI agent (chép từ `INSTALL.md` ở gốc repo, có test đồng bộ) và phần cài tay |
| `feature/index.html` | Chuyển hướng sang `about/`, giữ fragment URL (liên kết cũ "Power Agent") |
| `template/index.html` | Chuyển hướng sang `architecture/#template-kit`, giữ fragment URL nếu có |
| `template/templates.json` | Đầu ra của `scripts/build_template_gallery.py` (gallery mẫu đã duyệt); giữ nguyên vị trí |
| `INSTALL.html` | Chuyển liên kết cũ sang `/install/`, giữ fragment URL |
| `assets/site.css`, `assets/site.js` | Style và script dùng chung cho mọi trang, kể cả trang chủ; khối infographic dùng chung có tiền tố `.ig-` (HTML + SVG inline, màu theo token, tự đổi dọc/ngang theo bề rộng) |
| `UAT-REPORT.md` | Hồ sơ thử nghiệm của v0.2.0; không chứng nhận bản hiện tại |

Header và footer là cùng một khối markup chép vào năm trang chính (không có bước build). Menu luôn gồm năm mục theo thứ tự Trang chủ · Giới thiệu · Hướng dẫn · Thiết kế · Cài đặt; trang đang xem (kể cả trang chủ) có đúng một mục `class="active"` + `aria-current="page"`, hiện dạng pill màu nhấn. `tests/test_site_nav.py` bắt lệch thứ tự, `aria-current` và link hỏng; footer có cùng năm mục. Sửa header/footer thì sửa đủ năm trang.

Năm trang nạp `assets/site.css?v=…` và `assets/site.js?v=…`. GitHub Pages cho trình duyệt giữ cache khoảng 10 phút, nên sửa CSS/JS thì **đổi số `v=` ở cả năm trang** (dùng ngày, vd `20260929`) — nếu không, khách quay lại sẽ thấy HTML mới ghép với CSS cũ.

Gallery mẫu công khai chỉ được thêm kit sau khi kiểm tra quyền sử dụng, dữ liệu và bản xem trước. Dữ liệu dự án của người dùng nằm ở `workspace/` hoặc trạm ngoài do họ chọn; không được đưa vào `docs/`.
