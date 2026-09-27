# -*- coding: utf-8 -*-
"""gen_skeleton — generator mẫu bán lẻ, chạy từ repo với spec và output ở trạm.

Bản mẫu này sinh đúng bộ BÁN LẺ mô tả trong `templates/documents/dataset/dataset.template.yaml` (gốc repo),
chạy được ngay để bạn thấy pipeline đầy đủ. Spec ngành khác cần generator riêng được
triển khai trong source repo; script mẫu không tự suy ra builder từ mọi spec.

    python gen_skeleton.py <dataset.yaml> -o <thu-muc-du-an>/data
    python mockpack.py verify <dataset.yaml> <thu-muc-du-an>/data -o <thu-muc-du-an>/DATA_QUALITY_REPORT.md
    python mockpack.py pack <dataset.yaml> <thu-muc-du-an>/data -o <thu-muc-du-an>/BanLe.xlsx

Khi phát triển generator khác trong source repo, giữ 4 nguyên tắc:

1. Một nguồn ngẫu nhiên duy nhất `r = mp.rng(seed)` — không dùng random.* toàn cục.
2. Thứ tự sinh: cfg → dim → bridge → fact → lớp nghiệp vụ.
3. Cột dẫn xuất tính bằng công thức, không sinh ngẫu nhiên rời rạc (nếu không rule sẽ FAIL).
4. Mọi mốc thời gian ≤ `as_of_date`.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np
import pandas as pd

# Helper và generator dùng chung luôn ở cùng thư mục scripts của repo.
import mockpack as mp  # noqa: E402


# =============================================================================
# DIM
# =============================================================================

TINH_THANH = ["Hà Nội", "TP HCM", "Đà Nẵng", "Hải Phòng", "Cần Thơ"]
NGANH_HANG = ["Thực phẩm", "Đồ uống", "Hoá mỹ phẩm", "Gia dụng", "Điện tử"]
KHU_VUC = ["Bắc", "Trung", "Nam"]
# phân khúc chi phối hành vi mua — nguồn của các tương quan trong bộ dữ liệu
PHAN_KHUC = {"Pho thong": 0.62, "Than thiet": 0.29, "VIP": 0.09}


def build_dim_khach_hang(r, cfg, tables):
    n = cfg["rows"]["dim_khach_hang"]
    ten = mp.vn_names(r, n)
    dang_ky = mp.date_series(r, n, "2023-01-01", cfg["as_of"], trend=0.4)
    tinh = list(r.choice(TINH_THANH, n, p=[0.30, 0.34, 0.14, 0.12, 0.10]))

    # LỖI CÀI CẮM DQ-01: ~2% ghi sai chính tả tên tỉnh — đã khai trong intentional_issues
    for idx in r.choice(n, size=max(1, int(n * 0.02)), replace=False):
        if tinh[idx] == "Hà Nội":
            tinh[idx] = "Ha Noi"

    return pd.DataFrame({
        "ma_kh": mp.id_seq("KH-", n),
        "ho_ten": ten,
        "nhom_tuoi": r.choice(["18-24", "25-34", "35-44", "45-54", "55+"], n, p=[.14, .34, .27, .17, .08]),
        "gioi_tinh": r.choice(["Nam", "Nữ", "Khác"], n, p=[.46, .52, .02]),
        "tinh_thanh": tinh,
        "phan_khuc": r.choice(list(PHAN_KHUC), n, p=list(PHAN_KHUC.values())),
        "ngay_dang_ky": dang_ky.date,
        "email_masked": [mp.mask_email(mp.slugify(t)) for t in ten],
        "sdt_masked": [mp.mask_phone(f"09{r.integers(10**7, 10**8)}") for _ in range(n)],
    })


def build_dim_san_pham(r, cfg, tables):
    n = cfg["rows"]["dim_san_pham"]
    nganh = r.choice(NGANH_HANG, n, p=[.30, .22, .20, .18, .10])
    # giá theo ngành hàng: điện tử đắt hơn thực phẩm cả chục lần
    median = {"Thực phẩm": 45_000, "Đồ uống": 30_000, "Hoá mỹ phẩm": 120_000,
              "Gia dụng": 350_000, "Điện tử": 2_500_000}
    don_gia = np.array([mp.lognormal_amount(r, 1, median[g], sigma=0.45)[0] for g in nganh])
    don_gia = np.maximum(don_gia, 1000)
    bien = r.uniform(0.18, 0.42, n)                       # biên gộp mục tiêu theo mã
    gia_von = np.maximum(np.round(don_gia * (1 - bien) / 500) * 500, 500)
    return pd.DataFrame({
        "ma_sp": mp.id_seq("SP-", n, width=4),
        "ten_sp": [f"{g} mẫu {i:03d}" for i, g in enumerate(nganh, 1)],
        "nganh_hang": nganh,
        "don_gia": don_gia,
        "gia_von": gia_von,
    })


def build_dim_cua_hang(r, cfg, tables):
    n = cfg["rows"]["dim_cua_hang"]
    kv = [KHU_VUC[i % 3] for i in range(n)]
    return pd.DataFrame({
        "ma_ch": mp.id_seq("CH-", n, width=2),
        "ten_ch": [f"Cửa hàng Mẫu {k} {i:02d}" for i, k in enumerate(kv, 1)],
        "khu_vuc": kv,
        "ngay_khai_truong": mp.date_series(r, n, "2019-01-01", "2024-12-31").date,
    })


# =============================================================================
# FACT
# =============================================================================

# mùa vụ: Tết (T1–T2) và mùa mua sắm cuối năm (T11–T12) cao hơn hẳn
MONTH_W = {1: 1.45, 2: 1.30, 3: 0.95, 4: 0.90, 5: 0.95, 6: 1.00,
           7: 1.00, 8: 0.95, 9: 1.00, 10: 1.05, 11: 1.25, 12: 1.50}
DOW_W = {0: 0.85, 1: 0.85, 2: 0.90, 3: 0.95, 4: 1.15, 5: 1.45, 6: 1.30}   # T2..CN
# phân khúc → số dòng hàng mỗi đơn và mức chi
SEG_LINES = {"Pho thong": 1.4, "Than thiet": 2.2, "VIP": 3.0}
SEG_QTY = {"Pho thong": 1.6, "Than thiet": 2.4, "VIP": 3.4}


def build_fact_don_hang(r, cfg, tables):
    target = cfg["rows"]["fact_don_hang"]
    kh, sp, ch = tables["dim_khach_hang"], tables["dim_san_pham"], tables["dim_cua_hang"]
    gia_von_map = dict(zip(sp["ma_sp"], sp["gia_von"]))
    don_gia_map = dict(zip(sp["ma_sp"], sp["don_gia"]))
    seg_map = dict(zip(kh["ma_kh"], kh["phan_khuc"]))

    n_orders = int(target / 2.0) + 200
    ngay = mp.date_series(r, n_orders, cfg["period_start"], cfg["as_of"],
                          month_weights=MONTH_W, dow_weights=DOW_W, trend=0.35)
    khach = mp.pareto_pick(r, list(kh["ma_kh"]), n_orders, alpha=0.7)   # 20% khách mua nhiều nhất
    cua_hang = r.choice(list(ch["ma_ch"]), n_orders)
    kenh = r.choice(["Offline", "Online", "App"], n_orders, p=[.55, .27, .18])
    trang_thai = r.choice(["Hoan thanh", "Huy", "Doi tra"], n_orders, p=[.905, .065, .030])
    as_of_ts = pd.Timestamp(cfg["as_of"])

    rows = []
    for i in range(n_orders):
        if len(rows) >= target:
            break
        seg = seg_map[khach[i]]
        n_line = int(np.clip(r.poisson(SEG_LINES[seg]) + 1, 1, 5))
        # BR-05: một đơn không lặp lại cùng sản phẩm
        mats = list(dict.fromkeys(mp.pareto_pick(r, list(sp["ma_sp"]), n_line * 3, alpha=1.1)))[:n_line]
        ma_don = f"DH-{i + 1:06d}"
        for j, ma_sp in enumerate(mats, 1):
            so_luong = int(np.clip(r.poisson(SEG_QTY[seg]) + 1, 1, 20))
            # giá bán thực tế lệch nhẹ so với niêm yết (khuyến mãi, làm tròn tại quầy)
            don_gia = float(max(round(don_gia_map[ma_sp] * r.uniform(0.93, 1.0) / 1000) * 1000, 1000))
            gia_tri = so_luong * don_gia
            giam = 0.0
            if r.random() < (0.45 if seg != "Pho thong" else 0.25):
                giam = float(min(round(gia_tri * r.uniform(0.02, 0.15) / 1000) * 1000, gia_tri))
            doanh_thu = gia_tri - giam                              # BR-01
            gia_von = float(so_luong * gia_von_map[ma_sp])
            rows.append({
                "ma_dong": f"{ma_don}-{j:02d}",
                "ma_don": ma_don,
                "ngay_dat": ngay[i].date(),
                "ma_kh": khach[i],
                "ma_sp": ma_sp,
                "ma_ch": cua_hang[i],
                "kenh_ban": kenh[i],
                "so_luong": so_luong,
                "don_gia": don_gia,
                "giam_gia": giam,
                "doanh_thu": doanh_thu,
                "gia_von": gia_von,
                "loi_nhuan_gop": doanh_thu - gia_von,               # BR-02
                "trang_thai": trang_thai[i],
                "load_ts": min(pd.Timestamp(ngay[i]) + pd.Timedelta(days=1, hours=2), as_of_ts),
            })
    return pd.DataFrame(rows[:target])


# =============================================================================
# ĐIỀU PHỐI
# =============================================================================

BUILDERS = [                      # đúng thứ tự phụ thuộc: cfg → dim → bridge → fact
    ("dim_khach_hang", build_dim_khach_hang),
    ("dim_san_pham", build_dim_san_pham),
    ("dim_cua_hang", build_dim_cua_hang),
    ("fact_don_hang", build_fact_don_hang),
]


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sinh dữ liệu mockup theo dataset.yaml")
    ap.add_argument("spec", nargs="?", default="dataset.yaml")
    ap.add_argument("-o", "--out", help="Thư mục dữ liệu đầu ra; mặc định ở trạm đang dùng")
    args = ap.parse_args(argv)

    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    sys.path.insert(0, repo_root)
    from powerbi_agent._env import data_dir
    from powerbi_agent.knowledge import ensure_outside_repo

    try:
        out_dir = ensure_outside_repo(args.out or os.path.join(data_dir(), "mockdata"), "dữ liệu mẫu")
    except (RuntimeError, ValueError) as exc:
        ap.error(str(exc))

    spec = mp.load_spec(args.spec)
    unsupported = sorted({table["name"] for table in spec["tables"]} - {name for name, _ in BUILDERS})
    if unsupported:
        ap.error("Generator bán lẻ mẫu chưa hỗ trợ bảng: " + ", ".join(unsupported))
    ds = spec["dataset"]
    cfg = {
        "as_of": str(ds["as_of_date"]),
        "period_start": str(ds.get("period_start", "2025-01-01")),
        "rows": {t["name"]: t.get("rows", 100) for t in spec["tables"]},
    }
    r = mp.rng(ds["seed"])          # nguồn ngẫu nhiên DUY NHẤT
    print(f"Sinh `{ds['id']}` — seed={ds['seed']}, mốc hiện tại={cfg['as_of']}")

    tables = {}
    for name, builder in BUILDERS:
        if not mp.find_table(spec, name):
            print(f"  ! `{name}` không có trong spec — bỏ qua")
            continue
        tables[name] = builder(r, cfg, tables)

    mp.save_frames(tables, out_dir)
    print(f"→ {out_dir}/  (chạy tiếp: mockpack.py verify {args.spec} {out_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
