# Bắt đầu với Agent Data Studio

Bạn có thể dùng repo này để làm việc với dữ liệu cùng Codex, Claude Code, Claude Desktop hoặc Google Antigravity. Bài thử đầu tiên chỉ cần CSV mẫu, chưa cần Power BI Desktop, tài khoản Power BI hay khóa truy cập.

## Nhờ AI cài giúp

Mở ứng dụng AI bạn đang dùng trên Windows và dán nguyên văn yêu cầu dưới đây. Agent tự đọc [hướng dẫn cài dành cho agent](INSTALL.md) trong repo, kiểm tra máy, **hỏi bạn trước** khi cài thêm phần mềm, rồi cài, kiểm tra và báo lại từng bước.

```text
Hãy cài Agent Data Studio lên máy Windows này cho chính ứng dụng AI bạn đang chạy
(Codex, Claude Code, Claude Desktop hoặc Google Antigravity).

Nguồn duy nhất: https://github.com/ducnguyen221/agent-data-studio
Đọc trước hướng dẫn dành cho agent tại
https://raw.githubusercontent.com/ducnguyen221/agent-data-studio/main/INSTALL.md
(không mở được link thì clone repo rồi đọc file INSTALL.md trong đó),
rồi làm đúng và đủ các bước trong đó: kiểm tra máy đã có gì (Git, Python, PowerShell),
hỏi tôi trước khi cài thêm phần mềm hoặc cần quyền admin, clone repo về thư mục an toàn
(không OneDrive/Desktop), chạy install.ps1 cho đúng host đang dùng, chạy doctor.ps1,
hướng dẫn tôi khởi động lại ứng dụng, rồi kiểm tra bằng bài mẫu samples/sales-demo.csv.

Quy tắc: chỉ chạy script/lệnh có trong repo trên hoặc trong INSTALL.md; không đổi chính sách
hệ thống; không đọc hay ghi mật khẩu/khóa; gặp lỗi thì dừng và giải thích bằng lời thường.
Kết thúc bằng bản tóm tắt: đường dẫn repo, host đã đăng ký, kết quả doctor từng dòng,
phần mềm đã cài thêm, và việc tôi cần làm tiếp.
```

Tab chat của Claude Desktop không chạy được lệnh PowerShell: hãy dán yêu cầu vào Claude Code, Codex hoặc Antigravity và nói thêm "cài cho Claude Desktop", hoặc tự làm theo phần cài tay bên dưới với `-Hosts claude-desktop`. Claude Desktop chỉ nhận 16 công cụ MCP, không có skill và quy trình `pbi-*`.

## Chuẩn bị máy

| Thành phần | Khi nào cần | Gói `winget` | Cần admin? |
|---|---|---|---|
| Git | Bắt buộc | `Git.Git` | Không khi cài `--scope user` |
| Python 3.11–3.14 (khuyến nghị 3.12) | Bắt buộc | `Python.Python.3.12` | Không |
| Power BI Desktop | Khi làm với báo cáo đang mở | `9NTXR16HNW1T` (Microsoft Store) | Không |
| ADOMD.NET + AMO/TOM | Khi truy vấn hoặc sửa model trong Desktop | `Microsoft.SQLServerManagementStudio.21`, hoặc MSI [Analysis Services client libraries](https://learn.microsoft.com/analysis-services/client-libraries) | Có |
| Node.js LTS | Khi dựng trang báo cáo bằng CLI của Microsoft | `OpenJS.NodeJS.LTS` | Có |
| Azure CLI | Chỉ khi xuất bản lên Power BI Service | `Microsoft.AzureCLI` | Có |

Không cần SQL Server hay SSAS server. Agent chỉ chạy lệnh cài khi bạn đồng ý; tự cài thì dùng PowerShell:

```powershell
winget install --id Git.Git -e --scope user
winget install --id Python.Python.3.12 -e --scope user
winget install --id 9NTXR16HNW1T --source msstore
```

Dòng thứ ba là Power BI Desktop, có thể cài sau. Cài xong, mở cửa sổ PowerShell mới để máy nhận Git và Python.

Máy không có `winget` (Windows LTSC, Windows Sandbox): tải từ trang chính thức — [Git](https://git-scm.com/download/win), [Python](https://www.python.org/downloads/windows/) (chọn 3.12 hoặc 3.13, tick "Add python.exe to PATH"), Power BI Desktop từ Microsoft Store hoặc [trang tải của Microsoft](https://learn.microsoft.com/power-bi/fundamentals/desktop-get-the-desktop). Python 3.14 mới được kiểm bằng bộ test, chưa kiểm kết nối Power BI Desktop thật; nên chọn 3.12 hoặc 3.13.

## Cài tay trên Windows

Mở PowerShell và chạy; thay `codex` bằng `claude`, `claude-desktop` hoặc `antigravity` theo ứng dụng bạn dùng:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Hosts codex
```

Muốn kiểm máy trước khi cài, chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\doctor.ps1 -Preflight` sau lệnh `cd`: lệnh in 7 dòng `prereq` (PowerShell, ExecutionPolicy, Git, Python, ADOMD.NET, Node, `az`), chưa cần `.venv`, và thoát mã 1 nếu có dòng `FAIL`. Cài nhiều host một lần thì ghi `-Hosts codex,claude`; `doctor.ps1` và `uninstall.ps1` gọi kiểu `-File` thì mỗi lần một host.

`-ExecutionPolicy Bypass` chỉ áp cho lệnh đó, không đổi chính sách của máy. Muốn chạy `.\install.ps1` trực tiếp về sau thì `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` là lựa chọn của riêng bạn; agent không tự đổi. Đặt repo ở thư mục cục bộ, không đặt trong OneDrive, Desktop hay Documents.

Bộ cài đăng ký MCP trong cấu hình người dùng của host (ví dụ `~/.codex/config.toml`). Mọi thư mục bạn mở trong host dùng chung server của checkout này, nên mỗi máy chỉ trỏ một checkout; xem [giới hạn](hosts/README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng) và [hướng dẫn chọn host](hosts/README.md). Sau khi script báo hoàn tất, đóng và mở lại ứng dụng AI trong **chính thư mục repo** để ứng dụng nhận công cụ và skill.

Script tạo môi trường Python `.venv/`, kiểm tra các thư viện Power BI và tạo `workspace/` gồm `projects/`, `knowledge/`, `outputs/`, `state/`. `workspace/` bị Git bỏ qua; dữ liệu và kết quả cá nhân có thể ở chung trong folder repo nhưng không đi vào bản mã nguồn chia sẻ. Skill và script gốc ở [`skills/`](skills/) và [`scripts/`](scripts/); ứng dụng AI đọc chúng từ repo, không cần bản sao skill trong thư mục cấu hình toàn máy.

Sau khi mở lại host, chạy `powershell -NoProfile -ExecutionPolicy Bypass -File .\doctor.ps1 -Hosts codex` (đổi tên host nếu cần). Doctor kiểm tiên quyết của máy (7 dòng `prereq`), source, adapter, Python, đăng ký MCP và khả năng nạp engine. Dòng `driver` báo `WARN` khi có module ADOMD cho Python nhưng không thấy DLL ADOMD.NET; DLL nằm ở thư mục lạ thì đặt `ADOMD_LIB_DIR=<thư mục>` trong `workspace\config.env`, không bọc nháy kép. Kết nối Power BI đang mở và việc host thực sự đọc skill cần kiểm ngay trong host; thông báo `NOT_CHECKED` không phải lỗi cài nhưng cũng chưa phải xác nhận hoàn tất. Nếu chính sách máy chặn script, hãy nhờ IT hỗ trợ; không tự vượt chính sách.

## Làm bài thử đầu tiên

Mở repo bằng ứng dụng AI của bạn rồi gửi yêu cầu này:

> Đọc `samples/sales-demo.csv` bằng skill `data-discovery` trong repo. Kiểm tra dữ liệu, tính tổng doanh thu theo tháng, lưu báo cáo tại `workspace/outputs/first-report.md` và cho tôi biết kết quả. Không dùng Power BI Desktop.

Bài thử có [dữ liệu và kết quả đối chiếu](samples/README.md). Nếu agent không thấy skill, hãy yêu cầu nó mở trực tiếp `skills/data-discovery/SKILL.md` trong repo. Kiểm tra file kết quả trong `workspace/outputs/`.

## Khi muốn làm với Power BI

Mở Power BI Desktop và báo cáo của bạn, rồi yêu cầu agent gọi `list_local_reports` để tìm báo cáo đang mở. Kết nối DAX với Desktop còn cần thư viện ADOMD.NET; phần kiểm tra lúc cài sẽ báo nếu máy thiếu. Khi báo cáo đang mở, chạy `.\doctor.ps1 -ProbeDesktop` trong PowerShell (thêm `-Hosts` như lúc cài) để kiểm kết nối bằng `EVALUATE ROW("x",1)`; nếu Desktop đang đóng, kết quả là `NOT_CHECKED` (chưa kiểm), không phải lỗi. Power BI Service là luồng riêng, chỉ cần cấu hình thông tin đăng nhập khi bạn thực sự dùng Service. [Xem các công cụ và quy trình](INDEX.md) hoặc [hướng dẫn từng host](hosts/README.md).

Đưa dữ liệu của bạn vào `workspace/projects/<ten-du-an>/`. Không đưa file thật, thông tin đăng nhập hoặc kết quả cá nhân ra ngoài `workspace/`. Trước khi chia sẻ hoặc `git add`, kiểm tra `git status`.

## Nếu đã có trạm dữ liệu riêng

Đặt `ADS_DATA` trỏ tới **thư mục ngoài repo** trước khi chạy `install.ps1`. Script lưu liên kết cục bộ để những lần mở sau dùng đúng trạm đó; mã nguồn và skill vẫn chạy từ repo. Ví dụ trong phiên PowerShell cài đặt:

```powershell
$env:ADS_DATA = 'D:\MyData\agent-data-studio'
.\install.ps1
```

Nếu repo cũ có cấu hình hoặc dữ liệu tại gốc, script dừng để bạn chọn trạm hiện hữu; nó không tự di chuyển dữ liệu. [Chi tiết từng host](hosts/README.md).

## Cập nhật hoặc gỡ cài đặt

Chạy `.\update.ps1` để xem commit mới; lệnh mặc định **không thay mã nguồn**. Đóng các phiên AI dùng repo, nhờ agent kiểm diff và SHA đầy đủ được in ra. Với bản **không đổi `requirements.txt` hoặc quy tắc `.gitignore`**, chạy `.\update.ps1 -Apply -ExpectedCommit <SHA đầy đủ>` trong PowerShell để kiểm candidate ở worktree tạm rồi fast-forward checkout. Candidate chứa file riêng hoặc file bị ignore cũng bị từ chối trước khi áp. Nếu hậu kiểm thất bại, updater thử quay về commit cũ bằng `git reset --keep`; nhật ký không chứa secret ở `<trạm>/state/update-journal.jsonl`. Sau khi áp dụng, mở lại từng host và chạy doctor; trạng thái host/Power BI vẫn là `NOT_CHECKED` cho tới khi kiểm thật. Bản đổi dependency, quy tắc ignore hoặc checkout bẩn bị từ chối, không tự sửa; nhờ người phụ trách cập nhật theo quy trình riêng. Lên 0.7.1 từ 0.7.0 thuộc trường hợp này (`requirements.txt` đổi): đóng các host, chạy `git pull`, rồi chạy lại lệnh `install.ps1` như lúc cài để pip tự nâng thư viện. Để bỏ đăng ký MCP của một host, chạy `.\uninstall.ps1 -Hosts codex` trong PowerShell (đổi tên host nếu cần). Script chỉ gỡ mục MCP trỏ tới checkout này, sao lưu cấu hình trước khi gỡ, giữ server khác, `workspace/` và trạm ngoài; chỉ chọn `-RemoveVenv` khi chắc chắn không host nào còn dùng môi trường Python của repo.
