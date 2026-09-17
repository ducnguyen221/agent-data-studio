"""Hợp đồng env: dữ liệu máy (`.env`, cấu hình cũ) tách khỏi mã nguồn.

`ADS_DATA` trỏ thư mục dữ liệu của máy (mặc định khuyến nghị `~/.data`). Chưa đặt thì lùi về
thư mục cha của package — đúng hành vi bản cài in-place cũ, để máy chưa migrate không gãy.
Khi engine được `pip install` (không `-e`), cha của package là `site-packages`, nên máy dùng
bản cài phải đặt `ADS_DATA`.
"""

import os

_PKG_PARENT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir() -> str:
    env = os.getenv("ADS_DATA")
    return os.path.abspath(os.path.expanduser(env)) if env else _PKG_PARENT


def env_file() -> str:
    return os.path.join(data_dir(), ".env")
