# 🛡️ Security Policy

The EraLang team takes compiler, runtime, and sandboxing security seriously.

---

## Supported Versions

We provide security updates and patches for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

---

## Reporting a Vulnerability

If you discover a security vulnerability (such as a sandbox escape in `era run --sandbox`, buffer overflow in the C transpiler, or arbitrary code execution bug), please **do not report it on public issue trackers**.

Please send an email to:
* **`security@eralang.org`** (or contact the maintainers privately via GitHub Security Advisories)

### What to Include:
1. Type of issue (e.g. sandbox bypass, compiler memory leak, parser DoS).
2. Minimal `.era` code snippet that triggers the vulnerability.
3. Operating system, Python version, and execution backend (`--vm` vs evaluator).
4. Any potential remediation steps you have identified.

We will acknowledge receipt within 48 hours and work with you on a coordinated disclosure timeline.
