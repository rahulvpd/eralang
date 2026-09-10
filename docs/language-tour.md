# 📖 EraLang Language Tour

This tour introduces the key syntax, semantics, and safety constructs of EraLang.

---

## 1. Variables & Immutability

EraLang enforces explicit mutability:
* `let`: Immutable binding (cannot be reassigned).
* `var`: Mutable variable.

```rust
let maximum_capacity = 100
// maximum_capacity = 200 // Compile Error: Cannot reassign immutable 'let' binding

var current_count = 0
current_count = current_count + 1 // Allowed
```

---

## 2. Zero Nulls: `Option<T>`

In EraLang, `null` and `NoneType` do not exist. Any value that may or may not be present must be an `Option<T>`:

```rust
fn fetch_config(key: string) -> Option<string> {
    if key == "PORT" {
        return Some("8080")
    }
    return None
}

let port = fetch_config("PORT")

// Exhaustive pattern matching is required
match port {
    Some(val) => print("Binding port to " + val)
    None => print("No port configured, using default")
}

// Or safe unwrapping with fallback default
let active_port = fetch_config("TIMEOUT").unwrap_or("30")
```

---

## 3. Explicit Error Handling: `Result<T, E>`

Unchecked runtime exceptions (`raise`, `throw`) are replaced with `Result<T, E>`:

```rust
fn parse_positive(val: int) -> Result<int, string> {
    if val < 0 {
        return Err("Value cannot be negative")
    }
    return Ok(val * 2)
}

let res = parse_positive(-5)
match res {
    Ok(v) => print("Computed: " + to_str(v))
    Err(e) => print("Safety check caught error: " + e)
}
```

---

## 4. Native Structs & Enums

```rust
struct User {
    id: int,
    username: string,
    active: bool
}

enum Role {
    Admin,
    Moderator,
    Guest
}

let u = User(1, "rahul", true)
let user_role = Role.Admin

match user_role {
    Role.Admin => print("User " + u.username + " has full root access.")
    Role.Moderator => print("User has moderation access.")
    Role.Guest => print("User has read-only access.")
}
```

---

## 5. Functional Data Pipelines

EraLang provides functional method chaining across arrays:

```rust
fn is_positive(x: int) -> bool { return x > 0 }
fn square(x: int) -> int { return x * x }
fn sum(acc: int, item: int) -> int { return acc + item }

let raw_data = [-2, -1, 0, 1, 2, 3, 4]

let total = raw_data
    .filter(is_positive)
    .map(square)
    .reduce(sum, 0)

print("Sum of positive squares: " + to_str(total)) // 1 + 4 + 9 + 16 = 30
```

---

## 6. Native Tensors & Linear Algebra

Tensors support native matrix multiplication using the `@` operator:

```rust
let A = Tensor.from_array([[1.0, 2.0], [3.0, 4.0]])
let B = Tensor.from_array([[5.0, 6.0], [7.0, 8.0]])

let C = A @ B

print("Matrix Product A @ B:")
print(C)
print("Mean: " + to_str(C.mean()))
print("Transpose: ")
print(C.transpose())
```
