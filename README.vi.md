# Agent Data Studio

**[Tiếng Việt](README.vi.md) · [English](README.md)**

Agent Data Studio là bộ công cụ và hướng dẫn để làm việc với dữ liệu bằng AI Agent. Bạn có thể bắt đầu bằng file CSV mẫu; khi có Power BI, agent có thể khám phá model, chạy DAX có kiểm soát và hỗ trợ xây báo cáo. Phần làm việc trực tiếp với Power BI Desktop cần Windows.

**Mới dùng lần đầu?** Làm theo [Bắt đầu tại đây](START-HERE.md). Trang [cài đặt trên website](docs/install/index.html) trình bày từng bước; [INDEX.md](INDEX.md) là bản đồ repo.

## Cài đặt nhanh bằng Codex

Cần Git và Python 3.11 trở lên. Mở PowerShell:

```powershell
git clone https://github.com/ducnguyen221/agent-data-studio "$env:USERPROFILE\agent-data-studio"
cd "$env:USERPROFILE\agent-data-studio"
.\install.ps1
```

Mặc định script đăng ký MCP cho **Codex** và tạo `workspace/` ngay trong repo. MCP được gộp vào cấu hình người dùng của host (ví dụ `~/.codex/config.toml`) cạnh các server sẵn có; mọi thư mục mở trong host dùng chung server của checkout này, nên mỗi máy trỏ một checkout ([giới hạn](hosts/README.md#mcp-được-đăng-ký-ở-cấu-hình-người-dùng)). Đóng và mở lại Codex tại thư mục repo. Để chọn Claude Code hoặc Antigravity, dùng `-Hosts claude` hoặc `-Hosts antigravity`; xem [hướng dẫn từng host](hosts/README.md). Script kiểm tra adapter skill tại chỗ; mọi skill, script và quy trình gốc luôn thuộc repo.

Sau cài, chạy `.\doctor.ps1 -Hosts codex` trong PowerShell để kiểm tra source, adapter, môi trường Python và MCP. Doctor ghi rõ tầng nào chưa được kiểm trực tiếp. Nếu chính sách máy tổ chức chặn script, hãy nhờ IT hỗ trợ theo quy định của tổ chức. `.\update.ps1` cho xem trước bản Git; nhánh áp dụng commit đã review hiện chỉ hỗ trợ khi dependency không đổi và vẫn cần mở lại host. Xem [START-HERE.md](START-HERE.md) để cập nhật có guard và gỡ đăng ký host.

Muốn agent tự cài? Mở Codex tại nơi bạn muốn clone và gửi: “Clone `https://github.com/ducnguyen221/agent-data-studio`, đọc `START-HERE.md`, chạy `install.ps1` cho Codex, kiểm tra kết quả và hướng dẫn tôi làm bài CSV mẫu.”

## Thử ngay, chưa cần Power BI

Trong Codex mở repo, gửi: “Đọc `samples/sales-demo.csv` với `skills/data-discovery/SKILL.md`, kiểm chất lượng dữ liệu, tính doanh thu theo tháng và lưu báo cáo vào `workspace/outputs/first-report.md`.” [Kết quả đối chiếu](samples/README.md) giúp bạn kiểm tra.

`workspace/` chứa `projects/`, `knowledge/`, `outputs/`, `state/` và cấu hình cục bộ. Git bỏ qua toàn bộ thư mục này. Dữ liệu cá nhân, kết quả công việc và khóa truy cập không được thêm vào Git. Nếu bạn đã có trạm riêng, đặt `ADS_DATA` trước khi cài để trỏ đến thư mục ngoài repo; installer lưu liên kết cục bộ và vẫn chạy engine/skill từ repo.

## Khi cần Power BI

MCP server có 16 công cụ trong 6 nhóm: khám phá Desktop/model; truy vấn DAX; chỉnh model; kit trang báo cáo; chưng cất thiết kế; quản lý tri thức dự án. Các công cụ Power BI Desktop cần Power BI Desktop và thư viện ADOMD.NET. Để kiểm kết nối, mở một báo cáo trong Power BI Desktop rồi chạy `.\doctor.ps1 -ProbeDesktop` trong PowerShell: doctor chạy `EVALUATE ROW("x",1)`; nếu Desktop đang đóng, kết quả là `NOT_CHECKED` chứ không phải lỗi. Power BI Service cần cấu hình xác thực riêng. Bộ 9 skill gốc ở [`skills/`](skills/), 8 quy trình ở [`commands/`](commands/), kit trang ở [`report-templates/`](report-templates/README.md), mẫu tài liệu ở [`templates/documents/`](templates/documents/).

Truy vấn DAX đi qua policy phía server với giới hạn số dòng và nhật ký audit. Chính sách giúp hạn chế rò rỉ do nhầm thao tác; bạn vẫn cần kiểm soát quyền trên nguồn dữ liệu. Microsoft Power BI Modeling MCP có thể được cài riêng nếu cần thao tác model nâng cao.

## Nguồn và dữ liệu

Mã nguồn được cập nhật qua Git tại repo này. Adapter `.agents/skills/` và `.claude/skills/` trỏ về `skills/`, còn script chạy từ repo. Không sửa bản copy trong cache plugin hoặc thư mục máy để thay đổi quy trình của repo. `workspace/`, `.venv/`, cấu hình thực và file đăng nhập bị loại khỏi Git. Hãy xem `git status` trước khi commit.

Asset mẫu của KPIM (hồ sơ bộ dữ liệu, kit `kpim-business-light`, `Project_Management.xlsx`) thuộc sở hữu của KPIM; KPIM cho phép sử dụng và phân phối cùng repo theo giấy phép MIT. Cách ghi nguồn xem [NOTICE.md](NOTICE.md).

[Hướng dẫn cài từng host](hosts/README.md) · [Bản đồ repo](INDEX.md) · [Website](https://ducnguyen.vn/agent-data-studio/) · [Giấy phép MIT](LICENSE)
