"""
EraLang Builtin Standard Library
Provides pure, safe, and first-class modules for:
- math
- fs
- json
- time
- crypto
- http
- os
- linalg (Scientific Linear Algebra)
- signal (Digital Signal Processing & Fourier Analysis)
- physics (Universal Physical Constants & Mechanics)
"""
import os
import sys
import math
import json
import time
import hashlib
import hmac
import secrets
import urllib.request
import urllib.error
from typing import Dict, Any, List
from .values import (
    EraValue, EraInt, EraFloat, EraString, EraBool, EraArray, EraMap,
    EraOption, EraResult, EraBuiltinFunction, EraTensor
)


class EraStdLibModule(EraValue):
    """Represents a builtin EraLang standard library module."""
    def __init__(self, name: str, exports: Dict[str, EraValue]):
        self.name = name
        self.exports = exports

    def type_name(self) -> str:
        return f"Module<{self.name}>"

    def to_string(self) -> str:
        return f"<module '{self.name}'>"

    def get_attr(self, name: str) -> EraValue:
        if name in self.exports:
            return self.exports[name]
        raise AttributeError(f"Module '{self.name}' has no attribute or function '{name}'")

    def __repr__(self) -> str:
        return self.to_string()


def _py_to_era(val: Any) -> EraValue:
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
        return EraArray([_py_to_era(x) for x in val])
    if isinstance(val, dict):
        return EraMap({str(k): _py_to_era(v) for k, v in val.items()})
    return EraString(str(val))


def _era_to_py(val: EraValue) -> Any:
    if isinstance(val, EraInt):
        return val.value
    if isinstance(val, EraFloat):
        return val.value
    if isinstance(val, EraString):
        return val.value
    if isinstance(val, EraBool):
        return val.value
    if isinstance(val, EraArray):
        return [_era_to_py(x) for x in val.elements]
    if isinstance(val, EraMap):
        return {k: _era_to_py(v) for k, v in val.entries.items()}
    if isinstance(val, EraOption):
        return _era_to_py(val.val) if val.is_some else None
    if isinstance(val, EraResult):
        return _era_to_py(val.val) if val.is_ok else None
    if isinstance(val, EraTensor):
        return val.data
    return str(val)


# ==============================================================================
# Math Module
# ==============================================================================
def create_math_module() -> EraStdLibModule:
    exports: Dict[str, EraValue] = {
        "PI": EraFloat(math.pi),
        "E": EraFloat(math.e),
        "sqrt": EraBuiltinFunction("math.sqrt", lambda x: EraFloat(math.sqrt(x.value if isinstance(x, (EraInt, EraFloat)) else float(x.to_string())))),
        "pow": EraBuiltinFunction("math.pow", lambda x, y: EraFloat(math.pow(
            x.value if isinstance(x, (EraInt, EraFloat)) else float(x.to_string()),
            y.value if isinstance(y, (EraInt, EraFloat)) else float(y.to_string())
        ))),
        "abs": EraBuiltinFunction("math.abs", lambda x: EraFloat(abs(x.value)) if isinstance(x, (EraInt, EraFloat)) else EraFloat(0.0)),
        "floor": EraBuiltinFunction("math.floor", lambda x: EraInt(math.floor(x.value if isinstance(x, (EraInt, EraFloat)) else 0))),
        "ceil": EraBuiltinFunction("math.ceil", lambda x: EraInt(math.ceil(x.value if isinstance(x, (EraInt, EraFloat)) else 0))),
        "round": EraBuiltinFunction("math.round", lambda x: EraInt(round(x.value if isinstance(x, (EraInt, EraFloat)) else 0))),
        "sin": EraBuiltinFunction("math.sin", lambda x: EraFloat(math.sin(x.value if isinstance(x, (EraInt, EraFloat)) else 0.0))),
        "cos": EraBuiltinFunction("math.cos", lambda x: EraFloat(math.cos(x.value if isinstance(x, (EraInt, EraFloat)) else 0.0))),
        "tan": EraBuiltinFunction("math.tan", lambda x: EraFloat(math.tan(x.value if isinstance(x, (EraInt, EraFloat)) else 0.0))),
        "log": EraBuiltinFunction("math.log", lambda x: EraFloat(math.log(x.value if isinstance(x, (EraInt, EraFloat)) else 1.0))),
        "exp": EraBuiltinFunction("math.exp", lambda x: EraFloat(math.exp(x.value if isinstance(x, (EraInt, EraFloat)) else 0.0))),
        "min": EraBuiltinFunction("math.min", lambda a, b: a if (a.value if isinstance(a, (EraInt, EraFloat)) else 0) <= (b.value if isinstance(b, (EraInt, EraFloat)) else 0) else b),
        "max": EraBuiltinFunction("math.max", lambda a, b: a if (a.value if isinstance(a, (EraInt, EraFloat)) else 0) >= (b.value if isinstance(b, (EraInt, EraFloat)) else 0) else b),
    }
    return EraStdLibModule("math", exports)


# ==============================================================================
# File System (fs) Module
# ==============================================================================
def create_fs_module() -> EraStdLibModule:
    def _read_file(path_val: EraValue) -> EraResult:
        path = path_val.to_string()
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return EraResult.ok(EraString(content))
        except Exception as e:
            return EraResult.err(EraString(str(e)))

    def _write_file(path_val: EraValue, content_val: EraValue) -> EraResult:
        path = path_val.to_string()
        content = content_val.to_string()
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return EraResult.ok(EraBool(True))
        except Exception as e:
            return EraResult.err(EraString(str(e)))

    def _append_file(path_val: EraValue, content_val: EraValue) -> EraResult:
        path = path_val.to_string()
        content = content_val.to_string()
        try:
            with open(path, "a", encoding="utf-8") as f:
                f.write(content)
            return EraResult.ok(EraBool(True))
        except Exception as e:
            return EraResult.err(EraString(str(e)))

    def _file_exists(path_val: EraValue) -> EraBool:
        return EraBool(os.path.exists(path_val.to_string()))

    def _read_lines(path_val: EraValue) -> EraResult:
        path = path_val.to_string()
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = [EraString(line.rstrip("\r\n")) for line in f.readlines()]
            return EraResult.ok(EraArray(lines))
        except Exception as e:
            return EraResult.err(EraString(str(e)))

    exports: Dict[str, EraValue] = {
        "read_file": EraBuiltinFunction("fs.read_file", _read_file),
        "write_file": EraBuiltinFunction("fs.write_file", _write_file),
        "append_file": EraBuiltinFunction("fs.append_file", _append_file),
        "file_exists": EraBuiltinFunction("fs.file_exists", _file_exists),
        "read_lines": EraBuiltinFunction("fs.read_lines", _read_lines),
    }
    return EraStdLibModule("fs", exports)


# ==============================================================================
# JSON Module
# ==============================================================================
def create_json_module() -> EraStdLibModule:
    def _parse(str_val: EraValue) -> EraResult:
        raw_str = str_val.to_string()
        try:
            parsed = json.loads(raw_str)
            return EraResult.ok(_py_to_era(parsed))
        except Exception as e:
            return EraResult.err(EraString(f"JSON Parse Error: {str(e)}"))

    def _stringify(val: EraValue, indent: EraValue = None) -> EraString:
        py_obj = _era_to_py(val)
        ind = indent.value if (indent and isinstance(indent, EraInt)) else None
        res = json.dumps(py_obj, indent=ind)
        return EraString(res)

    exports: Dict[str, EraValue] = {
        "parse": EraBuiltinFunction("json.parse", _parse),
        "stringify": EraBuiltinFunction("json.stringify", _stringify),
    }
    return EraStdLibModule("json", exports)


# ==============================================================================
# Time Module
# ==============================================================================
def create_time_module() -> EraStdLibModule:
    def _now() -> EraFloat:
        return EraFloat(time.time())

    def _elapsed_ms(start_val: EraValue) -> EraFloat:
        s = start_val.value if isinstance(start_val, (EraInt, EraFloat)) else 0.0
        return EraFloat((time.time() - s) * 1000.0)

    def _sleep(sec_val: EraValue) -> EraOption:
        s = sec_val.value if isinstance(sec_val, (EraInt, EraFloat)) else 0.0
        time.sleep(s)
        return EraOption.none()

    exports: Dict[str, EraValue] = {
        "now": EraBuiltinFunction("time.now", _now),
        "elapsed_ms": EraBuiltinFunction("time.elapsed_ms", _elapsed_ms),
        "sleep": EraBuiltinFunction("time.sleep", _sleep),
    }
    return EraStdLibModule("time", exports)


# ==============================================================================
# Crypto Module
# ==============================================================================
def create_crypto_module() -> EraStdLibModule:
    def _sha256(data_val: EraValue) -> EraString:
        text = data_val.to_string().encode("utf-8")
        return EraString(hashlib.sha256(text).hexdigest())

    def _sha1(data_val: EraValue) -> EraString:
        text = data_val.to_string().encode("utf-8")
        return EraString(hashlib.sha1(text).hexdigest())

    def _md5(data_val: EraValue) -> EraString:
        text = data_val.to_string().encode("utf-8")
        return EraString(hashlib.md5(text).hexdigest())

    def _hmac_sha256(key_val: EraValue, msg_val: EraValue) -> EraString:
        k = key_val.to_string().encode("utf-8")
        m = msg_val.to_string().encode("utf-8")
        return EraString(hmac.new(k, m, hashlib.sha256).hexdigest())

    def _random_token(len_val: EraValue = None) -> EraString:
        n = len_val.value if (len_val and isinstance(len_val, EraInt)) else 16
        return EraString(secrets.token_hex(n))

    exports: Dict[str, EraValue] = {
        "sha256": EraBuiltinFunction("crypto.sha256", _sha256),
        "sha1": EraBuiltinFunction("crypto.sha1", _sha1),
        "md5": EraBuiltinFunction("crypto.md5", _md5),
        "hmac_sha256": EraBuiltinFunction("crypto.hmac_sha256", _hmac_sha256),
        "random_token": EraBuiltinFunction("crypto.random_token", _random_token),
    }
    return EraStdLibModule("crypto", exports)


# ==============================================================================
# HTTP Module
# ==============================================================================
def create_http_module() -> EraStdLibModule:
    def _http_get(url_val: EraValue, timeout_val: EraValue = None) -> EraResult:
        url = url_val.to_string()
        timeout = timeout_val.value if (timeout_val and isinstance(timeout_val, (EraInt, EraFloat))) else 10.0
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "EraLang-HTTP/2.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.getcode()
                body = response.read().decode("utf-8", errors="replace")
                res_map = EraMap({
                    "status": EraInt(status),
                    "body": EraString(body),
                    "ok": EraBool(200 <= status < 300)
                })
                return EraResult.ok(res_map)
        except Exception as e:
            return EraResult.err(EraString(f"HTTP GET Error: {str(e)}"))

    def _http_post(url_val: EraValue, body_val: EraValue, timeout_val: EraValue = None) -> EraResult:
        url = url_val.to_string()
        data = body_val.to_string().encode("utf-8")
        timeout = timeout_val.value if (timeout_val and isinstance(timeout_val, (EraInt, EraFloat))) else 10.0
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json", "User-Agent": "EraLang-HTTP/2.0"}, method="POST")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status = response.getcode()
                body = response.read().decode("utf-8", errors="replace")
                res_map = EraMap({
                    "status": EraInt(status),
                    "body": EraString(body),
                    "ok": EraBool(200 <= status < 300)
                })
                return EraResult.ok(res_map)
        except Exception as e:
            return EraResult.err(EraString(f"HTTP POST Error: {str(e)}"))

    exports: Dict[str, EraValue] = {
        "get": EraBuiltinFunction("http.get", _http_get),
        "post": EraBuiltinFunction("http.post", _http_post),
    }
    return EraStdLibModule("http", exports)


# ==============================================================================
# OS Module
# ==============================================================================
def create_os_module() -> EraStdLibModule:
    def _env(name_val: EraValue) -> EraOption:
        k = name_val.to_string()
        if k in os.environ:
            return EraOption.some(EraString(os.environ[k]))
        return EraOption.none()

    def _cwd() -> EraString:
        return EraString(os.getcwd())

    def _platform() -> EraString:
        return EraString(sys.platform)

    exports: Dict[str, EraValue] = {
        "env": EraBuiltinFunction("os.env", _env),
        "cwd": EraBuiltinFunction("os.cwd", _cwd),
        "platform": EraBuiltinFunction("os.platform", _platform),
    }
    return EraStdLibModule("os", exports)


# ==============================================================================
# Linear Algebra (linalg) Module
# ==============================================================================
def create_linalg_module() -> EraStdLibModule:
    def _dot(a_val: EraValue, b_val: EraValue) -> EraFloat:
        a_list = _era_to_py(a_val)
        b_list = _era_to_py(b_val)
        if not isinstance(a_list, list) or not isinstance(b_list, list):
            raise RuntimeError("linalg.dot requires two 1D array vectors")
        dot_product = sum(float(x) * float(y) for x, y in zip(a_list, b_list))
        return EraFloat(dot_product)

    def _cross(a_val: EraValue, b_val: EraValue) -> EraArray:
        a = _era_to_py(a_val)
        b = _era_to_py(b_val)
        if len(a) != 3 or len(b) != 3:
            raise RuntimeError("linalg.cross requires 3-dimensional vectors [x, y, z]")
        cx = float(a[1]) * float(b[2]) - float(a[2]) * float(b[1])
        cy = float(a[2]) * float(b[0]) - float(a[0]) * float(b[2])
        cz = float(a[0]) * float(b[1]) - float(a[1]) * float(b[0])
        return EraArray([EraFloat(cx), EraFloat(cy), EraFloat(cz)])

    def _norm(vec_val: EraValue) -> EraFloat:
        v = _era_to_py(vec_val)
        if isinstance(v, list):
            # Flatten if 2D
            flat = [float(x) for row in v for x in (row if isinstance(row, list) else [row])]
            return EraFloat(math.sqrt(sum(x * x for x in flat)))
        return EraFloat(abs(float(v)))

    def _det2x2(mat_val: EraValue) -> EraFloat:
        m = _era_to_py(mat_val)
        if len(m) == 2 and len(m[0]) == 2 and len(m[1]) == 2:
            d = (float(m[0][0]) * float(m[1][1])) - (float(m[0][1]) * float(m[1][0]))
            return EraFloat(d)
        raise RuntimeError("linalg.det2x2 requires a 2x2 matrix [[a, b], [c, d]]")

    def _inv2x2(mat_val: EraValue) -> EraResult:
        m = _era_to_py(mat_val)
        if len(m) == 2 and len(m[0]) == 2 and len(m[1]) == 2:
            a, b = float(m[0][0]), float(m[0][1])
            c, d = float(m[1][0]), float(m[1][1])
            det = (a * d) - (b * c)
            if abs(det) < 1e-12:
                return EraResult.err(EraString("Singular matrix: determinant is 0"))
            inv = [
                [EraFloat(d / det), EraFloat(-b / det)],
                [EraFloat(-c / det), EraFloat(a / det)]
            ]
            return EraResult.ok(EraTensor.from_array(inv))
        return EraResult.err(EraString("linalg.inv2x2 requires 2x2 matrix"))

    exports: Dict[str, EraValue] = {
        "dot": EraBuiltinFunction("linalg.dot", _dot),
        "cross": EraBuiltinFunction("linalg.cross", _cross),
        "norm": EraBuiltinFunction("linalg.norm", _norm),
        "det2x2": EraBuiltinFunction("linalg.det2x2", _det2x2),
        "inv2x2": EraBuiltinFunction("linalg.inv2x2", _inv2x2),
    }
    return EraStdLibModule("linalg", exports)


# ==============================================================================
# Signal Processing (signal) Module
# ==============================================================================
def create_signal_module() -> EraStdLibModule:
    def _dft(samples_val: EraValue) -> EraArray:
        samples = _era_to_py(samples_val)
        if not isinstance(samples, list):
            raise RuntimeError("signal.dft requires an array of numeric samples")
        N = len(samples)
        magnitudes = []
        for k in range(N):
            re = 0.0
            im = 0.0
            for n in range(N):
                angle = (2.0 * math.pi * k * n) / N
                s = float(samples[n])
                re += s * math.cos(angle)
                im -= s * math.sin(angle)
            mag = math.sqrt(re * re + im * im)
            magnitudes.append(EraFloat(mag))
        return EraArray(magnitudes)

    def _rms(samples_val: EraValue) -> EraFloat:
        samples = _era_to_py(samples_val)
        if not isinstance(samples, list) or len(samples) == 0:
            return EraFloat(0.0)
        mean_sq = sum(float(x) ** 2 for x in samples) / len(samples)
        return EraFloat(math.sqrt(mean_sq))

    def _peak_to_peak(samples_val: EraValue) -> EraFloat:
        samples = _era_to_py(samples_val)
        if not isinstance(samples, list) or len(samples) == 0:
            return EraFloat(0.0)
        vals = [float(x) for x in samples]
        return EraFloat(max(vals) - min(vals))

    exports: Dict[str, EraValue] = {
        "dft": EraBuiltinFunction("signal.dft", _dft),
        "rms": EraBuiltinFunction("signal.rms", _rms),
        "peak_to_peak": EraBuiltinFunction("signal.peak_to_peak", _peak_to_peak),
    }
    return EraStdLibModule("signal", exports)


# ==============================================================================
# Universal Physics & Mechanics Module
# ==============================================================================
def create_physics_module() -> EraStdLibModule:
    C_LIGHT = 299792458.0              # Speed of light (m/s)
    G_CONST = 6.67430e-11              # Gravitational constant (m^3 kg^-1 s^-2)
    H_PLANCK = 6.62607015e-34          # Planck constant (J s)
    KB_BOLTZMANN = 1.380649e-23        # Boltzmann constant (J/K)
    G_EARTH = 9.80665                  # Standard Earth gravity (m/s^2)
    EPSILON_0 = 8.8541878128e-12       # Vacuum permittivity (F/m)
    MU_0 = 1.25663706212e-6            # Vacuum permeability (N/A^2)

    def _kinetic_energy(m_val: EraValue, v_val: EraValue) -> EraFloat:
        m = float(m_val.value if isinstance(m_val, (EraInt, EraFloat)) else 0)
        v = float(v_val.value if isinstance(v_val, (EraInt, EraFloat)) else 0)
        return EraFloat(0.5 * m * v * v)

    def _gravitational_force(m1_val: EraValue, m2_val: EraValue, r_val: EraValue) -> EraFloat:
        m1 = float(m1_val.value if isinstance(m1_val, (EraInt, EraFloat)) else 0)
        m2 = float(m2_val.value if isinstance(m2_val, (EraInt, EraFloat)) else 0)
        r = float(r_val.value if isinstance(r_val, (EraInt, EraFloat)) else 1)
        if r == 0:
            raise ZeroDivisionError("Radius cannot be 0 in gravitational force")
        return EraFloat((G_CONST * m1 * m2) / (r * r))

    def _lorentz_factor(v_val: EraValue) -> EraFloat:
        v = float(v_val.value if isinstance(v_val, (EraInt, EraFloat)) else 0)
        beta = v / C_LIGHT
        if beta >= 1.0:
            raise RuntimeError("Velocity exceeds or equals speed of light")
        return EraFloat(1.0 / math.sqrt(1.0 - beta * beta))

    exports: Dict[str, EraValue] = {
        "C": EraFloat(C_LIGHT),
        "G": EraFloat(G_CONST),
        "H": EraFloat(H_PLANCK),
        "KB": EraFloat(KB_BOLTZMANN),
        "G_EARTH": EraFloat(G_EARTH),
        "EPSILON_0": EraFloat(EPSILON_0),
        "MU_0": EraFloat(MU_0),
        "kinetic_energy": EraBuiltinFunction("physics.kinetic_energy", _kinetic_energy),
        "gravitational_force": EraBuiltinFunction("physics.gravitational_force", _gravitational_force),
        "lorentz_factor": EraBuiltinFunction("physics.lorentz_factor", _lorentz_factor),
    }
    return EraStdLibModule("physics", exports)


BUILTIN_STDLIB_MODULES = {
    "math": create_math_module,
    "fs": create_fs_module,
    "json": create_json_module,
    "time": create_time_module,
    "crypto": create_crypto_module,
    "http": create_http_module,
    "os": create_os_module,
    "linalg": create_linalg_module,
    "signal": create_signal_module,
    "physics": create_physics_module,
}


def get_stdlib_module(name: str) -> EraOption:
    if name in BUILTIN_STDLIB_MODULES:
        return EraOption.some(BUILTIN_STDLIB_MODULES[name]())
    return EraOption.none()
