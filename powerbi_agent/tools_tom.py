"""Tool GHI model qua TOM (fallback nhẹ).

LƯU Ý PHÂN VAI: thao tác modeling đầy đủ (bulk, transaction, TMDL, validate)
nên dùng `microsoft/powerbi-modeling-mcp`. Hai tool này giữ làm fallback khi
máy không cài modeling-mcp hoặc cần thao tác đơn lẻ nhanh — KHÔNG mở rộng thêm.
"""

from powerbi_agent.connection import local_connection_string
from powerbi_agent.util import log, short_err


def _connect_db(TOM, port: str, model_id: str):
    """Mở kết nối TOM và trả (server, db). Caller chịu trách nhiệm Disconnect."""
    server = TOM.Server()
    server.Connect(local_connection_string(port, model_id))
    db = None
    if server.Databases.Contains(model_id):
        db = server.Databases[model_id]
    return server, db


def _disconnect_safely(server) -> None:
    """Lỗi đóng TOM không được thay thế phản hồi lỗi đã che cho người dùng."""
    if server is None:
        return
    try:
        if server.Connected:
            server.Disconnect()
    except Exception as exc:
        log.warning("TOM disconnect thất bại (%s)", type(exc).__name__)


def register(mcp, tabular_loaded: bool):
    """Đăng ký các tool TOM vào instance FastMCP."""

    _NOT_LOADED = (
        "Lỗi: Thư viện Microsoft.AnalysisServices.Tabular (TOM) chưa được nạp. "
        "Hãy cài SSMS hoặc Analysis Services client libraries (override ADOMD_LIB_DIR nếu cần)."
    )

    @mcp.tool()
    def add_measure_local(
        port: str,
        model_id: str,
        table_name: str,
        measure_name: str,
        expression: str,
        format_string: str = None,
        description: str = None,
    ) -> str:
        """
        Tạo mới hoặc cập nhật một Measure DAX trực tiếp vào mô hình Power BI Desktop đang mở (TOM).
        Với thao tác modeling hàng loạt/phức tạp, ưu tiên MCP `powerbi-modeling` (Microsoft) nếu có.
        - port / model_id: lấy từ list_local_reports.
        - table_name: bảng chứa Measure (ví dụ: 'Sales').
        - measure_name: tên Measure (ví dụ: 'Total Sales').
        - expression: công thức DAX (ví dụ: 'SUM(Sales[Amount])').
        - format_string: định dạng hiển thị (ví dụ: '#,0' hoặc '0.0%').
        - description: mô tả ghi chú.
        """
        if not tabular_loaded:
            return _NOT_LOADED
        try:
            import Microsoft.AnalysisServices.Tabular as TOM
        except ImportError:
            return "Lỗi import TOM namespace."

        server = None
        try:
            server, db = _connect_db(TOM, port, model_id)
            if not db:
                return f"Không tìm thấy Database/Catalog '{model_id}' trên cổng {port}."

            model = db.Model
            if not model.Tables.Contains(table_name):
                return f"Bảng '{table_name}' không tồn tại trong mô hình dữ liệu."

            table = model.Tables[table_name]
            is_update = table.Measures.Contains(measure_name)
            if is_update:
                measure = table.Measures[measure_name]
            else:
                measure = TOM.Measure()
                measure.Name = measure_name

            measure.Expression = expression
            if format_string:
                measure.FormatString = format_string
            if description:
                measure.Description = description

            if not is_update:
                table.Measures.Add(measure)

            model.SaveChanges()
            action = "cập nhật" if is_update else "tạo mới"
            return f"Thành công: Đã {action} measure '[{measure_name}]' trong bảng '{table_name}'."
        except Exception as e:
            log.error("add_measure_local thất bại (%s)", type(e).__name__)
            return f"Lỗi khi thêm/sửa measure qua TOM: {short_err(e)}"
        finally:
            _disconnect_safely(server)

    @mcp.tool()
    def add_relationship_local(
        port: str,
        model_id: str,
        from_table: str,
        from_column: str,
        to_table: str,
        to_column: str,
        is_active: bool = True,
    ) -> str:
        """
        Tạo mối quan hệ Many-to-One giữa hai bảng trong mô hình Power BI Desktop đang mở (TOM).
        Với thao tác modeling hàng loạt/phức tạp, ưu tiên MCP `powerbi-modeling` (Microsoft) nếu có.
        - from_table/from_column: phía NHIỀU (Many) — thường là bảng Fact.
        - to_table/to_column: phía MỘT (One) — thường là bảng Dim.
        - is_active: True = quan hệ active (mặc định).
        """
        if not tabular_loaded:
            return _NOT_LOADED
        try:
            import Microsoft.AnalysisServices.Tabular as TOM
        except ImportError:
            return "Lỗi import TOM namespace."

        server = None
        try:
            server, db = _connect_db(TOM, port, model_id)
            if not db:
                return f"Không tìm thấy Database/Catalog '{model_id}' trên cổng {port}."

            model = db.Model

            if not model.Tables.Contains(from_table):
                return f"Bảng nguồn '{from_table}' không tồn tại."
            if not model.Tables.Contains(to_table):
                return f"Bảng đích '{to_table}' không tồn tại."

            tbl_from = model.Tables[from_table]
            tbl_to = model.Tables[to_table]

            if not tbl_from.Columns.Contains(from_column):
                return f"Cột '{from_column}' không tồn tại trong bảng '{from_table}'."
            if not tbl_to.Columns.Contains(to_column):
                return f"Cột '{to_column}' không tồn tại trong bảng '{to_table}'."

            rel = TOM.SingleColumnRelationship()
            rel.FromTable = tbl_from
            rel.FromColumn = tbl_from.Columns[from_column]
            rel.ToTable = tbl_to
            rel.ToColumn = tbl_to.Columns[to_column]
            rel.IsActive = is_active
            rel.FromCardinality = TOM.RelationshipCardinality.Many
            rel.ToCardinality = TOM.RelationshipCardinality.One

            model.Relationships.Add(rel)
            model.SaveChanges()

            return (
                f"Thành công: Đã tạo mối quan hệ '{from_table}[{from_column}]' (Nhiều) "
                f"-> '{to_table}[{to_column}]' (Một)."
            )
        except Exception as e:
            log.error("add_relationship_local thất bại (%s)", type(e).__name__)
            return f"Lỗi khi tạo mối quan hệ qua TOM: {short_err(e)}"
        finally:
            _disconnect_safely(server)
