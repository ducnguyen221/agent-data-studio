# Power BI — Knowledge Map (concept clusters, agent reference)

> Distill từ kho tri thức Power BI của KPIM (glossary ~380 thuật ngữ, 8 cụm) + tài liệu vận hành. Dùng để agent "định vị" khái niệm và biết chỗ đào sâu (xem dax/powerquery/sql references kèm).

## 8 cụm khái niệm (concept clusters)
1. **Foundation** — Power BI Desktop/Service/Report Server, PBIX/PBIP/PBIR, Report, Dashboard, Semantic model, Workspace, App, License (Free/Pro/PPU/Premium/Fabric capacity).
2. **Prepare (Power Query)** — M language, Applied Steps, Get Data, Import/DirectQuery/Direct Lake/Live connection, Query folding, Reference/Duplicate, Merge/Append, Parameter, Privacy level, Incremental refresh. → xem `powerquery-m-best-practices.md`.
3. **Model** — Fact/Dimension, Star/Snowflake/Galaxy schema, Grain, PK/FK, Cardinality, Cross-filter direction, Active/Inactive relationship (USERELATIONSHIP), Many-to-many, Bridge table, Role-playing dimension, Date table. → xem `dax-best-practices.md` §3.
4. **DAX** — Measure (explicit/implicit), Calculated column/table, Row/Filter context, Context transition, CALCULATE/CALCULATETABLE, FILTER, ALL/REMOVEFILTERS/ALLSELECTED/ALLEXCEPT/KEEPFILTERS, Time-intelligence, Calculation groups, Variables (VAR), UDF. → xem `dax-best-practices.md`.
5. **Visual** — Card, Matrix, Slicer, Conditional formatting, Tooltip page, Drill-through/down, Bookmark, Field/Numeric parameter, Selection pane, Sync slicers, Mobile layout, Paginated report, Waterfall/combo/scatter. → dựng qua kit `report-templates/kpim-business-light` + `apply_template`.
6. **Service** — Gateway (on-premises data gateway), Scheduled/Incremental refresh, Dataflow, Datamart, OneLake, Endorsement (Promoted/Certified), Deployment pipeline, Publish/Share, Build permission, App audience.
7. **Security** — RLS (static/dynamic), OLS, Workspace role, Item-level access, Sensitivity label, USERPRINCIPALNAME/USERNAME/CUSTOMDATA, Microsoft Entra ID, B2B guest. Bảo mật cứng = RLS + service principal quyền tối thiểu.
8. **Optimize** — Performance Analyzer, DAX query view, VertiPaq, Cardinality reduction, Composite model, Aggregation table, DAX Studio, VertiPaq Analyzer, columnstore/batch mode.

## Thứ tự học/dependency
Power Query basics → Data types → Model (star schema + relationships + date table) → DAX (context → CALCULATE → measures → time-intelligence) → Visual/report → Service (refresh/RLS/publish) → Optimize.

## Vận hành (governance) — lưu ý thực chiến
- **Gateway**: cần cho refresh nguồn on-prem từ Service; standard (enterprise, chia sẻ) vs personal.
- **Development lifecycle**: Dev → Test → Prod qua **Deployment pipeline**; PBIP + git để version control.
- **Report Server (on-prem)**: bản Developer free; thiếu Dashboard/Scorecard/Subscription so với Service; RLS 2 lớp.
- **SSRS/paginated**: cho báo cáo in ấn/pixel-perfect; kết hợp Power BI cho tương tác.
- **Power Query vs DAX**: biến đổi/chuẩn hóa dữ liệu → làm ở **Power Query** (fold về nguồn); tính toán theo ngữ cảnh báo cáo → **DAX measure**. Không nhồi logic nghiệp vụ nặng vào DAX nếu Power Query/SQL làm được rẻ hơn.

## Nguồn sâu hơn
`dax-best-practices.md` · `powerquery-m-best-practices.md` · `sql-best-practices.md` · `gotchas.md` · Microsoft Learn (learn.microsoft.com/power-bi, /dax, /power-query).
