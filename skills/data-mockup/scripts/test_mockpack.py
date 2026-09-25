# -*- coding: utf-8 -*-
"""Self-test cho mockpack + mockverify — chạy `python test_mockpack.py`, KHÔNG cần pytest.

In PASS/FAIL từng case, exit 1 nếu có case fail. Mọi file trung gian nằm trong
thư mục tạm (tempfile.mkdtemp) và được dọn sạch sau khi chạy — không để rác lại.
"""
from __future__ import annotations

import contextlib
import io
import os
import shutil
import sys
import tempfile

import pandas as pd
import yaml

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPTS_DIR)
import mockpack as mp          # noqa: E402
import mockverify              # noqa: E402
import gen_skeleton            # noqa: E402

TEMPLATE_YAML = os.path.join(SCRIPTS_DIR, "..", "..", "..", "templates", "documents", "dataset", "dataset.template.yaml")

TMP = tempfile.mkdtemp(prefix="mockpack_test_")
_counter = [0]


def _write_spec(spec_dict) -> str:
    """Ghi spec dict ra file yaml tạm, trả về đường dẫn — mỗi lần một file riêng."""
    _counter[0] += 1
    path = os.path.join(TMP, f"spec_{_counter[0]}.yaml")
    with open(path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(spec_dict, fh, allow_unicode=True)
    return path


def _load(spec_dict):
    # nuốt stdout để cảnh báo `! cảnh báo:` không làm nhiễu output test
    with contextlib.redirect_stdout(io.StringIO()):
        return mp.load_spec(_write_spec(spec_dict))


def _must_raise(spec_dict, hint: str):
    try:
        _load(spec_dict)
    except ValueError:
        return
    raise AssertionError(f"load_spec PHẢI raise ValueError ({hint}) nhưng lại chạy qua")


def base_spec():
    """Spec tối thiểu hợp lệ — mỗi case mutate một bản copy riêng."""
    return {
        "dataset": {"id": "t", "seed": 1, "as_of_date": "2026-01-31", "layer": "business"},
        "tables": [
            {"name": "dim_a", "grain": "1 dòng / a", "sheet": "A", "layer": "both",
             "columns": [
                 {"name": "id_a", "type": "text", "key": "PK", "definition": "khoá"},
                 {"name": "ten", "type": "text", "definition": "tên"},
             ]},
        ],
    }


# =============================================================================
# CASES
# =============================================================================


def case_template_loads():
    with contextlib.redirect_stdout(io.StringIO()):
        spec = mp.load_spec(TEMPLATE_YAML)
    assert spec["dataset"]["id"] == "ban-le-demo"
    assert len(spec["tables"]) == 4


def case_bad_table_name():
    s = base_spec(); s["tables"][0]["name"] = "Dim-A"
    _must_raise(s, "tên bảng xấu")
    s = base_spec(); s["tables"][0]["name"] = "../evil"
    _must_raise(s, "tên bảng path traversal")


def case_bad_column_name():
    s = base_spec(); s["tables"][0]["columns"][1]["name"] = "Tên Cột"
    _must_raise(s, "tên cột xấu")


def case_bad_type():
    s = base_spec(); s["tables"][0]["columns"][1]["type"] = "varchar"
    _must_raise(s, "type lạ")


def case_bad_layer():
    s = base_spec(); s["dataset"]["layer"] = "prod"
    _must_raise(s, "dataset.layer lạ")
    s = base_spec(); s["tables"][0]["layer"] = "weird"
    _must_raise(s, "table.layer lạ")


def case_enum_missing_values():
    s = base_spec(); s["tables"][0]["columns"][1]["type"] = "enum"
    _must_raise(s, "enum thiếu values")


def case_fk_non_pk():
    s = base_spec()
    s["tables"].append({"name": "fact_b", "grain": "1 dòng / b", "sheet": "B",
                        "columns": [{"name": "ten", "type": "text",
                                     "key": "FK->dim_a.ten", "definition": "trỏ cột thường"}]})
    _must_raise(s, "FK trỏ non-PK")


def case_duplicate_label():
    s = base_spec()
    s["tables"][0]["columns"][0]["label"] = "Trùng"
    s["tables"][0]["columns"][1]["label"] = "Trùng"
    _must_raise(s, "label trùng trong một bảng")


def case_duplicate_sheet():
    s = base_spec()
    s["tables"][0]["sheet"] = "S/1"      # sanitize → S-1
    s["tables"].append({"name": "dim_b", "grain": "1 dòng / b", "sheet": "S:1",  # sanitize → S-1
                        "columns": [{"name": "id_b", "type": "text", "definition": "x"}]})
    _must_raise(s, "sheet trùng sau sanitize")


def case_two_pk():
    s = base_spec(); s["tables"][0]["columns"][1]["key"] = "PK"
    _must_raise(s, "2 cột PK")


def case_metric_ghost_table():
    s = base_spec(); s["metrics"] = [{"name": "X", "table": "ghost"}]
    _must_raise(s, "metric trỏ bảng ma")


def case_missing_definition_only_warns():
    s = base_spec(); del s["tables"][0]["columns"][1]["definition"]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        mp.load_spec(_write_spec(s))       # KHÔNG được raise — đang soạn dở vẫn chạy
    assert "! cảnh báo" in buf.getvalue()


def case_to_datetime_smart():
    iso = mp.to_datetime_smart(pd.Series(["2026-09-12"]))
    assert iso.iloc[0].month == 9 and iso.iloc[0].day == 12, "ISO bị lật ngày/tháng"
    vn = mp.to_datetime_smart(pd.Series(["12/09/2026"]))
    assert vn.iloc[0].month == 9 and vn.iloc[0].day == 12, "dd/mm/yyyy đọc sai"


def case_safe_excel_text():
    for bad in ("=1+1", "+x", "-x", "@x"):
        assert mp.safe_excel_text(bad) == "'" + bad, f"thiếu prefix cho {bad!r}"
    assert mp.safe_excel_text("abc") == "abc"
    assert mp.safe_excel_text("") == ""
    assert mp.safe_excel_text(None) is None
    assert mp.safe_excel_text(5) == 5
    assert mp.safe_excel_text(3.14) == 3.14


def case_pack_fail_fast():
    spec = _load(base_spec())
    empty = os.path.join(TMP, "empty_data"); os.makedirs(empty, exist_ok=True)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            mp.pack(spec, empty, os.path.join(TMP, "should_not_exist.xlsx"))
    except ValueError:
        assert not os.path.exists(os.path.join(TMP, "should_not_exist.xlsx")), "raise nhưng vẫn lưu file"
        return
    raise AssertionError("pack PHẢI raise khi thiếu bảng dữ liệu")


def _verify_spec_dict():
    """Spec 2 bảng cho case verify: đủ PK, FK, enum, bool, date để cài lỗi."""
    return {
        "dataset": {"id": "v", "seed": 1, "as_of_date": "2026-01-31", "layer": "both"},
        "tables": [
            {"name": "dim_a", "grain": "1 dòng / a", "sheet": "A",
             "columns": [
                 {"name": "id_a", "type": "text", "key": "PK", "nullable": False, "definition": "khoá"},
                 {"name": "flag", "type": "bool", "definition": "cờ"},
                 {"name": "cat", "type": "enum", "values": ["X", "Y"], "definition": "danh mục"},
                 {"name": "d", "type": "date", "definition": "ngày"},
             ]},
            {"name": "fact_b", "grain": "1 dòng / b", "sheet": "B",
             "columns": [
                 {"name": "id_b", "type": "text", "key": "PK", "definition": "khoá"},
                 {"name": "id_a", "type": "text", "key": "FK->dim_a.id_a", "definition": "fk"},
             ]},
        ],
    }


def _run_verify(spec_dict, dim_a_rows, fact_b_rows):
    spec = _load(spec_dict)
    _counter[0] += 1
    data = os.path.join(TMP, f"vdata_{_counter[0]}"); os.makedirs(data, exist_ok=True)
    with open(os.path.join(data, "dim_a.csv"), "w", encoding="utf-8") as fh:
        fh.write("id_a,flag,cat,d\n" + "\n".join(dim_a_rows) + "\n")
    with open(os.path.join(data, "fact_b.csv"), "w", encoding="utf-8") as fh:
        fh.write("id_b,id_a\n" + "\n".join(fact_b_rows) + "\n")
    with contextlib.redirect_stdout(io.StringIO()):
        return mockverify.verify(spec, data)


def case_verify_catches_errors():
    rep = _run_verify(
        _verify_spec_dict(),
        # dòng 2: PK trùng + bool rác + enum lạ + ngày vượt as_of (2026-01-31)
        ["A1,true,X,2026-01-01", "A1,rác,Z,2026-02-15"],
        ["B1,A9"],                                        # FK mồ côi
    )
    status = {r[0]: r[2] for r in rep.rows}
    for rid in ("pk_unique:dim_a.id_a", "dtype:dim_a.flag", "enum_values:dim_a.cat",
                "as_of:dim_a.d", "fk_subset:fact_b.id_a"):
        assert status.get(rid) == "FAIL", f"rule {rid} phải FAIL, đang là {status.get(rid)}"


def case_verify_waived():
    s = _verify_spec_dict()
    s["intentional_issues"] = [{"id": "DQ-T", "description": "enum lạ cố ý",
                                "waives": ["enum_values:dim_a.cat"]}]
    rep = _run_verify(s, ["A1,true,X,2026-01-01", "A2,false,Z,2026-01-02"], ["B1,A1"])
    status = {r[0]: r[2] for r in rep.rows}
    assert status["enum_values:dim_a.cat"] == "WAIVED"
    assert all(r[0] != "enum_values:dim_a.cat" for r in rep.failed), "rule waived không được tính là FAIL"


def case_round_trip():
    """gen_skeleton → verify(dir) → pack → verify(.xlsx) — cả hai lần 0 FAIL."""
    with open(TEMPLATE_YAML, "r", encoding="utf-8") as fh:
        spec_dict = yaml.safe_load(fh)
    for t in spec_dict["tables"]:       # giảm fact xuống 300 dòng cho test chạy nhanh
        if t["name"] == "fact_don_hang":
            t["rows"] = 300
    spec_path = _write_spec(spec_dict)
    data = os.path.join(TMP, "rt_data")
    xlsx = os.path.join(TMP, "rt_pack.xlsx")
    with contextlib.redirect_stdout(io.StringIO()):
        gen_skeleton.main([spec_path, "-o", data])
        spec = mp.load_spec(spec_path)
        rep1 = mockverify.verify(spec, data)
        mp.pack(spec, data, xlsx)
        rep2 = mockverify.verify(spec, xlsx)
    assert not rep1.failed, f"verify(dir) còn FAIL: {[r[0] for r in rep1.failed]}"
    assert not rep2.failed, f"verify(xlsx) còn FAIL: {[r[0] for r in rep2.failed]}"
    assert rep1.waived_rows, "DQ-01 của template phải ra WAIVED"
    assert rep1.warned, "cột pii (ho_ten) phải ra WARN"


# =============================================================================
# RUNNER
# =============================================================================

CASES = [
    ("load_spec chấp nhận template", case_template_loads),
    ("FIX A: tên bảng xấu → raise", case_bad_table_name),
    ("FIX A: tên cột xấu → raise", case_bad_column_name),
    ("FIX A: type lạ → raise", case_bad_type),
    ("FIX A: layer lạ → raise", case_bad_layer),
    ("FIX A: enum thiếu values → raise", case_enum_missing_values),
    ("FIX A: FK trỏ non-PK → raise", case_fk_non_pk),
    ("FIX A: label trùng → raise", case_duplicate_label),
    ("FIX A: sheet trùng sau sanitize → raise", case_duplicate_sheet),
    ("FIX A: 2 cột PK → raise", case_two_pk),
    ("FIX A: metric trỏ bảng ma → raise", case_metric_ghost_table),
    ("FIX A: thiếu definition chỉ cảnh báo", case_missing_definition_only_warns),
    ("to_datetime_smart: ISO không lật ngày/tháng", case_to_datetime_smart),
    ("safe_excel_text: prefix đúng", case_safe_excel_text),
    ("FIX C: pack fail-fast khi thiếu bảng", case_pack_fail_fast),
    ("verify bắt FK mồ côi/PK trùng/enum lạ/bool rác/vượt as_of", case_verify_catches_errors),
    ("verify: WAIVED không tính là FAIL", case_verify_waived),
    ("round-trip gen → verify → pack → verify: 0 FAIL", case_round_trip),
]


def main():
    fails = 0
    try:
        for name, fn in CASES:
            try:
                fn()
                print(f"PASS  {name}")
            except Exception as exc:
                fails += 1
                print(f"FAIL  {name}: {exc}")
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print(f"\n{len(CASES)} case | FAIL={fails}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
