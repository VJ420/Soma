# Archived probes

These scripts and JSON files are older local experiments. They are kept so the history of the repository stays readable. They are not the Soma ranking.

The ranking is [docs/MEASURED_PERFORMANCE.md](../../docs/MEASURED_PERFORMANCE.md), produced by [../extreme/run_benchmarks.py](../extreme/run_benchmarks.py).

| File | What it actually times |
|---|---|
| `benchmark.py` | The in-process interpreter against the bytecode machine, on one loop. |
| `bench_swarm_v2.py` | Flat swarm versus the three-tier swarm, in Python threads. |
| `run_suite.py` | Fibonacci and a loop, across Python, Node, the interpreter, and the bytecode machine. |
| `run_domain_benchmarks.py` | Python and Node on six small kernels, plus the swarm. Writes `empirical_results.json`. |
| `cross_domain_benchmark.py` | Python and JavaScript kernels. Writes `cross_domain_extreme_results.json`. |
| `hard_math_benchmark.py` | Python and JavaScript kernels. Writes `hard_math_results.json`. |
| `e2e_full_benchmark.py` | Python, Node, and the swarm on one reduction. |
| `e2e_agentic_benchmark.py` | Python threads against the swarm coordinator. |

A number printed by these scripts is a number from that script. It does not update the published table.
