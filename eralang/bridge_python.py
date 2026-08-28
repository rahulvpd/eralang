"""
EraLang Python Ecosystem Polyglot Bridge
Allows seamless zero-boilerplate importing and calling of any Python package.
"""
import importlib
from typing import Any
from .values import (
    EraValue, EraInt, EraFloat, EraString, EraBool,
    EraArray, EraMap, EraOption, EraResult, EraForeignObject, EraBuiltinFunction
)


def to_era_value(val: Any) -> EraValue:
    """Converts a native Python value into an EraLang EraValue."""
    if val is None:
        return EraOption.none()
    if isinstance(val, bool):
        return EraBool(val)
    if isinstance(val, int):
        return EraInt(val)
    if isinstance(val, float):
        return EraFloat(val)
    if isinstance(val, str):
        return EraString(val)
    if isinstance(val, list):
        return EraArray([to_era_value(x) for x in val])
    if isinstance(val, dict):
        return EraMap({str(k): to_era_value(v) for k, v in val.items()})
    return EraForeignObject(val)


def to_py_value(val: EraValue) -> Any:
    """Converts an EraLang EraValue into a native Python value."""
    if isinstance(val, EraInt):
        return val.value
    if isinstance(val, EraFloat):
        return val.value
    if isinstance(val, EraString):
        return val.value
    if isinstance(val, EraBool):
        return val.value
    if isinstance(val, EraArray):
        return [to_py_value(x) for x in val.elements]
    if isinstance(val, EraMap):
        return {k: to_py_value(v) for k, v in val.entries.items()}
    if isinstance(val, EraOption):
        return to_py_value(val.val) if val.is_some else None
    if isinstance(val, EraResult):
        # Do not leak Exception objects into Python args; unwrap Ok or return None for Err
        # Callers expecting Result should handle EraResult directly; for py bridge we pass the ok value or None
        return to_py_value(val.val) if val.is_ok else None
    if isinstance(val, EraForeignObject):
        return val.py_obj
    # Fallback for Tensor/Channel/Actor etc - pass through as string or native
    if hasattr(val, 'to_string'):
        try:
            return val.to_string()
        except Exception:
            return val
    return val


class PythonBridgeModule(EraValue):
    """Represents an imported Python module inside EraLang."""
    def __init__(self, module_name: str, module_obj: Any):
        self.module_name = module_name
        self.module_obj = module_obj

    def get_attr(self, name: str) -> EraValue:
        if not hasattr(self.module_obj, name):
            raise AttributeError(f"Python module '{self.module_name}' has no attribute or function '{name}'")
        
        attr = getattr(self.module_obj, name)
        if callable(attr):
            def _caller(*args):
                py_args = [to_py_value(a) for a in args]
                try:
                    result = attr(*py_args)
                    return to_era_value(result)
                except Exception as e:
                    return EraResult.err(EraString(f"Python Exception in {self.module_name}.{name}: {str(e)}"))
            return EraBuiltinFunction(name=f"{self.module_name}.{name}", func=_caller)
        else:
            return to_era_value(attr)

    def type_name(self) -> str:
        return f"PythonModule<{self.module_name}>"

    def to_string(self) -> str:
        return f"<PythonModule {self.module_name}>"

    def __repr__(self) -> str:
        return self.to_string()


def load_python_module(module_path: str) -> PythonBridgeModule:
    """Dynamically loads a Python module by name and wraps it for EraLang."""
    try:
        mod = importlib.import_module(module_path)
        return PythonBridgeModule(module_name=module_path, module_obj=mod)
    except ImportError as e:
        raise ImportError(f"Could not import Python package '{module_path}': {str(e)}")
