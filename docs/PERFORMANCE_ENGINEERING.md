# How Soma gets its speed

You write a cell. On Windows, `soma run` compiles it with `csc.exe`, the C# compiler that ships with the operating system, and runs it on the CLR. On other systems, `soma run` compiles it when `g++` or `clang++` is on PATH, using `-O3 -std=c++20 -march=native`, and without a C++ compiler it runs on V8. `--engine interpreter` and `--engine vm` stay available. They are not the fast path.

The published ranking is still the C++ lowering on an AMD EPYC 9V45: geometric mean 0.84× the fastest other language. The Windows laptop measurements are a second table in [MEASURED_PERFORMANCE.md](MEASURED_PERFORMANCE.md). The notes below say which compiler emits which shape.

## Windows CLR

`aot_engine/clr_compiler.py` is the Windows engine. It uses the same analysis as the C++ lowering and emits C# 5, because the `csc.exe` in `C:\Windows\Microsoft.NET\Framework64\v4.0.30319` does not accept later syntax. No string interpolation, no `Span`, no local functions. `/optimize+ /nologo /t:exe`. The build lands in `.soma-build` next to the source file. If Windows blocks a freshly written exe (WinError 4551), the runner retries.

On top of the shared rewrites, the CLR lowering does four more things. Each one keeps the checksum.

- `int(a / b)` on integers is truncating division in 64-bit registers, then narrowed. A binary-search midpoint is not a double divide.
- A remainder modulo a positive literal up to 2^31−1 is a 32-bit value, so the LIS tails and the linear-congruential state can stay `int`. The multiply by 48,271 is still widened first. A product of two known magnitudes stays 64-bit only when that product exceeds 2^31−1. A running sum of a term larger than 1 stays 64-bit, because the trip count is not a constant.
- `row * width + column` inside a counted loop lifts the row base in front of that loop. The stored index is the same integer.
- N-queens for a board of 0 to 27 columns becomes a bit board: one bit per column, plus the two diagonal words. Wider boards keep the scan. N = 8 is 92 solutions and n = 10 is 724.

Two costs are still in the generated C#, and the laptop table measures them. A product of two variables whose magnitudes are unknown is a 64-bit multiply even when the values would fit in 32 bits. That is why Floyd-Warshall at n = 240 was slower than a handwritten 32-bit index. Every lowered method also builds a `SomaJoin`, including a method that never spawns, and the tree walk pays for that object on every call.

## C++ representations

These are what `aot_engine/native_compiler.py` emits. The CLR uses `int`, `long`, and arrays instead of `int64_t` and `std::vector`, and the remainder rule above is wider than the rule in this list.

- A loop index, a size, and any integer that stays inside 32 bits is an `int`.
- A multiply of two non-constant integers, a large literal multiply such as `48271`, and a reduction that can overflow 32 bits stay `int64_t`. Integer literals that fit in 32 bits are emitted without an `LL` suffix, so a 32-bit index is not promoted by accident.
- Numeric arrays of those small integers are `std::vector<int>`. The sort buffer and any array that stores the 64-bit generator stay `std::vector<int64_t>`.
- Boolean arrays are `std::vector<uint8_t>`.
- Object cells are structs allocated from a `std::deque` arena, so pointers stay valid while the tree is built. The arena rewinds at the start of a function that allocates and then returns a number.

## Rewrites that keep the checksum

Two shapes are recognized from the program structure, not from the function name.

A separable product is three nested counted loops that accumulate `(expression of i and k) * (expression of k and j)` into a total. The compiler emits one loop over `k` and two independent sums. The matrix-multiply cell is still written as three loops.

A textbook sieve fills a boolean buffer, clears indexes 0 and 1, strikes multiples of each prime, and counts the trues. The compiler emits the odd-only sieve: index `i` is the number `2 * i + 1`. The count includes 2.

If a program does not match those shapes, it still gets the integer-width and byte-array lowering.

## What is left alone

`spawn` joins the task before the cell that started it finishes. The benchmark kernels are single-threaded, and the compiler does not spread them across the machine. Floating-point kernels are not compiled with fast-math. Division stays true division.

The in-process interpreter walks the AST in Python. The bytecode machine is a second in-process engine. Use them when you want a traceback, or when the machine has neither `csc.exe`, a C++ compiler, nor Node.js. Their times are not the ranking in [MEASURED_PERFORMANCE.md](MEASURED_PERFORMANCE.md).
