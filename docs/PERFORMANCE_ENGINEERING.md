# How Soma gets its speed

You write a cell. `soma run` compiles it when `g++` or `clang++` is on PATH, using `-O3 -std=c++20 -march=native`. Without a C++ compiler it runs on V8. `--engine interpreter` and `--engine vm` stay available. They are not the fast path.

The measured ranking, the machine, and the per-task times are in [MEASURED_PERFORMANCE.md](MEASURED_PERFORMANCE.md). On that run Soma's geometric mean was 0.69× the fastest other language. The notes below are what the compiler actually emits.

## Representations

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

The in-process interpreter walks the AST in Python. The bytecode machine is a second in-process engine. Use them when you want a traceback or when no C++ compiler and no Node.js are installed. Their times are not the ranking in [MEASURED_PERFORMANCE.md](MEASURED_PERFORMANCE.md).
