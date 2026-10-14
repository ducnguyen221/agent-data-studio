# ECOSYSTEM — Agent Data Studio trong hệ thống ACD

## 🤝 ACD Ecosystem Integration
- **Role in ACD:** Studio thuộc Nhóm 2 (Production Studio) — Data Hub trung tâm của hệ thống nhiều repo ACD: khám phá dữ liệu, mô hình hóa, truy vấn DAX an toàn và dựng báo cáo Power BI. `agent-skill-studio` là xưởng nền cấp chuẩn `SKILL.md` portable, công cụ kiểm (`validate`/`audit`/`package`) và đóng gói skill; repo này tự giữ nghiệp vụ của mình, không nhờ xưởng nền viết thay.
- **Upstream Controllers:** Cả 10 Team phòng ban cần số liệu để ra quyết định; mức Cốt lõi với `agent-executive-team`, `agent-operations-team`, `agent-customer-team`, `agent-finance-legal-team`, `agent-accounting-team` và `agent-academy-team`. `agent-design-studio` cấp quy tắc theme và nhận diện cho dashboard.
- **Downstream Consumers:** Các Team nhận dashboard, phân tích và bộ dữ liệu mẫu. `agent-slide-studio` và `agent-writing-studio` nhận số liệu và biểu đồ đã kiểm chứng để đưa vào deck, bài PR, whitepaper, case study.
- **Recommended Bundles:** Bundle B (B2B Sales & Revenue Engine, case study số liệu ROI) và Bundle C (Corporate Academy & L&D Engine, dataset bài tập thực hành). Không thuộc Bundle E; repo chỉ dùng chuẩn của `agent-skill-studio`.
- **Handoff Artifacts:** Đầu vào là `production-brief.md` do Team giao (Target Studio, Objective, Raw Context, Technical Specs, Deadline & Priority). Đầu ra là báo cáo hoặc dashboard Power BI cùng biên nhận nghiệm thu; kết quả truy vấn chỉ ở dạng tổng hợp theo chính sách an toàn của repo.
