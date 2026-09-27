import logging
import os
import sys

# Ghi log ra stderr (KHÔNG dùng stdout — sẽ làm hỏng luồng JSON-RPC của MCP stdio)
logging.basicConfig(
    level=logging.INFO,
    stream=sys.stderr,
    format="%(asctime)s [powerbi-agent] %(levelname)s: %(message)s",
)
log = logging.getLogger("powerbi-agent")

# Số dòng tối đa trả về cho mỗi truy vấn để tránh tràn context / OOM.
# Có thể ghi đè qua biến môi trường POWERBI_MAX_ROWS.
try:
    MAX_ROWS = int(os.getenv("POWERBI_MAX_ROWS", "1000"))
except ValueError:
    MAX_ROWS = 1000


def short_err(err, limit: int = 400) -> str:
    """Chỉ trả loại lỗi; exception có thể mang query, URL hoặc credential."""
    return type(err).__name__ if not isinstance(err, str) else "Chi tiết phản hồi đã ẩn"


def df_to_markdown_capped(df, max_rows: int) -> str:
    """Chuyển DataFrame -> bảng Markdown, cắt bớt nếu vượt quá max_rows."""
    total = len(df)
    if max_rows and total > max_rows:
        note = (
            f"\n\n> ⚠️ Kết quả có {total} dòng, chỉ hiển thị {max_rows} dòng đầu. "
            "Hãy dùng TOPN / bộ lọc để thu hẹp truy vấn."
        )
        return df.head(max_rows).to_markdown(index=False) + note
    return df.to_markdown(index=False)
