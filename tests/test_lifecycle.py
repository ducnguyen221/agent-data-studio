"""Lifecycle guards use disposable repositories and synthetic host profiles only."""

import os
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
# Windows PowerShell 5.1 is the target shell (T15); pwsh is only the fallback.
POWERSHELL = shutil.which("powershell") or shutil.which("pwsh")
GIT = shutil.which("git")


def run(*args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True, check=False,
                          timeout=120)


@pytest.mark.skipif(not POWERSHELL, reason="PowerShell required")
def test_uninstall_keeps_venv_when_unselected_host_uses_it(tmp_path):
    source = tmp_path / "checkout"
    source.mkdir()
    shutil.copy2(REPO / "uninstall.ps1", source / "uninstall.ps1")
    (source / "mcp_server_powerbi.py").write_text("# fixture\n", encoding="utf-8")
    venv = source / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = fixture\n", encoding="utf-8")
    (venv / ".ads-venv-owned").write_text(str(source), encoding="utf-8")
    profile = tmp_path / "profile"
    profile.mkdir()
    import json

    (profile / ".claude.json").write_text(
        json.dumps(
            {
                "mcpServers": {
                    "powerbi-mcp-bridge": {
                        "command": str(venv / "Scripts" / "python.exe"),
                        "args": [str(source / "mcp_server_powerbi.py")],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["USERPROFILE"] = str(profile)
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    result = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(source / "uninstall.ps1"), "-Hosts", "codex", "-RemoveVenv",
        env=env,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert venv.exists()
    assert "another host still uses it" in result.stdout
    assert (profile / ".claude.json").exists()
    (profile / ".claude.json").unlink()
    (venv / ".ads-venv-owned").unlink()
    no_marker = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(source / "uninstall.ps1"), "-Hosts", "codex", "-RemoveVenv",
        env=env,
    )
    assert no_marker.returncode == 1
    assert "without an ownership marker" in no_marker.stdout
    assert venv.exists()


@pytest.mark.skipif(not POWERSHELL, reason="PowerShell required")
def test_uninstall_removes_only_marked_idle_venv(tmp_path):
    source = tmp_path / "checkout"
    source.mkdir()
    shutil.copy2(REPO / "uninstall.ps1", source / "uninstall.ps1")
    (source / "mcp_server_powerbi.py").write_text("# fixture\n", encoding="utf-8")
    venv = source / ".venv"
    venv.mkdir()
    (venv / "pyvenv.cfg").write_text("home = fixture\n", encoding="utf-8")
    (venv / ".ads-venv-owned").write_text(str(source), encoding="utf-8")
    profile = tmp_path / "profile"
    profile.mkdir()
    env = os.environ.copy()
    env["USERPROFILE"] = str(profile)
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    result = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(source / "uninstall.ps1"), "-Hosts", "codex", "-RemoveVenv",
        env=env,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert not venv.exists()
    assert (source / "mcp_server_powerbi.py").exists()


@pytest.mark.skipif(not POWERSHELL, reason="PowerShell required")
def test_doctor_reads_only_selected_host(tmp_path):
    source = tmp_path / "checkout"
    source.mkdir()
    shutil.copy2(REPO / "doctor.ps1", source / "doctor.ps1")
    (source / "mcp_server_powerbi.py").write_text("pass\n", encoding="utf-8")
    shutil.copytree(REPO / "powerbi_agent", source / "powerbi_agent",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (source / ".agents" / "skills").mkdir(parents=True)
    (source / ".claude" / "skills").mkdir(parents=True)
    profile = tmp_path / "profile"
    (profile / ".codex").mkdir(parents=True)
    (profile / ".claude.json").write_text('{"mcpServers": {', encoding="utf-8")
    server_path = str(source / "mcp_server_powerbi.py").replace("\\", "\\\\")
    (profile / ".codex" / "config.toml").write_text(
        '[mcp_servers.powerbi-mcp-bridge]\ncommand = "python"\n'
        + f'args = ["{server_path}"]\n',
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["USERPROFILE"] = str(profile)
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    result = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(source / "doctor.ps1"), "-Hosts", "codex", env=env,
    )
    assert "mcp: codex points to this checkout" in result.stdout
    assert "claude" not in result.stdout.lower()
    assert "[PASS] startup:" in result.stdout, result.stdout + result.stderr
    assert "[NOT_CHECKED] connection:" in result.stdout

    (source / "workspace").mkdir()
    env.pop("ADS_DATA", None)
    basic = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(source / "doctor.ps1"), "-Hosts", "codex", env=env,
    )
    assert "[PASS] station: Basic workspace exists." in basic.stdout

    env["ADS_DATA"] = str(tmp_path / "external-station")
    external = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(source / "doctor.ps1"), "-Hosts", "codex", env=env,
    )
    assert "[WARN] station: ADS_DATA is set but this checkout has no station binding." in external.stdout
    assert "[PASS] station: Basic workspace exists." not in external.stdout


@pytest.mark.skipif(not POWERSHELL or not GIT, reason="PowerShell and Git required")
def test_update_preflights_candidate_without_changing_checkout(tmp_path):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    run(GIT, "init", "-b", "main", str(upstream))
    for name in ("install.ps1", "uninstall.ps1", "doctor.ps1"):
        (upstream / name).write_text("Write-Host 'fixture'\n", encoding="utf-8")
    shutil.copy2(REPO / "update.ps1", upstream / "update.ps1")
    (upstream / "scripts").mkdir()
    shutil.copy2(REPO / "scripts" / "update_release.py", upstream / "scripts" / "update_release.py")
    (upstream / "powerbi_agent").mkdir()
    (upstream / "powerbi_agent" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy2(REPO / "powerbi_agent" / "_env.py", upstream / "powerbi_agent" / "_env.py")
    (upstream / "powerbi_agent" / "app.py").write_text(
        "class Manager:\n    def list_tools(self):\n        return list(range(16))\n"
        "class MCP:\n    _tool_manager = Manager()\n"
        "mcp = MCP()\n", encoding="utf-8",
    )
    (upstream / "skills").mkdir()
    (upstream / "skills" / "README.md").write_text("fixture\n", encoding="utf-8")
    (upstream / "requirements.txt").write_text("packaging==25.0\n", encoding="utf-8")
    (upstream / "mcp_server_powerbi.py").write_text("pass\n", encoding="utf-8")
    (upstream / "sample.py").write_text("value = 1\n", encoding="utf-8")
    run(GIT, "add", ".", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "seed", cwd=upstream).returncode == 0
    bare = tmp_path / "remote.git"
    assert run(GIT, "clone", "--bare", str(upstream), str(bare)).returncode == 0
    checkout = tmp_path / "checkout"
    assert run(GIT, "clone", str(bare), str(checkout)).returncode == 0
    old = run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip()
    (upstream / "sample.py").write_text("value = 2\n", encoding="utf-8")
    run(GIT, "add", ".", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "candidate", cwd=upstream).returncode == 0
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    (checkout / "sample.py").write_text("user local edit\n", encoding="utf-8")
    dirty = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(checkout / "update.ps1"), cwd=checkout,
    )
    assert dirty.returncode == 1
    assert (checkout / "sample.py").read_text(encoding="utf-8") == "user local edit\n"
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == old
    (checkout / "sample.py").write_text("value = 1\n", encoding="utf-8")
    result = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(checkout / "update.ps1"), cwd=checkout,
    )
    assert result.returncode == 2, result.stdout + result.stderr
    assert "READY_FOR_REVIEW" in result.stdout
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == old
    assert (checkout / "sample.py").read_text(encoding="utf-8") == "value = 1\n"
    (upstream / ".gitignore").write_text("artifacts/private.txt\n", encoding="utf-8")
    nested = upstream / "artifacts" / "private.txt"
    nested.parent.mkdir()
    nested.write_text("forced private file\n", encoding="utf-8")
    run(GIT, "add", ".gitignore", cwd=upstream)
    run(GIT, "add", "-f", "artifacts/private.txt", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "changed ignore rules", cwd=upstream).returncode == 0
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    unsafe = run(POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 str(checkout / "update.ps1"), cwd=checkout)
    assert unsafe.returncode == 1, unsafe.stdout + unsafe.stderr
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == old
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "revert", "--no-edit", "HEAD", cwd=upstream).returncode == 0
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    (upstream / "requirements.txt").write_text("packaging==26.0\n", encoding="utf-8")
    run(GIT, "add", ".", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "dependency change", cwd=upstream).returncode == 0
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    changed_target = run(GIT, "rev-parse", "HEAD", cwd=upstream).stdout.strip()
    changed_deps = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(checkout / "update.ps1"), cwd=checkout,
    )
    assert changed_deps.returncode == 1
    assert "dependencies changed" in changed_deps.stdout.lower(), changed_deps.stdout
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == old
    denied_apply = run(
        POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
        str(checkout / "update.ps1"), "-Apply", "-ExpectedCommit", changed_target,
        cwd=checkout,
    )
    assert denied_apply.returncode == 1
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == old


@pytest.mark.skipif(not POWERSHELL or not GIT, reason="PowerShell and Git required")
def test_update_apply_and_failed_candidate_preserve_station(tmp_path):
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    run(GIT, "init", "-b", "main", str(upstream))
    (upstream / ".gitignore").write_text("/workspace/\n/.ads-binding.json\n", encoding="utf-8")
    for name in ("install.ps1", "uninstall.ps1", "doctor.ps1"):
        (upstream / name).write_text("Write-Host 'fixture'\n", encoding="utf-8")
    shutil.copy2(REPO / "update.ps1", upstream / "update.ps1")
    (upstream / "scripts").mkdir()
    shutil.copy2(REPO / "scripts" / "update_release.py", upstream / "scripts" / "update_release.py")
    (upstream / "powerbi_agent").mkdir()
    (upstream / "powerbi_agent" / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy2(REPO / "powerbi_agent" / "_env.py", upstream / "powerbi_agent" / "_env.py")
    app = upstream / "powerbi_agent" / "app.py"
    app.write_text("from powerbi_agent._env import data_dir\ndata_dir()\n"
                   "class Manager:\n    def list_tools(self):\n        return list(range(16))\n"
                   "class MCP:\n    _tool_manager = Manager()\n"
                   "mcp = MCP()\n", encoding="utf-8")
    (upstream / "skills").mkdir()
    (upstream / "skills" / "README.md").write_text("fixture\n", encoding="utf-8")
    (upstream / "requirements.txt").write_text("packaging==25.0\n", encoding="utf-8")
    (upstream / "mcp_server_powerbi.py").write_text("pass\n", encoding="utf-8")
    (upstream / "sample.py").write_text("value = 1\n", encoding="utf-8")
    run(GIT, "add", ".", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "seed", cwd=upstream).returncode == 0
    bare = tmp_path / "remote.git"
    assert run(GIT, "clone", "--bare", str(upstream), str(bare)).returncode == 0
    checkout = tmp_path / "checkout"
    assert run(GIT, "clone", str(bare), str(checkout)).returncode == 0
    old = run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip()
    station = tmp_path / "station"
    station.mkdir()
    payload = station / "project.txt"
    payload.write_text("private fixture stays here\n", encoding="utf-8")
    env = os.environ.copy()
    env["ADS_DATA"] = str(station)
    env["POWERBI_INSTALL_PYTHON"] = sys.executable
    (checkout / ".ads-binding.json").write_text(
        json.dumps({"station_root": str(station)}), encoding="utf-8")
    (upstream / "sample.py").write_text("value = 2\n", encoding="utf-8")
    run(GIT, "add", ".", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "candidate", cwd=upstream).returncode == 0
    target = run(GIT, "rev-parse", "HEAD", cwd=upstream).stdout.strip()
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    mismatch = run(POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(checkout / "update.ps1"), "-Apply", "-ExpectedCommit", old,
                   cwd=checkout, env=env)
    assert mismatch.returncode == 1, mismatch.stdout + mismatch.stderr
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == old
    applied = run(POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                  str(checkout / "update.ps1"), "-Apply", "-ExpectedCommit", target,
                  cwd=checkout, env=env)
    assert applied.returncode == 0, applied.stdout + applied.stderr
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == target
    assert not run(GIT, "status", "--porcelain=v1", cwd=checkout).stdout.strip()
    assert payload.read_text(encoding="utf-8") == "private fixture stays here\n"
    journal = station / "state" / "update-journal.jsonl"
    assert '"event": "end"' in journal.read_text(encoding="utf-8")
    app.write_text(
        "from pathlib import Path\n"
        "if Path(__file__).resolve().parents[1].name == 'checkout':\n"
        "    raise RuntimeError('synthetic post-merge failure')\n"
        "from powerbi_agent._env import data_dir\ndata_dir()\n"
        "class Manager:\n    def list_tools(self):\n        return list(range(16))\n"
        "class MCP:\n    _tool_manager = Manager()\n"
        "mcp = MCP()\n", encoding="utf-8",
    )
    run(GIT, "add", ".", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "post-merge failure candidate", cwd=upstream).returncode == 0
    broken = run(GIT, "rev-parse", "HEAD", cwd=upstream).stdout.strip()
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    failed = run(POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                 str(checkout / "update.ps1"), "-Apply", "-ExpectedCommit", broken,
                 cwd=checkout, env=env)
    assert failed.returncode == 1, failed.stdout + failed.stderr
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == target
    assert payload.read_text(encoding="utf-8") == "private fixture stays here\n"
    assert '"event": "aborted"' in journal.read_text(encoding="utf-8"), failed.stdout + failed.stderr
    private = checkout / "workspace" / "projects" / "private.txt"
    private.parent.mkdir(parents=True)
    private.write_text("basic user payload\n", encoding="utf-8")
    upstream_private = upstream / "workspace" / "projects" / "private.txt"
    upstream_private.parent.mkdir(parents=True)
    upstream_private.write_text("malicious candidate payload\n", encoding="utf-8")
    (upstream / ".gitignore").write_text("/workspace/\n/.ads-binding.json\n", encoding="utf-8")
    run(GIT, "add", ".gitignore", cwd=upstream)
    run(GIT, "add", "-f", "workspace/projects/private.txt", cwd=upstream)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "private path candidate", cwd=upstream).returncode == 0
    unsafe = run(GIT, "rev-parse", "HEAD", cwd=upstream).stdout.strip()
    assert run(GIT, "push", str(bare), "main", cwd=upstream).returncode == 0
    rejected = run(POWERSHELL, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                   str(checkout / "update.ps1"), "-Apply", "-ExpectedCommit", unsafe,
                   cwd=checkout, env=env)
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    assert run(GIT, "rev-parse", "HEAD", cwd=checkout).stdout.strip() == target
    assert private.read_text(encoding="utf-8") == "basic user payload\n"
    assert payload.read_text(encoding="utf-8") == "private fixture stays here\n"


def test_update_rollback_timeout_is_partial(monkeypatch, tmp_path):
    from scripts import update_release

    def timeout(*_args):
        raise subprocess.TimeoutExpired("git", 60)

    monkeypatch.setattr(update_release, "_rollback", timeout)
    assert not update_release._try_rollback(tmp_path, "old", "target", True)


def test_update_partial_worktree_add_reports_cleanup(monkeypatch, tmp_path, capsys):
    from scripts import update_release

    repo = tmp_path / "repo"
    repo.mkdir()
    station = tmp_path / "station"
    station.mkdir()
    candidate = tmp_path / "ads-update-candidate-test"
    candidate.mkdir()
    monkeypatch.setattr(update_release, "_head", lambda _repo: "old")
    monkeypatch.setattr(update_release, "_clean", lambda _repo: True)
    monkeypatch.setattr(update_release, "_station", lambda _repo: station)
    monkeypatch.setattr(update_release, "_candidate_paths_safe", lambda *_args: True)
    monkeypatch.setattr(update_release.tempfile, "mkdtemp", lambda **_kwargs: str(candidate))

    def git(_repo, *args, **_kwargs):
        if args[:2] == ("worktree", "add"):
            (candidate / "partial.txt").write_text("partial\n", encoding="utf-8")
            raise subprocess.TimeoutExpired("git worktree add", 60)
        code = 1 if args[:2] == ("worktree", "remove") else 0
        return subprocess.CompletedProcess(args, code, "", "")

    monkeypatch.setattr(update_release, "_git", git)
    assert update_release.apply(repo, "old", "target", Path(sys.executable)) == 1
    assert "cleanup pending" in capsys.readouterr().out.lower()
    assert not candidate.exists()
    assert '"event": "aborted"' in (station / "state" / "update-journal.jsonl").read_text(encoding="utf-8")


def test_update_journal_rejects_dangling_link(tmp_path):
    from scripts import update_release

    station = tmp_path / "station"
    state = station / "state"
    state.mkdir(parents=True)
    destination = tmp_path / "outside.txt"
    try:
        (state / "update-journal.jsonl").symlink_to(destination)
    except OSError:
        pytest.skip("Creating symlinks requires OS permission")
    with pytest.raises(update_release.UpdateError):
        update_release._journal(station, {"event": "start"})
    assert not destination.exists()


@pytest.mark.skipif(not GIT, reason="Git required")
def test_update_rejects_renamed_gitignore(tmp_path):
    from scripts import update_release

    repo = tmp_path / "repo"
    repo.mkdir()
    assert run(GIT, "init", "-b", "main", str(repo)).returncode == 0
    (repo / ".gitignore").write_text("private.txt\n", encoding="utf-8")
    (repo / "public.txt").write_text("source\n", encoding="utf-8")
    run(GIT, "add", ".", cwd=repo)
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "old", cwd=repo).returncode == 0
    old = run(GIT, "rev-parse", "HEAD", cwd=repo).stdout.strip()
    assert run(GIT, "mv", ".gitignore", "ignore-backup.txt", cwd=repo).returncode == 0
    assert run(GIT, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
               "commit", "-m", "renamed ignore", cwd=repo).returncode == 0
    target = run(GIT, "rev-parse", "HEAD", cwd=repo).stdout.strip()
    assert not update_release._candidate_paths_safe(repo, old, target)


@pytest.mark.skipif(os.name != "nt", reason="Windows process query required")
def test_update_rechecks_live_python_before_merge(tmp_path):
    from scripts import update_release

    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(30)", str(tmp_path)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        assert update_release._runtime_busy(tmp_path)
    finally:
        child.terminate()
        child.wait(timeout=10)


def test_update_journal_failure_is_visible_and_rolls_back(monkeypatch, tmp_path, capsys):
    from scripts import update_release

    repo = tmp_path / "repo"
    repo.mkdir()
    station = tmp_path / "station"
    station.mkdir()
    current = ["old"]
    journal_calls = [0]
    real_journal = update_release._journal
    monkeypatch.setattr(update_release, "_head", lambda _repo: current[0])
    monkeypatch.setattr(update_release, "_clean", lambda _repo: True)
    monkeypatch.setattr(update_release, "_station", lambda _repo: station)
    monkeypatch.setattr(update_release, "_candidate_paths_safe", lambda *_args: True)
    monkeypatch.setattr(update_release, "_runtime_busy", lambda _repo: False)
    monkeypatch.setattr(update_release, "_smoke", lambda *_args: None)

    def git(_repo, *args, **_kwargs):
        if args[0] == "merge" and args[1] == "--ff-only":
            current[0] = "target"
        if args[0] == "reset" and args[1] == "--keep":
            current[0] = "old"
        return subprocess.CompletedProcess(args, 0, "", "")

    def journal(*args):
        journal_calls[0] += 1
        if journal_calls[0] > 1:
            raise OSError("synthetic disk failure")
        real_journal(*args)

    monkeypatch.setattr(update_release, "_git", git)
    monkeypatch.setattr(update_release, "_journal", journal)
    assert update_release.apply(repo, "old", "target", Path(sys.executable)) == 1
    assert current[0] == "old"
    assert "JOURNAL_WRITE_FAILED" in capsys.readouterr().out
    assert '"event": "start"' in (station / "state" / "update-journal.jsonl").read_text(encoding="utf-8")
