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
        _ => panic!("unknown workload"),
    };
    let started = Instant::now();
    let total: f64 = (0..iterations).map(|_| function(size)).sum();
    let elapsed_ms = started.elapsed().as_secs_f64() * 1000.0;
    println!("CHECKSUM:{total:.9}");
    println!("ELAPSED_MS:{elapsed_ms:.9}");
}
