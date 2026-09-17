---
name: data-mockup
description: "Build a sample (mockup) dataset from business requirements: interview, spec as Markdown plus YAML, a fixed-seed generator, verification against the spec, and an Excel workbook with a Data Dictionary sheet. Numbers must tell a story (trend, seasonality, plan vs actual, anomalies with reasons), names must look real, no real PII. Works without Power BI. Use when: create mockup or sample data, demo or lab dataset, fake data for a POC, BI training or tests, sample data Excel with a data dictionary. Not: surveying and documenting REAL data -> data-discovery; Power Query, model or DAX -> pbi-model; querying a real model -> pbi-analysis."
metadata:
  group: data
  chain_position: 1
  status: stable
  sources:
    - "kpim: OpcOS data-bi skill mockup-data (playbooks, kpim-datasets profiles, mockpack/mockverify/gen_skeleton, spec templates)"
---

# data-mockup — dựng bộ dữ liệu mẫu từ yêu cầu nghiệp vụ

## Mục đích
Biến mô tả nghiệp vụ (thường mơ hồ) thành **bộ dữ liệu Excel dùng được ngay**: cấu trúc chuẩn, số liệu biết nói,
sheet Data Dictionary đầy đủ, generator tái lập y hệt khi yêu cầu đổi. Ba lăng kính cùng lúc: **chuyên gia nghiệp vụ**
(quy trình, sự kiện, đo gì) · **data engineer** (grain, khoá, kiểu, star schema) · **data analyst** (phân phối, mùa vụ, tương quan).

## Trước / Sau trong chuỗi

| | Skill | Khi nào |
|---|---|---|
| Trước | [`data-discovery`](../data-discovery/SKILL.md) | Có (hoặc cần) DATA_DICTIONARY / METRICS làm spec |
| Sau | [`pbi-model`](../pbi-model/SKILL.md) | Nạp bộ mẫu vào Power BI (lab, demo, fixture) |
| Liên quan | [`pbi-knowledge`](../pbi-knowledge/SKILL.md) | Lưu bộ mẫu vào `projects/<slug>/` |

## Must / Prefer / Avoid (7 nguyên tắc)
- **Must** — **spec là nguồn sự thật**: `DATASET_SPEC.md` ↔ `dataset.yaml`; phần cấu trúc MD **sinh từ YAML**. Đổi yêu cầu = sửa spec + re-gen, không sửa tay Excel.
- **Must** — **seed cố định** ghi trong spec; chạy lại ra đúng bộ cũ.
- **Must** — **không PASS verify thì không bàn giao**; lỗi cài cắm để dạy học khai `intentional_fail: true`.
- **Must** — **không PII thật**: dữ liệu sinh + cột `*_masked`.
- **Prefer** — **chuẩn hoá trước, chiếu ra sau**: lớp DB (dim/fact/bridge/cfg) làm gốc → lớp nghiệp vụ (wide, nhãn tiếng Việt) là bản bàn giao mặc định (`layer: both` khi user cần cả hai).
- **Prefer** — **số phải biết nói**: xu hướng, mùa vụ, tháng tăng xen giảm, đạt/hụt kế hoạch, so MoM–QoQ–YoY (≥ 24 tháng), bất thường có lý do.
- **Prefer** — **tên đối tượng thật**: tổ chức hư cấu (mặc định thương hiệu nhà KPIM), địa danh/ngành hàng/hàng hoá dùng tên thật.
- **Avoid** — `random.uniform` phẳng; `Sản phẩm 001`; kế hoạch đạt 100 % mọi nơi; cột không phục vụ KPI nào; dictionary viết tay.

## Quy trình 5 pha

| Pha | Việc | Đọc | Cổng kiểm |
|---|---|---|---|
| P1 Interview | Agent dẫn dắt: suy diễn trước, hỏi theo lô ≤ 3 vòng, mỗi câu có phương án + khuyến nghị; đủ 6 nhóm (bối cảnh · mục đích · quy trình/thực thể/sự kiện · grain/khối lượng/khung thời gian + mốc "hiện tại" · KPI & câu hỏi · ràng buộc: ngôn ngữ cột, tiền tệ, PII, thương hiệu, lỗi cài cắm). Chưa rõ → đề xuất 8 domain mẫu hoặc 5 bộ KPIM | [mockup-design-playbook](references/kpim/mockup-design-playbook.md) PHẦN 0 · [kpim-datasets](references/kpim/kpim-datasets/README.md) | Trả lời được "1 dòng bảng chính là gì?" và "bộ này trả lời câu hỏi nào?"; đã tóm tắt ngược cho user xác nhận |
| P2 Thiết kế | Chép `templates/documents/dataset/dataset.template.yaml` + `DATASET_SPEC.template.md` (gốc repo) vào thư mục dự án, điền theo BA → DE → DA; `python <skill>/scripts/mockpack.py dict dataset.yaml -o DATASET_SPEC.md` | [mockup-design-playbook](references/kpim/mockup-design-playbook.md) | Mọi bảng có `grain` bằng lời; mọi cột có `type` + `definition`; FK trỏ PK có thật; KPI tính được từ cột đã khai |
| P3 Sinh dữ liệu | Chép `scripts/gen_skeleton.py` thành `gen_<slug>.py`; thứ tự **cfg → dim → bridge → fact → lớp nghiệp vụ**; dùng helper phân phối của `mockpack.py` (lognormal, mùa vụ, phễu, Pareto) | [mockup-build-playbook](references/kpim/mockup-build-playbook.md) | Chạy 2 lần ra file giống hệt |
| P4 Verify | `python <skill>/scripts/mockpack.py verify dataset.yaml data/ -o DATA_QUALITY_REPORT.md` — rule cơ bản tự suy từ spec + rule nghiệp vụ trong `rules:` | [mockup-build-playbook](references/kpim/mockup-build-playbook.md) catalog rule | 0 FAIL ngoài `intentional_fail`; FAIL thật → quay P3/P2, không sửa tay dữ liệu |
| P5 Đóng gói | `python <skill>/scripts/mockpack.py pack dataset.yaml data/ -o <Ten>.xlsx` → `00_README` · `01_Data_Dictionary` · `02_Relationships` · `03_Metrics` · sheet dữ liệu | [mockup-build-playbook](references/kpim/mockup-build-playbook.md) bẫy Excel | Dictionary khớp số cột từng sheet; verify trên chính `.xlsx` vẫn PASS |

`<skill>` = thư mục của skill này (`skills/data-mockup/`).

## Bàn giao chuẩn (trong thư mục dự án user chỉ định, không vào repo)

```
<ten-bo-du-lieu>/
  DATASET_SPEC.md          người đọc — brief viết tay + cấu trúc sinh tự động
  dataset.yaml             máy đọc — nguồn sự thật
  gen_<slug>.py            generator seed cố định
  data/                    CSV trung gian (mỗi bảng 1 file)
  <Ten>.xlsx               SẢN PHẨM — kèm sheet Data Dictionary
  DATA_QUALITY_REPORT.md   kết quả verify
```

## Scripts — `scripts/`

| File | Vai |
|---|---|
| `mockpack.py` | Thư viện dùng chung: `dict` · `pack` · `verify` + helper phân phối. **Không sửa cho từng dự án** |
| `mockverify.py` | Engine verify (report + rule); `mockpack verify` tự import — chép `mockpack.py` đi đâu thì chép kèm |
| `gen_skeleton.py` | Khung generator (bộ bán lẻ mẫu) — chép đi sửa cho từng dự án |
| `test_mockpack.py` | Tự kiểm `python scripts/test_mockpack.py` (không phải pytest; dọn file tạm sau khi chạy) |
| `requirements.txt` | Phụ thuộc: pandas, PyYAML, openpyxl… |

## References — `references/kpim/`

| File | Đọc khi |
|---|---|
| [mockup-design-playbook.md](references/kpim/mockup-design-playbook.md) | P1–P2: dẫn dắt phỏng vấn, 6 nhóm câu hỏi, chính sách thương hiệu, 3 lăng kính, 8 domain mẫu, 5 bộ KPIM |
| [mockup-build-playbook.md](references/kpim/mockup-build-playbook.md) | P3–P5: 8 hình dạng câu chuyện, phân phối, cơ chế đặt tên, catalog rule verify, bẫy Excel |
| [kpim-datasets/README.md](references/kpim/kpim-datasets/README.md) | Chọn bộ tham chiếu gần nhất (Mart · Bank · HR · Marketing) trước khi thiết kế mới |

Mẫu spec: `templates/documents/dataset/` ở gốc repo (`dataset.template.yaml`, `DATASET_SPEC.template.md`).

---
*Quy trình, script & mẫu: KPIM practice (Duc Nguyen), MIT.*
