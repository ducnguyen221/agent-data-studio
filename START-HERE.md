# Bắt đầu với Agent Data Studio

Bạn có thể dùng repo này để làm việc với dữ liệu cùng Codex, Claude Code hoặc Antigravity. Bài thử đầu tiên chỉ cần CSV mẫu, chưa cần Power BI Desktop, tài khoản Power BI hay khóa truy cập.

## Cài trên Windows

Cần có Git và Python 3.11 trở lên. Mở PowerShell và chạy:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
.\install.ps1
```

Lệnh mặc định đăng ký MCP cho **Codex**, trong cấu hình người dùng của host (`~/.codex/config.toml`). Mọi thư mục bạn mở trong host dùng chung server của checkout này, nên mỗi máy chỉ trỏ một checkout; xem [giới hạn](hosts/README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng). Nếu dùng Claude Code hoặc Antigravity, xem [hướng dẫn chọn host](hosts/README.md). Sau khi script báo hoàn tất, đóng và mở lại ứng dụng AI trong **chính thư mục repo** để ứng dụng nhận công cụ và skill.

Script tạo môi trường Python `.venv/`, kiểm tra các thư viện Power BI và tạo `workspace/` gồm `projects/`, `knowledge/`, `outputs/`, `state/`. `workspace/` bị Git bỏ qua; dữ liệu và kết quả cá nhân có thể ở chung trong folder repo nhưng không đi vào bản mã nguồn chia sẻ. Skill và script gốc ở [`skills/`](skills/) và [`scripts/`](scripts/); ứng dụng AI đọc chúng từ repo, không cần bản sao skill trong thư mục cấu hình toàn máy.

Sau khi mở lại host, có thể nhờ Codex chạy `.\doctor.ps1 -Hosts codex` trong PowerShell. Doctor kiểm source, adapter, Python, đăng ký MCP và khả năng nạp engine. Kết nối Power BI đang mở và việc host thực sự đọc skill cần kiểm ngay trong host; thông báo `NOT_CHECKED` không phải lỗi cài nhưng cũng chưa phải xác nhận hoàn tất. Nếu chính sách máy chặn script, hãy nhờ IT hỗ trợ; không tự vượt chính sách.

## Làm bài thử đầu tiên

Mở repo bằng Codex rồi gửi yêu cầu này:

> Đọc `samples/sales-demo.csv` bằng skill `data-discovery` trong repo. Kiểm tra dữ liệu, tính tổng doanh thu theo tháng, lưu báo cáo tại `workspace/outputs/first-report.md` và cho tôi biết kết quả. Không dùng Power BI Desktop.

Bài thử có [dữ liệu và kết quả đối chiếu](samples/README.md). Nếu agent không thấy skill, hãy yêu cầu nó mở trực tiếp `skills/data-discovery/SKILL.md` trong repo. Kiểm tra file kết quả trong `workspace/outputs/`.

## Khi muốn làm với Power BI

Mở Power BI Desktop và báo cáo của bạn, rồi yêu cầu agent gọi `list_local_reports` để tìm báo cáo đang mở. Kết nối DAX với Desktop còn cần thư viện ADOMD.NET; phần kiểm tra lúc cài sẽ báo nếu máy thiếu. Khi báo cáo đang mở, chạy `.\doctor.ps1 -ProbeDesktop` trong PowerShell để kiểm kết nối bằng `EVALUATE ROW("x",1)`; nếu Desktop đang đóng, kết quả là `NOT_CHECKED` (chưa kiểm), không phải lỗi. Power BI Service là luồng riêng, chỉ cần cấu hình thông tin đăng nhập khi bạn thực sự dùng Service. [Xem các công cụ và quy trình](INDEX.md) hoặc [hướng dẫn Codex](hosts/codex/README.md).

Đưa dữ liệu của bạn vào `workspace/projects/<ten-du-an>/`. Không đưa file thật, thông tin đăng nhập hoặc kết quả cá nhân ra ngoài `workspace/`. Trước khi chia sẻ hoặc `git add`, kiểm tra `git status`.

## Nếu đã có trạm dữ liệu riêng

Đặt `ADS_DATA` trỏ tới **thư mục ngoài repo** trước khi chạy `install.ps1`. Script lưu liên kết cục bộ để những lần mở sau dùng đúng trạm đó; mã nguồn và skill vẫn chạy từ repo. Ví dụ trong phiên PowerShell cài đặt:

```powershell
$env:ADS_DATA = 'D:\MyData\agent-data-studio'
.\install.ps1
```

Nếu repo cũ có cấu hình hoặc dữ liệu tại gốc, script dừng để bạn chọn trạm hiện hữu; nó không tự di chuyển dữ liệu. [Chi tiết từng host](hosts/README.md).

## Cập nhật hoặc gỡ cài đặt

Chạy `.\update.ps1` để xem commit mới; lệnh mặc định **không thay mã nguồn**. Đóng các phiên AI dùng repo, nhờ Codex kiểm diff và SHA đầy đủ được in ra. Với bản **không đổi `requirements.txt` hoặc quy tắc `.gitignore`**, chạy `.\update.ps1 -Apply -ExpectedCommit <SHA đầy đủ>` trong PowerShell để kiểm candidate ở worktree tạm rồi fast-forward checkout. Candidate chứa file riêng hoặc file bị ignore cũng bị từ chối trước khi áp. Nếu hậu kiểm thất bại, updater thử quay về commit cũ bằng `git reset --keep`; nhật ký không chứa secret ở `<trạm>/state/update-journal.jsonl`. Sau khi áp dụng, mở lại từng host và chạy doctor; trạng thái host/Power BI vẫn là `NOT_CHECKED` cho tới khi kiểm thật. Bản đổi dependency, quy tắc ignore hoặc checkout bẩn bị từ chối, không tự sửa; nhờ người phụ trách cập nhật theo quy trình riêng. Để bỏ đăng ký MCP của một host, chạy `.\uninstall.ps1 -Hosts codex` trong PowerShell (đổi tên host nếu cần). Script chỉ gỡ mục MCP trỏ tới checkout này, sao lưu cấu hình trước khi gỡ, giữ server khác, `workspace/` và trạm ngoài; chỉ chọn `-RemoveVenv` khi chắc chắn không host nào còn dùng môi trường Python của repo.
