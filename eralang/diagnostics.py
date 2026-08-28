"""
EraLang Mentor Diagnostics Engine
Provides clear error diagnostics, source code highlights, and auto-fix suggestions.
"""
from typing import Optional, Dict, Any
from .token import SourceLocation


class DiagnosticError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        location: SourceLocation,
        source_code: Optional[str] = None,
        suggestion: Optional[str] = None,
        autofix_patch: Optional[str] = None
    ):
        self.code = code
        self.message = message
        self.location = location
        self.source_code = source_code
        self.suggestion = suggestion
        self.autofix_patch = autofix_patch
        super().__init__(self.format_diagnostic())

    def format_diagnostic(self) -> str:
        lines = [
            f"\033[91m[EraLang Error {self.code}]\033[0m: Line {self.location.line}, Column {self.location.column} in {self.location.filename}",
            f"  \033[1m{self.message}\033[0m"
        ]

        if self.source_code:
            src_lines = self.source_code.splitlines()
            if 1 <= self.location.line <= len(src_lines):
                target_line = src_lines[self.location.line - 1]
                line_prefix = f"  {self.location.line} | "
                lines.append(f"{line_prefix}{target_line}")
                caret_indent = " " * (len(line_prefix) + max(0, self.location.column - 1))
                lines.append(f"{caret_indent}\033[91m^\033[0m")

        if self.suggestion:
            lines.append(f"\n  \033[96m💡 Mentor Suggestion:\033[0m {self.suggestion}")

        if self.autofix_patch:
            lines.append(f"  \033[92m👉 Auto-Fix Patch:\033[0m\n{self.autofix_patch}")

        return "\n".join(lines)

    def to_json(self) -> Dict[str, Any]:
        return {
            "error_code": self.code,
            "message": self.message,
            "filename": self.location.filename,
            "line": self.location.line,
            "column": self.location.column,
            "suggestion": self.suggestion,
            "autofix_patch": self.autofix_patch
        }
