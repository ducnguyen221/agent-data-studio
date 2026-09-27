"""CLI đọc Power BI Desktop qua cùng policy và giới hạn của MCP."""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from powerbi_agent import app  # noqa: F401 - nạp config trước ADOMD
from powerbi_agent import policy
from powerbi_agent.adomd import adomd_missing_message, import_pyadomd
from powerbi_agent.connection import local_connection_string
from powerbi_agent.discovery import find_active_pbi_ports
from powerbi_agent.tools_query import _query_df
from powerbi_agent.util import MAX_ROWS


def _print(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, default=str))


def _list_models() -> list[dict]:
    # Gate TRƯỚC import pyadomd (như tools_query): thiếu DLL thì pyadomd in banner ra stdout
    # rồi hỏng muộn bằng NameError; stdout của CLI phải chỉ là JSON.
    if not app.ADOMD_LOADED:
        raise RuntimeError(adomd_missing_message())
    try:
        Pyadomd = import_pyadomd()
    except (ImportError, OSError) as exc:
        raise RuntimeError("Chưa có ADOMD.NET/pyadomd; cài driver rồi chạy lại lệnh list.") from exc

    models = []
    for instance in find_active_pbi_ports():
        port = str(instance["port"])
        try:
            with Pyadomd(local_connection_string(port)) as conn:
                with conn.cursor().execute("SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS") as cursor:
                    for row in cursor.fetchall():
                        models.append({"port": port, "model_id": str(row[0])})
        except Exception:
            print(f"Không đọc được model ở cổng {port}; kiểm tra Power BI Desktop/ADOMD.NET.", file=sys.stderr)
    return models


def _rows(port: str, model_id: str, query: str, tool: str, max_rows: int) -> dict:
    try:
        local_connection_string(port, model_id)
    except ValueError:
        return {"status": "error", "message": "Cần chọn cổng và model cụ thể từ lệnh list."}
    # Gate như _list_models: thiếu ADOMD thì báo rõ lý do, không đi tiếp tới truy vấn/pyadomd.
    if not app.ADOMD_LOADED:
        return {"status": "error", "message": adomd_missing_message()}
    allowed, reason = policy.check_dax(query, tool=tool)
    if not allowed:
        return {"status": "blocked", "message": reason}
    try:
        df = _query_df(port, model_id, query)
        cap = policy.cap_dimension_rows(df, min(max_rows, MAX_ROWS))
        rows = df.head(cap).to_dict(orient="records")
        policy.audit(tool, query, "allowed", len(rows))
        return {"status": "success", "data": rows, "truncated": len(df) > len(rows)}
    except Exception:
        policy.audit(tool, query, "error")
        print("Truy vấn Power BI Desktop thất bại; kiểm tra report/model đã chọn và driver.", file=sys.stderr)
        return {"status": "error", "message": "Không truy vấn được model đã chọn; kiểm tra Power BI Desktop và quyền truy cập."}


def main() -> int:
    parser = argparse.ArgumentParser(description="Truy vấn Power BI Desktop với policy chung của Agent Data Studio.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="Liệt kê cổng Power BI Desktop đang mở.")
    for name in ("query", "tables"):
        cmd = sub.add_parser(name)
        cmd.add_argument("port")
        cmd.add_argument("model_id")
        if name == "query":
            cmd.add_argument("dax")
        cmd.add_argument("--max-rows", type=int, default=MAX_ROWS)
    args = parser.parse_args()
    if args.command == "list":
        try:
            _print({"status": "success", "data": _list_models()})
            return 0
        except RuntimeError as exc:
            _print({"status": "error", "message": str(exc)})
            return 2
    if args.max_rows < 1:
        _print({"status": "error", "message": "--max-rows phải lớn hơn 0."})
        return 2
    query = args.dax if args.command == "query" else "SELECT [Name] FROM $SYSTEM.TMSCHEMA_TABLES"
    result = _rows(args.port, args.model_id, query, args.command, args.max_rows)
    _print(result)
    return 0 if result["status"] == "success" else 2


if __name__ == "__main__":
    raise SystemExit(main())
