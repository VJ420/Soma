"""
Fractal High-Performance Bytecode Virtual Machine (FVM).
A stack-based execution machine with native call frames and dynamic scoping.
"""
import math
import time
import json
from typing import Any, Dict, List, Optional
from bytecode import OpCode, Instruction, BytecodeChunk

class VMCellInstance:
    """Represents an instantiated Cell inside the VM."""
    def __init__(self, name: str, members: Dict[str, Any]):
        self.name = name
        self.members = members

    def __repr__(self):
        return f"<Cell '{self.name}': {list(self.members.keys())}>"

class VMCallableCell:
    """Represents a compiled callable Cell / function in the VM."""
    def __init__(
        self,
        name: str,
        chunk: BytecodeChunk,
        param_names: List[str],
        env: Dict[str, Any],
        returns_instance: bool = False,
    ):
        self.name = name
        self.chunk = chunk
        self.param_names = param_names
        self.closure_env = env
        self.returns_instance = returns_instance

    def __repr__(self):
        return f"<CompiledCell '{self.name}({', '.join(self.param_names)})'>"

class CallFrame:
    def __init__(self, chunk: BytecodeChunk, locals_env: Dict[str, Any], caller_cell: Optional[VMCallableCell] = None):
        self.chunk = chunk
        self.ip = 0
        self.locals = locals_env
        self.caller_cell = caller_cell

class FractalVM:
    def __init__(self):
        self.frames: List[CallFrame] = []
        self.stack: List[Any] = []
        self.globals: Dict[str, Any] = {}
        self._init_builtins()

    def _init_builtins(self):
        def _print(*args):
            formatted = [str(a) if not isinstance(a, bool) else ("true" if a else "false") for a in args]
            print(*formatted)
            return args[-1] if args else None

        self.globals["print"] = _print
        self.globals["sqrt"] = math.sqrt
        self.globals["sin"] = math.sin
        self.globals["cos"] = math.cos
        self.globals["abs"] = abs
        self.globals["len"] = len
        self.globals["range"] = lambda *args: list(range(*args))
        self.globals["str"] = str
        self.globals["int"] = int
        self.globals["float"] = float
        self.globals["type"] = lambda x: type(x).__name__
        self.globals["time"] = time.time
        self.globals["perf"] = time.perf_counter
        self.globals["push"] = lambda lst, item: lst.append(item) or lst
        self.globals["json_parse"] = json.loads
        self.globals["json_stringify"] = lambda obj, indent=2: json.dumps(obj, indent=indent)
        self.globals["__get_index"] = lambda collection, idx: collection[idx]

    def push(self, val: Any):
        self.stack.append(val)

    def pop(self) -> Any:
        if not self.stack:
            raise RuntimeError("Stack underflow in Fractal VM")
        return self.stack.pop()

    def peek(self) -> Any:
        return self.stack[-1] if self.stack else None

    def execute(self, root_chunk: BytecodeChunk) -> Any:
        main_frame = CallFrame(root_chunk, self.globals)
        self.frames = [main_frame]

        while self.frames:
            frame = self.frames[-1]
            if frame.ip >= len(frame.chunk.instructions):
                self.frames.pop()
                continue

            inst = frame.chunk.instructions[frame.ip]
            frame.ip += 1
            op = inst.opcode
            arg = inst.arg

            if op == OpCode.LOAD_CONST:
                self.push(frame.chunk.constants[arg])

            elif op == OpCode.LOAD_NAME:
                name = frame.chunk.names[arg]
                self.push(self._load(frame, name))

            elif op == OpCode.STORE_NAME:
                name = frame.chunk.names[arg]
                self._store(frame, name, self.pop())

            elif op == OpCode.POP:
                self.pop()

            elif op == OpCode.DUP:
                self.push(self.peek())

            elif op == OpCode.ADD:
                b = self.pop()
                a = self.pop()
                self.push(a + b)

            elif op == OpCode.SUB:
                b = self.pop()
                a = self.pop()
                self.push(a - b)

            elif op == OpCode.MUL:
                b = self.pop()
                a = self.pop()
                self.push(a * b)

            elif op == OpCode.DIV:
                b = self.pop()
                a = self.pop()
                self.push(a / b)

            elif op == OpCode.MOD:
                b = self.pop()
                a = self.pop()
                self.push(a % b)

            elif op == OpCode.POW:
                b = self.pop()
                a = self.pop()
                self.push(a ** b)

            elif op == OpCode.EQ:
                b = self.pop()
                a = self.pop()
                self.push(a == b)

            elif op == OpCode.NEQ:
                b = self.pop()
                a = self.pop()
                self.push(a != b)

            elif op == OpCode.LT:
                b = self.pop()
                a = self.pop()
                self.push(a < b)

            elif op == OpCode.GT:
                b = self.pop()
                a = self.pop()
                self.push(a > b)

            elif op == OpCode.LTE:
                b = self.pop()
                a = self.pop()
                self.push(a <= b)

            elif op == OpCode.GTE:
                b = self.pop()
                a = self.pop()
                self.push(a >= b)

            elif op == OpCode.NOT:
                val = self.pop()
                self.push(not val)

            elif op == OpCode.JUMP:
                frame.ip = arg

            elif op == OpCode.JUMP_IF_FALSE:
                condition = self.pop()
                if not condition:
                    frame.ip = arg

            elif op == OpCode.JUMP_IF_TRUE:
                condition = self.pop()
                if condition:
                    frame.ip = arg

            elif op == OpCode.BUILD_LIST:
                count = arg
                elements = [self.pop() for _ in range(count)]
                elements.reverse()
                self.push(elements)

            elif op == OpCode.BUILD_MAP:
                count = arg
                d = {}
                for _ in range(count):
                    v = self.pop()
                    k = self.pop()
                    d[k] = v
                self.push(d)

            elif op == OpCode.GET_ATTR:
                attr_name = frame.chunk.names[arg]
                target = self.pop()
                if isinstance(target, VMCellInstance):
                    if attr_name in target.members:
                        self.push(target.members[attr_name])
                    else:
                        raise AttributeError(f"Cell '{target.name}' has no attribute '{attr_name}'")
                elif isinstance(target, dict):
                    self.push(target[attr_name])
                elif hasattr(target, attr_name):
                    self.push(getattr(target, attr_name))
                else:
                    raise AttributeError(f"Object {target} has no attribute '{attr_name}'")

            elif op == OpCode.GET_INDEX:
                index = self.pop()
                target = self.pop()
                self.push(target[index])

            elif op == OpCode.SET_INDEX:
                value = self.pop()
                index = self.pop()
                target = self.pop()
                target[index] = value
                self.push(value)

            elif op == OpCode.SET_ATTR:
                attr_name = frame.chunk.names[arg]
                val = self.pop()
                target = self.pop()
                if isinstance(target, VMCellInstance):
                    target.members[attr_name] = val
                elif isinstance(target, dict):
                    target[attr_name] = val
                else:
                    setattr(target, attr_name, val)
                self.push(val)

            elif op == OpCode.MAKE_CELL:
                cell_meta = frame.chunk.constants[arg]
                name = cell_meta["name"]
                cell_chunk = cell_meta["chunk"]
                params = cell_meta["params"]
                if params is not None:
                    callable_obj = VMCallableCell(
                        name,
                        cell_chunk,
                        params,
                        frame.locals,
                        bool(cell_meta.get("returns_instance")),
                    )
                    self.push(callable_obj)
                else:
                    # Module / Namespace cell
                    cell_locals = dict(frame.locals)
                    child_frame = CallFrame(cell_chunk, cell_locals)
                    self.frames.append(child_frame)

            elif op == OpCode.CALL_CELL:
                arg_count = arg
                args = [self.pop() for _ in range(arg_count)]
                args.reverse()
                callee = self.pop()

                if isinstance(callee, VMCallableCell):
                    call_locals = {}
                    for p_name, val in zip(callee.param_names, args):
                        call_locals[p_name] = val
                    new_frame = CallFrame(callee.chunk, call_locals, callee)
                    self.frames.append(new_frame)
                elif callable(callee):
                    res = callee(*args)
                    self.push(res)
                else:
                    raise TypeError(f"'{callee}' is not callable")

            elif op == OpCode.RETURN:
                ret_val = self.pop() if self.stack else None
                popped_frame = self.frames.pop()
                cell = popped_frame.caller_cell
                if cell is not None and cell.returns_instance:
                    self.push(VMCellInstance(cell.name, popped_frame.locals))
                else:
                    self.push(ret_val)

            elif op == OpCode.HALT:
                break

        return self.pop() if self.stack else None

    def _load(self, frame: CallFrame, name: str) -> Any:
        if name in frame.locals:
            return frame.locals[name]
        cell = frame.caller_cell
        if cell is not None and name in cell.closure_env:
            return cell.closure_env[name]
        if name in self.globals:
            return self.globals[name]
        raise NameError(f"Undefined variable '{name}' in VM scope")

    def _store(self, frame: CallFrame, name: str, value: Any) -> None:
        cell = frame.caller_cell
        if name in frame.locals:
            frame.locals[name] = value
        elif cell is not None and name in cell.closure_env:
            cell.closure_env[name] = value
        else:
            frame.locals[name] = value

    def _is_primitive(self, val: Any) -> bool:
        return isinstance(val, (int, float, str, bool, list, dict, type(None)))
