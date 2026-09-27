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
