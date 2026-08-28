"""
EraLang Runtime Values and Object Model
"""
from dataclasses import dataclass
from typing import Any, List, Dict, Optional, Callable
import math
import random
import queue
import threading


class EraValue:
    def type_name(self) -> str:
        return "value"

    def to_string(self) -> str:
        return str(self)

    def is_truthy(self) -> bool:
        return True


@dataclass
class EraInt(EraValue):
    value: int

    def type_name(self) -> str:
        return "int"

    def to_string(self) -> str:
        return str(self.value)

    def is_truthy(self) -> bool:
        return self.value != 0

    def __repr__(self) -> str:
        return f"{self.value}"


@dataclass
class EraFloat(EraValue):
    value: float

    def type_name(self) -> str:
        return "float"

    def to_string(self) -> str:
        return str(self.value)

    def is_truthy(self) -> bool:
        return self.value != 0.0

    def __repr__(self) -> str:
        return f"{self.value}"


@dataclass
class EraString(EraValue):
    value: str

    def type_name(self) -> str:
        return "string"

    def to_string(self) -> str:
        return self.value

    def is_truthy(self) -> bool:
        return len(self.value) > 0

    def __repr__(self) -> str:
        return f'"{self.value}"'


@dataclass
class EraBool(EraValue):
    value: bool

    def type_name(self) -> str:
        return "bool"

    def to_string(self) -> str:
        return "true" if self.value else "false"

    def is_truthy(self) -> bool:
        return self.value

    def __repr__(self) -> str:
        return "true" if self.value else "false"


@dataclass
class EraOption(EraValue):
    is_some: bool
    val: Optional[EraValue] = None

    @classmethod
    def some(cls, val: EraValue) -> 'EraOption':
        return cls(is_some=True, val=val)

    @classmethod
    def none(cls) -> 'EraOption':
        return cls(is_some=False, val=None)

    def type_name(self) -> str:
        if self.is_some:
            return f"Option<{self.val.type_name()}>"
        return "Option"

    def to_string(self) -> str:
        if self.is_some:
            return f"Some({self.val.to_string()})"
        return "None"

    def is_truthy(self) -> bool:
        return self.is_some

    def unwrap_or(self, default_val: EraValue) -> EraValue:
        if self.is_some and self.val is not None:
            return self.val
        return default_val

    def __repr__(self) -> str:
        return self.to_string()


@dataclass
class EraResult(EraValue):
    is_ok: bool
    val: Optional[EraValue] = None
    err: Optional[EraValue] = None

    @classmethod
    def ok(cls, val: EraValue) -> 'EraResult':
        return cls(is_ok=True, val=val, err=None)

    @classmethod
    def err(cls, err: EraValue) -> 'EraResult':
        return cls(is_ok=False, val=None, err=err)

    def type_name(self) -> str:
        if self.is_ok:
            return f"Result<{self.val.type_name()}, _>"
        return f"Result<_, {self.err.type_name()}>"

    def to_string(self) -> str:
        if self.is_ok:
            return f"Ok({self.val.to_string()})"
        return f"Err({self.err.to_string()})"

    def is_truthy(self) -> bool:
        return self.is_ok

    def unwrap_or(self, default_val: EraValue) -> EraValue:
        if self.is_ok and self.val is not None:
            return self.val
        return default_val

    def __repr__(self) -> str:
        return self.to_string()


class EraArray(EraValue):
    def __init__(self, elements: List[EraValue]):
        self.elements = elements

    def type_name(self) -> str:
        return "Array"

    def to_string(self) -> str:
        inner = ", ".join(e.to_string() for e in self.elements)
        return f"[{inner}]"

    def is_truthy(self) -> bool:
        return len(self.elements) > 0

    def get(self, index: int) -> EraOption:
        if 0 <= index < len(self.elements):
            return EraOption.some(self.elements[index])
        return EraOption.none()

    def push(self, val: EraValue):
        self.elements.append(val)

    def pop(self) -> EraOption:
        if self.elements:
            return EraOption.some(self.elements.pop())
        return EraOption.none()

    def __repr__(self) -> str:
        return self.to_string()


class EraMap(EraValue):
    def __init__(self, entries: Dict[str, EraValue]):
        self.entries = entries

    def type_name(self) -> str:
        return "Map"

    def to_string(self) -> str:
        pairs = [f'"{k}": {v.to_string()}' for k, v in self.entries.items()]
        return "{" + ", ".join(pairs) + "}"

    def get(self, key: str) -> EraOption:
        if key in self.entries:
            return EraOption.some(self.entries[key])
        return EraOption.none()

    def set(self, key: str, val: EraValue):
        self.entries[key] = val

    def __repr__(self) -> str:
        return self.to_string()


class EraTensor(EraValue):
    """
    Native Multi-Dimensional Tensor supporting Matrix Multiplication,
    Transposition, Reduction, and Element-wise Operations.
    """
    def __init__(self, data: List[Any], shape: List[int], dtype: str = "float32"):
        self.data = data
        self.shape = shape
        self.dtype = dtype

    def type_name(self) -> str:
        shape_str = ", ".join(str(s) for s in self.shape)
        return f"Tensor<{self.dtype}, [{shape_str}]>"

    @classmethod
    def zeros(cls, shape: List[int], dtype: str = "float32") -> 'EraTensor':
        def _build_zeros(dims):
            if len(dims) == 1:
                return [0.0] * dims[0]
            return [_build_zeros(dims[1:]) for _ in range(dims[0])]
        return cls(data=_build_zeros(shape), shape=shape, dtype=dtype)

    @classmethod
    def ones(cls, shape: List[int], dtype: str = "float32") -> 'EraTensor':
        def _build_ones(dims):
            if len(dims) == 1:
                return [1.0] * dims[0]
            return [_build_ones(dims[1:]) for _ in range(dims[0])]
        return cls(data=_build_ones(shape), shape=shape, dtype=dtype)

    @classmethod
    def randn(cls, shape: List[int], dtype: str = "float32") -> 'EraTensor':
        def _build_randn(dims):
            if len(dims) == 1:
                return [random.gauss(0, 1) for _ in range(dims[0])]
            return [_build_randn(dims[1:]) for _ in range(dims[0])]
        return cls(data=_build_randn(shape), shape=shape, dtype=dtype)

    @classmethod
    def from_array(cls, array: EraArray) -> 'EraTensor':
        raw_data = []
        for elem in array.elements:
            if isinstance(elem, (EraInt, EraFloat)):
                raw_data.append(float(elem.value))
            elif isinstance(elem, EraArray):
                nested = [float(x.value) for x in elem.elements if isinstance(x, (EraInt, EraFloat))]
                raw_data.append(nested)
        
        # Calculate shape
        if raw_data and isinstance(raw_data[0], list):
            shape = [len(raw_data), len(raw_data[0])]
        else:
            shape = [len(raw_data)]
        return cls(data=raw_data, shape=shape)

    def matmul(self, other: 'EraTensor') -> 'EraTensor':
        # 2D Matrix Multiplication (numpy-accelerated when available, pure-python fallback)
        if len(self.shape) != 2 or len(other.shape) != 2:
            raise RuntimeError(f"Matmul (@) requires 2D tensors, got {self.shape} and {other.shape}")
        
        M, K1 = self.shape
        K2, N = other.shape
        if K1 != K2:
            raise RuntimeError(f"Dimension mismatch in Tensor matmul: [{M}, {K1}] @ [{K2}, {N}] (K dimensions {K1} != {K2})")

        # Try numpy for 10-50x speedup on large matrices
        try:
            import numpy as np
            a = np.array(self.data, dtype=float)
            b = np.array(other.data, dtype=float)
            res = a @ b
            res_data = res.tolist()
            return EraTensor(data=res_data, shape=[M, N], dtype=self.dtype)
        except ImportError:
            pass
        except Exception:
            pass

        res_data = [[0.0 for _ in range(N)] for _ in range(M)]
        for i in range(M):
            for j in range(N):
                s = 0.0
                for k in range(K1):
                    s += self.data[i][k] * other.data[k][j]
                res_data[i][j] = s

        return EraTensor(data=res_data, shape=[M, N], dtype=self.dtype)

    def sum(self) -> float:
        def _recursive_sum(d):
            if isinstance(d, list):
                return sum(_recursive_sum(x) for x in d)
            return float(d)
        return _recursive_sum(self.data)

    def mean(self) -> float:
        total_elements = 1
        for s in self.shape:
            total_elements *= s
        return self.sum() / max(1, total_elements)

    def transpose(self) -> 'EraTensor':
        if len(self.shape) != 2:
            raise RuntimeError(f"Transpose currently supports 2D tensors, got shape {self.shape}")
        M, N = self.shape
        res = [[self.data[r][c] for r in range(M)] for c in range(N)]
        return EraTensor(data=res, shape=[N, M], dtype=self.dtype)

    def to_string(self) -> str:
        shape_str = "x".join(str(s) for s in self.shape)
        return f"Tensor({shape_str}, {self.data})"

    def __repr__(self) -> str:
        return self.to_string()


class EraFunction(EraValue):
    def __init__(self, name: str, params: List[Any], body: Any, closure: Any, capabilities: List[str] = None):
        self.name = name
        self.params = params
        self.body = body
        self.closure = closure
        self.capabilities = capabilities or []

    def type_name(self) -> str:
        return f"fn({len(self.params)} params)"

    def to_string(self) -> str:
        return f"<fn {self.name}>"

    def __repr__(self) -> str:
        return self.to_string()


class EraBuiltinFunction(EraValue):
    def __init__(self, name: str, func: Callable):
        self.name = name
        self.func = func

    def type_name(self) -> str:
        return "builtin_fn"

    def to_string(self) -> str:
        return f"<builtin_fn {self.name}>"

    def __repr__(self) -> str:
        return self.to_string()


class EraChannel(EraValue):
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.queue = queue.Queue(maxsize=capacity)

    def type_name(self) -> str:
        return "Chan"

    def send(self, val: EraValue):
        self.queue.put(val)

    def recv(self) -> EraOption:
        try:
            val = self.queue.get(timeout=2.0)
            return EraOption.some(val)
        except queue.Empty:
            return EraOption.none()

    def try_recv(self) -> EraOption:
        """Non-blocking receive - returns None immediately if empty (avoids hidden deadlock)."""
        try:
            val = self.queue.get_nowait()
            return EraOption.some(val)
        except queue.Empty:
            return EraOption.none()

    def is_empty(self) -> bool:
        return self.queue.empty()

    def size(self) -> int:
        return self.queue.qsize()

    def to_string(self) -> str:
        return f"<Chan cap={self.capacity} size={self.queue.qsize()}>"

    def __repr__(self) -> str:
        return self.to_string()


class EraActor(EraValue):
    def __init__(self, name: str, env: Any):
        self.name = name
        self.env = env
        self.lock = threading.Lock()

    def type_name(self) -> str:
        return f"Actor<{self.name}>"

    def to_string(self) -> str:
        return f"<actor {self.name}>"

    def __repr__(self) -> str:
        return self.to_string()


class EraForeignObject(EraValue):
    """
    Wraps Python modules and objects for seamless polyglot interoperability.
    """
    def __init__(self, py_obj: Any):
        self.py_obj = py_obj

    def type_name(self) -> str:
        return f"PythonObject<{type(self.py_obj).__name__}>"

    def to_string(self) -> str:
        return str(self.py_obj)

    def __repr__(self) -> str:
        return f"Python({self.py_obj})"


class EraStructDef(EraValue):
    def __init__(self, name: str, fields: List[Any], methods: Dict[str, Any]):
        self.name = name
        self.fields = fields      # List of field names or StructField AST
        self.methods = methods    # Dict[str, EraFunction]

    def type_name(self) -> str:
        return f"struct {self.name}"

    def to_string(self) -> str:
        return f"<struct {self.name}>"

    def __repr__(self) -> str:
        return self.to_string()


class EraStructInstance(EraValue):
    def __init__(self, struct_def: EraStructDef, fields: Dict[str, EraValue]):
        self.struct_def = struct_def
        self.fields = fields

    def type_name(self) -> str:
        return self.struct_def.name

    def get(self, name: str) -> Optional[EraValue]:
        if name in self.fields:
            return self.fields[name]
        if name in self.struct_def.methods:
            return self.struct_def.methods[name]
        return None

    def set(self, name: str, val: EraValue):
        self.fields[name] = val

    def to_string(self) -> str:
        f_str = ", ".join(f"{k}: {v.to_string()}" for k, v in self.fields.items())
        return f"{self.struct_def.name}({f_str})"

    def __repr__(self) -> str:
        return self.to_string()


class EraEnumDef(EraValue):
    def __init__(self, name: str, variants: List[str]):
        self.name = name
        self.variants = variants

    def get_variant(self, variant_name: str, inner: Optional[EraValue] = None) -> 'EraEnumValue':
        if variant_name not in self.variants:
            raise AttributeError(f"Enum '{self.name}' has no variant '{variant_name}'")
        return EraEnumValue(enum_name=self.name, variant=variant_name, inner=inner)

    def type_name(self) -> str:
        return f"enum {self.name}"

    def to_string(self) -> str:
        return f"<enum {self.name}>"

    def __repr__(self) -> str:
        return self.to_string()


class EraEnumValue(EraValue):
    def __init__(self, enum_name: str, variant: str, inner: Optional[EraValue] = None):
        self.enum_name = enum_name
        self.variant = variant
        self.inner = inner

    def type_name(self) -> str:
        return self.enum_name

    def to_string(self) -> str:
        if self.inner:
            return f"{self.enum_name}.{self.variant}({self.inner.to_string()})"
        return f"{self.enum_name}.{self.variant}"

    def __repr__(self) -> str:
        return self.to_string()
