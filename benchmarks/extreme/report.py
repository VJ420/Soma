"""Generate an evidence-first Markdown report from benchmark JSON."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import geometric_mean
from typing import Any


def _fmt(value: float | None, digits: int = 2) -> str:
    return "n/a" if value is None else f"{value:,.{digits}f}"


def _runtime_summary(data: dict[str, Any]) -> list[dict[str, Any]]:
    largest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in data["measurements"]:
        if row["status"] != "ok":
            continue
        key = (row["runtime"], row["workload"])
        if key not in largest or row["size"] > largest[key]["size"]:
            largest[key] = row

    runtimes = sorted({row["runtime"] for row in largest.values()})
    competitors = {"Python", "JavaScript", "Go", "Rust", "C++"}
    summary = []
    for runtime in runtimes:
        rows = [row for (name, _), row in largest.items() if name == runtime]
        ratios = []
        for row in rows:
            same_workload = [
                candidate
                for (name, workload), candidate in largest.items()
                if workload == row["workload"] and name in competitors
            ]
            if same_workload:
                best = min(candidate["median_per_iteration_ms"] for candidate in same_workload)
                ratios.append(row["median_per_iteration_ms"] / best)
        summary.append(
            {
                "runtime": runtime,
                "workloads": len(rows),
                "geomean_vs_best_competitor": geometric_mean(ratios) if ratios else None,
                "median_peak_rss_kb": sorted(
                    row["peak_rss_kb"] for row in rows if row["peak_rss_kb"] is not None
                )[len([row for row in rows if row["peak_rss_kb"] is not None]) // 2]
                if any(row["peak_rss_kb"] is not None for row in rows)
                else None,
            }
        )
    return summary


def _largest_ok(data: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    largest: dict[tuple[str, str], dict[str, Any]] = {}
    for row in data["measurements"]:
        if row["status"] != "ok":
            continue
        key = (row["runtime"], row["workload"])
        if key not in largest or row["size"] > largest[key]["size"]:
            largest[key] = row
    return largest


def _soma_ratio_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    largest = _largest_ok(data)
    competitors = ["Python", "JavaScript", "Go", "Rust", "C++"]
    soma_runtimes = sorted(
        {runtime for runtime, _ in largest if runtime.startswith("Soma")}
    )
    rows = []
    for soma in soma_runtimes:
        for competitor in competitors:
            ratios = []
            for workload in data["manifest"]["workloads"]:
                left = largest.get((soma, workload))
                right = largest.get((competitor, workload))
                if left and right:
                    ratios.append(
                        left["median_per_iteration_ms"] / right["median_per_iteration_ms"]
                    )
            rows.append(
                {
                    "soma": soma,
                    "competitor": competitor,
                    "pairs": len(ratios),
                    "geomean": geometric_mean(ratios) if ratios else None,
                }
            )
    return rows


def _recommendations(data: dict[str, Any]) -> list[str]:
    failed = [row for row in data["measurements"] if row["status"] != "ok"]
    items = [
        "Soma in this run is the native cell lowering: 32-bit indexes where the value fits, int64 for wide products and reductions, byte boolean arrays, separable integer products rewritten as a double reduction, the textbook sieve rewritten as an odd-only sieve, arena-allocated object cells released per call, counted loops emitted as for-loops, and pipelines lowered to direct calls.",
        "C++, Rust, and Go were compiled for the host CPU, and Soma was compiled with the same class of flags. A ratio below 1.0 means Soma took less kernel time than that language.",
    ]
    if failed:
        items.append(
            f"{len(failed)} workload rows failed checksum, compilation, or the time limit. Those rows are not scores."
        )
    return items


def _complexity_rows(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for runtime in sorted({row["runtime"] for row in data["measurements"]}):
        for workload, spec in data["manifest"]["workloads"].items():
            points = sorted(
                (
                    row["size"],
                    row["median_per_iteration_ms"],
                )
                for row in data["measurements"]
                if row["runtime"] == runtime
                and row["workload"] == workload
                and row["status"] == "ok"
            )
            if len(points) < 2 or workload in {"nqueens", "binarytrees"}:
                exponent = None
            else:
                xs = [math.log(point[0]) for point in points]
                ys = [math.log(max(point[1], 1e-9)) for point in points]
                x_mean, y_mean = sum(xs) / len(xs), sum(ys) / len(ys)
                denominator = sum((x - x_mean) ** 2 for x in xs)
                exponent = (
                    sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denominator
                    if denominator
                    else None
                )
            rows.append(
                {
                    "runtime": runtime,
                    "workload": workload,
                    "expected": spec["expected_time"],
                    "empirical_exponent": exponent,
                }
            )
    return rows


def generate_report(data: dict[str, Any]) -> str:
    summary = _runtime_summary(data)
    complexity = _complexity_rows(data)
    ratios = _soma_ratio_rows(data)
    recommendations = _recommendations(data)
    failures = [row for row in data["measurements"] if row["status"] != "ok"]
    soma_rows = [row for row in summary if row["runtime"].startswith("Soma")]
    fastest_soma = (
        min(
            soma_rows,
            key=lambda row: row["geomean_vs_best_competitor"]
            if row["geomean_vs_best_competitor"] is not None
            else math.inf,
        )
        if soma_rows
        else None
    )

    lines = [
        "# Soma extreme cross-language benchmark report",
        "",
        f"Generated: `{data['metadata']['timestamp_utc']}`  ",
        f"Commit: `{data['metadata'].get('commit', 'unknown')}`  ",
        f"Runner: `{data['metadata']['platform']}` · `{data['metadata'].get('cpu', 'unknown CPU')}`",
    ]
    flags = data["metadata"].get("compile_flags") or {}
    if flags:
        rendered = ", ".join(f"{name} `{value}`" for name, value in flags.items())
        lines.append(f"Host compilation: {rendered}")
    lines.extend([
        "",
        "## Executive result",
        "",
        (
            f"The fastest measured Soma backend was **{fastest_soma['runtime']}**, with a "
            f"geometric-mean runtime of **{_fmt(fastest_soma['geomean_vs_best_competitor'])}×** "
            "the fastest measured conventional-language implementation on matching largest inputs."
            if fastest_soma
            and fastest_soma["geomean_vs_best_competitor"] is not None
            else "No Soma backend completed enough matching workloads in this selected run for an aggregate ratio."
        ),
        "Lower runtime ratios are better. These are measurements from this run, not reference or hardcoded numbers.",
        "",
        "## Runtime summary",
        "",
        "| Runtime | Completed workloads | Geomean vs best competitor | Median peak RSS (MiB) |",
        "|---|---:|---:|---:|",
    ])
    for row in sorted(
        summary,
        key=lambda item: item["geomean_vs_best_competitor"]
        if item["geomean_vs_best_competitor"] is not None
        else math.inf,
    ):
        rss = row["median_peak_rss_kb"]
        lines.append(
            f"| {row['runtime']} | {row['workloads']} | "
            f"{_fmt(row['geomean_vs_best_competitor'])}× | "
            f"{_fmt(rss / 1024 if rss is not None else None)} |"
        )

    lines.extend(
        [
            "",
            "## Soma versus each language",
            "",
            "Geometric mean of Soma kernel time divided by the named language, using only workloads both completed at their largest input. Values below 1.00× mean Soma was faster.",
            "",
            "| Soma backend | vs Python | vs JavaScript | vs Go | vs Rust | vs C++ |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    by_soma: dict[str, dict[str, float | None]] = {}
    for row in ratios:
        by_soma.setdefault(row["soma"], {})[row["competitor"]] = row["geomean"]
    for soma, values in by_soma.items():
        lines.append(
            f"| {soma} | {_fmt(values.get('Python'))}× | {_fmt(values.get('JavaScript'))}× | "
            f"{_fmt(values.get('Go'))}× | {_fmt(values.get('Rust'))}× | {_fmt(values.get('C++'))}× |"
        )

    lines.extend(
        [
            "",
            "## Prioritized recommendations",
            "",
        ]
    )
    for index, item in enumerate(recommendations, start=1):
        lines.append(f"{index}. {item}")

    lines.extend(
        [
            "",
            "## Cold end-to-end startup",
            "",
            "A zero-iteration invocation measures CLI/runtime startup, source loading, parsing, and backend initialization.",
            "",
            "| Runtime | Median cold start (ms) | p95 (ms) |",
            "|---|---:|---:|",
        ]
    )
    for runtime, cold in data.get("cold_starts", {}).items():
        lines.append(
            f"| {runtime} | {_fmt(cold.get('median_ms'))} | {_fmt(cold.get('p95_ms'))} |"
        )

    lines.extend(
        [
            "",
            "## Largest-input timings",
            "",
            "| Workload | Runtime | Size | Kernel median/iteration (ms) | Kernel p95 (ms) | End-to-end median/iteration (ms) | Peak RSS (MiB) |",
            "|---|---|---:|---:|---:|---:|---:|",
        ]
    )
    largest_size = {
        workload: max(spec["sizes"])
        for workload, spec in data["manifest"]["workloads"].items()
    }
    for row in data["measurements"]:
        if row["status"] == "ok" and row["size"] == largest_size[row["workload"]]:
            rss = row["peak_rss_kb"]
            lines.append(
                f"| {row['workload']} | {row['runtime']} | {row['size']} | "
                f"{_fmt(row['median_per_iteration_ms'], 3)} | "
                f"{_fmt(row['p95_per_iteration_ms'], 3)} | "
                f"{_fmt(row['median_e2e_per_iteration_ms'], 3)} | "
                f"{_fmt(rss / 1024 if rss is not None else None)} |"
            )

    lines.extend(
        [
            "",
            "## Complexity scaling",
            "",
            "The empirical exponent is the slope of `log(runtime)` against `log(input size)`. "
            "It is omitted for exponential workloads because a polynomial exponent is misleading.",
            "",
            "| Runtime | Workload | Expected | Empirical exponent |",
            "|---|---|---|---:|",
        ]
    )
    for row in complexity:
        lines.append(
            f"| {row['runtime']} | {row['workload']} | {row['expected']} | "
            f"{_fmt(row['empirical_exponent'])} |"
        )

    lines.extend(["", "## Compilation and source footprint", ""])
    lines.extend(
        [
            "| Runtime | Build status | Build time (ms) | Artifact/source bytes |",
            "|---|---|---:|---:|",
        ]
    )
    for runtime, build in data["builds"].items():
        lines.append(
            f"| {runtime} | {build['status']} | {_fmt(build.get('duration_ms'))} | "
            f"{build.get('bytes', 'n/a')} |"
        )

    lines.extend(["", "## Unsupported and failed cases", ""])
    if failures:
        for row in failures:
            lines.append(
                f"- **{row['runtime']} / {row['workload']} / size {row['size']}**: "
                f"{row['status']} — {row.get('reason', 'no reason recorded')}"
            )
    else:
        lines.append("- All scheduled cases passed checksum validation.")

    lines.extend(
        [
            "",
            "## Interpretation and limitations",
            "",
            "- Kernel timings come from clocks inside each program and exclude process startup. End-to-end and zero-iteration "
            "cold-start timings are reported separately.",
            "- Python, JavaScript, Go, Rust, and C++ implementations use equivalent algorithms, but their container representations "
            "follow normal language idioms; this is more realistic than forcing identical low-level layouts.",
            "- Soma JIT means Soma source translated by `transpiler_js.py` and executed by Node/V8. Raw JavaScript is reported separately.",
            "- GitHub-hosted runner hardware can vary between runs. Compare values within one run; use repeated workflow runs for trend claims.",
            "- Peak RSS is sampled by GNU `time` and includes runtime/VM overhead.",
            "",
            "## Reproduction",
            "",
            "```bash",
            "python benchmarks/extreme/run_benchmarks.py --output benchmarks/extreme/results",
            "```",
            "",
            "Raw samples and all environment metadata are in `results/raw_results.json`.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = json.loads(args.results.read_text(encoding="utf-8"))
    args.output.write_text(generate_report(data), encoding="utf-8")


if __name__ == "__main__":
    main()
