# 🌟 EraLang for Visual Studio Code & Cursor

Official language extension for **EraLang** — The AI-Native, Pitfall-Proof Programming Language.

## ✨ Features

* **Syntax Highlighting:** Full TextMate grammar highlighting keywords (`let`, `var`, `fn`, `struct`, `enum`, `match`), types (`int`, `float`, `string`, `bool`, `Option`, `Result`), tensors (`@`), and built-ins.
* **Snippets:** Productivity snippets for structs, enums, exhaustive match statements, and standard library imports.
* **Brackets & Formatting:** Auto-closing pairs, brackets matching, and block folding.

## 📦 Local Installation

1. Package the extension:
   ```bash
   npx @vscode/vsce package
   ```
2. In VS Code or Cursor, press `Ctrl+Shift+P` (or `Cmd+Shift+P`) and choose **Extensions: Install from VSIX...**, then select the generated `.vsix` file.
