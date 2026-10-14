"""Measured-only cross-language benchmark orchestrator."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import platform
import re
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from report import generate_report


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
LANGUAGES = HERE / "languages"
CHECKSUM_RE = re.compile(r"CHECKSUM:([-+0-9.eE]+)")
ELAPSED_RE = re.compile(r"ELAPSED_MS:([-+0-9.eE]+)")
RSS_RE = re.compile(r"__MAX_RSS_KB:(\d+)")


def command_version(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=15,
        )
        return (result.stdout or result.stderr).splitlines()[0].strip()
    except (OSError, subprocess.SubprocessError, IndexError):
        return None


def run_process(command: list[str], timeout: int) -> dict[str, Any]:
    wrapped = command
    uses_gnu_time = os.name != "nt" and Path("/usr/bin/time").exists()
    if uses_gnu_time:
        wrapped = ["/usr/bin/time", "-f", "__MAX_RSS_KB:%M", *command]
    started = time.perf_counter()
    try:
        result = subprocess.run(
            wrapped,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        return {
            "status": "timeout",
            "duration_ms": timeout * 1000.0,
            "stdout": error.stdout or "",
            "stderr": error.stderr or "",
            "peak_rss_kb": None,
        }
    duration_ms = (time.perf_counter() - started) * 1000.0
    rss_match = RSS_RE.search(result.stderr)
    return {
        "status": "ok" if result.returncode == 0 else "error",
        "returncode": result.returncode,
        "duration_ms": duration_ms,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "peak_rss_kb": int(rss_match.group(1)) if rss_match else None,
    }


def build_binary(
    runtime: str,
    command: list[str],
    artifact: Path,
    source: Path,
) -> dict[str, Any]:
    if shutil.which(command[0]) is None:
        return {
            "status": "unavailable",
            "reason": f"{command[0]} was not found on PATH",
            "duration_ms": None,
            "bytes": source.stat().st_size,
        }
    artifact.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    duration_ms = (time.perf_counter() - started) * 1000.0
    if result.returncode != 0:
        return {
            "status": "failed",
            "reason": (result.stderr or result.stdout)[-2000:],
            "duration_ms": duration_ms,
            "bytes": source.stat().st_size,
        }
    return {
        "status": "ok",
        "duration_ms": duration_ms,
        "bytes": artifact.stat().st_size,
        "artifact": str(artifact.relative_to(ROOT)),
    }


def render_soma(
    template: str,
    generated_dir: Path,
    workload: str,
    size: int,
    iterations: int,
) -> Path:
    rendered = (
        template.replace("{{WORKLOAD}}", workload)
        .replace("{{SIZE}}", str(size))
        .replace("{{ITERATIONS}}", str(iterations))
    )
    path = generated_dir / f"{workload}_{size}_{iterations}.sm"
    path.write_text(rendered, encoding="utf-8")
    return path


def runtime_commands(build_dir: Path) -> dict[str, Any]:
    python_file = LANGUAGES / "python_bench.py"
    javascript_file = LANGUAGES / "javascript_bench.js"
    go_binary = build_dir / ("go_bench.exe" if os.name == "nt" else "go_bench")
    rust_binary = build_dir / ("rust_bench.exe" if os.name == "nt" else "rust_bench")
    cpp_binary = build_dir / ("cpp_bench.exe" if os.name == "nt" else "cpp_bench")
    return {
        "Python": lambda workload, size, iterations, _soma: [
            sys.executable,
            str(python_file),
            workload,
            str(size),
            str(iterations),
        ],
        "JavaScript": lambda workload, size, iterations, _soma: [
            "node",
            str(javascript_file),
            workload,
            str(size),
            str(iterations),
        ],
        "Go": lambda workload, size, iterations, _soma: [
            str(go_binary),
            workload,
            str(size),
            str(iterations),
        ],
        "Rust": lambda workload, size, iterations, _soma: [
            str(rust_binary),
            workload,
            str(size),
            str(iterations),
        ],
        "C++": lambda workload, size, iterations, _soma: [
            str(cpp_binary),
            workload,
            str(size),
            str(iterations),
        ],
        "Soma interpreter": lambda _workload, _size, _iterations, soma: [
            sys.executable,
            str(ROOT / "soma_cli.py"),
            "run",
            str(soma),
        ],
        "Soma JIT": lambda _workload, _size, _iterations, soma: [
            sys.executable,
            str(ROOT / "soma_cli.py"),
            "jit",
            str(soma),
        ],
        "Soma VM": lambda _workload, _size, _iterations, soma: [
            sys.executable,
            str(ROOT / "soma_cli.py"),
            "vm",
            str(soma),
        ],
    }


def percentile95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def parse_checksum(output: str) -> float | None:
    matches = CHECKSUM_RE.findall(output)
    return float(matches[-1]) if matches else None


def parse_elapsed_ms(output: str) -> float | None:
    matches = ELAPSED_RE.findall(output)
    return float(matches[-1]) if matches else None


def checksums_match(workload: str, expected: float, actual: float) -> bool:
    if workload == "nbody":
        return math.isclose(expected, actual, rel_tol=1e-8, abs_tol=1e-7)
    return expected == actual


def cpu_name() -> str:
    if platform.system() == "Linux" and Path("/proc/cpuinfo").exists():
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    return platform.processor() or os.environ.get("PROCESSOR_IDENTIFIER", "unknown CPU")


def git_commit() -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True
    )
    return result.stdout.strip() if result.returncode == 0 else "unknown"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "results")
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--workload", action="append", dest="workloads")
    parser.add_argument("--runtime", action="append", dest="runtimes")
    parser.add_argument(
        "--max-sizes",
        type=int,
        help="Run only the first N configured sizes (useful for smoke tests).",
    )
    args = parser.parse_args()

    manifest = json.loads((HERE / "manifest.json").read_text(encoding="utf-8"))
    repetitions = args.repetitions or manifest["repetitions"]
    timeout = manifest["timeout_seconds"]
    runtime_iterations = {
        "Python": 10,
        "JavaScript": 20,
        "Go": 100,
        "Rust": 100,
        "C++": 100,
        "Soma interpreter": 1,
        "Soma JIT": 10,
        "Soma VM": 1,
    }
    output_dir = args.output.resolve()
    build_dir = output_dir / "build"
    generated_dir = output_dir / "generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)

    go_source = LANGUAGES / "go_bench.go"
    rust_source = LANGUAGES / "rust_bench.rs"
    cpp_source = LANGUAGES / "cpp_bench.cpp"
    go_binary = build_dir / ("go_bench.exe" if os.name == "nt" else "go_bench")
    rust_binary = build_dir / ("rust_bench.exe" if os.name == "nt" else "rust_bench")
    cpp_binary = build_dir / ("cpp_bench.exe" if os.name == "nt" else "cpp_bench")

    builds = {
        "Python": {
            "status": "interpreted",
            "duration_ms": 0.0,
            "bytes": (LANGUAGES / "python_bench.py").stat().st_size,
        },
        "JavaScript": {
            "status": "interpreted",
            "duration_ms": 0.0,
            "bytes": (LANGUAGES / "javascript_bench.js").stat().st_size,
        },
        "Soma interpreter": {
            "status": "interpreted",
            "duration_ms": 0.0,
            "bytes": (LANGUAGES / "soma_bench.sm.in").stat().st_size,
        },
        "Soma JIT": {
            "status": "transpiled-per-run",
            "duration_ms": None,
            "bytes": (LANGUAGES / "soma_bench.sm.in").stat().st_size,
        },
        "Soma VM": {
            "status": "compiled-per-run",
            "duration_ms": None,
            "bytes": (LANGUAGES / "soma_bench.sm.in").stat().st_size,
        },
        "Go": build_binary(
            "Go",
            ["go", "build", "-ldflags=-s -w", "-o", str(go_binary), str(go_source)],
            go_binary,
            go_source,
        ),
        "Rust": build_binary(
            "Rust",
            ["rustc", "-C", "opt-level=3", "-C", "debuginfo=0", "-o", str(rust_binary), str(rust_source)],
            rust_binary,
            rust_source,
        ),
        "C++": build_binary(
            "C++",
            ["g++", "-O3", "-std=c++20", "-o", str(cpp_binary), str(cpp_source)],
            cpp_binary,
            cpp_source,
        ),
    }

    commands = runtime_commands(build_dir)
    selected_runtimes = args.runtimes or list(commands)
    selected_workloads = args.workloads or list(manifest["workloads"])
    template = (LANGUAGES / "soma_bench.sm.in").read_text(encoding="utf-8")
    vm_template = (LANGUAGES / "soma_vm_bench.sm.in").read_text(encoding="utf-8")
    measurements: list[dict[str, Any]] = []
    cold_starts: dict[str, Any] = {}

    cold_soma = render_soma(template, generated_dir, "mandelbrot", 1, 0)
    cold_vm = render_soma(vm_template, generated_dir, "mandelbrot", 1, 0)
    for runtime in selected_runtimes:
        if builds[runtime]["status"] in {"unavailable", "failed"}:
            cold_starts[runtime] = {
                "status": "unavailable",
                "reason": builds[runtime].get("reason", "build unavailable"),
            }
            continue
        soma_source = cold_vm if runtime == "Soma VM" else cold_soma
        command = commands[runtime]("mandelbrot", 1, 0, soma_source)
        samples = [run_process(command, timeout) for _ in range(repetitions)]
        successful = [
            sample["duration_ms"]
            for sample in samples
            if sample["status"] == "ok"
            and parse_checksum(sample["stdout"]) == 0.0
        ]
        cold_starts[runtime] = (
            {
                "status": "ok",
                "samples_ms": successful,
                "median_ms": statistics.median(successful),
                "p95_ms": percentile95(successful),
            }
            if len(successful) == repetitions
            else {"status": "failed", "reason": "Cold-start command failed validation."}
        )

    for workload in selected_workloads:
        spec = manifest["workloads"][workload]
        sizes = spec["sizes"][: args.max_sizes] if args.max_sizes else spec["sizes"]
        for size in sizes:
            expected_command = commands["Python"](workload, size, 1, None)
            expected_result = run_process(expected_command, timeout)
            unit_checksum = parse_checksum(expected_result["stdout"])
            if expected_result["status"] != "ok" or unit_checksum is None:
                raise RuntimeError(
                    f"Reference failed for {workload}/{size}: {expected_result}"
                )
            for runtime in selected_runtimes:
                inner_iterations = runtime_iterations[runtime]
                expected = unit_checksum * inner_iterations
                base = {
                    "runtime": runtime,
                    "workload": workload,
                    "size": size,
                    "inner_iterations": inner_iterations,
                    "expected_checksum": expected,
                    "expected_time": spec["expected_time"],
                    "expected_space": spec["expected_space"],
                }
                if runtime == "Soma VM" and not spec["soma_vm"]:
                    measurements.append(
                        {
                            **base,
                            "status": "unsupported",
                            "reason": spec["vm_reason"],
                        }
                    )
                    continue
                if builds[runtime]["status"] in {"unavailable", "failed"}:
                    measurements.append(
                        {
                            **base,
                            "status": "unavailable",
                            "reason": builds[runtime].get("reason", "build unavailable"),
                        }
                    )
                    continue
                runtime_slug = runtime.lower().replace(" ", "_").replace("+", "p")
                rendered_workload = f"{workload}_{runtime_slug}"
                source_template = vm_template if runtime == "Soma VM" else template
                runtime_soma_path = render_soma(
                    source_template,
                    generated_dir,
                    rendered_workload,
                    size,
                    inner_iterations,
                )
                soma_source = runtime_soma_path.read_text(encoding="utf-8").replace(
                    f'workload: "{rendered_workload}"', f'workload: "{workload}"'
                )
                runtime_soma_path.write_text(soma_source, encoding="utf-8")
                command = commands[runtime](
                    workload, size, inner_iterations, runtime_soma_path
                )
                warmup = run_process(command, timeout)
                warmup_checksum = parse_checksum(warmup["stdout"])
                warmup_elapsed = parse_elapsed_ms(warmup["stdout"])
                if (
                    warmup["status"] != "ok"
                    or warmup_checksum is None
                    or warmup_elapsed is None
                    or not checksums_match(workload, expected, warmup_checksum)
                ):
                    measurements.append(
                        {
                            **base,
                            "status": "failed",
                            "reason": (
                                f"warmup status={warmup['status']} "
                                f"checksum={warmup_checksum}; "
                                f"stderr={warmup['stderr'][-800:]}"
                            ),
                        }
                    )
                    continue
                samples = []
                kernel_samples = []
                rss_samples = []
                failure = None
                for _ in range(repetitions):
                    result = run_process(command, timeout)
                    checksum = parse_checksum(result["stdout"])
                    elapsed_ms = parse_elapsed_ms(result["stdout"])
                    if (
                        result["status"] != "ok"
                        or checksum is None
                        or elapsed_ms is None
                        or not checksums_match(workload, expected, checksum)
                    ):
                        failure = (
                            f"status={result['status']} checksum={checksum}; "
                            f"stderr={result['stderr'][-800:]}"
                        )
                        break
                    samples.append(result["duration_ms"])
                    kernel_samples.append(elapsed_ms)
                    if result["peak_rss_kb"] is not None:
                        rss_samples.append(result["peak_rss_kb"])
                if failure:
                    measurements.append({**base, "status": "failed", "reason": failure})
                    continue
                median = statistics.median(samples)
                kernel_median = statistics.median(kernel_samples)
                measurements.append(
                    {
                        **base,
                        "status": "ok",
                        "checksum": warmup_checksum,
                        "samples_ms": samples,
                        "kernel_samples_ms": kernel_samples,
                        "median_ms": median,
                        "p95_ms": percentile95(samples),
                        "mad_ms": statistics.median(
                            [abs(value - median) for value in samples]
                        ),
                        "median_per_iteration_ms": kernel_median / inner_iterations,
                        "p95_per_iteration_ms": percentile95(kernel_samples)
                        / inner_iterations,
                        "median_e2e_per_iteration_ms": median / inner_iterations,
                        "peak_rss_kb": max(rss_samples) if rss_samples else None,
                    }
                )
                print(
                    f"{runtime:18} {workload:12} n={size:<6} "
                    f"{kernel_median / inner_iterations:10.3f} ms/iteration"
                )

    versions = {
        "python": command_version([sys.executable, "--version"]),
        "node": command_version(["node", "--version"]),
        "go": command_version(["go", "version"]),
        "rustc": command_version(["rustc", "--version"]),
        "g++": command_version(["g++", "--version"]),
    }
    data = {
        "schema_version": 1,
        "metadata": {
            "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "commit": git_commit(),
            "platform": platform.platform(),
            "cpu": cpu_name(),
            "logical_cpus": os.cpu_count(),
            "versions": versions,
            "repetitions": repetitions,
            "runtime_iterations": runtime_iterations,
            "timeout_seconds": timeout,
        },
        "manifest": manifest,
        "builds": builds,
        "cold_starts": cold_starts,
        "measurements": measurements,
    }
    raw_path = output_dir / "raw_results.json"
    raw_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    report = generate_report(data)
    (output_dir / "REPORT.md").write_text(report, encoding="utf-8")
    (HERE / "REPORT.md").write_text(report, encoding="utf-8")
    print(f"Wrote {raw_path}")


if __name__ == "__main__":
    main()
