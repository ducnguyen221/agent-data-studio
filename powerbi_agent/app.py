"""Khởi tạo MCP server: nạp ADOMD → tạo FastMCP → đăng ký tool.

THỨ TỰ QUAN TRỌNG: load_adomd() phải chạy TRƯỚC import pyadomd (tools_query),
vì pyadomd resolve assembly AdomdClient ngay lúc import.
"""

from dotenv import load_dotenv
from powerbi_agent._env import env_file

load_dotenv(env_file())  # config.env không chứa credential; file secret chỉ nạp ở tool Service

from powerbi_agent.adomd import load_adomd, load_tabular
from powerbi_agent.util import log  # noqa: F401 — khởi tạo logging stderr sớm

ADOMD_LOADED = load_adomd()
TABULAR_LOADED = load_tabular()

from mcp.server.fastmcp import FastMCP

# Khởi tạo MCP Server với tên gọi định danh (giữ nguyên tên từ v0 — host đã đăng ký)
mcp = FastMCP("PowerBI-Bridge-Server")

from powerbi_agent import (  # sau load_adomd()
    tools_design,
    tools_distill,
    tools_knowledge,
    tools_query,
    tools_template,
    tools_tom,
)

tools_query.register(mcp, ADOMD_LOADED)
tools_tom.register(mcp, TABULAR_LOADED)
tools_distill.register(mcp, ADOMD_LOADED)
tools_template.register(mcp)
tools_design.register(mcp)
tools_knowledge.register(mcp)


def main():
    """Chạy server qua stdio."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
