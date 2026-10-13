# Soma Standard Library Reference

**Conceived and Crafted in India**  
Created & Designed by **[Vighnesh Jha](https://github.com/VJ420)** ([@VJ420](https://github.com/VJ420))  
**Core Modules:** `std/math.fc`, `std/array.fc`, `std/string.fc`

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
- `array.sum(list)`: Computes the sum of all numeric elements in $O(N)$ time with minimal allocation.
- `array.average(list)`: Computes the arithmetic mean of numeric elements.
- `array.min(list)`: Returns the lowest value in the array.
- `array.max(list)`: Returns the highest value in the array.
- `array.contains(list, item)`: Performs $O(N)$ containment lookup.
- `array.reverse(list)`: Inverts the sequence of elements.

```fractal
[10, 20, 30, 40] -> array.average -> print
```

---

## 3. `std/string.fc` — String Manipulation & Formatting

High-speed text processing and validation.

### Functions
- `string.length(s)`: Returns the character count.
- `string.is_empty(s)`: Returns `true` if string length is 0.
- `string.wrap(s, prefix, suffix)`: Surrounds string with formatting tokens.
- `string.repeat(s, count)`: Generates concatenated repetitions.

```fractal
"FRACTAL" -> string.wrap("==[ ", " ]==") -> print
```
