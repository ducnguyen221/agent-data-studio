"""Kiểm đường cài basic và cổng index trên một bản source giả trong thư mục tạm."""

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def source_fixture(tmp_path):
    """Tạo source tối thiểu, không chép credential/config của máy."""
    source = tmp_path / "source"
    source.mkdir()
    for name in ("install.ps1", "mcp_server_powerbi.py", ".gitignore"):
        shutil.copy2(REPO / name, source / name)
    (source / ".env.example").write_text("POWERBI_AGGREGATE_ONLY=1\n", encoding="utf-8")
    (source / "scripts").mkdir()
    shutil.copy2(REPO / "scripts" / "build_host_adapters.py", source / "scripts" / "build_host_adapters.py")
    for skill in (REPO / "skills").iterdir():
        if skill.is_dir() and (skill / "SKILL.md").exists():
            target = source / "skills" / skill.name
            target.mkdir(parents=True)
            (target / "SKILL.md").write_text(
                f"---\nname: {skill.name}\ndescription: Test skill.\n---\n", encoding="utf-8"
            )
    for command in (REPO / "commands").glob("pbi-*.md"):
        target = source / "commands" / command.name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("---\ndescription: Test command.\n---\n", encoding="utf-8")
    generated = subprocess.run(
        [sys.executable, str(source / "scripts" / "build_host_adapters.py")],
        capture_output=True, text=True,
    )
    assert generated.returncode == 0, generated.stderr
    return source


def run_install(source: Path, *, ads_data: str | None = None, only_plugin: bool = False):
    env = os.environ.copy()
    for name in ("ADS_DATA", "POWERBI_PROJECT_DIR", "POWERBI_POLICY_FILE", "POWERBI_AUDIT_DIR"):
        env.pop(name, None)
    if ads_data is not None:
        env["ADS_DATA"] = ads_data
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    env["USERPROFILE"] = str(source.parent / "fakehome")
    args = ["powershell", "-NoProfile", "-File", str(source / "install.ps1")]
    args += ["-Only", "plugin"] if only_plugin else ["-SkipVenv", "-SkipHosts"]
    return subprocess.run(args, cwd=source, env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=90)


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_basic_station_created_and_idempotent(source_fixture):
    source = source_fixture
    first = run_install(source)
    assert first.returncode == 0, first.stdout[-1500:] + first.stderr[-1500:]
    station = source / "workspace"
    for name in ("projects", "knowledge", "outputs", "state", "config.env"):
        assert (station / name).exists(), name
    marker = station / "projects" / "keep.txt"
    marker.write_text("user data", encoding="utf-8")
    second = run_install(source)
    assert second.returncode == 0, second.stdout[-1500:] + second.stderr[-1500:]
    assert marker.read_text(encoding="utf-8") == "user data"
    assert not (source / ".ads-binding.json").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_external_station_binding_and_conflict(source_fixture):
    source = source_fixture
    station = source.parent / "station"
    first = run_install(source, ads_data=str(station))
    assert first.returncode == 0, first.stdout[-1500:] + first.stderr[-1500:]
    assert (station / "projects").is_dir()
    assert (station / "config.env").is_file()
    assert not (source / "workspace").exists()
    binding = source / ".ads-binding.json"
    before = binding.read_bytes()
    different = source.parent / "different-station"
    second = run_install(source, ads_data=str(different))
    assert second.returncode != 0
    assert binding.read_bytes() == before
    assert not different.exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_nested_workspace_refused_before_write(source_fixture):
    source = source_fixture
    result = run_install(source, ads_data=str(source / "workspace" / "team"))
    assert result.returncode != 0
    assert not (source / "workspace").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_forced_tracked_workspace_refused_before_write(source_fixture):
    source = source_fixture
    subprocess.run(["git", "init", "-q", str(source)], check=True, capture_output=True)
    candidate = source / "workspace" / "private.txt"
    candidate.parent.mkdir()
    candidate.write_text("fixture only", encoding="utf-8")
    subprocess.run(["git", "-C", str(source), "add", "-f", "workspace/private.txt"],
                   check=True, capture_output=True)
    result = run_install(source)
    assert result.returncode != 0
    assert not (source / "workspace" / "projects").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_adapter_check_does_not_create_station(source_fixture):
    source = source_fixture
    (source / ".ads-binding.json").write_text("{}", encoding="utf-8")
    result = run_install(source, only_plugin=True)
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    assert not (source / "workspace").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
@pytest.mark.parametrize("version", ["3.10", "3.15"])
def test_python_outside_supported_range_is_refused_with_clear_message(source_fixture, version):
    """WP-A — Python ngoài 3.11–3.14 bị từ chối bằng câu nêu bản tìm thấy + khoảng hỗ trợ; không tạo .venv."""
    source = source_fixture
    fake_bin = source.parent / "fake-bin"
    fake_bin.mkdir()
    for name in ("py.cmd", "python.cmd", "python3.cmd"):  # mọi ứng viên đều trả cùng bản ngoài khoảng
        (fake_bin / name).write_text(f"@echo {version}\r\n", encoding="ascii")
    powershell = shutil.which("powershell")
    assert powershell is not None
    env = {k: v for k, v in os.environ.items()
           if k.upper() not in ("PATH", "PSMODULEPATH", "POWERBI_INSTALL_PYTHON", "ADS_DATA")}
    env["USERPROFILE"] = str(source.parent / "fakehome")
    env["PATH"] = os.pathsep.join([str(fake_bin), str(Path(powershell).parent),
                                   str(Path(os.environ["SystemRoot"]) / "System32")])
    # Ép UTF-8 cho stdout của PowerShell 5.1 để đọc đúng câu tiếng Việt khi bị chuyển hướng.
    command = ("[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); "
               f"& '{source / 'install.ps1'}' -SkipHosts; exit $LASTEXITCODE")
    result = subprocess.run(
        [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        cwd=source, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=90,
    )
    assert result.returncode == 1, result.stdout[-1500:] + result.stderr[-1500:]
    assert f"Máy có Python {version}" in result.stdout, result.stdout[-1500:]
    assert "3.11–3.14" in result.stdout
    assert "winget install --id Python.Python.3.12 -e" in result.stdout
    assert not (source / ".venv").exists()


def test_python_range_in_sync():
    """Khoảng Python một nguồn: pyproject requires-python == install.ps1 == doctor.ps1."""
    import re
    import tomllib

    spec = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["project"]["requires-python"]
    low, high = re.fullmatch(r">=3\.(\d+),<3\.(\d+)", spec).groups()
    expected = f"$PyMinMinor = {low}; $PyMaxMinor = {int(high) - 1}"
    for script in ("install.ps1", "doctor.ps1"):
        assert expected in (REPO / script).read_text(encoding="utf-8-sig"), script
    pin = re.search(r"^pythonnet==(\S+)$", (REPO / "requirements.txt").read_text(encoding="utf-8"), re.M)
    assert pin and pin.group(1) == "3.1.0"  # 3.0.5 chỉ tới <3.14; nâng trần phải nâng pin cùng lúc



@pytest.mark.skipif(sys.platform != "win32", reason="Windows PowerShell required")
@pytest.mark.parametrize("script", ["install.ps1", "doctor.ps1"])
def test_invoke_native_passes_single_argument_whole(script):
    """`$command, $rest = $args` biến MỘT đối số thành chuỗi -> splat tách từng ký tự.

    install.ps1 kiểm venv bằng `Invoke-Native $venvPy --version`: bản lỗi chạy `python - - v e r ...`
    (đọc script từ stdin) -> cài lại trong console của người dùng thì treo chờ bàn phím.
    """
    import re

    text = (REPO / script).read_text(encoding="utf-8-sig")
    helper = re.search(r"^function Invoke-Native \{.*\}\s*$", text, re.M)
    assert helper, script
    command = (helper.group(0).strip() + "; function Show { 'COUNT=' + $args.Count; 'ARGS=' + ($args -join '|') }; "
               "Invoke-Native Show --version; Invoke-Native Show -m venv 'C:/thư mục có dấu'")
    env = {k: v for k, v in os.environ.items() if k.upper() != "PSMODULEPATH"}
    result = subprocess.run(["powershell", "-NoProfile", "-Command", command], env=env,
                            capture_output=True, text=True, timeout=60)
    lines = result.stdout.split()
    assert lines[:2] == ["COUNT=1", "ARGS=--version"], result.stdout + result.stderr
    assert "COUNT=3" in result.stdout, result.stdout


def _install_utf8(source: Path, env: dict, *args: str) -> subprocess.CompletedProcess[str]:
    command = ("[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false); "
               f"& '{source / 'install.ps1'}' {' '.join(args)}; exit $LASTEXITCODE")
    return subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
                          cwd=source, env=env, capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=90)


@pytest.mark.skipif(sys.platform != "win32", reason="installer chạy trên Windows")
def test_installer_adomd_check_uses_engine_rules(source_fixture):
    """WP-B — installer hỏi powerbi_agent.adomd.find_adomd_dlls(): tôn trọng ADOMD_LIB_DIR (biến môi
    trường, rồi config.env của trạm), override độc quyền, và báo thiếu Tabular.dll."""
    source = source_fixture
    shutil.copytree(REPO / "powerbi_agent", source / "powerbi_agent",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    empty = source.parent / "ADOMD rỗng"
    empty.mkdir()
    chosen = source.parent / "ADOMD đã chọn"
    chosen.mkdir()
    (chosen / "Microsoft.AnalysisServices.AdomdClient.dll").write_bytes(b"fixture")
    env = {k: v for k, v in os.environ.items() if k.upper() not in ("PSMODULEPATH", "ADS_DATA", "ADOMD_LIB_DIR")}
    env["USERPROFILE"] = str(source.parent / "fakehome")
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    env["ADOMD_LIB_DIR"] = str(empty)
    result = _install_utf8(source, env, "-SkipVenv", "-SkipHosts")
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    assert f"ADOMD_LIB_DIR={empty} không chứa Microsoft.AnalysisServices.AdomdClient.dll" in result.stdout, \
        result.stdout[-1500:]
    assert "Tìm thấy ADOMD.NET" not in result.stdout  # không lặng lẽ rơi về SSMS/GAC

    del env["ADOMD_LIB_DIR"]
    (source / "workspace" / "config.env").write_text(f"ADOMD_LIB_DIR={chosen}\n", encoding="utf-8")
    result = _install_utf8(source, env, "-SkipVenv", "-SkipHosts")
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    assert f"Tìm thấy ADOMD.NET (ADOMD_LIB_DIR): {chosen}" in result.stdout, result.stdout[-1500:]
    assert "Thiếu Microsoft.AnalysisServices.Tabular.dll" in result.stdout
