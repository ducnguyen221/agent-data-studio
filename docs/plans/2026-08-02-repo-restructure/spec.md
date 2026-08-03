# SPEC — Tái cấu trúc & điều hướng repo powerbi-agent

Ngày: 2026-08-02 · Trạng thái: **FINAL — chờ duyệt một lượt (Gate 1)** · Chưa thực thi thay đổi nào.
Đã qua review đối kháng bằng Codex (gpt-5.6, read-only) — 15 finding, đã kiểm chứng lại từng cái.

---

## 1. Vấn đề

Chủ repo đánh giá cấu trúc thư mục "tạp nham, chưa có sự sắp xếp dễ hiểu, chưa có phân loại".

**Chẩn đoán:** repo được sắp theo **loại artifact kỹ thuật** (`powerbi_agent/`, `plugins/`, `scripts/`,
`templates/`, `hosts/`, `tests/`), còn giá trị bán ra được mô tả theo **4 trụ cột nghiệp vụ**.
Hai trục không khớp ở bất kỳ chỗ nào → người đọc lần đầu không có đường đi từ "tôi muốn X" đến "mở folder nào".

Bằng chứng đo được:

| Bằng chứng | Ở đâu |
|---|---|
| Docs phải viết chú thích "**≠**" để phân biệt folder trùng tên | `README.md:266` · `README.vi.md:259` · `AGENTS.md:25` · `templates/README.md:13` · `scripts/README.md:8` |
| Chữ **"templates" mang 4 nghĩa** | ① `templates/` (kit visual PBIR) ② `skills/kpim-analysis/templates/` (mẫu tài liệu) ③ `<Knowledge Dir>/templates/` (kit riêng, `knowledge.py:59`) ④ `docs/template/` (route website) |
| Chữ **"scripts" mang 2 nghĩa** | `scripts/` (tiện ích dev) vs `skills/kpim-analysis/scripts/` (generator cho người dùng) |
| Trụ cột giá trị nhất nằm sâu nhất, mang tên **cơ chế đóng gói** | Trụ 2 (34 file) ở `plugins/powerbi-agent/skills/` |
| Trụ cột 4 ở **độ sâu 5–6** | `plugins/…/skills/kpim-analysis/templates/mindmaps/*.png` |

**Kết luận:** repo **không** lộn xộn vật lý — 109 file tracked đều đúng chỗ kỹ thuật. Vấn đề là
**từ ngữ đa nghĩa + thiếu lớp điều hướng**. ⇒ ~80% chữa bằng tài liệu (rủi ro 0), ~20% bằng đổi tên
(rủi ro thấp), **0%** bằng di chuyển folder load-bearing.

---

## 2. Bốn trụ cột (nguyên văn yêu cầu chủ repo)

1. **MCP Server setup** để AI Agent làm việc trực tiếp với Power BI và tạo nội dung như nhân viên.
2. **Số hóa workflow / agent / skill / knowledge** của chính chủ repo như chuyên gia dữ liệu.
3. **Template Power BI Dashboard DESIGN UI/UX** để agent dựng báo cáo như chuyên gia thiết kế.
4. **Template Word / Excel / md…** để tạo và quản lý tài liệu phân tích dữ liệu.

| Trụ | Hiện ở đâu | Độ sâu | Vấn đề |
|---|---|---|---|
| 1 | `powerbi_agent/` · `mcp_server_powerbi.py` · `install.ps1` · `hosts/` · `policy.example.json` | 1 | Rải **5 chỗ**, không có cửa vào |
| 2 | `plugins/powerbi-agent/{skills,commands,agents}/` (34 file) | 2–3 | Phần giá trị nhất bị chôn dưới tên nói về đóng gói |
| 3 | `templates/kpim-business-light/` (17 file) | 1–2 | **Trùng tên** với trụ 4 |
| 4 | `plugins/…/skills/kpim-analysis/templates/` + `scripts/` | 5–6 | **Sâu nhất repo**, **trùng tên** với trụ 3 |

---

## 3. Yêu cầu

- **R1** — Tên folder dễ hiểu với người không kỹ thuật **ở những folder họ thật sự ghé**, đồng thời đúng kỹ thuật.
- **R2** — `INDEX.md` hai trục: (A) trụ cột → tính năng → tài liệu; (B) folder → là gì + file quan trọng.
- **R3** — `README.md` là bản dễ hiểu cho người đọc lần đầu: **dùng làm gì · cài thế nào · tính năng chính**.
- **R4** — Không phá thứ đang chạy: cài đặt hiện có, ID MCP server, đường dẫn skill installer phụ thuộc, URL website.

---

## 4. Quyết định đã chốt

| # | Quyết định | Người chốt |
|---|---|---|
| Q1 | Trụ 3: `templates/` → **`report-templates/`** | Chủ repo (2026-08-02) |
| Q2 | Trụ 4: `skills/kpim-analysis/templates/` → **`document-templates/`** | Khuyến nghị 95/100, được chấp thuận |
| Q3 | `INDEX.md` **chỉ tiếng Anh**, không tạo `INDEX.vi.md` | Chủ repo (2026-08-02) |
| Q4 | Duyệt **một lượt** toàn bộ lộ trình, thực thi liền mạch | Chủ repo (2026-08-02) |

Review độc lập củng cố Q1: `report-templates/` khớp đúng từ vựng repo đang dùng sẵn
("report page", "report layer", "Visual report kits" ở `README.md:266`).

---

## 5. Ràng buộc

Phân biệt rõ **định luật vật lý** (không thể phá) và **quyết định tương thích** (chọn không phá):

| # | Nội dung | Loại | Bằng chứng |
|---|---|---|---|
| L1 | Skill phải nằm trong plugin root, manifest trỏ `./skills/` | **Cứng** | `plugin.json:14`; `install.ps1:289`; plugin không tham chiếu ra ngoài plugin root |
| L2 | Mẫu tài liệu trụ 4 nằm trong folder skill | **Quyết định tương thích** (không phải định luật) | `install.ps1:292–302` copy cả thư mục skill. Sửa được nếu đổi installer — nhưng ta **chọn không đổi** để giữ tương thích |
| L3 | Root `templates/` chỉ ghép vào code ở 2 chỗ | **Cứng** | `tools_template.py:20` · `build_template_gallery.py:19` |
| L4 | `<Knowledge Dir>/templates/` nằm ngoài repo, thuộc sở hữu user | **Cứng** | `knowledge.py:59` · `tools_knowledge.py:57` |
| L5 | `docs/` là web root GitHub Pages | **GIẢ ĐỊNH** — không kiểm chứng được từ file (cấu hình nằm ở repo settings) | Dù đúng hay sai, kết luận "không đổi `docs/template/`" vẫn giữ vì đã có link ngoài trỏ vào |
| L6 | Skill single-source ở repo, không sửa bản đã cài | **Governance** | `AGENTS.md:126` |
| L7 | Sửa `README.md` phải mirror `README.vi.md` cùng commit | **Governance** | `AGENTS.md:133` |
| L8 | `.ps1` phải UTF-8 **có BOM** | **Cứng** | `AGENTS.md:128`; 3 file `.ps1` hiện bắt đầu bằng `EF BB BF` |
| L9 | `templates/` **KHÔNG** phải tên dành riêng trong spec skill của Claude/Codex | **Đã giải quyết** | Spec chỉ bắt buộc `SKILL.md`; `references/`/`scripts/`/`assets/` là quy ước, không cưỡng chế ⇒ `document-templates/` hợp lệ |

---

## 6. Tiêu chí nghiệm thu

1. **Không còn folder nào cần chú thích "≠" để giải thích tên.** Kiểm bằng **assertion có mục tiêu**,
   không phải grep mù: repo không còn chuỗi `templates/kpim-business-light` và `kpim-analysis/templates`;
   `templates/README.md:13` và chú thích ở `README.md:266` / `README.vi.md:259` / `AGENTS.md:25` đã xóa.
   *(Chú thích "≠" ở `AGENTS.md:22`, `plugins/README.md:6` nói về `marketplace.json` vs `plugin.json` —
   không liên quan, giữ nguyên.)*
2. Người mới chỉ đọc `README.md` trả lời được: repo làm gì · cài thế nào · có 4 nhóm tính năng nào.
3. Từ `INDEX.md`, đi từ bất kỳ trụ cột nào tới file cụ thể trong **≤ 2 cú click**.
4. `pytest tests -m "not integration"` xanh · `ruff check` xanh (mở rộng phủ cả `scripts/`).
5. **Test hồi quy mới** xanh: kit `report-templates/kpim-business-light` được `list_templates()` nhìn thấy;
   installer (chạy trên **fake profile**, không đụng máy thật) copy đủ `kpim-analysis/document-templates/`
   và không còn folder cũ.
6. `build_template_gallery.py` sinh lại `docs/template/templates.json` chỉ đổi `readme_url`.
7. Website `docs/` không đổi URL nào.
8. `plugin.json` + `marketplace.json` cùng bump version → người dùng marketplace thật sự nhận được layout mới.

---

## 7. Ngoài phạm vi

| Việc | Vì sao KHÔNG làm |
|---|---|
| Đưa `skills/` ra root | Phá L1 |
| Đổi ID MCP server `powerbi-mcp-bridge` | Gãy **mọi** config host đang cài. Rủi ro cao, giá trị ~0 |
| Thống nhất 4 tên (repo `powerbi-agent` · package `powerbi_agent` · server `powerbi-mcp-bridge` · folder `.mcp/powerbi-mcp`) | Như trên. Chữa bằng **giải thích ở `INDEX.md §3`** |
| Dọn file ở root | Bắt buộc theo convention / theo lệnh cài 1 dòng đã công bố |
| Đổi tên `docs/template/` | Gãy URL công khai |
| `scripts/` → `dev-tools/` | **Bỏ** — mâu thuẫn nguyên tắc A2 của chính kế hoạch: non-tech không bao giờ mở folder này, nên đổi tên chỉ tạo churn |
| Đổi tên `<Knowledge Dir>/templates/` | **Bỏ** — folder của user, ngoài repo, đã tự phân biệt bằng ngữ cảnh sở hữu. Migration "giữ tên cũ nếu có" sẽ đẻ ra 2 schema vĩnh viễn |

---

## 8. ⚠️ Phát hiện NGOÀI phạm vi — cần chủ repo quyết riêng

**`pack.ps1` đóng gói cả file riêng tư vào zip phân phối.**

`pack.ps1:31` chỉ loại trừ `.venv`, `.git`, `__pycache__`; `pack.ps1:36` copy **mọi** entry ở root.
Nghĩa là zip `powerbi-mcp-setup-*.zip` sẽ mang theo, nếu tồn tại trên máy:

- `policy.json` — **danh sách cột PII thật của khách hàng** (`.gitignore:24`)
- `knowledge.config.json` — đường dẫn tới Brain/Knowledge Dir cá nhân (`.gitignore:30`)
- `docs/internal/` — tài liệu nội bộ, client context (`.gitignore:21`)
- `tests/installer/fakehome/`, `.ruff_cache/`, `.pytest_cache/` — rác

Đây là **rò rỉ dữ liệu thật**, không phải vấn đề cấu trúc. Cách chữa đúng: đóng gói theo
**allowlist file đã tracked** (`git ls-files`) thay vì blacklist.
Không gộp vào lần này để giữ commit sạch — **đề nghị làm ngay sau, ở task riêng.**
