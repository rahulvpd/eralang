# 🔬 EraLang Standard Library Reference

EraLang includes a 10-module pure standard library built for scientific, mathematical, systems, and cryptographic tasks.

---

## 1. `math`
High-precision mathematical functions and constants.
* `math.pi`: `3.141592653589793`
* `math.e`: `2.718281828459045`
* `math.sqrt(x)`: Square root of `x`
* `math.pow(x, y)`: $x^y$
* `math.sin(x)`, `math.cos(x)`, `math.tan(x)`: Trigonometric functions (radians)
* `math.abs(x)`: Absolute value
* `math.floor(x)`, `math.ceil(x)`: Rounding

---

## 2. `linalg`
Vector geometry and linear algebra.
* `linalg.dot(a, b)`: Vector dot product
* `linalg.cross(a, b)`: 3D vector cross product
* `linalg.norm(a)`: Euclidean norm ($L_2$)
* `linalg.normalize(a)`: Unit vector
* `linalg.matmul(A, B)`: 2D matrix multiplication

---

## 3. `physics`
Universal physical formulas, relativistic mechanics, and orbital dynamics.
* `physics.kinetic_energy(mass, velocity)`: $E_k = \frac{1}{2} m v^2$
* `physics.potential_energy(mass, height)`: $E_p = m g h$
* `physics.lorentz_factor(velocity)`: $\gamma = \frac{1}{\sqrt{1 - v^2/c^2}}$
* `physics.gravitational_force(m1, m2, r)`: $F = G \frac{m_1 m_2}{r^2}$

---

## 4. `signal`
Digital Signal Processing (DSP) and spectral analysis.
* `signal.dft(samples)`: Discrete Fourier Transform magnitude spectrum
* `signal.rms(samples)`: Root Mean Square signal power
* `signal.convolve(a, b)`: 1D discrete convolution
* `signal.moving_average(samples, window)`: Moving average filter

---

## 5. `fs`
Safe, capability-restricted filesystem I/O.
* `fs.read(path)`: Read file text
* `fs.write(path, content)`: Write file text
* `fs.exists(path)`: Check file existence
* `fs.delete(path)`: Delete file
* `fs.list_dir(path)`: List directory contents

---

## 6. `json`
JSON serialization and parsing.
* `json.parse(str)`: Parse JSON string into EraLang native values
* `json.stringify(val)`: Serialize EraLang value to formatted JSON string

---

## 7. `time`
Timestamps and execution benchmarking.
* `time.now()`: Current UNIX timestamp in seconds
* `time.sleep(sec)`: Suspend thread execution for `sec` seconds

---

## 8. `crypto`
Cryptographic hashes and digests.
* `crypto.sha256(data)`: Compute SHA-256 hex digest
* `crypto.sha512(data)`: Compute SHA-512 hex digest
* `crypto.md5(data)`: Compute legacy MD5 hex digest

---

## 9. `http`
Safe HTTP network client.
* `http.get(url)`: Send HTTP GET request, returns response text or error
* `http.post(url, body)`: Send HTTP POST request with payload

---

## 10. `os`
Operating system environment.
* `os.getenv(key)`: Retrieve environment variable (returns `Option<string>`)
* `os.platform()`: Current platform identifier (`linux`, `darwin`, `win32`)
