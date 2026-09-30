"""Example usage for JustInTimeMCPToolCompiler."""
import json
from client import JustInTimeMCPToolCompiler

def main():
    print("=== Just-In-Time MCP Tool Synthesizer & Compiler Demo (Manus Generalist Sandbox) ===")
    compiler = JustInTimeMCPToolCompiler()

    # 1. Compile custom Black-Scholes financial formula tool on the fly
    bs_code = """
def handle(args):
    s = args.get('spot', 100.0)
    k = args.get('strike', 100.0)
    intrinsic_call = max(0.0, s - k)
    intrinsic_put = max(0.0, k - s)
    return {
        'spot': s,
        'strike': k,
        'intrinsic_call': intrinsic_call,
        'intrinsic_put': intrinsic_put
    }
"""
    print("\n--- 1. Compiling On-the-Fly MCP Financial Tool ---")
    comp = compiler.synthesize_and_compile_tool(
        tool_name="option_intrinsic_evaluator",
        tool_description="Evaluates call and put intrinsic option value",
        python_code=bs_code
    )
    print("Compilation Result:", json.dumps(comp, indent=2))

    # 2. Invoke the compiled tool instantly
    print("\n--- 2. Invoking JIT Compiled MCP Tool ---")
    res = compiler.execute_compiled_tool("option_intrinsic_evaluator", {"spot": 142.50, "strike": 130.0})
    print(json.dumps(res, indent=2))

    # 3. Security audit rejects forbidden OS syscalls
    print("\n--- 3. Testing Sandbox AST Rejection of Unsafe Code ---")
    malicious_code = "import os\nos.system('rm -rf /')"
    audit = compiler.audit_code_safety(malicious_code)
    print(f"Malicious Code Safe: {audit['safe']} (Violations: {audit['violations']})")

if __name__ == "__main__":
    main()
