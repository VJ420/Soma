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

function bfs(nodeCount) {
  const dist = new Int32Array(nodeCount);
  dist.fill(-1);
  const queue = new Int32Array(nodeCount);
  dist[0] = 0;
  let head = 0, tail = 1;
  while (head < tail) {
    const node = queue[head++];
    const first = (node + 1) % nodeCount;
    const second = (node * 3 + 1) % nodeCount;
    if (dist[first] < 0) {
      dist[first] = dist[node] + 1;
      queue[tail++] = first;
    }
    if (first !== second && dist[second] < 0) {
      dist[second] = dist[node] + 1;
      queue[tail++] = second;
    }
  }
  let checksum = 0;
  for (const value of dist) if (value >= 0) checksum += value;
  return checksum;
}

function mergesort(count) {
  const values = new Array(count);
  const aux = new Array(count);
  let state = 1;
  for (let index = 0; index < count; index++) {
    state = (state * 48271) % 2147483647;
    values[index] = state;
  }
  for (let width = 1; width < count; width *= 2) {
    for (let start = 0; start < count; start += 2 * width) {
      const left = start;
      const mid = Math.min(start + width, count);
      const right = Math.min(start + 2 * width, count);
      let leftIndex = left, rightIndex = mid, writeIndex = left;
      while (leftIndex < mid && rightIndex < right) {
        if (values[leftIndex] <= values[rightIndex]) aux[writeIndex++] = values[leftIndex++];
        else aux[writeIndex++] = values[rightIndex++];
      }
      while (leftIndex < mid) aux[writeIndex++] = values[leftIndex++];
      while (rightIndex < right) aux[writeIndex++] = values[rightIndex++];
      for (let copy = left; copy < right; copy++) values[copy] = aux[copy];
    }
  }
  let checksum = 0;
  for (let index = 0; index < count; index++) {
    checksum = (checksum + values[index] * (index + 1)) % 1000000007;
  }
  return checksum;
}

function stencil(grid) {
  const cells = grid * grid;
  let current = new Float64Array(cells);
  let next = new Float64Array(cells);
  for (let diagonal = 0; diagonal < grid; diagonal++) current[diagonal * grid + diagonal] = 1;
  for (let step = 0; step < 12; step++) {
    for (let y = 0; y < grid; y++) {
      for (let x = 0; x < grid; x++) {
        const center = current[y * grid + x];
        const left = x > 0 ? current[y * grid + (x - 1)] : center;
        const right = x + 1 < grid ? current[y * grid + (x + 1)] : center;
        const up = y > 0 ? current[(y - 1) * grid + x] : center;
        const down = y + 1 < grid ? current[(y + 1) * grid + x] : center;
        next[y * grid + x] = (center + left + right + up + down) / 5;
      }
    }
    const swap = current;
    current = next;
    next = swap;
  }
  let checksum = 0;
  for (let index = 0; index < cells; index++) checksum += current[index] * (index + 1);
  return checksum;
}

const MOD = 1000000007;
const INF = 1000000000;

function dijkstra(n) {
  const dist = new Array(n).fill(INF);
  const used = new Array(n).fill(0);
  dist[0] = 0;
  for (let step = 0; step < n; step++) {
    let selected = 0;
    let best = INF;
    let found = 0;
    for (let index = 0; index < n; index++) {
      if (used[index] === 0 && dist[index] < best) {
        best = dist[index];
        selected = index;
        found = 1;
      }
    }
    if (found === 1) {
      used[selected] = 1;
      for (let vertex = 0; vertex < n; vertex++) {
        if (used[vertex] === 0 && selected !== vertex) {
          const weight = (selected * 17 + vertex * 13) % 97 + 1;
          const candidate = dist[selected] + weight;
          if (candidate < dist[vertex]) dist[vertex] = candidate;
        }
      }
    }
  }
  let checksum = 0;
  for (let index = 0; index < n; index++) checksum = (checksum + dist[index] * (index + 1)) % MOD;
  return checksum;
}

function floyd(n) {
  const dist = new Array(n * n).fill(0);
  for (let row = 0; row < n; row++) {
    for (let column = 0; column < n; column++) {
      dist[row * n + column] = row === column ? 0 : (row * 17 + column * 13) % 97 + 1;
    }
  }
  for (let via = 0; via < n; via++) {
    for (let row = 0; row < n; row++) {
      const viaCost = dist[row * n + via];
      for (let column = 0; column < n; column++) {
        const candidate = viaCost + dist[via * n + column];
        const index = row * n + column;
        if (candidate < dist[index]) dist[index] = candidate;
      }
    }
  }
  let checksum = 0;
  for (let index = 0; index < dist.length; index++) checksum = (checksum + dist[index] * (index + 1)) % MOD;
  return checksum;
}

function knapsack(n) {
  const best = new Array(n + 1).fill(0);
  for (let item = 1; item <= n; item++) {
    const weight = (item % 17) + 1;
    const value = (item * 3) % 23 + 1;
    for (let slot = n; slot >= weight; slot--) {
      const candidate = best[slot - weight] + value;
      if (candidate > best[slot]) best[slot] = candidate;
    }
  }
  let checksum = 0;
  for (let index = 0; index < best.length; index++) checksum = (checksum + best[index] * (index + 1)) % MOD;
  return checksum;
}

function editdist(n) {
  const previous = new Array(n + 1);
  const current = new Array(n + 1).fill(0);
  for (let index = 0; index <= n; index++) previous[index] = index;
  for (let row = 1; row <= n; row++) {
    current[0] = row;
    const leftSymbol = (row * 3) % 26;
    for (let column = 1; column <= n; column++) {
      const cost = leftSymbol === (column * 5) % 26 ? 0 : 1;
      let choice = previous[column] + 1;
      const insert = current[column - 1] + 1;
      const replace = previous[column - 1] + cost;
      if (insert < choice) choice = insert;
      if (replace < choice) choice = replace;
      current[column] = choice;
    }
    for (let index = 0; index <= n; index++) {
      const saved = previous[index];
      previous[index] = current[index];
      current[index] = saved;
    }
  }
  let checksum = 0;
  for (let index = 0; index <= n; index++) checksum = (checksum + previous[index] * (index + 1)) % MOD;
  return checksum;
}

function lis(n) {
  const tails = new Array(n).fill(0);
  let length = 0;
  let state = 1;
  for (let sample = 0; sample < n; sample++) {
    state = (state * 48271) % 2147483647;
    const value = state % 1000003;
    let low = 0;
    let high = length;
    while (low < high) {
      const mid = Math.floor((low + high) / 2);
      if (tails[mid] < value) low = mid + 1;
      else high = mid;
    }
    if (low === length) {
      tails[length] = value;
      length += 1;
    } else tails[low] = value;
  }
  let checksum = 0;
  for (let index = 0; index < length; index++) checksum = (checksum + tails[index] * (index + 1)) % MOD;
  return checksum;
}

function life(n) {
  const cells = n * n;
  let current = new Array(cells).fill(0);
  let next = new Array(cells).fill(0);
  for (let index = 0; index < n; index++) {
    current[index * n + index] = 1;
    current[index * n + ((index * 3) % n)] = 1;
  }
  for (let step = 0; step < 12; step++) {
    for (let y = 0; y < n; y++) {
      for (let x = 0; x < n; x++) {
        let neighbors = 0;
        if (y > 0 && x > 0 && current[(y - 1) * n + (x - 1)] === 1) neighbors += 1;
        if (y > 0 && current[(y - 1) * n + x] === 1) neighbors += 1;
        if (y > 0 && x + 1 < n && current[(y - 1) * n + (x + 1)] === 1) neighbors += 1;
        if (x > 0 && current[y * n + (x - 1)] === 1) neighbors += 1;
        if (x + 1 < n && current[y * n + (x + 1)] === 1) neighbors += 1;
        if (y + 1 < n && x > 0 && current[(y + 1) * n + (x - 1)] === 1) neighbors += 1;
        if (y + 1 < n && current[(y + 1) * n + x] === 1) neighbors += 1;
        if (y + 1 < n && x + 1 < n && current[(y + 1) * n + (x + 1)] === 1) neighbors += 1;
        const alive = current[y * n + x];
        let born = 0;
        if (alive === 1 && (neighbors === 2 || neighbors === 3)) born = 1;
        if (alive === 0 && neighbors === 3) born = 1;
        next[y * n + x] = born;
      }
    }
    const swap = current;
    current = next;
    next = swap;
  }
  let checksum = 0;
  for (let index = 0; index < cells; index++) checksum += current[index] * (index + 1);
  return checksum;
}

function histogram(sampleCount) {
  const bins = new Array(1024).fill(0);
  let state = 1;
  for (let sample = 0; sample < sampleCount; sample++) {
    state = (state * 48271) % 2147483647;
    bins[state % 1024] += 1;
  }
  let checksum = 0;
  for (let index = 0; index < 1024; index++) checksum += (index + 1) * bins[index];
  return checksum;
}

const workloads = { nqueens, mandelbrot, matmul, lcs, sieve, nbody, binarytrees, bfs, sort: mergesort, stencil, histogram, dijkstra, floyd, knapsack, editdist, lis, life };
const [workload, sizeText, iterationsText] = process.argv.slice(2);
let total = 0.0;
const started = performance.now();
for (let iteration = 0; iteration < Number(iterationsText); iteration++) {
  total += workloads[workload](Number(sizeText));
}
const elapsedMs = performance.now() - started;
console.log(`CHECKSUM:${total.toFixed(9)}`);
console.log(`ELAPSED_MS:${elapsedMs.toFixed(9)}`);
