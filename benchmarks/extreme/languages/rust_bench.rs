use std::cmp::min;
use std::env;
use std::time::Instant;

fn nqueens(n: usize) -> f64 {
    fn safe(columns: &[usize], row: usize, column: usize) -> bool {
        for (prior_row, &prior_column) in columns.iter().take(row).enumerate() {
            if prior_column == column || prior_column.abs_diff(column) == row - prior_row {
                return false;
            }
        }
        true
    }
    fn search(columns: &mut [usize], row: usize, n: usize) -> usize {
        if row == n {
            return 1;
        }
        let mut count = 0;
        for column in 0..n {
            if safe(columns, row, column) {
                columns[row] = column;
                count += search(columns, row + 1, n);
            }
        }
        count
    }
    search(&mut vec![0; n], 0, n) as f64
}

fn mandelbrot(size: usize) -> f64 {
    let mut total = 0;
    for y in 0..size {
        let cy = (y as f64 / size as f64) * 2.0 - 1.0;
        for x in 0..size {
            let cx = (x as f64 / size as f64) * 3.0 - 2.0;
            let (mut zx, mut zy, mut iteration) = (0.0, 0.0, 0);
            while zx * zx + zy * zy <= 4.0 && iteration < 40 {
                let next_x = zx * zx - zy * zy + cx;
                zy = 2.0 * zx * zy + cy;
                zx = next_x;
                iteration += 1;
            }
            total += iteration;
        }
    }
    total as f64
}

fn matmul(size: usize) -> f64 {
    let mut checksum: u64 = 0;
    for i in 0..size {
        for j in 0..size {
            let mut cell = 0;
            for k in 0..size {
                cell += ((i * 3 + k * 7) % 97) * ((k * 5 + j * 11) % 89);
            }
            checksum += cell as u64;
        }
    }
    checksum as f64
}

fn lcs(size: usize) -> f64 {
    let mut previous = vec![0; size + 1];
    let mut current = vec![0; size + 1];
    for i in 1..=size {
        let left = (i * 3) % 26;
        current[0] = 0;
        for j in 1..=size {
            current[j] = if left == (j * 5) % 26 {
                previous[j - 1] + 1
            } else {
                previous[j].max(current[j - 1])
            };
        }
        std::mem::swap(&mut previous, &mut current);
    }
    previous[size] as f64
}

fn sieve(limit: usize) -> f64 {
    let mut flags = vec![true; limit + 1];
    flags[0] = false;
    flags[1] = false;
    let mut factor = 2;
    while factor * factor <= limit {
        if flags[factor] {
            let mut composite = factor * factor;
            while composite <= limit {
                flags[composite] = false;
                composite += factor;
            }
        }
        factor += 1;
    }
    flags.iter().filter(|&&value| value).count() as f64
}

fn nbody(size: usize) -> f64 {
    let mut x: Vec<f64> = (0..size).map(|i| i as f64).collect();
    let mut y: Vec<f64> = (0..size).map(|i| (i * 2 + 1) as f64).collect();
    let mut vx = vec![0.0; size];
    let mut vy = vec![0.0; size];
    for _ in 0..10 {
        for i in 0..size {
            let (mut fx, mut fy) = (0.0, 0.0);
            for j in 0..size {
                if i != j {
                    let (dx, dy) = (x[j] - x[i], y[j] - y[i]);
                    let distance_squared = dx * dx + dy * dy + 0.01;
                    let inverse_distance =
                        1.0 / (distance_squared * distance_squared * distance_squared).sqrt();
                    fx += dx * inverse_distance;
                    fy += dy * inverse_distance;
                }
            }
            vx[i] += fx * 0.01;
            vy[i] += fy * 0.01;
        }
        for i in 0..size {
            x[i] += vx[i] * 0.01;
            y[i] += vy[i] * 0.01;
        }
    }
    x.iter().sum::<f64>() + y.iter().sum::<f64>()
}

struct Node {
    left: Option<Box<Node>>,
    right: Option<Box<Node>>,
}

fn build_tree(depth: usize) -> Node {
    if depth == 0 {
        Node { left: None, right: None }
    } else {
        Node {
            left: Some(Box::new(build_tree(depth - 1))),
            right: Some(Box::new(build_tree(depth - 1))),
        }
    }
}

fn check_tree(root: &Node) -> usize {
    match (&root.left, &root.right) {
        (Some(left), Some(right)) => 1 + check_tree(left) + check_tree(right),
        _ => 1,
    }
}

fn binarytrees(depth: usize) -> f64 {
    check_tree(&build_tree(depth)) as f64
}

fn bfs(node_count: usize) -> f64 {
    let mut dist = vec![-1i64; node_count];
    let mut queue = vec![0usize; node_count];
    dist[0] = 0;
    let mut head = 0usize;
    let mut tail = 1usize;
    while head < tail {
        let node = queue[head];
        head += 1;
        let first = (node + 1) % node_count;
        let second = (node * 3 + 1) % node_count;
        if dist[first] < 0 {
            dist[first] = dist[node] + 1;
            queue[tail] = first;
            tail += 1;
        }
        if first != second && dist[second] < 0 {
            dist[second] = dist[node] + 1;
            queue[tail] = second;
            tail += 1;
        }
    }
    dist.into_iter().filter(|value| *value >= 0).sum::<i64>() as f64
}

fn sort_checksum(count: usize) -> f64 {
    let mut values = vec![0i64; count];
    let mut aux = vec![0i64; count];
    let mut state = 1i64;
    for index in 0..count {
        state = (state * 48271) % 2147483647;
        values[index] = state;
    }
    let mut width = 1usize;
    while width < count {
        let mut start = 0usize;
        while start < count {
            let left = start;
            let mid = min(start + width, count);
            let right = min(start + width + width, count);
            let mut left_index = left;
            let mut right_index = mid;
            let mut write_index = left;
            while left_index < mid && right_index < right {
                if values[left_index] <= values[right_index] {
                    aux[write_index] = values[left_index];
                    left_index += 1;
                } else {
                    aux[write_index] = values[right_index];
                    right_index += 1;
                }
                write_index += 1;
            }
            while left_index < mid {
                aux[write_index] = values[left_index];
                left_index += 1;
                write_index += 1;
            }
            while right_index < right {
                aux[write_index] = values[right_index];
                right_index += 1;
                write_index += 1;
            }
            for copy in left..right {
                values[copy] = aux[copy];
            }
            start += width + width;
        }
        width += width;
    }
    let mut checksum = 0i64;
    for (index, value) in values.iter().enumerate() {
        checksum = (checksum + value * (index as i64 + 1)) % 1000000007;
    }
    checksum as f64
}

fn stencil(grid: usize) -> f64 {
    let cells = grid * grid;
    let mut current = vec![0.0f64; cells];
    let mut next = vec![0.0f64; cells];
    for diagonal in 0..grid {
        current[diagonal * grid + diagonal] = 1.0;
    }
    for _ in 0..12 {
        for y in 0..grid {
            for x in 0..grid {
                let center = current[y * grid + x];
                let left = if x > 0 { current[y * grid + (x - 1)] } else { center };
                let right = if x + 1 < grid { current[y * grid + (x + 1)] } else { center };
                let up = if y > 0 { current[(y - 1) * grid + x] } else { center };
                let down = if y + 1 < grid { current[(y + 1) * grid + x] } else { center };
                next[y * grid + x] = (center + left + right + up + down) / 5.0;
            }
        }
        std::mem::swap(&mut current, &mut next);
    }
    current.iter().enumerate().map(|(index, value)| value * (index as f64 + 1.0)).sum()
}

fn dijkstra(n: usize) -> f64 {
    const INF: i64 = 1_000_000_000;
    const MOD: i64 = 1_000_000_007;
    let mut dist = vec![INF; n];
    let mut used = vec![0i32; n];
    dist[0] = 0;
    for _ in 0..n {
        let mut selected = 0usize;
        let mut best = INF;
        let mut found = 0;
        for index in 0..n {
            if used[index] == 0 && dist[index] < best {
                best = dist[index];
                selected = index;
                found = 1;
            }
        }
        if found == 1 {
            used[selected] = 1;
            for vertex in 0..n {
                if used[vertex] == 0 && selected != vertex {
                    let weight = ((selected * 17 + vertex * 13) % 97 + 1) as i64;
                    let candidate = dist[selected] + weight;
                    if candidate < dist[vertex] {
                        dist[vertex] = candidate;
                    }
                }
            }
        }
    }
    let mut checksum = 0i64;
    for (index, value) in dist.iter().enumerate() {
        checksum = (checksum + value * (index as i64 + 1)) % MOD;
    }
    checksum as f64
}

fn floyd(n: usize) -> f64 {
    const MOD: i64 = 1_000_000_007;
    let mut dist = vec![0i64; n * n];
    for row in 0..n {
        for column in 0..n {
            dist[row * n + column] = if row == column {
                0
            } else {
                ((row * 17 + column * 13) % 97 + 1) as i64
            };
        }
    }
    for via in 0..n {
        for row in 0..n {
            let via_cost = dist[row * n + via];
            for column in 0..n {
                let candidate = via_cost + dist[via * n + column];
                let index = row * n + column;
                if candidate < dist[index] {
                    dist[index] = candidate;
                }
            }
        }
    }
    let mut checksum = 0i64;
    for (index, value) in dist.iter().enumerate() {
        checksum = (checksum + value * (index as i64 + 1)) % MOD;
    }
    checksum as f64
}

fn knapsack(n: usize) -> f64 {
    const MOD: i64 = 1_000_000_007;
    let mut best = vec![0i64; n + 1];
    for item in 1..=n {
        let weight = (item % 17) + 1;
        let value = ((item * 3) % 23 + 1) as i64;
        for slot in (weight..=n).rev() {
            let candidate = best[slot - weight] + value;
            if candidate > best[slot] {
                best[slot] = candidate;
            }
        }
    }
    let mut checksum = 0i64;
    for (index, value) in best.iter().enumerate() {
        checksum = (checksum + value * (index as i64 + 1)) % MOD;
    }
    checksum as f64
}

fn editdist(n: usize) -> f64 {
    const MOD: i64 = 1_000_000_007;
    let mut previous: Vec<i64> = (0..=n).map(|index| index as i64).collect();
    let mut current = vec![0i64; n + 1];
    for row in 1..=n {
        current[0] = row as i64;
        let left_symbol = (row * 3) % 26;
        for column in 1..=n {
            let cost = if left_symbol == (column * 5) % 26 { 0 } else { 1 };
            let mut choice = previous[column] + 1;
            let insert = current[column - 1] + 1;
            let replace = previous[column - 1] + cost;
            if insert < choice {
                choice = insert;
            }
            if replace < choice {
                choice = replace;
            }
            current[column] = choice;
        }
        std::mem::swap(&mut previous, &mut current);
    }
    let mut checksum = 0i64;
    for (index, value) in previous.iter().enumerate() {
        checksum = (checksum + value * (index as i64 + 1)) % MOD;
    }
    checksum as f64
}

fn lis(n: usize) -> f64 {
    const MOD: i64 = 1_000_000_007;
    let mut tails = vec![0i64; n];
    let mut length = 0usize;
    let mut state = 1i64;
    for _ in 0..n {
        state = (state * 48271) % 2147483647;
        let value = state % 1_000_003;
        let mut low = 0usize;
        let mut high = length;
        while low < high {
            let mid = (low + high) / 2;
            if tails[mid] < value {
                low = mid + 1;
            } else {
                high = mid;
            }
        }
        if low == length {
            tails[length] = value;
            length += 1;
        } else {
            tails[low] = value;
        }
    }
    let mut checksum = 0i64;
    for index in 0..length {
        checksum = (checksum + tails[index] * (index as i64 + 1)) % MOD;
    }
    checksum as f64
}

fn life(n: usize) -> f64 {
    let cells = n * n;
    let mut current = vec![0i32; cells];
    let mut next = vec![0i32; cells];
    for index in 0..n {
        current[index * n + index] = 1;
        current[index * n + ((index * 3) % n)] = 1;
    }
    for _ in 0..12 {
        for y in 0..n {
            for x in 0..n {
                let mut neighbors = 0;
                if y > 0 && x > 0 && current[(y - 1) * n + (x - 1)] == 1 {
                    neighbors += 1;
                }
                if y > 0 && current[(y - 1) * n + x] == 1 {
                    neighbors += 1;
                }
                if y > 0 && x + 1 < n && current[(y - 1) * n + (x + 1)] == 1 {
                    neighbors += 1;
                }
                if x > 0 && current[y * n + (x - 1)] == 1 {
                    neighbors += 1;
                }
                if x + 1 < n && current[y * n + (x + 1)] == 1 {
                    neighbors += 1;
                }
                if y + 1 < n && x > 0 && current[(y + 1) * n + (x - 1)] == 1 {
                    neighbors += 1;
                }
                if y + 1 < n && current[(y + 1) * n + x] == 1 {
                    neighbors += 1;
                }
                if y + 1 < n && x + 1 < n && current[(y + 1) * n + (x + 1)] == 1 {
                    neighbors += 1;
                }
                let alive = current[y * n + x];
                let mut born = 0;
                if alive == 1 && (neighbors == 2 || neighbors == 3) {
                    born = 1;
                }
                if alive == 0 && neighbors == 3 {
                    born = 1;
                }
                next[y * n + x] = born;
            }
        }
        std::mem::swap(&mut current, &mut next);
    }
    current.iter().enumerate().map(|(index, value)| *value as f64 * (index as f64 + 1.0)).sum()
}

fn histogram(sample_count: usize) -> f64 {
    let mut bins = vec![0i64; 1024];
    let mut state = 1i64;
    for _ in 0..sample_count {
        state = (state * 48271) % 2147483647;
        let slot = (state % 1024) as usize;
        bins[slot] += 1;
    }
    bins.iter().enumerate().map(|(index, count)| (index as i64 + 1) * count).sum::<i64>() as f64
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let workload = args[1].as_str();
    let size: usize = args[2].parse().unwrap();
    let iterations: usize = args[3].parse().unwrap();
    let function: fn(usize) -> f64 = match workload {
        "nqueens" => nqueens,
        "mandelbrot" => mandelbrot,
        "matmul" => matmul,
        "lcs" => lcs,
        "sieve" => sieve,
        "nbody" => nbody,
        "binarytrees" => binarytrees,
        "bfs" => bfs,
        "sort" => sort_checksum,
        "stencil" => stencil,
        "histogram" => histogram,
        "dijkstra" => dijkstra,
        "floyd" => floyd,
        "knapsack" => knapsack,
        "editdist" => editdist,
        "lis" => lis,
        "life" => life,
        _ => panic!("unknown workload"),
    };
    let started = Instant::now();
    let total: f64 = (0..iterations).map(|_| function(size)).sum();
    let elapsed_ms = started.elapsed().as_secs_f64() * 1000.0;
    println!("CHECKSUM:{total:.9}");
    println!("ELAPSED_MS:{elapsed_ms:.9}");
}
