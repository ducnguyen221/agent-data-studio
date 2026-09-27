# Bản đồ Agent Data Studio

| Tôi muốn… | Bắt đầu tại |
|---|---|
| Nhờ AI agent cài giúp (một prompt copy-dán) | [INSTALL.md](INSTALL.md) |
| Tự cài và thử với dữ liệu mẫu | [START-HERE.md](START-HERE.md) |
| Chọn Codex, Claude Code, Claude Desktop hoặc Antigravity | [hosts/README.md](hosts/README.md) |
| Hiểu quy trình phân tích | [skills/README.md](skills/README.md) và [commands/](commands/) |
| Làm việc với Power BI | [skills/pbi-analysis/SKILL.md](skills/pbi-analysis/SKILL.md) |
| Tìm bộ mẫu báo cáo | [report-templates/README.md](report-templates/README.md) |
| Đóng góp mã nguồn | [AGENTS.md](AGENTS.md) và [scripts/README.md](scripts/README.md) |

## Mã nguồn và trạm làm việc

| Nơi | Vai trò | Có đưa lên Git? |
|---|---|---|
| [`powerbi_agent/`](powerbi_agent/) · [`mcp_server_powerbi.py`](mcp_server_powerbi.py) | Engine MCP và 16 công cụ | Có |
| [`skills/`](skills/) · [`commands/`](commands/) · [`agents/`](agents/) | Nguồn gốc của skill, quy trình và agent | Có |
| [`.agents/skills/`](.agents/skills/) · [`.claude/skills/`](.claude/skills/) | Adapter mỏng để host tìm skill trong repo | Có |
| [`scripts/`](scripts/) · [`install.ps1`](install.ps1) | Script thực thi, cập nhật adapter và bộ cài | Có |
| [`INSTALL.md`](INSTALL.md) | Hướng dẫn cài dành cho AI agent và bản gốc của prompt copy-dán | Có |
| [`hosts/`](hosts/) | Hướng dẫn đăng ký MCP cho từng ứng dụng AI | Có |
| [`samples/`](samples/) | Dữ liệu tổng hợp cho bài thử đầu tiên | Có |
| `workspace/` | Dự án, tri thức, kết quả và cấu hình cá nhân của bản cài cơ bản | **Không** — Git bỏ qua cả thư mục |
| `ADS_DATA` bên ngoài repo | Trạm đã có của người dùng nâng cao | Không |

Mã nguồn, skill và script luôn được đọc hoặc chạy từ checkout này. Bản cài cơ bản giữ `workspace/` cùng một thư mục repo cho dễ tìm; Git không theo dõi nó. Nếu dùng trạm ngoài, installer lưu đường dẫn trong `.ads-binding.json` cục bộ (cũng bị Git bỏ qua). Trước khi thêm file lên Git, xem `git status`.

## Bạn có thể làm gì?

**Phân tích dữ liệu:** dùng [`data-discovery`](skills/data-discovery/SKILL.md) để tìm hiểu bài toán, [`data-mockup`](skills/data-mockup/SKILL.md) để tạo dữ liệu mẫu, rồi lưu kết quả trong `workspace/outputs/`. [CSV thực hành](samples/README.md) không cần Power BI.

**Làm Power BI:** dùng [`pbi-model`](skills/pbi-model/SKILL.md), [`pbi-analysis`](skills/pbi-analysis/SKILL.md), [`pbi-design`](skills/pbi-design/SKILL.md), [`pbi-build`](skills/pbi-build/SKILL.md), [`pbi-review`](skills/pbi-review/SKILL.md), [`pbi-publish`](skills/pbi-publish/SKILL.md) và [`pbi-knowledge`](skills/pbi-knowledge/SKILL.md). MCP có công cụ khám phá model, truy vấn DAX có policy, sửa model, áp kit và lưu tri thức dự án. Power BI Desktop và ADOMD.NET chỉ cần cho công việc với Desktop; Service có bước đăng nhập riêng.

**Dùng mẫu:** [`report-templates/`](report-templates/README.md) chứa kit trang báo cáo; [`templates/documents/`](templates/documents/) chứa mẫu tài liệu. Mẫu công khai là ví dụ chung. Tài liệu dự án thật lưu ở trạm cá nhân, không đưa vào `report-templates/` hay `templates/` khi chưa rà soát.

## 16 công cụ MCP

| Nhóm | Công cụ |
|---|---|
| Khám phá | `list_local_reports`, `list_tables`, `describe_table` |
| Truy vấn | `execute_dax_local`, `execute_dax_service` |
| Sửa model | `add_measure_local`, `add_relationship_local` |
| Kit trang | `list_templates`, `apply_template`, `distill_template` |
| Chưng cất | `distill_model_schema`, `distill_report_design` |
| Tri thức | `knowledge_status`, `setup_knowledge`, `init_project`, `log_timeline` |

Các lệnh có thể gọi và cách gọi khác nhau giữa các host. Tám file quy trình `pbi-*` nằm ở [`commands/`](commands/); bạn có thể bảo agent đọc file tương ứng từ repo bằng lời thường. [Hướng dẫn host](hosts/README.md) ghi rõ cách kiểm tra MCP.

## Đường dẫn quan trọng

`workspace/projects/<ten-du-an>/` dành cho dự án; `workspace/knowledge/` cho tri thức dùng lại; `workspace/outputs/` cho kết quả; `workspace/state/` cho trạng thái cục bộ. Cấu hình không chứa mật khẩu ở `workspace/config.env`. Khóa cho Power BI Service chỉ được cung cấp khi dùng Service, trong file secret riêng ngoài Git. Repo có [mẫu cấu hình](.env.example) và [mẫu policy](policy.example.json).

Khi sửa file PBIR trên đĩa, hãy đóng báo cáo `.pbip` trong Power BI Desktop trước để bản đang mở không ghi đè kết quả. Với model hoặc report có nhiều agent tham gia, chỉ một agent ghi tại một thời điểm.
