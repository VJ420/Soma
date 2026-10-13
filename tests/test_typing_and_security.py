import sys
sys.path.insert(0, '.')
from typing_engine.type_system import TypeInferenceEngine
from security.sandbox import SecuritySandboxPolicy, Permission, SecurityViolationException
from lexer import Lexer
from parser import Parser

code = """
x: 42
pi: 3.14159
name: "Fractal"
numbers: [1, 2, 3]
add(a, b): a + b
"""

ast = Parser(Lexer(code).tokenize()).parse()
inferred = TypeInferenceEngine().infer_program(ast)
print("Type Inference Results:")
for name, typ in inferred.items():
    print(f"  {name}: {typ}")

# Test Security Policy
policy = SecuritySandboxPolicy.create_restricted()
policy.check_permission(Permission.CONCURRENCY_SPAWN)
try:
    policy.check_permission(Permission.WRITE_FILE, "/etc/passwd")
    print("Security check failed!")
except SecurityViolationException as e:
    print("Security check succeeded (denied prohibited write):", e)
