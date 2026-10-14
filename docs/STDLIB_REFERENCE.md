# Soma Standard Library Reference

**Conceived and Crafted in India**  
Created & Designed by **[Vighnesh Jha](https://github.com/VJ420)** ([@VJ420](https://github.com/VJ420))  
**Core Modules:** `std/math.fc`, `std/array.fc`, `std/string.fc` (`.sm` paths resolve the same way)

---

## 1. `std/math.fc` — Mathematical & Numerical Kernels

High-precision constants and optimized numeric functions.

### Constants
- `math.pi`: Mathematical constant $\pi \approx 3.141592653589793$
- `math.e`: Euler's number $e \approx 2.718281828459045$
- `math.tau`: Full circle constant $\tau = 2\pi \approx 6.283185307179586$

### Functions
- `math.abs(x)`: Returns the absolute magnitude of $x$.
- `math.min(a, b)`: Returns the minimum of two values.
- `math.max(a, b)`: Returns the maximum of two values.
- `math.clamp(val, low, high)`: Clamps $val$ between $[low, high]$.
- `math.square(x)`: Evaluates $x^2$.
- `math.circle_area(r)`: Evaluates $\pi r^2$.
- `math.factorial(n)`: Evaluates $n!$ recursively.

```fractal
15 -> math.square -> print
```

---

## 2. `std/array.fc` — Functional Collection Pipelines

High-throughput array transformations supporting functional pipelining (`->`).

### Functions
- `array.sum(list)`: Sum of the elements.
- `array.average(list)`: Arithmetic mean.
- `array.min(list)` / `array.min_of(list)`: Lowest value.
- `array.max(list)` / `array.max_of(list)`: Highest value.
- `array.contains(list, item)`: Containment lookup.
- `array.reverse(list)`: Reversed copy.

```fractal
[10, 20, 30, 40] -> array.average -> print
```

---

## 3. `std/string.fc` — String Manipulation & Formatting

High-speed text processing and validation.

### Functions
- `string.length(s)`: Character count.
- `string.is_empty(s)`: `true` when the string is empty.
- `string.wrap(s, prefix, suffix)`: Prefix and suffix around `s`.
- `string.repeat(s, count)` / `string.repeat_str(s, count)`: Repeated copy.
- `string.join(list, sep)`: Join elements with a separator.

```fractal
"FRACTAL" -> string.wrap("==[ ", " ]==") -> print
```
