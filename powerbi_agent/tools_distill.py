"""Distill model schema → Markdown blueprint (bảng/cột/measure/relationship + Mermaid ERD).

Tên tool là `distill_model_schema` vì nó distill MODEL — distill report template (PBIR)
là việc của tools_template.py.

Đích ghi KHÔNG hardcode theo máy: tham số `output_dir` → env `POWERBI_DISTILL_DIR`
→ mặc định `<thư mục dự án>/distilled/` (NGOÀI repo — schema model khách hàng
là dữ liệu nhạy cảm, không được commit).
"""

import os
import tempfile
import re

import pandas as pd
from pyadomd import Pyadomd

from powerbi_agent.discovery import find_active_pbi_ports
from powerbi_agent.util import log, short_err


# TOM DataType enum (Microsoft.AnalysisServices.Tabular) — xác nhận live qua RowNumber (luôn Int64=6)
_DATA_TYPE_MAP = {
    2: "String", 5: "Boolean", 6: "Int64", 8: "Double",
    9: "DateTime", 10: "Decimal", 17: "Binary", 19: "Unknown", 20: "Variant",
}


def _resolve_output_dir(output_dir: str | None) -> str:
    if output_dir:
        return output_dir
    env_dir = os.getenv("POWERBI_DISTILL_DIR")
    if env_dir:
        return env_dir
    from powerbi_agent.knowledge import resolve_root
    root = resolve_root()
    # Schema model là dữ liệu khách hàng -> đi cùng thư mục dữ liệu, không vào repo.
    return os.path.join(root, "distilled") if root else os.path.join(tempfile.gettempdir(), "powerbi-agent-distilled")


def _catalog_of(port: str) -> str:
    conn_str = f"Provider=MSOLAP;Data Source=localhost:{port};"
    with Pyadomd(conn_str) as conn:
        with conn.cursor().execute("SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS") as cur:
            catalogs = cur.fetchall()
            return catalogs[0][0] if catalogs else "Unknown"


def register(mcp):
    """Đăng ký tool distill vào instance FastMCP."""

    @mcp.tool()
    def distill_model_schema(
        port: str = None,
        model_id: str = None,
        output_filename: str = None,
        output_dir: str = None,
    ) -> str:
        """
        Trích xuất cấu trúc mô hình dữ liệu (bảng, cột, quan hệ, measure) của báo cáo Power BI
        Desktop đang mở thành tài liệu Markdown blueprint (kèm sơ đồ Mermaid ERD) để Agent
        tham chiếu khi viết DAX / thiết kế báo cáo.
        - port / model_id: để trống sẽ tự dò (nếu chỉ có 1 báo cáo đang mở).
        - output_filename: tên file .md (mặc định 'distilled_model_<model_id>.md').
        - output_dir: thư mục ghi; mặc định env POWERBI_DISTILL_DIR hoặc <thư mục dự án>/distilled/.
          LƯU Ý: schema model có thể nhạy cảm (tên bảng/cột/công thức nghiệp vụ) — đừng ghi vào repo public.
        """
        try:
            # Tự động dò cổng & model_id nếu thiếu
            if not port or not model_id:
                instances = find_active_pbi_ports()
                if not instances:
                    return "Không tìm thấy phiên bản Power BI Desktop nào đang hoạt động để trích xuất."
                if len(instances) > 1:
                    output = "Có nhiều báo cáo đang mở. Vui lòng cung cấp chính xác cổng và model_id:\n"
                    for inst in instances:
                        try:
                            output += f"- Cổng: {inst['port']} | Mã Model: {_catalog_of(inst['port'])}\n"
                        except Exception:
                            output += f"- Cổng: {inst['port']} (Không lấy được model_id)\n"
                    return output
                port = port or instances[0]["port"]
                if not model_id:
                    try:
                        model_id = _catalog_of(port)
                    except Exception as e:
                        return f"Lỗi lấy tên Model từ cổng {port}: {short_err(e)}"

            conn_str = f"Provider=MSOLAP;Data Source=localhost:{port};Catalog={model_id};"
            with Pyadomd(conn_str) as conn:
                def get_df(query):
                    with conn.cursor().execute(query) as cur:
                        data = cur.fetchall()
                        if not data:
                            return pd.DataFrame()
                        cols = [desc[0] for desc in cur.description]
                        return pd.DataFrame(data, columns=cols)

                df_tables = get_df("SELECT [ID], [Name], [Description] FROM $SYSTEM.TMSCHEMA_TABLES")
                df_columns = get_df(
                    # LƯU Ý DMV: cột kiểu dữ liệu tên là [ExplicitDataType] — KHÔNG phải [DataType]
                    "SELECT [TableID], [ID] as [ColumnID], [ExplicitName] as [Name], "
                    "[ExplicitDataType] as [DataType], [Description] "
                    "FROM $SYSTEM.TMSCHEMA_COLUMNS"
                )
                df_measures = get_df(
                    "SELECT [TableID], [Name], [Expression], [Description], [FormatString] "
                    "FROM $SYSTEM.TMSCHEMA_MEASURES"
                )
                df_relationships = get_df(
                    "SELECT [FromTableID], [FromColumnID], [ToTableID], [ToColumnID], [IsActive] "
                    "FROM $SYSTEM.TMSCHEMA_RELATIONSHIPS"
                )

            if df_tables.empty:
                return f"Không tìm thấy bảng nào trong mô hình '{model_id}'."

            # Loại bỏ bảng hệ thống ngày
            df_tables = df_tables[
                ~df_tables["Name"].str.startswith("LocalDateTable_")
                & ~df_tables["Name"].str.startswith("DateTableTemplate_")
            ]
            valid_table_ids = set(df_tables["ID"].tolist())
            table_id_to_name = dict(zip(df_tables["ID"], df_tables["Name"]))
            column_id_to_name = {}

            if not df_columns.empty:
                df_columns = df_columns[df_columns["TableID"].isin(valid_table_ids)]
                df_columns = df_columns[df_columns["Name"].notna() & (df_columns["Name"] != "")]
                df_columns = df_columns[~df_columns["Name"].str.startswith("RowNumber-")]  # cột nội bộ engine
                column_id_to_name = dict(zip(df_columns["ColumnID"], df_columns["Name"]))
                df_columns["DataTypeStr"] = df_columns["DataType"].map(_DATA_TYPE_MAP).fillna("Unknown")

            if not df_measures.empty:
                df_measures = df_measures[df_measures["TableID"].isin(valid_table_ids)]

            if not df_relationships.empty:
                df_relationships = df_relationships[
                    df_relationships["FromTableID"].isin(valid_table_ids)
                    & df_relationships["ToTableID"].isin(valid_table_ids)
                ]

            # Tạo nội dung Markdown
            md = [f"# Power BI Model Blueprint: {model_id}"]
            md.append(f"\n- **Cổng kết nối:** {port}")
            md.append(f"- **Số lượng bảng:** {len(df_tables)}")
            md.append(f"- **Số lượng Measure:** {len(df_measures) if not df_measures.empty else 0}")

            md.append("\n## 1. Tables & Columns Schema")
            for _, tbl in df_tables.iterrows():
                t_id, t_name, t_desc = tbl["ID"], tbl["Name"], tbl["Description"]
                desc_str = f" - *{t_desc}*" if t_desc else ""
                md.append(f"\n### Table: `{t_name}`{desc_str}")

                tbl_cols = df_columns[df_columns["TableID"] == t_id] if not df_columns.empty else pd.DataFrame()
                if not tbl_cols.empty:
                    col_list = []
                    for _, col in tbl_cols.iterrows():
                        c_desc_str = f" ({col['Description']})" if col["Description"] else ""
                        col_list.append(f"- `{col['Name']}` ({col['DataTypeStr']}){c_desc_str}")
                    md.append("\n" + "\n".join(col_list))
                else:
                    md.append("\n*Không có cột tùy chỉnh.*")

            md.append("\n## 2. Measures Dictionary")
            if not df_measures.empty:
                for _, meas in df_measures.iterrows():
                    md.append(f"\n### Measure: `[{meas['Name']}]`")
                    md.append(f"- **Bảng chứa:** `{table_id_to_name.get(meas['TableID'], 'Unknown Table')}`")
                    if meas["FormatString"]:
                        md.append(f"- **Định dạng:** `{meas['FormatString']}`")
                    if meas["Description"]:
                        md.append(f"- **Mô tả:** *{meas['Description']}*")
                    md.append("- **Công thức DAX:**")
                    md.append(f"```dax\n{meas['Expression']}\n```")
            else:
                md.append("\n*Không tìm thấy measure nào.*")

            md.append("\n## 3. Data Model Relationships")
            if not df_relationships.empty:
                md.append("\n```mermaid")
                md.append("erDiagram")
                for _, rel in df_relationships.iterrows():
                    from_tbl = table_id_to_name.get(rel["FromTableID"], "Unknown")
                    from_col = column_id_to_name.get(rel["FromColumnID"], "Unknown")
                    to_tbl = table_id_to_name.get(rel["ToTableID"], "Unknown")
                    to_col = column_id_to_name.get(rel["ToColumnID"], "Unknown")
                    is_active = "active" if rel["IsActive"] else "inactive"
                    md.append(f'    {from_tbl} ||--o{{ {to_tbl} : "{from_col} -> {to_col} ({is_active})"')
                md.append("```")
            else:
                md.append("\n*Không có liên kết quan hệ.*")

            from powerbi_agent.knowledge import ensure_outside_repo
            dest_dir = ensure_outside_repo(_resolve_output_dir(output_dir), "schema model")
            os.makedirs(dest_dir, exist_ok=True)
            fname = output_filename if output_filename else f"distilled_model_{model_id}.md"
            fname = re.sub(r'[\\/*?:"<>|]', "_", fname)
            output_path = os.path.join(dest_dir, fname)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(md))

            link_path = output_path.replace("\\", "/")
            return f"Đã trích xuất thành công mô hình '{model_id}' và lưu blueprint tại:\n[Link File](file:///{link_path})"
        except Exception as e:
            log.exception("distill_model_schema thất bại")
            return f"Lỗi chưng cất mô hình: {short_err(e)}"
