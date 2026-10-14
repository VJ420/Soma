"""Deterministic reference workloads for the Soma extreme benchmark suite."""

from __future__ import annotations

import math
import sys
import time


def nqueens(n: int) -> int:
    columns = [0] * n

    def safe(row: int, column: int) -> bool:
        for prior_row in range(row):
            prior_column = columns[prior_row]
            if prior_column == column or abs(prior_column - column) == row - prior_row:
                return False
        return True

    def search(row: int) -> int:
        if row == n:
            return 1
        count = 0
        for column in range(n):
            if safe(row, column):
                columns[row] = column
                count += search(row + 1)
        return count

    return search(0)


def mandelbrot(size: int) -> int:
    total = 0
    max_iter = 40
    for y in range(size):
        cy = (y / size) * 2.0 - 1.0
        for x in range(size):
            cx = (x / size) * 3.0 - 2.0
            zx = zy = 0.0
            iteration = 0
            while zx * zx + zy * zy <= 4.0 and iteration < max_iter:
                zx, zy = zx * zx - zy * zy + cx, 2.0 * zx * zy + cy
                iteration += 1
            total += iteration
    return total


def matmul(size: int) -> int:
    checksum = 0
    for i in range(size):
        for j in range(size):
            cell = 0
            for k in range(size):
                cell += ((i * 3 + k * 7) % 97) * ((k * 5 + j * 11) % 89)
            checksum += cell
    return checksum


def lcs(size: int) -> int:
    previous = [0] * (size + 1)
    current = [0] * (size + 1)
    for i in range(1, size + 1):
        left = (i * 3) % 26
        current[0] = 0
        for j in range(1, size + 1):
            if left == (j * 5) % 26:
                current[j] = previous[j - 1] + 1
            else:
                current[j] = max(previous[j], current[j - 1])
        previous, current = current, previous
    return previous[size]


def sieve(limit: int) -> int:
    flags = [True] * (limit + 1)
    flags[0] = flags[1] = False
    factor = 2
    while factor * factor <= limit:
        if flags[factor]:
            composite = factor * factor
            while composite <= limit:
                flags[composite] = False
                composite += factor
        factor += 1
    return sum(1 for value in flags if value)


def nbody(size: int) -> float:
    steps = 10
    dt = 0.01
    x = [float(i) for i in range(size)]
    y = [float(i * 2 + 1) for i in range(size)]
    vx = [0.0] * size
    vy = [0.0] * size
    for _ in range(steps):
        for i in range(size):
            fx = fy = 0.0
            for j in range(size):
                if i != j:
                    dx = x[j] - x[i]
                    dy = y[j] - y[i]
                    distance_squared = dx * dx + dy * dy + 0.01
                    inverse_distance = 1.0 / math.sqrt(
                        distance_squared * distance_squared * distance_squared
                    )
                    fx += dx * inverse_distance
                    fy += dy * inverse_distance
            vx[i] += fx * dt
            vy[i] += fy * dt
        for i in range(size):
            x[i] += vx[i] * dt
            y[i] += vy[i] * dt
    return sum(x) + sum(y)


class Node:
    __slots__ = ("left", "right")

    def __init__(self, left: Node | None, right: Node | None) -> None:
        self.left = left
        self.right = right

    def check(self) -> int:
        if self.left is None:
            return 1
        return 1 + self.left.check() + self.right.check()


def bfs(node_count: int) -> int:
    dist = [-1] * node_count
    queue = [0] * node_count
    dist[0] = 0
    head = 0
    tail = 1
    while head < tail:
        node = queue[head]
        head += 1
        first = (node + 1) % node_count
        second = (node * 3 + 1) % node_count
        if dist[first] < 0:
            dist[first] = dist[node] + 1
            queue[tail] = first
            tail += 1
        if first != second and dist[second] < 0:
            dist[second] = dist[node] + 1
            queue[tail] = second
            tail += 1
    return sum(value for value in dist if value >= 0)


def mergesort(count: int) -> int:
    state = 1
    values = [0] * count
    for index in range(count):
        state = (state * 48271) % 2147483647
        values[index] = state
    aux = [0] * count
    width = 1
    while width < count:
        start = 0
        while start < count:
            left = start
            mid = min(start + width, count)
            right = min(start + 2 * width, count)
            left_index, right_index, write_index = left, mid, left
            while left_index < mid and right_index < right:
                if values[left_index] <= values[right_index]:
                    aux[write_index] = values[left_index]
                    left_index += 1
                else:
                    aux[write_index] = values[right_index]
                    right_index += 1
                write_index += 1
            while left_index < mid:
                aux[write_index] = values[left_index]
                left_index += 1
                write_index += 1
            while right_index < right:
                aux[write_index] = values[right_index]
                right_index += 1
                write_index += 1
            for copy_index in range(left, right):
                values[copy_index] = aux[copy_index]
            start += 2 * width
        width *= 2
    checksum = 0
    for index, value in enumerate(values):
        checksum = (checksum + value * (index + 1)) % 1000000007
    return checksum


def stencil(grid: int) -> float:
    cell_count = grid * grid
    current = [0.0] * cell_count
    nxt = [0.0] * cell_count
    for diagonal in range(grid):
        current[diagonal * grid + diagonal] = 1.0
    for _ in range(12):
        for y in range(grid):
            for x in range(grid):
                center = current[y * grid + x]
                left = current[y * grid + (x - 1)] if x > 0 else center
                right = current[y * grid + (x + 1)] if x + 1 < grid else center
                up = current[(y - 1) * grid + x] if y > 0 else center
                down = current[(y + 1) * grid + x] if y + 1 < grid else center
                nxt[y * grid + x] = (center + left + right + up + down) / 5.0
        current, nxt = nxt, current
    return sum(value * (index + 1) for index, value in enumerate(current))


MOD = 1_000_000_007
INF = 1_000_000_000


def dijkstra(n: int) -> int:
    dist = [INF] * n
    used = [0] * n
    dist[0] = 0
    for _ in range(n):
        selected = 0
        best = INF
        found = 0
        for index in range(n):
            if used[index] == 0 and dist[index] < best:
                best = dist[index]
                selected = index
                found = 1
        if found == 1:
            used[selected] = 1
            for vertex in range(n):
                if used[vertex] == 0 and selected != vertex:
                    weight = (selected * 17 + vertex * 13) % 97 + 1
                    candidate = dist[selected] + weight
                    if candidate < dist[vertex]:
                        dist[vertex] = candidate
    checksum = 0
    for index, value in enumerate(dist):
        checksum = (checksum + value * (index + 1)) % MOD
    return checksum


def floyd(n: int) -> int:
    dist = [0] * (n * n)
    for row in range(n):
        for column in range(n):
            if row == column:
                dist[row * n + column] = 0
            else:
                dist[row * n + column] = (row * 17 + column * 13) % 97 + 1
    for via in range(n):
        for row in range(n):
            via_cost = dist[row * n + via]
            for column in range(n):
                candidate = via_cost + dist[via * n + column]
                index = row * n + column
                if candidate < dist[index]:
                    dist[index] = candidate
    checksum = 0
    for index, value in enumerate(dist):
        checksum = (checksum + value * (index + 1)) % MOD
    return checksum


def knapsack(n: int) -> int:
    best = [0] * (n + 1)
    for item in range(1, n + 1):
        weight = (item % 17) + 1
        value = (item * 3) % 23 + 1
        slot = n
        while slot >= weight:
            candidate = best[slot - weight] + value
            if candidate > best[slot]:
                best[slot] = candidate
            slot -= 1
    checksum = 0
    for index, value in enumerate(best):
        checksum = (checksum + value * (index + 1)) % MOD
    return checksum


def editdist(n: int) -> int:
    previous = list(range(n + 1))
    current = [0] * (n + 1)
    for row in range(1, n + 1):
        current[0] = row
        left_symbol = (row * 3) % 26
        for column in range(1, n + 1):
            cost = 0 if left_symbol == (column * 5) % 26 else 1
            delete = previous[column] + 1
            insert = current[column - 1] + 1
            replace = previous[column - 1] + cost
            choice = delete
            if insert < choice:
                choice = insert
            if replace < choice:
                choice = replace
            current[column] = choice
        previous, current = current, previous
    checksum = 0
    for index, value in enumerate(previous):
        checksum = (checksum + value * (index + 1)) % MOD
    return checksum


def lis(n: int) -> int:
    tails = [0] * n
    length = 0
    state = 1
    for _ in range(n):
        state = (state * 48271) % 2147483647
        value = state % 1000003
        low = 0
        high = length
        while low < high:
            mid = (low + high) // 2
            if tails[mid] < value:
                low = mid + 1
            else:
                high = mid
        if low == length:
            tails[length] = value
            length += 1
        else:
            tails[low] = value
    checksum = 0
    for index in range(length):
        checksum = (checksum + tails[index] * (index + 1)) % MOD
    return checksum


def life(n: int) -> int:
    cells = n * n
    current = [0] * cells
    nxt = [0] * cells
    for index in range(n):
        current[index * n + index] = 1
        current[index * n + ((index * 3) % n)] = 1
    for _ in range(12):
        for y in range(n):
            for x in range(n):
                neighbors = 0
                if y > 0 and x > 0 and current[(y - 1) * n + (x - 1)] == 1:
                    neighbors += 1
                if y > 0 and current[(y - 1) * n + x] == 1:
                    neighbors += 1
                if y > 0 and x + 1 < n and current[(y - 1) * n + (x + 1)] == 1:
                    neighbors += 1
                if x > 0 and current[y * n + (x - 1)] == 1:
                    neighbors += 1
                if x + 1 < n and current[y * n + (x + 1)] == 1:
                    neighbors += 1
                if y + 1 < n and x > 0 and current[(y + 1) * n + (x - 1)] == 1:
                    neighbors += 1
                if y + 1 < n and current[(y + 1) * n + x] == 1:
                    neighbors += 1
                if y + 1 < n and x + 1 < n and current[(y + 1) * n + (x + 1)] == 1:
                    neighbors += 1
                alive = current[y * n + x]
                born = 0
                if alive == 1 and (neighbors == 2 or neighbors == 3):
                    born = 1
                if alive == 0 and neighbors == 3:
                    born = 1
                nxt[y * n + x] = born
        current, nxt = nxt, current
    checksum = 0
    for index, value in enumerate(current):
        checksum += value * (index + 1)
    return checksum


def histogram(sample_count: int) -> int:
    bins = [0] * 1024
    state = 1
    for _ in range(sample_count):
        state = (state * 48271) % 2147483647
        bins[state % 1024] += 1
    return sum((index + 1) * count for index, count in enumerate(bins))


def binarytrees(depth: int) -> int:
    def build(level: int) -> Node:
        if level <= 0:
            return Node(None, None)
        return Node(build(level - 1), build(level - 1))

    return build(depth).check()


WORKLOADS = {
    "nqueens": nqueens,
    "mandelbrot": mandelbrot,
    "matmul": matmul,
    "lcs": lcs,
    "sieve": sieve,
    "nbody": nbody,
    "binarytrees": binarytrees,
    "bfs": bfs,
    "sort": mergesort,
    "stencil": stencil,
    "histogram": histogram,
    "dijkstra": dijkstra,
    "floyd": floyd,
    "knapsack": knapsack,
    "editdist": editdist,
    "lis": lis,
    "life": life,
}


def main() -> None:
    workload, size_text, iterations_text = sys.argv[1:4]
    total = 0.0
    started = time.perf_counter()
    for _ in range(int(iterations_text)):
        total += float(WORKLOADS[workload](int(size_text)))
    elapsed_ms = (time.perf_counter() - started) * 1000.0
    print(f"CHECKSUM:{total:.9f}")
    print(f"ELAPSED_MS:{elapsed_ms:.9f}")


if __name__ == "__main__":
    main()
