"""Đóng gói thật trên Git fixture sạch, không dùng dữ liệu hoặc asset của người dùng."""

import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest


POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
GIT = shutil.which("git")
PACK = Path(__file__).resolve().parents[1] / "pack.ps1"
pytestmark = pytest.mark.skipif(not POWERSHELL or not GIT, reason="Requires Git and PowerShell")


def _run_git(repo: Path, *args: str) -> None:
    subprocess.run([GIT, "-C", str(repo), *args], check=True, capture_output=True, text=True)


def _clean_repo(tmp_path: Path, extra: str | None = None, extras: tuple[str, ...] = ()) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    shutil.copy2(PACK, repo / "pack.ps1")
    for name in (
        ".env.example",
        "LICENSE",
        "THIRD_PARTY_NOTICES.md",
        "LICENSES/microsoft-skills-for-fabric.txt",
        "install.ps1",
        "doctor.ps1",
    ):
        file = repo / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("synthetic public fixture\n", encoding="utf-8")
    for name in ((extra,) if extra else ()) + extras:
        file = repo / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text("synthetic unapproved asset\n", encoding="utf-8")
    _run_git(repo, "init", "-q")
    _run_git(repo, "add", ".")
    _run_git(repo, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "fixture")
    return repo


def _pack(repo: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(repo / "pack.ps1"),
         "-OutDir", str(out)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


def test_public_fixture_keeps_example_and_licenses(tmp_path):
    repo = _clean_repo(tmp_path)
    out = tmp_path / "out"
    result = _pack(repo, out)
    assert result.returncode == 0, result.stderr
    zips = list(out.glob("*.zip"))
    assert len(zips) == 1
    with zipfile.ZipFile(zips[0]) as archive:
        names = set(archive.namelist())
    assert {".env.example", "LICENSE", "THIRD_PARTY_NOTICES.md",
            "LICENSES/microsoft-skills-for-fabric.txt"}.issubset(names)


def test_unapproved_asset_is_denied_before_zip(tmp_path):
    repo = _clean_repo(tmp_path, "report-templates/unknown/kit.json")
    out = tmp_path / "out"
    result = _pack(repo, out)
    assert result.returncode != 0
    assert not out.exists() or not list(out.glob("*.zip"))


# Asset KPIM đã có ghi nguồn (quyết định G-A 26/09): nhóm có PROVENANCE.md và gốc có NOTICE.md
# thì được đóng gói; thiếu một trong hai thì vẫn chặn trước khi tạo ZIP.
KIT = "report-templates/sample-kit"
DATASETS = "skills/data-mockup/references/kpim/kpim-datasets"


def _assert_denied(repo: Path, out: Path) -> None:
    result = _pack(repo, out)
    assert result.returncode != 0
    # Đỏ đúng lý do: cổng ghi nguồn chặn, không phải lỗi khác của fixture.
    assert "PROVENANCE.md" in result.stderr or "NOTICE.md" in result.stderr, result.stderr
    assert not out.exists() or not list(out.glob("*.zip"))


def test_asset_with_provenance_and_notice_is_packed(tmp_path):
    repo = _clean_repo(tmp_path, extras=(
        "NOTICE.md", "report-templates/README.md", f"{KIT}/kit.json", f"{KIT}/PROVENANCE.md",
        f"{DATASETS}/README.md", f"{DATASETS}/PROVENANCE.md",
        "templates/documents/Project_Management.xlsx", "templates/documents/PROVENANCE.md",
    ))
    out = tmp_path / "out"
    result = _pack(repo, out)
    assert result.returncode == 0, result.stderr
    zips = list(out.glob("*.zip"))
    assert len(zips) == 1
    with zipfile.ZipFile(zips[0]) as archive:
        names = set(archive.namelist())
    assert {"NOTICE.md", f"{KIT}/kit.json", f"{KIT}/PROVENANCE.md", f"{DATASETS}/PROVENANCE.md",
            "templates/documents/Project_Management.xlsx"}.issubset(names)


def test_kit_without_provenance_is_denied_next_to_approved_kit(tmp_path):
    repo = _clean_repo(tmp_path, extras=(
        "NOTICE.md", f"{KIT}/kit.json", f"{KIT}/PROVENANCE.md", "report-templates/other-kit/kit.json",
    ))
    _assert_denied(repo, tmp_path / "out")


@pytest.mark.parametrize("files", [
    ("NOTICE.md", "templates/documents/Project_Management.xlsx"),
    ("NOTICE.md", f"{DATASETS}/README.md"),
    (f"{KIT}/kit.json", f"{KIT}/PROVENANCE.md"),
], ids=["workbook-no-provenance", "datasets-no-provenance", "kit-no-notice"])
def test_asset_missing_provenance_or_notice_is_denied(tmp_path, files):
    repo = _clean_repo(tmp_path, extras=files)
    _assert_denied(repo, tmp_path / "out")
