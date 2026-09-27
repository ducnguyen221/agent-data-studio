"""Tool truy vấn: Desktop (ADOMD) + Service (REST) + schema discovery. Đăng ký qua register()."""

import os
import re

import pandas as pd
import requests
from msal import ConfidentialClientApplication

from powerbi_agent import policy
from powerbi_agent.adomd import adomd_missing_message, import_pyadomd
from powerbi_agent.connection import local_connection_string
from powerbi_agent.discovery import find_active_pbi_ports
from powerbi_agent.util import MAX_ROWS, df_to_markdown_capped, log, short_err

# MSAL app singleton — giữ token cache trong process, hết 1-round-trip-mỗi-call
_msal_app = None
_DATASET_GUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\Z")


def get_azure_token():
    """Lấy Access Token từ Entra ID (client-credential). Cache token qua app singleton."""
    global _msal_app
    from dotenv import load_dotenv
    from powerbi_agent._env import secrets_file

    load_dotenv(secrets_file())
    client_id = os.getenv("CLIENT_ID")
    client_secret = os.getenv("CLIENT_SECRET")
    tenant_id = os.getenv("TENANT_ID")

    if not all([client_id, client_secret, tenant_id]):
        raise ValueError("Thiếu cấu hình Power BI Service trong kho thông tin xác thực đã chọn.")

    scope = ["https://analysis.windows.net/powerbi/api/.default"]
    if _msal_app is None:
        _msal_app = ConfidentialClientApplication(
            client_id,
            client_secret=client_secret,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
        )

    # acquire_token_for_client tự dùng cache của app trước, hết hạn mới gọi mạng
    result = _msal_app.acquire_token_for_client(scopes=scope)
    if "access_token" in result:
        return result["access_token"]
    raise RuntimeError("Không thể lấy token Power BI Service; kiểm tra quyền và cấu hình ứng dụng.")


def _query_df(port: str, model_id: str, query: str) -> pd.DataFrame:
    Pyadomd = import_pyadomd()

    conn_str = local_connection_string(port, model_id)
    with Pyadomd(conn_str) as conn:
        with conn.cursor().execute(query) as cur:
            data = cur.fetchall()
            if not data:
                return pd.DataFrame()
            columns = [desc[0] for desc in cur.description] if cur.description else None
            return pd.DataFrame(data, columns=columns)


def register(mcp, adomd_loaded: bool = True):
    """Đăng ký các tool truy vấn + discovery vào instance FastMCP.

    adomd_loaded: app truyền app.ADOMD_LOADED. False thì tool Desktop trả lỗi thiếu thành phần
    TRƯỚC khi import pyadomd (pyadomd nuốt lỗi thiếu DLL rồi hỏng muộn bằng NameError).
    Mặc định True giữ hành vi cũ cho người gọi trực tiếp (test đăng ký tool riêng lẻ).
    """

    @mcp.tool()
    def list_local_reports() -> str:
        """Liệt kê các báo cáo Power BI Desktop đang mở trên máy tính kèm thông tin cổng kết nối."""
        if not adomd_loaded:
            return adomd_missing_message()
        try:
            Pyadomd = import_pyadomd()
        except ImportError:
            return "Thiếu ADOMD.NET hoặc pyadomd; mở hướng dẫn cài Power BI Desktop để sửa."
        instances = find_active_pbi_ports()
        if not instances:
            return "Không tìm thấy phiên bản Power BI Desktop nào đang hoạt động trên máy."

        output = "Các báo cáo đang mở:\n"
        for inst in instances:
            try:
                conn_str = local_connection_string(inst["port"])
                with Pyadomd(conn_str) as conn:
                    with conn.cursor().execute("SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS") as cur:
                        catalogs = cur.fetchall()
                        catalog_name = catalogs[0][0] if catalogs else "Unknown"
                output += f"- Cổng: {inst['port']} | Mã Model: {catalog_name}\n"
            except Exception as e:
                output += f"- Cổng: {inst['port']} | Lỗi lấy tên Model (có thể do thiếu driver ADOMD.NET hoặc cổng bận): {short_err(e)}\n"

        return output

    @mcp.tool()
    def list_tables(port: str, model_id: str) -> str:
        """
        Liệt kê các bảng trong model đang mở (đã lọc bảng hệ thống LocalDateTable/DateTableTemplate).
        - port / model_id: lấy từ list_local_reports.
        """
        if not adomd_loaded:
            return f"Lỗi list_tables: {adomd_missing_message()}"
        try:
            df = _query_df(port, model_id, "SELECT [Name], [Description] FROM $SYSTEM.TMSCHEMA_TABLES")
            if df.empty:
                return "Model không có bảng nào."
            df = df[~df["Name"].str.startswith("LocalDateTable_") & ~df["Name"].str.startswith("DateTableTemplate_")]
            return df_to_markdown_capped(df, 0)
        except Exception as e:
            log.error("list_tables thất bại (%s)", type(e).__name__)
            return f"Lỗi list_tables: {short_err(e)}"

    @mcp.tool()
    def describe_table(port: str, model_id: str, table_name: str) -> str:
        """
        Mô tả 1 bảng: danh sách cột (tên + kiểu dữ liệu) và các measure đặt trong bảng đó.
        - port / model_id: lấy từ list_local_reports.
        - table_name: tên bảng (lấy từ list_tables).
        """
        if not adomd_loaded:
            return f"Lỗi describe_table: {adomd_missing_message()}"
        try:
            df_t = _query_df(port, model_id, "SELECT [ID], [Name] FROM $SYSTEM.TMSCHEMA_TABLES")
            row = df_t[df_t["Name"] == table_name]
            if row.empty:
                return f"Không tìm thấy bảng '{table_name}'. Dùng list_tables để xem danh sách."
            table_id = row.iloc[0]["ID"]

            df_c = _query_df(
                port, model_id,
                # LƯU Ý DMV: cột kiểu dữ liệu tên là [ExplicitDataType] — KHÔNG phải [DataType]
                "SELECT [TableID], [ExplicitName], [ExplicitDataType] AS [DataType] FROM $SYSTEM.TMSCHEMA_COLUMNS",
            )
            # TOM DataType enum — xác nhận live qua RowNumber (luôn Int64=6)
            dtype_map = {2: "String", 5: "Boolean", 6: "Int64", 8: "Double", 9: "DateTime",
                         10: "Decimal", 17: "Binary", 19: "Unknown", 20: "Variant"}
            out = [f"## Bảng `{table_name}`", "", "### Cột"]
            cols = df_c[(df_c["TableID"] == table_id) & df_c["ExplicitName"].notna()]
            cols = cols[~cols["ExplicitName"].str.startswith("RowNumber-")]  # cột nội bộ engine
            if cols.empty:
                out.append("*Không có cột tùy chỉnh.*")
            else:
                for _, c in cols.iterrows():
                    out.append(f"- `{c['ExplicitName']}` ({dtype_map.get(c['DataType'], 'Unknown')})")

            df_m = _query_df(
                port, model_id,
                "SELECT [TableID], [Name], [Expression] FROM $SYSTEM.TMSCHEMA_MEASURES",
            )
            meas = df_m[df_m["TableID"] == table_id] if not df_m.empty else pd.DataFrame()
            out.append("")
            out.append("### Measure trong bảng")
            if meas.empty:
                out.append("*Không có measure.*")
            else:
                for _, m in meas.iterrows():
                    out.append(f"- `[{m['Name']}]` = `{str(m['Expression'])[:200]}`")
            return "\n".join(out)
        except Exception as e:
            log.error("describe_table thất bại (%s)", type(e).__name__)
            return f"Lỗi describe_table: {short_err(e)}"

    @mcp.tool()
    def execute_dax_local(port: str, model_id: str, dax_query: str, max_rows: int = MAX_ROWS) -> str:
        """
        Thực thi một truy vấn DAX trực tiếp lên báo cáo Power BI Desktop đang mở.
        - port: Cổng kết nối (ví dụ: '51234')
        - model_id: Tên catalog/model ID lấy từ công cụ list_local_reports
        - dax_query: Câu lệnh DAX (ví dụ: 'EVALUATE SUMMARIZECOLUMNS(...)')
        - max_rows: Số dòng tối đa trả về (mặc định 1000; kết quả có cột dimension bị siết còn 200
          khi policy aggregate-only bật). Đặt 0 để bỏ giới hạn mềm.
        LƯU Ý POLICY: mặc định chặn dump bảng thô (EVALUATE 'Bảng' / ALL()) và cột trong PII blocklist.
        """
        allowed, reason = policy.check_dax(dax_query, tool="execute_dax_local")
        if not allowed:
            return reason
        if not adomd_loaded:
            policy.audit("execute_dax_local", dax_query, "error")
            return f"Lỗi khi thực thi DAX cục bộ: {adomd_missing_message()}"
        try:
            df = _query_df(port, model_id, dax_query)
            if df.empty:
                policy.audit("execute_dax_local", dax_query, "allowed", 0)
                return "Truy vấn thành công nhưng không có dữ liệu trả về."
            policy.audit("execute_dax_local", dax_query, "allowed", len(df))
            effective_max = policy.cap_dimension_rows(df, max_rows)
            return df_to_markdown_capped(df, effective_max)
        except Exception as e:
            policy.audit("execute_dax_local", dax_query, "error")
            log.error("execute_dax_local thất bại (%s)", type(e).__name__)
            return f"Lỗi khi thực thi DAX cục bộ: {short_err(e)}"

    @mcp.tool()
    def execute_dax_service(dataset_id: str, dax_query: str, max_rows: int = MAX_ROWS) -> str:
        """
        Truy vấn dữ liệu từ Dataset đã xuất bản trên Cloud Power BI Service thông qua REST API.
        - dataset_id: Mã GUID của dataset cần truy vấn.
        - dax_query: Câu lệnh DAX (ví dụ: 'EVALUATE SUMMARIZECOLUMNS(...)')
        - max_rows: Số dòng tối đa trả về (mặc định 1000; siết 200 khi kết quả có cột dimension).
        LƯU Ý POLICY: như execute_dax_local.
        """
        allowed, reason = policy.check_dax(dax_query, tool="execute_dax_service")
        if not allowed:
            return reason
        if not isinstance(dataset_id, str) or not _DATASET_GUID.fullmatch(dataset_id):
            policy.audit("execute_dax_service", dax_query, "invalid_target")
            return "Mã dataset không hợp lệ; chọn GUID của model từ Power BI."
        try:
            token = get_azure_token()
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries"
            payload = {
                "queries": [{"query": dax_query}],
                "serializerSettings": {"includeNulls": True}
            }

            response = requests.post(url, json=payload, headers=headers, timeout=(10, 60))
            if response.status_code != 200:
                policy.audit("execute_dax_service", dax_query, "error")
                return f"Lỗi gọi API Power BI (Code {response.status_code}); chi tiết phản hồi đã ẩn."

            res_data = response.json()
            if res_data.get("error") is not None:
                policy.audit("execute_dax_service", dax_query, "error")
                return "Power BI Service trả lỗi truy vấn; chi tiết phản hồi đã ẩn."
            results = res_data.get("results", [])
            if any(result.get("error") is not None or
                   any(table.get("error") is not None for table in result.get("tables", []))
                   for result in results):
                policy.audit("execute_dax_service", dax_query, "error")
                return "Power BI Service trả lỗi truy vấn; chi tiết phản hồi đã ẩn."
            tables = results[0].get('tables', []) if results else []
            if not tables:
                policy.audit("execute_dax_service", dax_query, "allowed", 0)
                return "Không có dữ liệu trả về từ Dataset."

            rows = tables[0].get('rows', [])
            df = pd.DataFrame(rows)
            policy.audit("execute_dax_service", dax_query, "allowed", len(df))
            effective_max = policy.cap_dimension_rows(df, max_rows)
            return df_to_markdown_capped(df, effective_max)

        except Exception as e:
            policy.audit("execute_dax_service", dax_query, "error")
            log.error("execute_dax_service thất bại (%s)", type(e).__name__)
            return f"Lỗi kết nối Power BI Service: {short_err(e)}"
