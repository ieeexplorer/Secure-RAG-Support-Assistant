from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.tools.support_tools import SupportToolService


service = SupportToolService()
mcp = FastMCP("secure-rag-support-tools")


@mcp.tool()
def search_ticket_status(ticket_id: str) -> dict:
    return service.search_ticket_status(ticket_id)


@mcp.tool()
def lookup_error_code(error_code: str) -> dict:
    return service.lookup_error_code(error_code)


@mcp.tool()
def create_followup_note(ticket_id: str, note: str, author: str = "assistant") -> dict:
    return service.create_followup_note(ticket_id=ticket_id, note=note, author=author)


if __name__ == "__main__":
    mcp.run()
