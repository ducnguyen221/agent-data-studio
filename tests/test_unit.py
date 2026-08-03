"""Unit tests — không cần Power BI Desktop hay ADOMD.NET."""

import json
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from powerbi_agent import policy
from powerbi_agent.adomd import candidate_adomd_dirs
from powerbi_agent.util import df_to_markdown_capped, short_err


class TestUtil:
    def test_short_err_passthrough(self):
        assert short_err("ngắn") == "ngắn"

    def test_short_err_caps_long_messages(self):
        msg = "x" * 1000
        out = short_err(msg)
        assert len(out) < 450
        assert out.endswith("…[đã cắt]")

    def test_df_markdown_no_cap(self):
        df = pd.DataFrame({"a": [1, 2]})
        out = df_to_markdown_capped(df, 100)
        assert "⚠️" not in out

    def test_df_markdown_caps_rows(self):
        df = pd.DataFrame({"a": range(50)})
        out = df_to_markdown_capped(df, 10)
        assert "50 dòng" in out and "10 dòng đầu" in out

    def test_df_markdown_zero_disables_cap(self):
        df = pd.DataFrame({"a": range(50)})
        assert "⚠️" not in df_to_markdown_capped(df, 0)


class TestAdomdProbe:
    def test_candidate_dirs_returns_list(self):
        assert isinstance(candidate_adomd_dirs(), list)

    def test_env_override_first(self, tmp_path, monkeypatch):
        monkeypatch.setenv("ADOMD_LIB_DIR", str(tmp_path))
        dirs = candidate_adomd_dirs()
        assert dirs and dirs[0] == str(tmp_path)


class TestPolicy:
    @pytest.fixture(autouse=True)
    def enable(self, monkeypatch):
        monkeypatch.setenv("POWERBI_AGGREGATE_ONLY", "1")

    @pytest.mark.parametrize("dax", [
        "EVALUATE 'Sales'",
        "EVALUATE Sales",
        "evaluate 'Bảng Khách Hàng'",
        "EVALUATE ALL('Sales')",
        "EVALUATE ALLNOBLANKROW('Sales')",
    ])
    def test_blocks_raw_dumps(self, dax):
        allowed, reason = policy.check_dax(dax)
        assert not allowed and "SUMMARIZECOLUMNS" in reason

    @pytest.mark.parametrize("dax", [
        'EVALUATE SUMMARIZECOLUMNS(Cal[Year], "Qty", [Total Qty])',
        "EVALUATE TOPN(10, SUMMARIZECOLUMNS(Cal[Year]))",
        'EVALUATE ROW("KQ", [Total])',
        "EVALUATE FILTER(SUMMARIZECOLUMNS(Cal[Year]), TRUE())",
    ])
    def test_allows_aggregates(self, dax):
        allowed, _ = policy.check_dax(dax)
        assert allowed

    def test_opt_out_with_env_zero(self, monkeypatch):
        monkeypatch.setenv("POWERBI_AGGREGATE_ONLY", "0")
        allowed, _ = policy.check_dax("EVALUATE 'Sales'")
        assert allowed


class TestPolicyM1:
    def test_default_is_on(self, monkeypatch):
        monkeypatch.delenv("POWERBI_AGGREGATE_ONLY", raising=False)
        allowed, reason = policy.check_dax("EVALUATE 'Sales'")
        assert not allowed and "aggregate-only" in reason

    def test_pii_blocklist_blocks(self, tmp_path, monkeypatch):
        pf = tmp_path / "policy.json"
        pf.write_text(
            '{"blocked_columns": ["\'Khách hàng\'[Số điện thoại]"]}', encoding="utf-8"
        )
        monkeypatch.setenv("POWERBI_POLICY_FILE", str(pf))
        monkeypatch.setenv("POWERBI_AUDIT_DIR", str(tmp_path / "audit"))
        dax = "EVALUATE SUMMARIZECOLUMNS('Khách hàng'[Số điện thoại], \"n\", [Đếm KH])"
        allowed, reason = policy.check_dax(dax)
        assert not allowed and "PII blocklist" in reason
        # audit đã ghi verdict blocked_pii
        files = list((tmp_path / "audit").glob("*.jsonl"))
        assert files and "blocked_pii" in files[0].read_text(encoding="utf-8")

    def test_pii_allows_other_columns(self, tmp_path, monkeypatch):
        pf = tmp_path / "policy.json"
        pf.write_text('{"blocked_columns": ["[Số điện thoại]"]}', encoding="utf-8")
        monkeypatch.setenv("POWERBI_POLICY_FILE", str(pf))
        allowed, _ = policy.check_dax("EVALUATE SUMMARIZECOLUMNS('KH'[Phân khúc])")
        assert allowed

    def test_audit_never_breaks_query(self, monkeypatch):
        monkeypatch.setenv("POWERBI_AUDIT_DIR", "Z:/duong/dan/khong/ton/tai")
        policy.audit("t", "EVALUATE ROW(1)", "allowed", 1)  # không raise là PASS

    def test_dimension_cap(self, monkeypatch):
        monkeypatch.delenv("POWERBI_AGGREGATE_ONLY", raising=False)
        df_dim = pd.DataFrame({"khu_vuc": ["A", "B"], "v": [1, 2]})
        df_num = pd.DataFrame({"v": [1.0, 2.0]})
        assert policy.cap_dimension_rows(df_dim, 1000) == policy.DIMENSION_ROW_CAP
        assert policy.cap_dimension_rows(df_dim, 0) == policy.DIMENSION_ROW_CAP
        assert policy.cap_dimension_rows(df_num, 1000) == 1000
        monkeypatch.setenv("POWERBI_AGGREGATE_ONLY", "0")
        assert policy.cap_dimension_rows(df_dim, 1000) == 1000


class TestPbir:
    def test_new_guid_format(self):
        from powerbi_agent import pbir
        g = pbir.new_guid()
        assert len(g) == 20 and all(c in "0123456789abcdef" for c in g)

    def test_projection_measure(self):
        from powerbi_agent import pbir
        p = pbir.projection("Measure", "Công thức", "Tổng TB")
        assert p["field"]["Measure"]["Expression"]["SourceRef"]["Entity"] == "Công thức"
        assert p["queryRef"] == "Công thức.Tổng TB" and p["nativeQueryRef"] == "Tổng TB"

    def test_projection_rejects_bad_kind(self):
        from powerbi_agent import pbir
        with pytest.raises(ValueError):
            pbir.projection("Hierarchy", "T", "C")

    def test_rebind_replaces_role(self):
        from powerbi_agent import pbir
        v = {"visual": {"query": {"queryState": {"Data": {"projections": [{"queryRef": "Old.X"}]}}}}}
        pbir.rebind_query_state(v, {"Data": [{"type": "Measure", "entity": "M", "property": "Doanh thu"}]})
        projs = v["visual"]["query"]["queryState"]["Data"]["projections"]
        assert len(projs) == 1 and projs[0]["queryRef"] == "M.Doanh thu"

    def test_deep_sanitize_covers_style_refs(self):
        from powerbi_agent import pbir
        v = {
            "visual": {
                "visualType": "cardVisual",
                "query": {"queryState": {"Data": {"projections": [
                    {"field": {"Measure": {"Expression": {"SourceRef": {"Entity": "Công thức"}},
                               "Property": "TB PTM"}},
                     "queryRef": "Công thức.TB PTM", "nativeQueryRef": "TB PTM"}]}}},
                "visualContainerObjects": {"x": [{"sel": "Công thức.TB PTM"}]},
            },
            "filterConfig": {"filters": [{"field": "bí mật"}]},
        }
        e, p = pbir.collect_field_names(v)
        m = pbir.build_sanitize_map(e, p)
        pbir.deep_sanitize(v, m)
        s = json.dumps(v, ensure_ascii=False)
        assert "Công thức" not in s and "TB PTM" not in s
        assert "filterConfig" not in v
        assert "TEMPLATE_TABLE" in s

    def test_deep_sanitize_image_resource_names(self):
        from powerbi_agent import pbir
        v = {"visual": {"visualType": "image", "objects": {"general": [
            {"properties": {"imageUrl": {"expr": {"ResourcePackageItem": {
                "ItemName": "client-logo47855673.png"}}}}}]}}}
        pbir.deep_sanitize(v, {})
        assert "client-logo" not in json.dumps(v)
        assert "TEMPLATE_IMAGE.png" in json.dumps(v)


class TestBackCompat:
    """Shim mcp_server_powerbi phải giữ nguyên bề mặt import cho host/cli."""

    def test_shim_exports(self):
        import mcp_server_powerbi as m
        assert callable(m.find_active_pbi_ports)
        assert hasattr(m, "mcp") and hasattr(m, "ADOMD_LOADED")

    def test_six_tools_registered(self):
        import asyncio

        import mcp_server_powerbi as m
        tools = asyncio.run(m.mcp.list_tools())
        names = {t.name for t in tools}
        assert {
            "list_local_reports", "execute_dax_local", "execute_dax_service",
            "add_measure_local", "add_relationship_local", "distill_model_schema",
        } <= names


class TestReportTemplates:
    """Hồi quy cho lần đổi tên templates/ -> report-templates/.

    Không có mấy test này thì CI vẫn xanh trong khi list_templates/apply_template
    đã trỏ vào thư mục không tồn tại.
    """

    def test_repo_kit_dir_is_report_templates(self, monkeypatch):
        # PHẢI gỡ env: POWERBI_TEMPLATES_DIR trỏ vào Knowledge Dir của user, mà thư mục
        # đó TÊN LÀ "templates" theo đúng thiết kế. Không isolate thì test đỏ trên chính
        # cấu hình mà repo khuyến nghị, và chỉ xanh trên CI vì CI không có env.
        monkeypatch.delenv("POWERBI_TEMPLATES_DIR", raising=False)
        from powerbi_agent.tools_template import _template_dirs
        assert os.path.basename(_template_dirs()[0]) == "report-templates"

    def test_bundled_kit_is_discoverable(self, monkeypatch):
        monkeypatch.delenv("POWERBI_TEMPLATES_DIR", raising=False)
        from powerbi_agent.tools_template import _load_kits
        names = {os.path.basename(p) for p, _ in _load_kits()}
        assert "kpim-business-light" in names

    def test_bundled_kit_manifest_readable(self):
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        kit = os.path.join(repo, "report-templates", "kpim-business-light", "kit.json")
        assert os.path.isfile(kit)
        with open(kit, encoding="utf-8") as fh:
            assert json.load(fh)

    def test_document_templates_folder_shipped_with_skill(self):
        """Mẫu tài liệu (trụ 4) phải nằm TRONG folder skill — installer copy cả thư mục."""
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        skill = os.path.join(repo, "plugins", "powerbi-agent", "skills", "kpim-analysis")
        assert os.path.isdir(os.path.join(skill, "document-templates"))
        assert not os.path.isdir(os.path.join(skill, "templates"))
        assert os.path.isfile(os.path.join(skill, "document-templates", "PROJECT.md"))


class TestKnowledgeIndexMigration:
    """Knowledge Dir dựng bởi bản < 0.5.0 mang placeholder `/pbi-new` cũ.

    ensure_skeleton chỉ ghi INDEX.md khi file CHƯA tồn tại, nên người nâng cấp giữ
    nguyên dòng cũ trên đĩa. Nếu register_project_in_index chỉ khớp tên mới thì
    placeholder cũ không bao giờ được thay -> INDEX của họ mãi bảo chạy `/pbi-new`,
    lệnh mà installer vừa xoá.
    """

    def _index_with(self, tmp_path, placeholder: str) -> str:
        (tmp_path / "INDEX.md").write_text(
            "# INDEX\n\n## Dự án (projects/)\n\n" + placeholder + "\n## Khác\n",
            encoding="utf-8",
        )
        return str(tmp_path)

    def test_replaces_legacy_pbi_placeholder(self, tmp_path):
        from powerbi_agent import knowledge as kn
        root = self._index_with(tmp_path, "_(chưa có — `/pbi-new <tên>` để bắt đầu)_\n")
        kn.register_project_in_index(root, "ban-le", "Bán lẻ")
        txt = (tmp_path / "INDEX.md").read_text(encoding="utf-8")
        assert "pbi-new" not in txt, "placeholder cũ còn sót — người nâng cấp thấy lệnh đã bị xoá"
        assert "projects/ban-le/PROJECT.md" in txt

    def test_replaces_current_placeholder(self, tmp_path):
        from powerbi_agent import knowledge as kn
        root = self._index_with(tmp_path, "_(chưa có — `/powerbi-new <tên>` để bắt đầu)_\n")
        kn.register_project_in_index(root, "ban-le", "Bán lẻ")
        txt = (tmp_path / "INDEX.md").read_text(encoding="utf-8")
        assert "chưa có" not in txt
        assert "projects/ban-le/PROJECT.md" in txt


class TestKnowledge:
    def test_slugify_vietnamese(self):
        from powerbi_agent import knowledge as kn
        assert kn.slugify("Dashboard Quản Trị Doanh Nghiệp — 2026!") == "dashboard-quan-tri-doanh-nghiep-2026"
        assert kn.slugify("Đơn đặt hàng") == "don-dat-hang"
        assert kn.slugify("///") == "project"

    def test_resolve_root_env(self, tmp_path, monkeypatch):
        """Thư mục user chọn CHÍNH LÀ gốc — không tự đẻ thêm cấp con."""
        from powerbi_agent import knowledge as kn
        monkeypatch.setenv("POWERBI_PROJECT_DIR", str(tmp_path))
        assert kn.resolve_root() == str(tmp_path)

    def test_resolve_root_none_when_unset(self, monkeypatch):
        from powerbi_agent import knowledge as kn
        monkeypatch.delenv(kn.ENV_KEY, raising=False)
        monkeypatch.setattr(kn, "LEGACY_CONFIG_FILE", "Z:/khong/ton/tai-cu.json")
        assert kn.resolve_root() is None

    def test_set_project_dir_preserves_secrets_in_env(self, tmp_path, monkeypatch):
        """Con trỏ ghi vào .env — mà .env CHỨA SECRET. Ghi ẩu = mất credential của user."""
        from powerbi_agent import knowledge as kn
        env = tmp_path / ".env"
        env.write_text(
            "\n".join([
                "# Cấu hình Power BI Service",
                "POWERBI_CLIENT_SECRET=sieu-bi-mat",
                "POWERBI_TENANT_ID=abc-123",
                "",
            ]),
            encoding="utf-8",
        )
        monkeypatch.setattr(kn, "ENV_FILE", str(env))
        monkeypatch.delenv(kn.ENV_KEY, raising=False)
        target = tmp_path / "du-an"
        out = kn.set_project_dir(str(target))

        txt = env.read_text(encoding="utf-8")
        assert "POWERBI_CLIENT_SECRET=sieu-bi-mat" in txt, "SECRET BỊ MẤT"
        assert "POWERBI_TENANT_ID=abc-123" in txt
        assert "Cấu hình Power BI Service" in txt, "comment tiếng Việt bị mất"
        assert f"{kn.ENV_KEY}={os.path.abspath(str(target))}" in txt
        assert out == os.path.abspath(str(target))
        # có bản backup trước khi ghi
        assert list(tmp_path.glob(".env.bak.*")), "không tạo backup trước khi sửa .env"

    def test_set_project_dir_is_idempotent(self, tmp_path, monkeypatch):
        """Chạy lại phải THAY dòng cũ, không nối thêm dòng thứ hai."""
        from powerbi_agent import knowledge as kn
        env = tmp_path / ".env"
        env.write_text("KEEP=1" + chr(10), encoding="utf-8")
        monkeypatch.setattr(kn, "ENV_FILE", str(env))
        monkeypatch.delenv(kn.ENV_KEY, raising=False)
        kn.set_project_dir(str(tmp_path / "a"))
        kn.set_project_dir(str(tmp_path / "b"))
        lines = [ln for ln in env.read_text(encoding="utf-8").splitlines()
                 if ln.startswith(kn.ENV_KEY + "=")]
        assert len(lines) == 1 and lines[0].endswith("b")
        assert "KEEP=1" in env.read_text(encoding="utf-8")

    def test_registry_lives_in_data_dir_not_repo(self, tmp_path, monkeypatch):
        """Sổ ghi nhớ đi cùng DỮ LIỆU: xoá repo không làm agent quên dự án."""
        from powerbi_agent import knowledge as kn
        monkeypatch.setenv(kn.ENV_KEY, str(tmp_path))
        assert kn.registry_file() == os.path.join(str(tmp_path), "projects.json")
        kn.register_project("bao-cao-a", "Báo cáo A", str(tmp_path / "noi-khac"))
        items = kn.load_registry()
        assert len(items) == 1 and items[0]["name"] == "Báo cáo A"
        # ghi lại cùng slug -> cập nhật, KHÔNG tạo bản trùng
        kn.register_project("bao-cao-a", "Báo cáo A", str(tmp_path / "moi"))
        items = kn.load_registry()
        assert len(items) == 1 and items[0]["path"].endswith("moi")

    def test_nothing_machine_specific_left_in_repo(self, tmp_path, monkeypatch):
        """audit/ · policy.json · distilled/ đều nói VỀ dữ liệu khách -> không được ở repo."""
        from powerbi_agent import policy
        from powerbi_agent.tools_distill import _resolve_output_dir
        from powerbi_agent import knowledge as kn
        repo = os.path.dirname(os.path.dirname(os.path.abspath(kn.__file__)))
        monkeypatch.setenv(kn.ENV_KEY, str(tmp_path))
        monkeypatch.delenv("POWERBI_AUDIT_DIR", raising=False)
        monkeypatch.delenv("POWERBI_POLICY_FILE", raising=False)
        monkeypatch.delenv("POWERBI_DISTILL_DIR", raising=False)
        for got in (policy._audit_dir(), policy._policy_file(), _resolve_output_dir(None)):
            assert os.path.commonpath([os.path.abspath(got), repo]) != repo, got

    def test_audit_falls_back_outside_repo_when_not_setup(self, monkeypatch):
        """Chạy DAX trước khi setup vẫn phải ghi audit — nhưng KHÔNG vào repo."""
        from powerbi_agent import policy
        from powerbi_agent import knowledge as kn
        repo = os.path.dirname(os.path.dirname(os.path.abspath(kn.__file__)))
        monkeypatch.delenv("POWERBI_AUDIT_DIR", raising=False)
        monkeypatch.delenv(kn.ENV_KEY, raising=False)
        monkeypatch.setattr(kn, "LEGACY_CONFIG_FILE", "Z:/khong/ton/tai.json")
        d = policy._audit_dir()
        assert os.path.commonpath([os.path.abspath(d), repo]) != repo

    def test_skeleton_and_timeline_and_index(self, tmp_path):
        from powerbi_agent import knowledge as kn
        root = str(tmp_path / "powerbi-agent")
        kn.ensure_skeleton(root)
        for ax in kn.KNOWLEDGE_AXES:
            assert os.path.isdir(os.path.join(root, "knowledge", ax))
        assert os.path.exists(os.path.join(root, "INDEX.md"))
        kn.append_timeline(root, "dự án A", "Khởi tạo", "bài học", "projects/a/")
        tl = open(os.path.join(root, "TIMELINE.md"), encoding="utf-8").read()
        assert "dự án A" in tl and "Khởi tạo" in tl
        kn.register_project_in_index(root, "a", "dự án A")
        idx = open(os.path.join(root, "INDEX.md"), encoding="utf-8").read()
        assert "projects/a/PROJECT.md" in idx
        # idempotent
        kn.register_project_in_index(root, "a", "dự án A")
        assert idx == open(os.path.join(root, "INDEX.md"), encoding="utf-8").read()


class TestDistill:
    def test_output_dir_param_wins(self, monkeypatch):
        from powerbi_agent.tools_distill import _resolve_output_dir
        monkeypatch.setenv("POWERBI_DISTILL_DIR", "C:/env-dir")
        assert _resolve_output_dir("C:/param-dir") == "C:/param-dir"

    def test_output_dir_env_fallback(self, monkeypatch):
        from powerbi_agent.tools_distill import _resolve_output_dir
        monkeypatch.setenv("POWERBI_DISTILL_DIR", "C:/env-dir")
        assert _resolve_output_dir(None) == "C:/env-dir"

    def test_output_dir_default_outside_repo(self, monkeypatch):
        from powerbi_agent.tools_distill import _resolve_output_dir
        monkeypatch.delenv("POWERBI_DISTILL_DIR", raising=False)
        out = _resolve_output_dir(None)
        assert ".powerbi-agent" not in out  # không dùng thư mục dấu chấm nữa


class TestIndexMigration:
    """INDEX.md dựng bởi bản <0.5.0 trỏ tới lệnh /pbi-* mà installer đã xoá."""

    def test_migrate_renames_old_commands(self, tmp_path):
        from powerbi_agent import knowledge as kn
        idx = tmp_path / "INDEX.md"
        idx.write_text("Chạy `/pbi-new <tên>` rồi `/pbi-done`.\n", encoding="utf-8")
        assert kn.migrate_index(str(tmp_path)) is True
        txt = idx.read_text(encoding="utf-8")
        assert "/powerbi-new" in txt and "/powerbi-done" in txt
        assert "/pbi-new" not in txt

    def test_migrate_is_idempotent_and_reports_no_change(self, tmp_path):
        from powerbi_agent import knowledge as kn
        idx = tmp_path / "INDEX.md"
        idx.write_text("Chạy `/powerbi-new`.\n", encoding="utf-8")
        assert kn.migrate_index(str(tmp_path)) is False

    def test_migrate_leaves_user_knowledge_alone(self, tmp_path):
        """Chỉ đổi TÊN LỆNH — không đụng nội dung tri thức user tự viết."""
        from powerbi_agent import knowledge as kn
        idx = tmp_path / "INDEX.md"
        idx.write_text("Bài học: dùng SUMMARIZECOLUMNS. Lệnh `/pbi-pack`.\n", encoding="utf-8")
        kn.migrate_index(str(tmp_path))
        assert "Bài học: dùng SUMMARIZECOLUMNS." in idx.read_text(encoding="utf-8")
