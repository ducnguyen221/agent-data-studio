import sys
import os
import io

# Cấu hình encoding UTF-8 cho stdout để tránh lỗi Unicode trên Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Bộ nạp ADOMD.NET đa-phiên-bản nằm trong mcp_server_powerbi; import bên dưới sẽ tự dò & nạp
# (mọi SSMS / ADOMD.NET standalone / GAC) — không hardcode đường dẫn SSMS.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root — script nằm trong scripts/

try:
    from mcp_server_powerbi import find_active_pbi_ports
    from powerbi_agent.connection import local_connection_string
    from pyadomd import Pyadomd
    print("[INFO] Đã nạp thành công các thư viện kết nối Power BI.")
except ImportError:
    print("[ERROR] Thiếu thư viện hoặc file mcp_server_powerbi.py; kiểm tra bộ cài.")
    sys.exit(1)

def run_test():
    print("\n--- BẮT ĐẦU KIỂM TRA KẾT NỐI POWER BI DESKTOP ---")
    
    # 1. Tìm các phiên bản đang chạy
    instances = find_active_pbi_ports()
    if not instances:
        print("[WARNING] Không tìm thấy phiên bản Power BI Desktop nào đang mở.")
        print("          -> Vui lòng mở ít nhất 1 tệp báo cáo (.pbix) trên máy và chạy lại file test này.")
        return False
        
    print(f"[SUCCESS] Tìm thấy {len(instances)} phiên bản Power BI Desktop đang mở:")
    connected = False
    for inst in instances:
        port = inst['port']
        workspace_id = inst['workspace_id']
        print(f"          - Cổng: {port} (Workspace ID: {workspace_id})")
        
        # 2. Thử nghiệm kết nối ADOMD.NET
        print(f"          -> Thử kết nối tới cổng {port}...")
        try:
            conn_str = local_connection_string(port)
            with Pyadomd(conn_str) as conn:
                query = "SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS"
                with conn.cursor().execute(query) as cur:
                    catalogs = cur.fetchall()
                    catalog_name = catalogs[0][0] if catalogs else "Unknown"
                    print(f"[SUCCESS] Kết nối thành công! Tên Model (Catalog): {catalog_name}")
                    
                print("          -> Thử lấy danh sách bảng (đối đa 5 bảng đầu)...")
                tables_query = "SELECT [Name] FROM $SYSTEM.TMSCHEMA_TABLES"
                with conn.cursor().execute(tables_query) as cur:
                    tables = cur.fetchall()
                    if tables:
                        # Lọc bỏ các bảng ngày tự động của hệ thống
                        filtered_tables = [t[0] for t in tables if not t[0].startswith('LocalDateTable_') and not t[0].startswith('DateTableTemplate_')][:5]
                        print(f"          - Các bảng mẫu tìm thấy: {filtered_tables}")
                    else:
                        print("          - Không tìm thấy bảng dữ liệu nào.")
                connected = True
        except Exception:
            print(f"[ERROR] Lỗi khi kết nối ADOMD tới cổng {port}.")
            print("        -> Có thể máy chưa cài đặt ADOMD.NET Client Library hoặc Power BI Desktop đang bận.")
            print("        -> Tải thư viện ADOMD.NET tại: https://learn.microsoft.com/en-us/analysis-services/client-libraries")
            
    print("--- KẾT THÚC KIỂM TRA ---")
    return connected

if __name__ == "__main__":
    sys.exit(0 if run_test() else 1)
