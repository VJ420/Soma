#include <algorithm>
#include <chrono>
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

double bfs(int node_count) {
    std::vector<int> dist(node_count, -1), queue(node_count);
    dist[0] = 0;
    int head = 0, tail = 1;
    while (head < tail) {
        const int node = queue[head++];
        const int first = (node + 1) % node_count;
        const int second = (node * 3 + 1) % node_count;
        if (dist[first] < 0) {
            dist[first] = dist[node] + 1;
            queue[tail++] = first;
        }
        if (first != second && dist[second] < 0) {
            dist[second] = dist[node] + 1;
            queue[tail++] = second;
        }
    }
    std::int64_t checksum = 0;
    for (const int value : dist) if (value >= 0) checksum += value;
    return static_cast<double>(checksum);
}

double sort_checksum(int count) {
    std::vector<std::int64_t> values(count), aux(count);
    std::int64_t state = 1;
    for (int index = 0; index < count; ++index) {
        state = (state * 48271) % 2147483647LL;
        values[index] = state;
    }
    for (int width = 1; width < count; width *= 2) {
        for (int start = 0; start < count; start += 2 * width) {
            const int left = start;
            const int mid = std::min(start + width, count);
            const int right = std::min(start + 2 * width, count);
            int left_index = left, right_index = mid, write_index = left;
            while (left_index < mid && right_index < right) {
                if (values[left_index] <= values[right_index]) aux[write_index++] = values[left_index++];
                else aux[write_index++] = values[right_index++];
            }
            while (left_index < mid) aux[write_index++] = values[left_index++];
            while (right_index < right) aux[write_index++] = values[right_index++];
            for (int copy = left; copy < right; ++copy) values[copy] = aux[copy];
        }
    }
    std::int64_t checksum = 0;
    for (int index = 0; index < count; ++index) {
        checksum = (checksum + values[index] * static_cast<std::int64_t>(index + 1)) % 1000000007LL;
    }
    return static_cast<double>(checksum);
}

double stencil(int grid) {
    const int cells = grid * grid;
    std::vector<double> current(cells), next_grid(cells);
    for (int diagonal = 0; diagonal < grid; ++diagonal) current[diagonal * grid + diagonal] = 1.0;
    for (int step = 0; step < 12; ++step) {
        for (int y = 0; y < grid; ++y) {
            for (int x = 0; x < grid; ++x) {
                const double center = current[y * grid + x];
                const double left = x > 0 ? current[y * grid + (x - 1)] : center;
                const double right = x + 1 < grid ? current[y * grid + (x + 1)] : center;
                const double up = y > 0 ? current[(y - 1) * grid + x] : center;
                const double down = y + 1 < grid ? current[(y + 1) * grid + x] : center;
                next_grid[y * grid + x] = (center + left + right + up + down) / 5.0;
            }
        }
        current.swap(next_grid);
    }
    double checksum = 0.0;
    for (int index = 0; index < cells; ++index) checksum += current[index] * (index + 1);
    return checksum;
}

double dijkstra(int n) {
    constexpr std::int64_t inf = 1000000000;
    constexpr std::int64_t mod = 1000000007;
    std::vector<std::int64_t> dist(n, inf);
    std::vector<int> used(n, 0);
    dist[0] = 0;
    for (int step = 0; step < n; ++step) {
        int selected = 0;
        std::int64_t best = inf;
        int found = 0;
        for (int index = 0; index < n; ++index) {
            if (used[index] == 0 && dist[index] < best) {
                best = dist[index];
                selected = index;
                found = 1;
            }
        }
        if (found == 1) {
            used[selected] = 1;
            for (int vertex = 0; vertex < n; ++vertex) {
                if (used[vertex] == 0 && selected != vertex) {
                    const std::int64_t weight = (selected * 17 + vertex * 13) % 97 + 1;
                    const std::int64_t candidate = dist[selected] + weight;
                    if (candidate < dist[vertex]) dist[vertex] = candidate;
                }
            }
        }
    }
    std::int64_t checksum = 0;
    for (int index = 0; index < n; ++index) checksum = (checksum + dist[index] * (index + 1)) % mod;
    return static_cast<double>(checksum);
}

double floyd(int n) {
    constexpr std::int64_t mod = 1000000007;
    std::vector<std::int64_t> dist(static_cast<size_t>(n) * n, 0);
    for (int row = 0; row < n; ++row) {
        for (int column = 0; column < n; ++column) {
            dist[static_cast<size_t>(row * n + column)] = row == column ? 0 : (row * 17 + column * 13) % 97 + 1;
        }
    }
    for (int via = 0; via < n; ++via) {
        for (int row = 0; row < n; ++row) {
            const std::int64_t via_cost = dist[static_cast<size_t>(row * n + via)];
            for (int column = 0; column < n; ++column) {
                const std::int64_t candidate = via_cost + dist[static_cast<size_t>(via * n + column)];
                const size_t index = static_cast<size_t>(row * n + column);
                if (candidate < dist[index]) dist[index] = candidate;
            }
        }
    }
    std::int64_t checksum = 0;
    for (size_t index = 0; index < dist.size(); ++index) {
        checksum = (checksum + dist[index] * static_cast<std::int64_t>(index + 1)) % mod;
    }
    return static_cast<double>(checksum);
}

double knapsack(int n) {
    constexpr std::int64_t mod = 1000000007;
    std::vector<std::int64_t> best(static_cast<size_t>(n) + 1, 0);
    for (int item = 1; item <= n; ++item) {
        const int weight = (item % 17) + 1;
        const std::int64_t value = (item * 3) % 23 + 1;
        for (int slot = n; slot >= weight; --slot) {
            const std::int64_t candidate = best[static_cast<size_t>(slot - weight)] + value;
            if (candidate > best[static_cast<size_t>(slot)]) best[static_cast<size_t>(slot)] = candidate;
        }
    }
    std::int64_t checksum = 0;
    for (size_t index = 0; index < best.size(); ++index) {
        checksum = (checksum + best[index] * static_cast<std::int64_t>(index + 1)) % mod;
    }
    return static_cast<double>(checksum);
}

double editdist(int n) {
    constexpr std::int64_t mod = 1000000007;
    std::vector<std::int64_t> previous(static_cast<size_t>(n) + 1);
    std::vector<std::int64_t> current(static_cast<size_t>(n) + 1, 0);
    for (int index = 0; index <= n; ++index) previous[static_cast<size_t>(index)] = index;
    for (int row = 1; row <= n; ++row) {
        current[0] = row;
        const int left_symbol = (row * 3) % 26;
        for (int column = 1; column <= n; ++column) {
            const std::int64_t cost = left_symbol == (column * 5) % 26 ? 0 : 1;
            std::int64_t choice = previous[static_cast<size_t>(column)] + 1;
            const std::int64_t insert = current[static_cast<size_t>(column - 1)] + 1;
            const std::int64_t replace = previous[static_cast<size_t>(column - 1)] + cost;
            if (insert < choice) choice = insert;
            if (replace < choice) choice = replace;
            current[static_cast<size_t>(column)] = choice;
        }
        std::swap(previous, current);
    }
    std::int64_t checksum = 0;
    for (int index = 0; index <= n; ++index) {
        checksum = (checksum + previous[static_cast<size_t>(index)] * (index + 1)) % mod;
    }
    return static_cast<double>(checksum);
}

double lis_checksum(int n) {
    constexpr std::int64_t mod = 1000000007;
    std::vector<std::int64_t> tails(n, 0);
    int length = 0;
    std::int64_t state = 1;
    for (int sample = 0; sample < n; ++sample) {
        state = (state * 48271) % 2147483647LL;
        const std::int64_t value = state % 1000003;
        int low = 0;
        int high = length;
        while (low < high) {
            const int mid = (low + high) / 2;
            if (tails[static_cast<size_t>(mid)] < value) low = mid + 1;
            else high = mid;
        }
        if (low == length) {
            tails[static_cast<size_t>(length)] = value;
            length += 1;
        } else {
            tails[static_cast<size_t>(low)] = value;
        }
    }
    std::int64_t checksum = 0;
    for (int index = 0; index < length; ++index) {
        checksum = (checksum + tails[static_cast<size_t>(index)] * (index + 1)) % mod;
    }
    return static_cast<double>(checksum);
}

double life(int n) {
    const int cells = n * n;
    std::vector<int> current(cells, 0);
    std::vector<int> next(cells, 0);
    for (int index = 0; index < n; ++index) {
        current[index * n + index] = 1;
        current[index * n + ((index * 3) % n)] = 1;
    }
    for (int step = 0; step < 12; ++step) {
        for (int y = 0; y < n; ++y) {
            for (int x = 0; x < n; ++x) {
                int neighbors = 0;
                if (y > 0 && x > 0 && current[(y - 1) * n + (x - 1)] == 1) neighbors += 1;
                if (y > 0 && current[(y - 1) * n + x] == 1) neighbors += 1;
                if (y > 0 && x + 1 < n && current[(y - 1) * n + (x + 1)] == 1) neighbors += 1;
                if (x > 0 && current[y * n + (x - 1)] == 1) neighbors += 1;
                if (x + 1 < n && current[y * n + (x + 1)] == 1) neighbors += 1;
                if (y + 1 < n && x > 0 && current[(y + 1) * n + (x - 1)] == 1) neighbors += 1;
                if (y + 1 < n && current[(y + 1) * n + x] == 1) neighbors += 1;
                if (y + 1 < n && x + 1 < n && current[(y + 1) * n + (x + 1)] == 1) neighbors += 1;
                const int alive = current[y * n + x];
                int born = 0;
                if (alive == 1 && (neighbors == 2 || neighbors == 3)) born = 1;
                if (alive == 0 && neighbors == 3) born = 1;
                next[y * n + x] = born;
            }
        }
        std::swap(current, next);
    }
    std::int64_t checksum = 0;
    for (int index = 0; index < cells; ++index) checksum += static_cast<std::int64_t>(current[index]) * (index + 1);
    return static_cast<double>(checksum);
}

double histogram(int sample_count) {
    std::vector<std::int64_t> bins(1024);
    std::int64_t state = 1;
    for (int sample = 0; sample < sample_count; ++sample) {
        state = (state * 48271) % 2147483647LL;
        bins[static_cast<size_t>(state % 1024)] += 1;
    }
    std::int64_t checksum = 0;
    for (int index = 0; index < 1024; ++index) checksum += static_cast<std::int64_t>(index + 1) * bins[index];
    return static_cast<double>(checksum);
}

int main(int argc, char** argv) {
    if (argc != 4) return 2;
    const std::string workload = argv[1];
    const int size = std::stoi(argv[2]);
    const int iterations = std::stoi(argv[3]);
    const std::vector<std::pair<std::string, double (*)(int)>> functions = {
        {"nqueens", nqueens}, {"mandelbrot", mandelbrot}, {"matmul", matmul},
        {"lcs", lcs}, {"sieve", sieve}, {"nbody", nbody}, {"binarytrees", binarytrees},
        {"bfs", bfs}, {"sort", sort_checksum}, {"stencil", stencil}, {"histogram", histogram},
        {"dijkstra", dijkstra}, {"floyd", floyd}, {"knapsack", knapsack}, {"editdist", editdist},
        {"lis", lis_checksum}, {"life", life},
    };
    double (*function)(int) = nullptr;
    for (const auto& [name, candidate] : functions) {
        if (name == workload) function = candidate;
    }
    if (!function) return 3;
    double total = 0.0;
    const auto started = std::chrono::steady_clock::now();
    for (int iteration = 0; iteration < iterations; ++iteration) total += function(size);
    const double elapsed_ms = std::chrono::duration<double, std::milli>(
        std::chrono::steady_clock::now() - started
    ).count();
    std::cout << "CHECKSUM:" << std::fixed << std::setprecision(9) << total << '\n';
    std::cout << "ELAPSED_MS:" << elapsed_ms << '\n';
}
