"""Xác thực đích Power BI Desktop trước khi tạo chuỗi kết nối MSOLAP."""

import re


def local_connection_string(port: str | int, model_id: str | None = None) -> str:
    """Chỉ kết nối localhost; từ chối ký tự có thể thêm thuộc tính kết nối."""
    port_text = str(port)
    if not re.fullmatch(r"[0-9]{1,5}", port_text) or not 1 <= int(port_text) <= 65535:
        raise ValueError("Cổng Power BI Desktop không hợp lệ.")
    connection = f"Provider=MSOLAP;Data Source=localhost:{port_text};"
    if model_id is not None:
        if (not isinstance(model_id, str) or not model_id.strip()
                or len(model_id) > 256 or re.search(r"[\x00-\x1f\x7f]", model_id)):
            raise ValueError("Mã model Power BI không hợp lệ.")
        # ADO.NET dùng nháy kép quanh value; nháy kép bên trong phải gấp đôi.
        # Ký tự ';' vì thế ở trong tên catalog, không tạo thêm thuộc tính kết nối.
        connection += 'Catalog="' + model_id.replace('"', '""') + '";'
    return connection
