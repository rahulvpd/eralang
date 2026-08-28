"""
EraLang Lexical Environment and Scope Management
"""
from typing import Dict, Any, Optional
from .values import EraValue


class EnvironmentError(Exception):
    pass


class Environment:
    def __init__(self, parent: Optional['Environment'] = None):
        self.parent = parent
        self.values: Dict[str, EraValue] = {}
        self.mutable_flags: Dict[str, bool] = {}  # True = var, False = let

    def define(self, name: str, value: EraValue, is_mutable: bool):
        # Warn on same-scope shadowing (do not silently overwrite without intent)
        if name in self.values:
            # Allow shadowing but keep mutable flag update explicit
            pass
        self.values[name] = value
        self.mutable_flags[name] = is_mutable

    def is_defined_in_current_scope(self, name: str) -> bool:
        return name in self.values

    def assign(self, name: str, value: EraValue) -> bool:
        if name in self.values:
            if not self.mutable_flags[name]:
                raise EnvironmentError(
                    f"Cannot reassign to immutable binding '{name}'. Declared with 'let' (use 'var' to allow mutation)."
                )
            self.values[name] = value
            return True

        if self.parent is not None:
            return self.parent.assign(name, value)

        raise EnvironmentError(f"Undefined variable '{name}'")

    def get(self, name: str) -> EraValue:
        if name in self.values:
            return self.values[name]

        if self.parent is not None:
            return self.parent.get(name)

        raise EnvironmentError(f"Undefined variable '{name}'")

    def exists(self, name: str) -> bool:
        if name in self.values:
            return True
        if self.parent is not None:
            return self.parent.exists(name)
        return False
