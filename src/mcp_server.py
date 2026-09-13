"""
Mock MCP server module.

The class name MCPAcademicServer is kept for compatibility with the original
starter lab, while the default server now exposes personal schedule tools too.
"""

import json
import sys
from typing import Any, Dict, List

from tools import TOOLS_SCHEMA, dispatch_tool_call

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


class MCPAcademicServer:
    """A small MCP-like server wrapper around local mock tools."""

    def __init__(self, server_name: str = "personal-schedule-mock-mcp-server"):
        self.server_name = server_name
        self.version = "2026.1.0"

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return tool schemas exposed through the mock MCP server."""
        return TOOLS_SCHEMA

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call and wrap the result in a JSON-RPC-like response."""
        if tool_name not in [tool["name"] for tool in TOOLS_SCHEMA]:
            return {
                "jsonrpc": "2.0",
                "server": self.server_name,
                "tool": tool_name,
                "result": {
                    "status": "UNKNOWN_TOOL",
                    "message": f"Tool '{tool_name}' không tồn tại trong MCP Server.",
                },
            }

        result = dispatch_tool_call(tool_name, arguments)
        content = json.loads(result)
        return {
            "jsonrpc": "2.0",
            "server": self.server_name,
            "tool": tool_name,
            "result": content,
        }


if __name__ == "__main__":
    print("==========================================================")
    print("🔌 KIỂM THỬ ĐỘC LẬP MCP SERVER")
    print("==========================================================")

    server = MCPAcademicServer()
    tools = server.list_tools()
    print(f"✅ Khởi tạo thành công MCP Server: {server.server_name} (Version: {server.version})")
    print(f"📦 Số lượng Tools công bố: {len(tools)}")

    sched_tool = next((tool for tool in tools if tool.get("name") == "schedule_fetch"), None)
    if sched_tool and sched_tool.get("parameters", {}).get("properties"):
        print("✅ Tool lịch cá nhân 'schedule_fetch' đã có schema đầy đủ.")
    else:
        print("⏳ Tool lịch cá nhân 'schedule_fetch' chưa có schema đầy đủ.")

    test_result = server.call_tool(
        "schedule_fetch",
        {
            "start_datetime": "2026-09-19T18:00:00+07:00",
            "end_datetime": "2026-09-19T22:00:00+07:00",
        },
    )
    print("✅ Test dispatch tool 'schedule_fetch':")
    print(f"   Phản hồi JSON-RPC: {json.dumps(test_result, ensure_ascii=False)}")
