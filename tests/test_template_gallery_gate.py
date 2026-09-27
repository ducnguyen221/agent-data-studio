"""Gallery chỉ ghi khi quyền và toàn bộ input được duyệt bằng hash."""

import hashlib
import json
import os

import pytest

from scripts import build_template_gallery as gallery


def _fixture(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    kit_dir = repo / "report-templates" / "sample-kit"
    kit_dir.mkdir(parents=True)
    (kit_dir / "kit.json").write_text(
        json.dumps({"name": "Mẫu tổng hợp", "sanitized": True, "blocks": [{"visualType": "cardVisual"}]}),
        encoding="utf-8",
    )
    (kit_dir / "README.md").write_text("# Mẫu\n\nMô tả tổng hợp.", encoding="utf-8")
    (kit_dir / "preview.png").write_bytes(b"synthetic preview")
    output = repo / "docs" / "template"
    monkeypatch.setattr(gallery, "REPO", repo)
    monkeypatch.setattr(gallery, "SRC", repo / "report-templates")
    monkeypatch.setattr(gallery, "OUT_DIR", output)
    files = {p.relative_to(kit_dir).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in kit_dir.iterdir()}
    manifest = tmp_path / "approval.json"
    approval = {"schema_version": 1, "kits": [{
        "dir": "sample-kit", "owner": "Synthetic owner", "license": "CC-BY-4.0", "files": files,
    }]}
    manifest.write_text(json.dumps(approval), encoding="utf-8")
    return kit_dir, output, manifest, approval


def test_default_run_is_denied_without_output(tmp_path, monkeypatch):
    _, output, _, _ = _fixture(tmp_path, monkeypatch)
    assert gallery.main([]) != 0
    assert not output.exists()


def test_all_inputs_are_validated_before_output(tmp_path, monkeypatch):
    kit_dir, output, manifest, _ = _fixture(tmp_path, monkeypatch)
    (kit_dir / "preview.png").write_bytes(b"changed")
    assert gallery.main(["--approval-manifest", str(manifest)]) != 0
    assert not output.exists()


def test_missing_rights_or_unlisted_file_is_denied(tmp_path, monkeypatch):
    kit_dir, output, manifest, approval = _fixture(tmp_path, monkeypatch)
    approval["kits"][0]["owner"] = ""
    manifest.write_text(json.dumps(approval), encoding="utf-8")
    assert gallery.main(["--approval-manifest", str(manifest)]) != 0
    assert not output.exists()
    approval["kits"][0]["owner"] = "Synthetic owner"
    manifest.write_text(json.dumps(approval), encoding="utf-8")
    (kit_dir / "extra.txt").write_text("new file", encoding="utf-8")
    assert gallery.main(["--approval-manifest", str(manifest)]) != 0
    assert not output.exists()


def test_approved_synthetic_kit_generates_gallery(tmp_path, monkeypatch):
    _, output, manifest, _ = _fixture(tmp_path, monkeypatch)
    assert gallery.main(["--approval-manifest", str(manifest)]) == 0
    published = json.loads((output / "templates.json").read_text(encoding="utf-8"))
    assert published["kits"][0]["owner"] == "Synthetic owner"
    assert published["kits"][0]["license"] == "CC-BY-4.0"
    assert published["kits"][0]["previews"] == []
    assert not (output / "assets").exists()


def test_existing_public_assets_refuse_generation(tmp_path, monkeypatch):
    _, output, manifest, _ = _fixture(tmp_path, monkeypatch)
    (output / "assets").mkdir(parents=True)
    (output / "assets" / "old.png").write_bytes(b"old")
    assert gallery.main(["--approval-manifest", str(manifest)]) != 0
    assert not (output / "templates.json").exists()


def test_linked_input_refuses_generation(tmp_path, monkeypatch):
    kit_dir, output, manifest, _ = _fixture(tmp_path, monkeypatch)
    (kit_dir / "preview.png").unlink()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"synthetic preview")
    try:
        os.symlink(outside, kit_dir / "preview.png")
    except OSError:
        pytest.skip("Máy không cho tạo symlink trong test")
    assert gallery.main(["--approval-manifest", str(manifest)]) != 0
    assert not output.exists()


def test_replace_failure_cleans_temporary_file(tmp_path, monkeypatch):
    _, output, manifest, _ = _fixture(tmp_path, monkeypatch)

    def fail_replace(*_args):
        raise OSError("synthetic replace failure")

    monkeypatch.setattr(gallery.os, "replace", fail_replace)
    with pytest.raises(OSError, match="synthetic replace failure"):
        gallery.build(manifest)
    assert not list(output.glob("tmp*"))
    assert not (output / "templates.json").exists()
