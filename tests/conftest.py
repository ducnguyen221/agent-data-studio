"""Cô lập trạm dữ liệu cho pytest — test không bao giờ ghi vào trạm thật của máy.

Engine chọn trạm theo `ADS_DATA` NGAY LÚC IMPORT: `knowledge.ENV_FILE`,
`knowledge.LEGACY_CONFIG_FILE` và `app` nạp `config.env` của trạm. Nếu kế thừa biến của
shell (vd `ADS_DATA=~/.data`), các test policy ghi audit `execute_dax blocked_raw_dump`
vào `audit/<yyyy-mm>.jsonl` của trạm thật. Vì vậy trạm tạm được đặt ở mức module của
conftest — pytest nạp file này TRƯỚC mọi test module — và fixture autouse giữ nguyên nó
cho từng test. Test cần trạm riêng vẫn tự `monkeypatch.setenv(...)` với `tmp_path` như cũ;
tiến trình con kế thừa trạm tạm qua `os.environ.copy()`.
"""

import os
import shutil
import tempfile

import pytest

# Biến đường dẫn có thể kéo engine ra khỏi trạm tạm (chọn trạm, dự án, audit, policy...).
_PATH_OVERRIDES = (
    "POWERBI_PROJECT_DIR",
    "POWERBI_AUDIT_DIR",
    "POWERBI_POLICY_FILE",
    "POWERBI_TEMPLATES_DIR",
    "POWERBI_DISTILL_DIR",
    "ADS_SECRETS_FILE",
)
_SAVED_ENV = {name: os.environ.get(name) for name in ("ADS_DATA", *_PATH_OVERRIDES)}
TEST_STATION = tempfile.mkdtemp(prefix="ads-pytest-station-")
os.environ["ADS_DATA"] = TEST_STATION
for _name in _PATH_OVERRIDES:
    os.environ.pop(_name, None)


@pytest.fixture(autouse=True)
def _isolated_station(monkeypatch):
    """Mỗi test bắt đầu ở trạm tạm của phiên, không mang biến đường dẫn của shell."""
    monkeypatch.setenv("ADS_DATA", TEST_STATION)
    for name in _PATH_OVERRIDES:
        monkeypatch.delenv(name, raising=False)


def pytest_unconfigure(config):
    for name, value in _SAVED_ENV.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value
    shutil.rmtree(TEST_STATION, ignore_errors=True)
