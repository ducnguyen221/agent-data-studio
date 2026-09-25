# -*- coding: utf-8 -*-
"""mockverify — engine kiểm tra dữ liệu của skill `mockup-data`.

Tách khỏi mockpack.py để mỗi file một việc: mockpack lo spec / helper sinh số /
đóng gói Excel; file này lo TOÀN BỘ rule verify — rule cơ bản tự suy từ spec
(PK, FK, not-null, dtype, enum, khoảng giá trị, as_of, PII) và rule nghiệp vụ
khai trong `rules:` của dataset.yaml.

KHÔNG chạy file này trực tiếp — người dùng vẫn gọi qua CLI cũ:

    python mockpack.py verify dataset.yaml data/ -o DATA_QUALITY_REPORT.md

(mockpack.main() import hàm `verify` từ đây ngay trong nhánh lệnh verify —
import cục bộ để tránh vòng lặp import, vì file này cũng `import mockpack`.)
"""
from __future__ import annotations

import pandas as pd

import mockpack as mp


class Report:
    """Gom kết quả rule. 4 trạng thái: PASS / FAIL / WAIVED / WARN.

    WARN là nhắc nhở (vd cột đã khai `pii: true`) — hiện trong báo cáo và stdout
    nhưng KHÔNG làm hỏng exit code; chỉ FAIL mới chặn bàn giao.
    """

    def __init__(self, waived: set):
        self.rows = []
        self.waived = waived

    def check(self, rule_id: str, name: str, ok: bool, detail: str = ""):
        status = "PASS" if ok else ("WAIVED" if rule_id in self.waived else "FAIL")
        self.rows.append((rule_id, name, status, detail))
        print(f"{status:<6}| {rule_id:<44}| {name}" + (f" | {detail}" if detail else ""))
        return status

    def warn(self, rule_id: str, name: str, detail: str = ""):
        self.rows.append((rule_id, name, "WARN", detail))
        print(f"{'WARN':<6}| {rule_id:<44}| {name}" + (f" | {detail}" if detail else ""))
        return "WARN"

    @property
    def failed(self):
        return [r for r in self.rows if r[2] == "FAIL"]

    @property
    def waived_rows(self):
        return [r for r in self.rows if r[2] == "WAIVED"]

    @property
    def warned(self):
        return [r for r in self.rows if r[2] == "WARN"]


def verify(spec: dict, source: str, out_path: str | None = None) -> Report:
    frames = mp.read_frames(spec, source)
    rep = Report(mp.waived_ids(spec))
    as_of = spec["dataset"].get("as_of_date")
    as_of = pd.Timestamp(as_of) if as_of else None

    # Đọc từ .xlsx thì chỉ đòi các bảng thuộc lớp đã đóng gói; đọc từ thư mục CSV thì đòi đủ.
    expected = mp.tables_for_layer(spec) if source.lower().endswith((".xlsx", ".xlsm")) else spec["tables"]

    typed = {}
    for tbl in expected:
        name = tbl["name"]
        if name not in frames:
            rep.check(f"exists:{name}", f"Có dữ liệu cho bảng `{name}`", False, "không tìm thấy file/sheet")
            continue
        rep.check(f"exists:{name}", f"Có dữ liệu cho bảng `{name}`", True, f"{len(frames[name])} dòng")
        typed[name] = mp.typed_frame(frames[name], tbl)

    # ---- rule cơ bản, suy ra từ spec ----
    for tbl in spec["tables"]:
        name = tbl["name"]
        if name not in typed:
            continue
        df, raw = typed[name], frames[tbl["name"]]

        declared = [c["name"] for c in tbl["columns"]]
        missing = [c for c in declared if c not in raw.columns]
        extra = [c for c in raw.columns if c not in declared]
        rep.check(f"schema:{name}", f"`{name}` đúng danh sách cột trong spec", not missing and not extra,
                  f"thiếu={missing} thừa={extra}" if (missing or extra) else f"{len(declared)} cột")

        if tbl.get("rows"):
            tol = float(tbl.get("rows_tolerance", 0))
            lo, hi = tbl["rows"] * (1 - tol), tbl["rows"] * (1 + tol)
            rep.check(f"row_count:{name}", f"`{name}` đúng số dòng khai báo", lo <= len(df) <= hi,
                      f"thực tế={len(df)} khai={tbl['rows']} dung sai=±{tol:.0%}")

        for col in tbl["columns"]:
            cn, ctype = col["name"], col["type"]
            if cn not in df.columns:
                continue
            series = df[cn]

            if col.get("key") == "PK":
                rep.check(f"pk_unique:{name}.{cn}", f"`{cn}` là khoá chính duy nhất, không rỗng",
                          series.is_unique and series.notna().all(),
                          f"trùng={int(series.duplicated().sum())} rỗng={int(series.isna().sum())}")

            if not col.get("nullable", True):
                nulls = int(series.isna().sum())
                rep.check(f"not_null:{name}.{cn}", f"`{cn}` không được rỗng", nulls == 0, f"rỗng={nulls}")

            if ctype in ("int", "decimal", "date", "timestamp", "bool"):
                # ô có nội dung ở bản thô nhưng ép kiểu thất bại = giá trị hỏng
                # (bool: typed_frame trả None cho giá trị rác — cũng bắt ở đây)
                filled = raw[cn].notna() & raw[cn].map(lambda v: str(v).strip() != "")
                bad = int((series.isna() & filled).sum())
                rep.check(f"dtype:{name}.{cn}", f"`{cn}` ép được về kiểu {ctype}", bad == 0, f"giá trị hỏng={bad}")

            if ctype == "enum" and col.get("values"):
                got = set(series.dropna().unique()) - set(col["values"])
                rep.check(f"enum_values:{name}.{cn}", f"`{cn}` chỉ nhận giá trị trong danh mục",
                          not got, f"giá trị lạ={sorted(got)[:5]}")

            if col.get("min") is not None or col.get("max") is not None:
                num = pd.to_numeric(series, errors="coerce")
                bad = 0
                if col.get("min") is not None:
                    bad += int((num < col["min"]).sum())
                if col.get("max") is not None:
                    bad += int((num > col["max"]).sum())
                rep.check(f"range:{name}.{cn}", f"`{cn}` nằm trong khoảng cho phép", bad == 0, f"ngoài khoảng={bad}")

            if as_of is not None and ctype in ("date", "timestamp"):
                bad = int((series > as_of).sum())
                rep.check(f"as_of:{name}.{cn}", f"`{cn}` không vượt mốc hiện tại {as_of.date()}", bad == 0,
                          f"vượt mốc={bad}")

            base = cn.lower()
            if any(base == p or base.startswith(p + "_") for p in mp.PII_FORBIDDEN) \
                    and not base.endswith(mp.PII_ALLOWED_SUFFIX) and not col.get("pii"):
                rep.check(f"no_pii:{name}.{cn}", f"`{cn}` là cột PII chưa được che/khai báo", False,
                          "đổi sang *_masked/*_hash hoặc khai `pii: true` nếu là dữ liệu giả lập")

            if col.get("pii"):
                # WARN chứ không FAIL: đã khai báo là hợp lệ, nhưng phải nhắc mỗi lần verify
                rep.warn(f"pii_declared:{name}.{cn}", f"`{cn}` khai `pii: true`",
                         "phải là dữ liệu giả lập/đã che, không được lấy từ người thật")

            ref = mp.parse_fk(col.get("key"))
            if ref and ref[0] in typed:
                parent = typed[ref[0]][ref[1]]
                child = series.dropna()
                orphan = set(child.unique()) - set(parent.dropna().unique())
                rep.check(f"fk_subset:{name}.{cn}", f"`{cn}` ⊆ `{ref[0]}.{ref[1]}`", not orphan,
                          f"mồ côi={len(orphan)} vd={sorted(orphan)[:3]}")

    # ---- rule nghiệp vụ khai trong spec ----
    for rule in spec.get("rules", []):
        rid = rule.get("id") or rule.get("name", "?")
        rname = rule.get("name", rid)
        kind = rule.get("kind", "expression")
        tname = rule.get("table")
        if kind != "sum_match" and tname not in typed:
            rep.check(rid, rname, False, f"bảng `{tname}` không có dữ liệu")
            continue
        try:
            if kind == "expression":
                df = typed[tname]
                res = df.eval(rule["expr"], engine="python")
                bad = int((~res.fillna(False)).sum())
                rep.check(rid, rname, bad == 0, f"vi phạm={bad}/{len(df)}")

            elif kind == "unique":
                df = typed[tname]
                dup = int(df.duplicated(subset=rule["columns"]).sum())
                rep.check(rid, rname, dup == 0, f"trùng={dup} trên {rule['columns']}")

            elif kind == "row_count":
                rep.check(rid, rname, len(typed[tname]) == rule["expected"],
                          f"thực tế={len(typed[tname])} kỳ vọng={rule['expected']}")

            elif kind == "ratio":
                df = typed[tname]
                num = df.eval(rule["numerator"], engine="python")
                num = float(num.fillna(False).sum()) if num.dtype == bool else float(num.fillna(0).sum())
                den = float(len(df)) if rule.get("denominator", "rows") == "rows" else \
                    float(df.eval(rule["denominator"], engine="python").fillna(0).sum())
                val = num / den if den else 0.0
                lo, hi = rule.get("min", 0), rule.get("max", 1)
                rep.check(rid, rname, lo <= val <= hi, f"tỉ lệ={val:.2%} khoảng=[{lo:.2%}, {hi:.2%}]")

            elif kind == "funnel":
                df = typed[tname]
                counts = []
                for step in rule["steps"]:
                    if step in df.columns:
                        counts.append(float(pd.to_numeric(df[step], errors="coerce").fillna(0).sum()))
                    else:
                        counts.append(float(df.eval(step, engine="python").fillna(False).sum()))
                ok = all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))
                rep.check(rid, rname, ok, " ≥ ".join(f"{c:,.0f}" for c in counts))

            elif kind == "sum_match":
                child, parent = typed[rule["child"]], typed[rule["parent"]]
                on = rule["on"]
                tol = float(rule.get("tolerance", 1))
                agg = pd.to_numeric(child[rule["child_col"]], errors="coerce").groupby(child[on]).sum()
                ref = pd.to_numeric(parent.set_index(on)[rule["parent_col"]], errors="coerce")
                joined = agg.reindex(ref.index).fillna(0)
                bad = int(((joined - ref).abs() > tol).sum())
                rep.check(rid, rname, bad == 0, f"lệch quá dung sai={bad}/{len(ref)}")

            else:
                rep.check(rid, rname, False, f"kind `{kind}` không được hỗ trợ")
        except Exception as exc:  # rule sai cú pháp cũng là lỗi cần thấy
            rep.check(rid, rname, False, f"lỗi khi chạy rule: {exc}")

    print(f"\n{len(rep.rows)} rule | PASS={sum(1 for r in rep.rows if r[2] == 'PASS')} "
          f"| FAIL={len(rep.failed)} | WAIVED={len(rep.waived_rows)} | WARN={len(rep.warned)}")

    if out_path:
        write_report(spec, rep, out_path, source)
        print(f"→ {out_path}")
    return rep


def write_report(spec: dict, rep: Report, path: str, source: str):
    ds = spec["dataset"]
    lines = [
        f"# DATA QUALITY REPORT — {ds.get('name', ds['id'])}",
        "",
        f"- Nguồn dữ liệu: `{source}`",
        f"- Seed: `{ds['seed']}` · mốc hiện tại: `{ds.get('as_of_date', '—')}` · lớp: `{ds.get('layer')}`",
        f"- Tổng: **{len(rep.rows)} rule** — PASS {sum(1 for r in rep.rows if r[2] == 'PASS')} · "
        f"FAIL {len(rep.failed)} · WAIVED {len(rep.waived_rows)} · WARN {len(rep.warned)}",
        "",
        "## Kết luận",
        "",
        ("**ĐẠT** — không còn lỗi thật, đủ điều kiện bàn giao." if not rep.failed
         else f"**CHƯA ĐẠT** — còn {len(rep.failed)} rule FAIL, phải quay lại pha sinh dữ liệu (hoặc sửa spec)."),
        "",
    ]
    if spec.get("intentional_issues"):
        lines += ["## Lỗi cài cắm có chủ đích", "",
                  "| ID | Mô tả | Rule được miễn |", "|---|---|---|"]
        for issue in spec["intentional_issues"]:
            lines.append(f"| {issue.get('id', '')} | {issue.get('description', '')} | "
                         f"{', '.join(f'`{w}`' for w in issue.get('waives', []) or []) or '—'} |")
        lines.append("")
    lines += ["## Chi tiết", "", "| Rule | Nội dung | Kết quả | Ghi chú |", "|---|---|---|---|"]
    for rid, name, status, detail in rep.rows:
        mark = {"PASS": "PASS", "FAIL": "**FAIL**", "WAIVED": "WAIVED (chủ đích)",
                "WARN": "WARN (nhắc nhở)"}[status]
        lines.append(f"| `{rid}` | {name} | {mark} | {detail} |")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
