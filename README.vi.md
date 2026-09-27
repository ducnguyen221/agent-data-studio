# Agent Data Studio

**[Tiếng Việt](README.vi.md) · [English](README.md)**

Agent Data Studio là bộ công cụ và hướng dẫn để làm việc với dữ liệu bằng AI Agent. Bạn có thể bắt đầu bằng file CSV mẫu; khi có Power BI, agent có thể khám phá model, chạy DAX có kiểm soát và hỗ trợ xây báo cáo. Phần làm việc trực tiếp với Power BI Desktop cần Windows.

**Mới dùng lần đầu?** Dán yêu cầu ở mục cài đặt bên dưới vào ứng dụng AI của bạn, hoặc làm theo [Bắt đầu tại đây](START-HERE.md). Trang [cài đặt trên website](docs/install/index.html) trình bày từng bước; [INDEX.md](INDEX.md) là bản đồ repo.

## Cài đặt — dán một yêu cầu vào ứng dụng AI của bạn

Mở Codex, Claude Code, Claude Desktop hoặc Google Antigravity trên Windows rồi dán nguyên văn yêu cầu dưới đây. Agent đọc [INSTALL.md](INSTALL.md) — hướng dẫn dành cho agent — rồi kiểm tra máy, **hỏi bạn trước** khi cài thêm phần mềm, cài, chạy doctor và báo lại từng dòng.

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

| Ứng dụng | `-Hosts` | Khác biệt cần biết |
|---|---|---|
| Codex (CLI và desktop) | `codex` | Giá trị mặc định của bộ cài |
| Claude Code | `claude` | — |
| Claude Desktop (tab chat) | `claude-desktop` | Chỉ có 16 công cụ MCP, không có skill; tab chat không chạy lệnh nên nhờ host khác cài hộ hoặc cài tay |
| Google Antigravity | `antigravity` | — |

Muốn tự gõ lệnh: cần Git và Python 3.11–3.14 ([chuẩn bị máy](START-HERE.md#chuẩn-bị-máy)), rồi mở PowerShell:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1 -Hosts codex
```

Thay `codex` bằng giá trị trong bảng. Script tạo `workspace/` ngay trong repo và gộp MCP vào cấu hình người dùng của host (ví dụ `~/.codex/config.toml`) cạnh các server sẵn có; mọi thư mục mở trong host dùng chung server của checkout này, nên mỗi máy trỏ một checkout ([giới hạn](hosts/README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng)). Đóng và mở lại ứng dụng AI tại thư mục repo; xem [hướng dẫn từng host](hosts/README.md). Script kiểm tra adapter skill tại chỗ; mọi skill, script và quy trình gốc luôn thuộc repo.

Sau cài, chạy `.\doctor.ps1 -Hosts <host>` trong PowerShell để kiểm tra source, adapter, môi trường Python và MCP. Doctor ghi rõ tầng nào chưa được kiểm trực tiếp. Nếu chính sách máy tổ chức chặn script, hãy nhờ IT hỗ trợ theo quy định của tổ chức. `.\update.ps1` cho xem trước bản Git; nhánh áp dụng commit đã review hiện chỉ hỗ trợ khi dependency không đổi và vẫn cần mở lại host. Xem [START-HERE.md](START-HERE.md) để cập nhật có guard và gỡ đăng ký host.

## Thử ngay, chưa cần Power BI

Mở repo trong ứng dụng AI của bạn, gửi: “Đọc `samples/sales-demo.csv` với `skills/data-discovery/SKILL.md`, kiểm chất lượng dữ liệu, tính doanh thu theo tháng và lưu báo cáo vào `workspace/outputs/first-report.md`.” [Kết quả đối chiếu](samples/README.md) giúp bạn kiểm tra.

`workspace/` chứa `projects/`, `knowledge/`, `outputs/`, `state/` và cấu hình cục bộ. Git bỏ qua toàn bộ thư mục này. Dữ liệu cá nhân, kết quả công việc và khóa truy cập không được thêm vào Git. Nếu bạn đã có trạm riêng, đặt `ADS_DATA` trước khi cài để trỏ đến thư mục ngoài repo; installer lưu liên kết cục bộ và vẫn chạy engine/skill từ repo.

## Khi cần Power BI

MCP server có 16 công cụ trong 6 nhóm: khám phá Desktop/model; truy vấn DAX; chỉnh model; kit trang báo cáo; chưng cất thiết kế; quản lý tri thức dự án. Các công cụ Power BI Desktop cần Power BI Desktop và thư viện ADOMD.NET. Để kiểm kết nối, mở một báo cáo trong Power BI Desktop rồi chạy `.\doctor.ps1 -ProbeDesktop` trong PowerShell: doctor chạy `EVALUATE ROW("x",1)`; nếu Desktop đang đóng, kết quả là `NOT_CHECKED` chứ không phải lỗi. Power BI Service cần cấu hình xác thực riêng. Bộ 9 skill gốc ở [`skills/`](skills/), 8 quy trình ở [`commands/`](commands/), kit trang ở [`report-templates/`](report-templates/README.md), mẫu tài liệu ở [`templates/documents/`](templates/documents/).

Truy vấn DAX đi qua policy phía server với giới hạn số dòng và nhật ký audit. Chính sách giúp hạn chế rò rỉ do nhầm thao tác; bạn vẫn cần kiểm soát quyền trên nguồn dữ liệu. Microsoft Power BI Modeling MCP có thể được cài riêng nếu cần thao tác model nâng cao.

## Nguồn và dữ liệu

Mã nguồn được cập nhật qua Git tại repo này. Adapter `.agents/skills/` và `.claude/skills/` trỏ về `skills/`, còn script chạy từ repo. Không sửa bản copy trong cache plugin hoặc thư mục máy để thay đổi quy trình của repo. `workspace/`, `.venv/`, cấu hình thực và file đăng nhập bị loại khỏi Git. Hãy xem `git status` trước khi commit.

Asset mẫu của KPIM (hồ sơ bộ dữ liệu, kit `kpim-business-light`, `Project_Management.xlsx`) thuộc sở hữu của KPIM; KPIM cho phép sử dụng và phân phối cùng repo theo giấy phép MIT. Cách ghi nguồn xem [NOTICE.md](NOTICE.md).

[Hướng dẫn cài từng host](hosts/README.md) · [Bản đồ repo](INDEX.md) · [Website](https://ducnguyen.vn/agent-data-studio/) · [Giấy phép MIT](LICENSE)
