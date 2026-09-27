"""Nạp ADOMD.NET đa-phiên-bản (portable).

Bản gốc hardcode đúng 1 đường dẫn SSMS 21. Bản này dò nhiều vị trí phổ biến
để chạy được trên máy bất kỳ (SSMS bản khác, ADOMD.NET standalone, hoặc GAC).
Override thủ công qua biến môi trường ADOMD_LIB_DIR là ĐỘC QUYỀN: đã đặt thì chỉ nạp DLL
trong đúng thư mục đó; thiếu DLL thì báo thiếu thành phần, không âm thầm dò SSMS/GAC.

QUAN TRỌNG: load_adomd() phải được gọi TRƯỚC khi import pyadomd ở bất kỳ đâu.
"""

import contextlib
import glob
import os
import sys

from powerbi_agent.util import log

ADOMD_DLL = "Microsoft.AnalysisServices.AdomdClient.dll"
TABULAR_DLL = "Microsoft.AnalysisServices.Tabular.dll"

# Lý do lần nạp ADOMD gần nhất thất bại (vd override thiếu DLL) — để tool nêu lại cho người dùng.
_adomd_issue = None


def candidate_adomd_dirs():
    """Sinh danh sách thư mục ứng viên có thể chứa AdomdClient.dll, theo thứ tự ưu tiên.

    Có ADOMD_LIB_DIR thì CHỈ trả thư mục đó (override độc quyền), không dò tiếp SSMS/SDK.
    """
    dirs = []

    # 1. Override tường minh từ môi trường (đường dẫn tới thư mục chứa DLL) — độc quyền
    env_dir = os.getenv("ADOMD_LIB_DIR")
    if env_dir:
        return [env_dir] if os.path.isdir(env_dir) else []

    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")

    # 2. SQL Server Management Studio (mọi phiên bản: 18, 19, 20, 21, 22, ...)
    for base in (pf, pf86):
        dirs += glob.glob(os.path.join(base, "Microsoft SQL Server Management Studio*", "*", "Common7", "IDE"))
        dirs += glob.glob(os.path.join(base, "Microsoft SQL Server Management Studio*", "Common7", "IDE"))

    # 3. ADOMD.NET cài standalone (MSI "Analysis Services client libraries")
    for base in (pf, pf86):
        dirs += glob.glob(os.path.join(base, "Microsoft.NET", "ADOMD.NET", "*"))

    # 4. SQL Server SDK assemblies
    for base in (pf, pf86):
        dirs += glob.glob(os.path.join(base, "Microsoft SQL Server", "*", "SDK", "Assemblies"))

    # 5. Power BI Desktop / Excel cài kèm bộ thư viện AS (ít gặp nhưng có)
    dirs += glob.glob(os.path.join(pf, "Microsoft Power BI Desktop", "bin"))

    # Khử trùng lặp giữ nguyên thứ tự
    seen = set()
    uniq = []
    for d in dirs:
        if d and d not in seen and os.path.isdir(d):
            seen.add(d)
            uniq.append(d)
    return uniq


def _load_from_override(clr, env_dir: str, dll: str) -> bool:
    """Nạp đúng file `dll` trong ADOMD_LIB_DIR; KHÔNG rơi về SSMS/GAC khi thất bại."""
    global _adomd_issue
    path = os.path.join(env_dir, dll)
    if os.path.isfile(path) and env_dir not in sys.path:
        sys.path.append(env_dir)
    try:
        clr.AddReference(path)  # đường tuyệt đối: pythonnet chỉ nạp đúng file này
        log.info("Đã nạp %s từ ADOMD_LIB_DIR.", dll)
        return True
    except Exception as e:
        if not os.path.isfile(path):
            issue = f"ADOMD_LIB_DIR={env_dir} không chứa {dll}"
        else:
            issue = f"ADOMD_LIB_DIR={env_dir}: nạp {dll} thất bại ({type(e).__name__})"
        if dll == ADOMD_DLL:
            _adomd_issue = issue
        log.warning("%s; override là độc quyền nên không dò SSMS/GAC.", issue)
        return False


def adomd_missing_message() -> str:
    """Thông điệp cho tool Desktop khi ADOMD.NET chưa nạp (trả TRƯỚC khi import pyadomd)."""
    reason = f" ({_adomd_issue})" if _adomd_issue else ""
    return (
        f"Thiếu ADOMD.NET{reason}. Cài SSMS/ADOMD.NET (Analysis Services client libraries) "
        f"hoặc đặt ADOMD_LIB_DIR tới thư mục chứa {ADOMD_DLL}, rồi mở lại host."
    )


def import_pyadomd():
    """Import `Pyadomd`, đẩy mọi print() lúc import sang stderr.

    pyadomd 0.1.1 in banner lỗi ra STDOUT khi thiếu DLL — với MCP stdio, stdout là kênh
    JSON-RPC nên phải chặn. Chỉ gọi sau khi load_adomd() đã trả True.
    """
    with contextlib.redirect_stdout(sys.stderr):
        from pyadomd import Pyadomd
    return Pyadomd


def load_adomd():
    """Thử nạp AdomdClient: dò thư mục có DLL trước, cuối cùng thử GAC. Trả về True nếu thành công.

    Có ADOMD_LIB_DIR thì chỉ thử thư mục đó (xem _load_from_override).
    """
    global _adomd_issue
    _adomd_issue = None
    try:
        import clr
    except Exception as e:  # pythonnet chưa sẵn sàng
        log.warning("Không import được pythonnet/clr (%s).", type(e).__name__)
        return False

    env_dir = os.getenv("ADOMD_LIB_DIR")
    if env_dir:
        return _load_from_override(clr, env_dir, ADOMD_DLL)

    # Dò các thư mục ứng viên có chứa DLL và thêm vào sys.path
    for d in candidate_adomd_dirs():
        if os.path.exists(os.path.join(d, ADOMD_DLL)):
            if d not in sys.path:
                sys.path.append(d)
            try:
                clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
                log.info("Đã nạp ADOMD.NET từ thư mục client library.")
                return True
            except Exception:
                continue  # thử thư mục kế tiếp

    # Phương án cuối: DLL đã đăng ký trong GAC -> AddReference theo tên là đủ
    try:
        clr.AddReference("Microsoft.AnalysisServices.AdomdClient")
        log.info("Đã nạp ADOMD.NET từ GAC.")
        return True
    except Exception as e:
        log.warning(
            "Chưa nạp được ADOMD.NET (%s). Các tool local sẽ báo lỗi cho tới khi cài "
            "ADOMD.NET / SSMS. Phần Power BI Service (cloud) vẫn hoạt động bình thường. "
            "Có thể trỏ thủ công qua biến môi trường ADOMD_LIB_DIR.",
            type(e).__name__,
        )
        return False


def load_tabular():
    """Thử nạp Microsoft.AnalysisServices.Tabular (TOM — đường GHI model). Trả về True nếu thành công.

    Dò cùng bộ thư mục ứng viên với ADOMD (SSMS ship cả 2 DLL cạnh nhau); cùng luật
    ADOMD_LIB_DIR độc quyền.
    """
    try:
        import clr
    except Exception as e:
        log.warning("Không import được pythonnet/clr (%s).", type(e).__name__)
        return False

    env_dir = os.getenv("ADOMD_LIB_DIR")
    if env_dir:
        return _load_from_override(clr, env_dir, TABULAR_DLL)

    for d in candidate_adomd_dirs():
        if os.path.exists(os.path.join(d, TABULAR_DLL)):
            if d not in sys.path:
                sys.path.append(d)
            try:
                clr.AddReference("Microsoft.AnalysisServices.Tabular")
                log.info("Đã nạp Microsoft.AnalysisServices.Tabular từ thư mục client library.")
                return True
            except Exception:
                continue

    try:
        clr.AddReference("Microsoft.AnalysisServices.Tabular")
        log.info("Đã nạp Microsoft.AnalysisServices.Tabular từ GAC.")
        return True
    except Exception as e:
        log.warning(
            "Chưa nạp được Microsoft.AnalysisServices.Tabular (%s). "
            "Các tool GHI local (TOM: add_measure_local, add_relationship_local) sẽ báo lỗi.",
            type(e).__name__,
        )
        return False
