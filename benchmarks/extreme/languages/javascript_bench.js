"use strict";

const { performance } = require("perf_hooks");

function nqueens(n) {
  const columns = new Int32Array(n);
  function safe(row, column) {
    for (let priorRow = 0; priorRow < row; priorRow++) {
      const priorColumn = columns[priorRow];
      if (priorColumn === column || Math.abs(priorColumn - column) === row - priorRow) return false;
    }
    return true;
  }
  function search(row) {
    if (row === n) return 1;
    let count = 0;
    for (let column = 0; column < n; column++) {
      if (safe(row, column)) {
        columns[row] = column;
        count += search(row + 1);
      }
    }
    return count;
  }
  return search(0);
}

function mandelbrot(size) {
  let total = 0;
  const maxIter = 40;
  for (let y = 0; y < size; y++) {
    const cy = (y / size) * 2.0 - 1.0;
    for (let x = 0; x < size; x++) {
      const cx = (x / size) * 3.0 - 2.0;
      let zx = 0.0, zy = 0.0, iteration = 0;
      while (zx * zx + zy * zy <= 4.0 && iteration < maxIter) {
        const nextX = zx * zx - zy * zy + cx;
        zy = 2.0 * zx * zy + cy;
        zx = nextX;
        iteration++;
      }
      total += iteration;
    }
  }
  return total;
}

function matmul(size) {
  let checksum = 0;
  for (let i = 0; i < size; i++) {
    for (let j = 0; j < size; j++) {
      let cell = 0;
      for (let k = 0; k < size; k++) {
        cell += ((i * 3 + k * 7) % 97) * ((k * 5 + j * 11) % 89);
      }
      checksum += cell;
    }
  }
  return checksum;
}

function lcs(size) {
  let previous = new Int32Array(size + 1);
  let current = new Int32Array(size + 1);
  for (let i = 1; i <= size; i++) {
    const left = (i * 3) % 26;
    current[0] = 0;
    for (let j = 1; j <= size; j++) {
      current[j] = left === (j * 5) % 26
        ? previous[j - 1] + 1
        : Math.max(previous[j], current[j - 1]);
    }
    const swap = previous;
    previous = current;
    current = swap;
  }
  return previous[size];
}

function sieve(limit) {
  const flags = new Uint8Array(limit + 1);
  flags.fill(1);
  flags[0] = 0;
  flags[1] = 0;
  for (let factor = 2; factor * factor <= limit; factor++) {
    if (flags[factor]) {
      for (let composite = factor * factor; composite <= limit; composite += factor) {
        flags[composite] = 0;
      }
    }
  }
  let count = 0;
  for (const value of flags) count += value;
  return count;
}

function nbody(size) {
  const steps = 10, dt = 0.01;
  const x = new Float64Array(size), y = new Float64Array(size);
  const vx = new Float64Array(size), vy = new Float64Array(size);
  for (let i = 0; i < size; i++) {
    x[i] = i;
    y[i] = i * 2 + 1;
  }
  for (let step = 0; step < steps; step++) {
    for (let i = 0; i < size; i++) {
      let fx = 0.0, fy = 0.0;
      for (let j = 0; j < size; j++) {
        if (i !== j) {
          const dx = x[j] - x[i], dy = y[j] - y[i];
          const distanceSquared = dx * dx + dy * dy + 0.01;
          const inverseDistance = 1.0 / Math.sqrt(distanceSquared * distanceSquared * distanceSquared);
          fx += dx * inverseDistance;
          fy += dy * inverseDistance;
        }
      }
      vx[i] += fx * dt;
      vy[i] += fy * dt;
    }
    for (let i = 0; i < size; i++) {
      x[i] += vx[i] * dt;
      y[i] += vy[i] * dt;
    }
  }
  let checksum = 0.0;
  for (let i = 0; i < size; i++) checksum += x[i] + y[i];
  return checksum;
}

function binarytrees(depth) {
  function build(level) {
    if (level <= 0) return { left: null, right: null };
    return { left: build(level - 1), right: build(level - 1) };
  }
  function check(node) {
    if (node.left === null) return 1;
    return 1 + check(node.left) + check(node.right);
  }
  return check(build(depth));
}

const workloads = { nqueens, mandelbrot, matmul, lcs, sieve, nbody, binarytrees };
const [workload, sizeText, iterationsText] = process.argv.slice(2);
let total = 0.0;
const started = performance.now();
for (let iteration = 0; iteration < Number(iterationsText); iteration++) {
  total += workloads[workload](Number(sizeText));
}
const elapsedMs = performance.now() - started;
console.log(`CHECKSUM:${total.toFixed(9)}`);
console.log(`ELAPSED_MS:${elapsedMs.toFixed(9)}`);
