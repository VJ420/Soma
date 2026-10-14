#include <algorithm>
#include <cmath>
#include <cstdint>
#include <functional>
#include <iomanip>
#include <iostream>
#include <memory>
#include <string>
#include <vector>

double nqueens(int n) {
    std::vector<int> columns(n);
    const auto safe = [&](int row, int column) {
        for (int prior_row = 0; prior_row < row; ++prior_row) {
            const int prior_column = columns[prior_row];
            if (prior_column == column || std::abs(prior_column - column) == row - prior_row) {
                return false;
            }
        }
        return true;
    };
    std::function<int(int)> search = [&](int row) {
        if (row == n) return 1;
        int count = 0;
        for (int column = 0; column < n; ++column) {
            if (safe(row, column)) {
                columns[row] = column;
                count += search(row + 1);
            }
        }
        return count;
    };
    return search(0);
}

double mandelbrot(int size) {
    std::int64_t total = 0;
    for (int y = 0; y < size; ++y) {
        const double cy = (static_cast<double>(y) / size) * 2.0 - 1.0;
        for (int x = 0; x < size; ++x) {
            const double cx = (static_cast<double>(x) / size) * 3.0 - 2.0;
            double zx = 0.0, zy = 0.0;
            int iteration = 0;
            while (zx * zx + zy * zy <= 4.0 && iteration < 40) {
                const double next_x = zx * zx - zy * zy + cx;
                zy = 2.0 * zx * zy + cy;
                zx = next_x;
                ++iteration;
            }
            total += iteration;
        }
    }
    return static_cast<double>(total);
}

double matmul(int size) {
    std::uint64_t checksum = 0;
    for (int i = 0; i < size; ++i) {
        for (int j = 0; j < size; ++j) {
            std::uint64_t cell = 0;
            for (int k = 0; k < size; ++k) {
                cell += ((i * 3 + k * 7) % 97) * ((k * 5 + j * 11) % 89);
            }
            checksum += cell;
        }
    }
    return static_cast<double>(checksum);
}

double lcs(int size) {
    std::vector<int> previous(size + 1), current(size + 1);
    for (int i = 1; i <= size; ++i) {
        const int left = (i * 3) % 26;
        current[0] = 0;
        for (int j = 1; j <= size; ++j) {
            current[j] = left == (j * 5) % 26
                ? previous[j - 1] + 1
                : std::max(previous[j], current[j - 1]);
        }
        previous.swap(current);
    }
    return previous[size];
}

double sieve(int limit) {
    std::vector<std::uint8_t> flags(limit + 1, 1);
    flags[0] = flags[1] = 0;
    for (int factor = 2; factor * factor <= limit; ++factor) {
        if (flags[factor]) {
            for (int composite = factor * factor; composite <= limit; composite += factor) {
                flags[composite] = 0;
            }
        }
    }
    std::uint64_t count = 0;
    for (const auto value : flags) count += value;
    return static_cast<double>(count);
}

double nbody(int size) {
    std::vector<double> x(size), y(size), vx(size), vy(size);
    for (int i = 0; i < size; ++i) {
        x[i] = i;
        y[i] = i * 2 + 1;
    }
    for (int step = 0; step < 10; ++step) {
        for (int i = 0; i < size; ++i) {
            double fx = 0.0, fy = 0.0;
            for (int j = 0; j < size; ++j) {
                if (i != j) {
                    const double dx = x[j] - x[i], dy = y[j] - y[i];
                    const double distance_squared = dx * dx + dy * dy + 0.01;
                    const double inverse_distance =
                        1.0 / std::sqrt(distance_squared * distance_squared * distance_squared);
                    fx += dx * inverse_distance;
                    fy += dy * inverse_distance;
                }
            }
            vx[i] += fx * 0.01;
            vy[i] += fy * 0.01;
        }
        for (int i = 0; i < size; ++i) {
            x[i] += vx[i] * 0.01;
            y[i] += vy[i] * 0.01;
        }
    }
    double checksum = 0.0;
    for (int i = 0; i < size; ++i) checksum += x[i] + y[i];
    return checksum;
}

struct Node {
    std::unique_ptr<Node> left;
    std::unique_ptr<Node> right;
};

std::unique_ptr<Node> build_tree(int depth) {
    auto root = std::make_unique<Node>();
    if (depth > 0) {
        root->left = build_tree(depth - 1);
        root->right = build_tree(depth - 1);
    }
    return root;
}

int check_tree(const Node& root) {
    if (!root.left) return 1;
    return 1 + check_tree(*root.left) + check_tree(*root.right);
}

double binarytrees(int depth) {
    return check_tree(*build_tree(depth));
}

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    const std::string workload = argv[1];
    const int size = std::stoi(argv[2]);
    const int iterations = std::stoi(argv[3]);
    const std::vector<std::pair<std::string, double (*)(int)>> functions = {
        {"nqueens", nqueens}, {"mandelbrot", mandelbrot}, {"matmul", matmul},
        {"lcs", lcs}, {"sieve", sieve}, {"nbody", nbody}, {"binarytrees", binarytrees},
    };
    double (*function)(int) = nullptr;
    for (const auto& [name, candidate] : functions) {
        if (name == workload) function = candidate;
    }
    if (!function) return 3;
    double total = 0.0;
    for (int iteration = 0; iteration < iterations; ++iteration) total += function(size);
    std::cout << "CHECKSUM:" << std::fixed << std::setprecision(9) << total << '\n';
}
