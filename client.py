"""
Autonomous Just-In-Time MCP Tool Synthesizer & Sandboxed Compiler (Zero External Dependencies)
Provides AST safety scanning (blocks os.system, socket, ctypes), dynamic compilation, and hot-plug invocation.
"""
import ast
import time
import math
import hashlib
import json
from typing import Dict, Any, List, Optional, Callable

FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "ctypes", "pty", "shutil"}
FORBIDDEN_CALLS = {"eval", "exec", "open", "__import__", "compile", "breakpoint"}

class JustInTimeMCPToolCompiler:
    def __init__(self):
        self.compiled_tools: Dict[str, Dict[str, Any]] = {}

    def audit_code_safety(self, python_code: str) -> Dict[str, Any]:
        """Performs static AST syntax tree inspection to block unsafe operations."""
        try:
            tree = ast.parse(python_code)
        except SyntaxError as e:
            return {"safe": False, "error": f"SyntaxError: {str(e)}"}

        violations = []
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in FORBIDDEN_IMPORTS:
                        violations.append(f"Forbidden import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module in FORBIDDEN_IMPORTS:
                    violations.append(f"Forbidden from-import: {node.module}")
            # Check dangerous calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    violations.append(f"Forbidden builtin call: {node.func.id}")

        return {
            "safe": len(violations) == 0,
            "violations_count": len(violations),
            "violations": violations
        }

    def synthesize_and_compile_tool(
        self,
        tool_name: str,
        tool_description: str,
        python_code: str,
        parameters_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Audits AST, compiles safe Python handler function, and registers tool in MCP registry.
        """
        audit = self.audit_code_safety(python_code)
        if not audit["safe"]:
            return {
                "compiled": False,
                "error": "Security audit failed",
                "violations": audit["violations"]
            }

        # Build sandboxed namespace with safe standard modules
        safe_globals = {
            "math": math,
            "json": json,
            "time": time,
            "__builtins__": {
                "len": len, "min": min, "max": max, "sum": sum,
                "range": range, "dict": dict, "list": list, "set": set,
                "str": str, "int": int, "float": float, "bool": bool,
                "round": round, "abs": abs
            }
        }
        local_scope = {}

        try:
            compiled_bytecode = compile(python_code, f"<jit_tool_{tool_name}>", "exec")
            # Execute in controlled scope to bind the handler
            exec(compiled_bytecode, safe_globals, local_scope)
        except Exception as e:
            return {"compiled": False, "error": f"CompilationError: {str(e)}"}

        # Find handler function (e.g. handle or run or same as tool_name)
        handler_func = None
        for candidate in ["handle", "run", "execute", tool_name]:
            if candidate in local_scope and callable(local_scope[candidate]):
                handler_func = local_scope[candidate]
                break

        if not handler_func:
            callables = [v for v in local_scope.values() if callable(v)]
            if callables:
                handler_func = callables[0]
            else:
                return {"compiled": False, "error": "No callable handler found in compiled source"}

        schema = parameters_schema or {"type": "object", "properties": {}}
        tool_entry = {
            "name": tool_name,
            "description": tool_description,
            "inputSchema": schema,
            "handler": handler_func,
            "compiled_at": time.time(),
            "sha256": hashlib.sha256(python_code.encode("utf-8")).hexdigest()
        }
        self.compiled_tools[tool_name] = tool_entry

        return {
            "compiled": True,
            "tool_name": tool_name,
            "description": tool_description,
            "inputSchema": schema,
            "sha256": tool_entry["sha256"]
        }

    def execute_compiled_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a previously compiled JIT MCP tool in sandboxed runtime."""
        if tool_name not in self.compiled_tools:
            return {"error": f"Tool '{tool_name}' not found"}

        entry = self.compiled_tools[tool_name]
        handler: Callable = entry["handler"]

        start_time = time.time()
        try:
            output = handler(arguments)
            duration_ms = round((time.time() - start_time) * 1000.0, 2)
            return {
                "success": True,
                "tool_name": tool_name,
                "execution_duration_ms": duration_ms,
                "result": output
            }
        except Exception as e:
            return {
                "success": False,
                "tool_name": tool_name,
                "error": str(e)
            }

    def list_active_jit_tools(self) -> Dict[str, Any]:
        tools_summary = []
        for name, entry in self.compiled_tools.items():
            tools_summary.append({
                "name": name,
                "description": entry["description"],
                "inputSchema": entry["inputSchema"],
                "sha256": entry["sha256"]
            })
        return {"total_jit_tools": len(tools_summary), "tools": tools_summary}
