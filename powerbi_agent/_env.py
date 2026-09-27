"""Hợp đồng env: config.env, credential và dữ liệu tách khỏi mã nguồn.

`ADS_DATA` trỏ thư mục dữ liệu của máy. Nếu chưa đặt, basic dùng `workspace/`
trong checkout; thư mục này bị loại hoàn toàn khỏi Git. Mã nguồn không được
đọc dữ liệu từ thư mục package hoặc site-packages.
"""

import os
import json
import re

_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_BINDING_FILE = os.path.join(_PKG_PARENT, ".ads-binding.json")


def _inside(path: str, root: str) -> bool:
    try:
        return os.path.commonpath([os.path.normcase(path), os.path.normcase(root)]) == os.path.normcase(root)
    except ValueError:
        return False


def _local_path(path: str) -> str:
    """Chuẩn hoá các bí danh Windows trỏ về chính ổ đĩa của máy."""
    value = os.path.expanduser(path.strip().strip('"').strip("'"))
    if os.name != "nt":
        return value
    value = value.replace("/", "\\")
    if value.startswith("\\\\?\\UNC\\"):
        value = "\\\\" + value[8:]
    elif value.startswith("\\\\?\\"):
        value = value[4:]
    match = re.match(r"^\\\\(localhost|127\.0\.0\.1)\\([A-Za-z])\$\\(.*)$", value, re.I)
    if match:
        value = f"{match.group(2)}:\\{match.group(3)}"
    return value


def _inside_by_identity(path: str, root: str) -> bool:
    """So danh tính inode của các tổ tiên tồn tại; không tin chuỗi đường dẫn."""
    root_stat = os.stat(root)
    current = path
    while not os.path.exists(current):
        parent = os.path.dirname(current)
        if parent == current:
            raise ValueError("Không xác minh được đường dẫn trạm dữ liệu.")
        current = parent
    while True:
        item = os.stat(current)
        if (item.st_dev, item.st_ino) == (root_stat.st_dev, root_stat.st_ino):
            return True
        parent = os.path.dirname(current)
        if parent == current:
            return False
        current = parent


def _validated_station(path: str, *, external_only: bool = False) -> str:
    lexical = os.path.abspath(_local_path(path))
    real = os.path.realpath(lexical)
    repo = os.path.realpath(_PKG_PARENT)
    workspace = os.path.join(repo, "workspace")
    try:
        in_repo = _inside_by_identity(lexical, repo) or _inside_by_identity(real, repo)
        in_workspace = (
            os.path.normcase(lexical) == os.path.normcase(workspace)
            and os.path.normcase(os.path.realpath(workspace)) == os.path.normcase(workspace)
            and not os.path.islink(workspace)
            and not (hasattr(os.path, "isjunction") and os.path.isjunction(workspace))
        )
    except OSError as exc:
        raise ValueError("Không xác minh được đường dẫn trạm dữ liệu.") from exc
    if in_repo and (external_only or not in_workspace):
        raise ValueError("Trạm dữ liệu trỏ vào source hoặc junction ngoài workspace.")
    if not in_repo and _inside(lexical, repo):
        raise ValueError("Trạm dữ liệu trỏ qua junction ra ngoài workspace.")
    return real


def _bound_data_dir() -> str | None:
    if not os.path.isfile(_BINDING_FILE):
        return None
    with open(_BINDING_FILE, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict) or not isinstance(data.get("station_root"), str):
        raise ValueError("Binding trạm dữ liệu không hợp lệ; chạy lại installer.")
    return _validated_station(data["station_root"], external_only=True)


def data_dir() -> str:
    if not all(os.path.exists(os.path.join(_PKG_PARENT, item)) for item in (
        "install.ps1", "mcp_server_powerbi.py", "skills"
    )):
        raise RuntimeError("Engine phải chạy trực tiếp từ checkout Agent Data Studio đầy đủ.")
    env = os.getenv("ADS_DATA")
    bound = _bound_data_dir()
    if env:
        chosen = _validated_station(env)
        if bound and os.path.normcase(chosen) != os.path.normcase(bound):
            raise ValueError("ADS_DATA khác binding trạm đã cài; xác nhận trạm rồi chạy lại installer.")
        return chosen
    if not bound and any(os.path.exists(os.path.join(_PKG_PARENT, name)) for name in (
        ".env", "knowledge.config.json", "policy.json"
    )):
        raise RuntimeError("Phát hiện cấu hình dữ liệu đời cũ ở source; chọn ADS_DATA rồi chạy lại installer trước khi mở phiên mới.")
    return bound or _validated_station(os.path.join(_PKG_PARENT, "workspace"))


def env_file() -> str:
    return os.path.join(data_dir(), "config.env")


def secrets_file() -> str:
    """Secret (Power BI Service) tách khỏi `.env`: `$ADS_SECRETS_FILE`, mặc định `$ADS_DATA/secrets.env`."""
    env = os.getenv("ADS_SECRETS_FILE")
    return os.path.abspath(os.path.expanduser(env)) if env else os.path.join(data_dir(), "secrets.env")
