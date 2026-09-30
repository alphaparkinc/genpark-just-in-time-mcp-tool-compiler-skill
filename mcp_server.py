"""MCP Server for Just-In-Time MCP Tool Compiler."""
import sys
import json
import time
from client import JustInTimeMCPToolCompiler

compiler = JustInTimeMCPToolCompiler()

def handle_call_tool(params):
    name = params.get("name")
    args = params.get("arguments", {})
    if name != "compile_dynamic_mcp_tool":
        raise ValueError(f"Unknown tool: {name}")

    action = args.get("action", "list_active_jit_tools")
    if action == "synthesize_and_compile_tool":
        return compiler.synthesize_and_compile_tool(
            tool_name=args.get("tool_name", "custom_calc"),
            tool_description=args.get("tool_description", "Custom calculator"),
            python_code=args.get("python_code", "def handle(args): return args"),
            parameters_schema=args.get("parameters_schema")
        )
    elif action == "execute_compiled_tool":
        return compiler.execute_compiled_tool(
            tool_name=args.get("tool_name", ""),
            arguments=args.get("call_arguments", {})
        )
    elif action == "audit_code_safety":
        return compiler.audit_code_safety(
            python_code=args.get("python_code", "")
        )
    elif action == "list_active_jit_tools":
        return compiler.list_active_jit_tools()
    else:
        raise ValueError(f"Invalid action: {action}")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Running self-test...")
        code = "def handle(args):\n    return {'celsius': (args.get('fahrenheit', 32) - 32) * 5 / 9}\n"
        comp = compiler.synthesize_and_compile_tool("f_to_c", "Converts F to C", code)
        assert comp["compiled"] is True
        res = compiler.execute_compiled_tool("f_to_c", {"fahrenheit": 212})
        assert res["success"] is True
        assert res["result"]["celsius"] == 100.0
        print("Self-test PASSED!")
        sys.exit(0)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            msg_id = req.get("id")
            method = req.get("method")
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "serverInfo": {"name": "JustInTimeMCPToolCompiler", "version": "1.0.0"},
                        "capabilities": {"tools": {}}
                    }
                }
            elif method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "tools": [{
                            "name": "compile_dynamic_mcp_tool",
                            "description": "Just-In-Time tool compilation: generate JSON schemas, audit Python code AST for safety violations, compile callable tool instances, and hot-plug new tools into agent mesh.",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string", "enum": ["synthesize_and_compile_tool", "execute_compiled_tool", "audit_code_safety", "list_active_jit_tools"]},
                                    "tool_name": {"type": "string"},
                                    "tool_description": {"type": "string"},
                                    "python_code": {"type": "string"},
                                    "parameters_schema": {"type": "object"},
                                    "call_arguments": {"type": "object"}
                                },
                                "required": ["action"]
                            }
                        }]
                    }
                }
            elif method == "tools/call":
                res = handle_call_tool(req.get("params", {}))
                resp = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
            else:
                resp = {"jsonrpc": "2.0", "id": msg_id, "result": {}}
            print(json.dumps(resp), flush=True)
        except Exception as e:
            err_resp = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(e)}}
            print(json.dumps(err_resp), flush=True)

if __name__ == "__main__":
    main()
