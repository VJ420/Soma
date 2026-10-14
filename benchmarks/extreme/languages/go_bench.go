package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
	"time"
)

func nqueens(n int) float64 {
	columns := make([]int, n)
	var safe func(int, int) bool
	safe = func(row, column int) bool {
		for priorRow := 0; priorRow < row; priorRow++ {
			priorColumn := columns[priorRow]
			delta := priorColumn - column
			if delta < 0 { delta = -delta }
			if priorColumn == column || delta == row-priorRow { return false }
		}
		return true
	}
	var search func(int) int
	search = func(row int) int {
		if row == n { return 1 }
		count := 0
		for column := 0; column < n; column++ {
			if safe(row, column) {
				columns[row] = column
				count += search(row + 1)
			}
		}
		return count
	}
	return float64(search(0))
}

func mandelbrot(size int) float64 {
	total := 0
	for y := 0; y < size; y++ {
		cy := (float64(y)/float64(size))*2.0 - 1.0
		for x := 0; x < size; x++ {
			cx := (float64(x)/float64(size))*3.0 - 2.0
			zx, zy, iteration := 0.0, 0.0, 0
			for zx*zx+zy*zy <= 4.0 && iteration < 40 {
				nextX := zx*zx - zy*zy + cx
				zy = 2.0*zx*zy + cy
				zx = nextX
				iteration++
			}
			total += iteration
		}
	}
	return float64(total)
}

func matmul(size int) float64 {
	checksum := 0
	for i := 0; i < size; i++ {
		for j := 0; j < size; j++ {
			cell := 0
			for k := 0; k < size; k++ {
				cell += ((i*3+k*7)%97) * ((k*5+j*11)%89)
			}
			checksum += cell
		}
	}
	return float64(checksum)
}

func lcs(size int) float64 {
	previous, current := make([]int, size+1), make([]int, size+1)
	for i := 1; i <= size; i++ {
		left := (i * 3) % 26
		current[0] = 0
		for j := 1; j <= size; j++ {
			if left == (j*5)%26 {
				current[j] = previous[j-1] + 1
			} else if previous[j] > current[j-1] {
				current[j] = previous[j]
			} else {
				current[j] = current[j-1]
			}
		}
		previous, current = current, previous
	}
	return float64(previous[size])
}

func sieve(limit int) float64 {
	flags := make([]bool, limit+1)
	for i := 2; i <= limit; i++ { flags[i] = true }
	for factor := 2; factor*factor <= limit; factor++ {
		if flags[factor] {
			for composite := factor*factor; composite <= limit; composite += factor {
				flags[composite] = false
			}
		}
	}
	count := 0
	for _, value := range flags { if value { count++ } }
	return float64(count)
}

func nbody(size int) float64 {
	x, y := make([]float64, size), make([]float64, size)
	vx, vy := make([]float64, size), make([]float64, size)
	for i := 0; i < size; i++ { x[i], y[i] = float64(i), float64(i*2+1) }
	for step := 0; step < 10; step++ {
		for i := 0; i < size; i++ {
			fx, fy := 0.0, 0.0
			for j := 0; j < size; j++ {
				if i != j {
					dx, dy := x[j]-x[i], y[j]-y[i]
					distanceSquared := dx*dx + dy*dy + 0.01
					inverseDistance := 1.0 / math.Sqrt(distanceSquared*distanceSquared*distanceSquared)
					fx += dx * inverseDistance
					fy += dy * inverseDistance
				}
			}
			vx[i] += fx * 0.01
			vy[i] += fy * 0.01
		}
		for i := 0; i < size; i++ { x[i] += vx[i]*0.01; y[i] += vy[i]*0.01 }
	}
	checksum := 0.0
	for i := 0; i < size; i++ { checksum += x[i] + y[i] }
	return checksum
}

type node struct { left, right *node }

func buildTree(depth int) *node {
	if depth <= 0 { return &node{} }
	return &node{left: buildTree(depth-1), right: buildTree(depth-1)}
}

func checkTree(root *node) int {
	if root.left == nil { return 1 }
	return 1 + checkTree(root.left) + checkTree(root.right)
}

func binarytrees(depth int) float64 { return float64(checkTree(buildTree(depth))) }

func bfs(nodeCount int) float64 {
	dist := make([]int, nodeCount)
	queue := make([]int, nodeCount)
	for i := range dist {
		dist[i] = -1
	}
	dist[0] = 0
	head, tail := 0, 1
	for head < tail {
		node := queue[head]
		head++
		first := (node + 1) % nodeCount
		second := (node*3 + 1) % nodeCount
		if dist[first] < 0 {
			dist[first] = dist[node] + 1
			queue[tail] = first
			tail++
		}
		if first != second && dist[second] < 0 {
			dist[second] = dist[node] + 1
			queue[tail] = second
			tail++
		}
	}
	checksum := 0
	for _, value := range dist {
		if value >= 0 {
			checksum += value
		}
	}
	return float64(checksum)
}

func sortChecksum(count int) float64 {
	values := make([]int64, count)
	aux := make([]int64, count)
	state := int64(1)
	for index := 0; index < count; index++ {
		state = (state * 48271) % 2147483647
		values[index] = state
	}
	for width := 1; width < count; width *= 2 {
		for start := 0; start < count; start += 2 * width {
			left, mid, right := start, start+width, start+2*width
			if mid > count {
				mid = count
			}
			if right > count {
				right = count
			}
			leftIndex, rightIndex, writeIndex := left, mid, left
			for leftIndex < mid && rightIndex < right {
				if values[leftIndex] <= values[rightIndex] {
					aux[writeIndex] = values[leftIndex]
					leftIndex++
				} else {
					aux[writeIndex] = values[rightIndex]
					rightIndex++
				}
				writeIndex++
			}
			for leftIndex < mid {
				aux[writeIndex] = values[leftIndex]
				leftIndex++
				writeIndex++
			}
			for rightIndex < right {
				aux[writeIndex] = values[rightIndex]
				rightIndex++
				writeIndex++
			}
			for copy := left; copy < right; copy++ {
				values[copy] = aux[copy]
			}
		}
	}
	checksum := int64(0)
	for index, value := range values {
		checksum = (checksum + value*int64(index+1)) % 1000000007
	}
	return float64(checksum)
}

func stencil(grid int) float64 {
	cells := grid * grid
	current := make([]float64, cells)
	next := make([]float64, cells)
	for diagonal := 0; diagonal < grid; diagonal++ {
		current[diagonal*grid+diagonal] = 1
	}
	for step := 0; step < 12; step++ {
		for y := 0; y < grid; y++ {
			for x := 0; x < grid; x++ {
				center := current[y*grid+x]
				left, right, up, down := center, center, center, center
				if x > 0 {
					left = current[y*grid+(x-1)]
				}
				if x+1 < grid {
					right = current[y*grid+(x+1)]
				}
				if y > 0 {
					up = current[(y-1)*grid+x]
				}
				if y+1 < grid {
					down = current[(y+1)*grid+x]
				}
				next[y*grid+x] = (center + left + right + up + down) / 5
			}
		}
		current, next = next, current
	}
	checksum := 0.0
	for index, value := range current {
		checksum += value * float64(index+1)
	}
	return checksum
}

func dijkstra(n int) float64 {
	const inf int64 = 1000000000
	const mod int64 = 1000000007
	dist := make([]int64, n)
	used := make([]int, n)
	for index := range dist {
		dist[index] = inf
	}
	dist[0] = 0
	for step := 0; step < n; step++ {
		selected := 0
		best := inf
		found := 0
		for index := 0; index < n; index++ {
			if used[index] == 0 && dist[index] < best {
				best = dist[index]
				selected = index
				found = 1
			}
		}
		if found == 1 {
			used[selected] = 1
			for vertex := 0; vertex < n; vertex++ {
				if used[vertex] == 0 && selected != vertex {
					weight := int64((selected*17+vertex*13)%97 + 1)
					candidate := dist[selected] + weight
					if candidate < dist[vertex] {
						dist[vertex] = candidate
					}
				}
			}
		}
	}
	checksum := int64(0)
	for index, value := range dist {
		checksum = (checksum + value*int64(index+1)) % mod
	}
	return float64(checksum)
}

func floyd(n int) float64 {
	const mod int64 = 1000000007
	dist := make([]int64, n*n)
	for row := 0; row < n; row++ {
		for column := 0; column < n; column++ {
			if row == column {
				dist[row*n+column] = 0
			} else {
				dist[row*n+column] = int64((row*17+column*13)%97 + 1)
			}
		}
	}
	for via := 0; via < n; via++ {
		for row := 0; row < n; row++ {
			viaCost := dist[row*n+via]
			for column := 0; column < n; column++ {
				candidate := viaCost + dist[via*n+column]
				index := row*n + column
				if candidate < dist[index] {
					dist[index] = candidate
				}
			}
		}
	}
	checksum := int64(0)
	for index, value := range dist {
		checksum = (checksum + value*int64(index+1)) % mod
	}
	return float64(checksum)
}

func knapsack(n int) float64 {
	const mod int64 = 1000000007
	best := make([]int64, n+1)
	for item := 1; item <= n; item++ {
		weight := (item % 17) + 1
		value := int64((item*3)%23 + 1)
		for slot := n; slot >= weight; slot-- {
			candidate := best[slot-weight] + value
			if candidate > best[slot] {
				best[slot] = candidate
			}
		}
	}
	checksum := int64(0)
	for index, value := range best {
		checksum = (checksum + value*int64(index+1)) % mod
	}
	return float64(checksum)
}

func editdist(n int) float64 {
	const mod int64 = 1000000007
	previous := make([]int64, n+1)
	current := make([]int64, n+1)
	for index := 0; index <= n; index++ {
		previous[index] = int64(index)
	}
	for row := 1; row <= n; row++ {
		current[0] = int64(row)
		leftSymbol := (row * 3) % 26
		for column := 1; column <= n; column++ {
			cost := int64(1)
			if leftSymbol == (column*5)%26 {
				cost = 0
			}
			choice := previous[column] + 1
			insert := current[column-1] + 1
			replace := previous[column-1] + cost
			if insert < choice {
				choice = insert
			}
			if replace < choice {
				choice = replace
			}
			current[column] = choice
		}
		previous, current = current, previous
	}
	checksum := int64(0)
	for index, value := range previous {
		checksum = (checksum + value*int64(index+1)) % mod
	}
	return float64(checksum)
}

func lis(n int) float64 {
	const mod int64 = 1000000007
	tails := make([]int64, n)
	length := 0
	state := int64(1)
	for sample := 0; sample < n; sample++ {
		state = (state * 48271) % 2147483647
		value := state % 1000003
		low := 0
		high := length
		for low < high {
			mid := (low + high) / 2
			if tails[mid] < value {
				low = mid + 1
			} else {
				high = mid
			}
		}
		if low == length {
			tails[length] = value
			length++
		} else {
			tails[low] = value
		}
	}
	checksum := int64(0)
	for index := 0; index < length; index++ {
		checksum = (checksum + tails[index]*int64(index+1)) % mod
	}
	return float64(checksum)
}

func life(n int) float64 {
	cells := n * n
	current := make([]int, cells)
	next := make([]int, cells)
	for index := 0; index < n; index++ {
		current[index*n+index] = 1
		current[index*n+((index*3)%n)] = 1
	}
	for step := 0; step < 12; step++ {
		for y := 0; y < n; y++ {
			for x := 0; x < n; x++ {
				neighbors := 0
				if y > 0 && x > 0 && current[(y-1)*n+(x-1)] == 1 {
					neighbors++
				}
				if y > 0 && current[(y-1)*n+x] == 1 {
					neighbors++
				}
				if y > 0 && x+1 < n && current[(y-1)*n+(x+1)] == 1 {
					neighbors++
				}
				if x > 0 && current[y*n+(x-1)] == 1 {
					neighbors++
				}
				if x+1 < n && current[y*n+(x+1)] == 1 {
					neighbors++
				}
				if y+1 < n && x > 0 && current[(y+1)*n+(x-1)] == 1 {
					neighbors++
				}
				if y+1 < n && current[(y+1)*n+x] == 1 {
					neighbors++
				}
				if y+1 < n && x+1 < n && current[(y+1)*n+(x+1)] == 1 {
					neighbors++
				}
				alive := current[y*n+x]
				born := 0
				if alive == 1 && (neighbors == 2 || neighbors == 3) {
					born = 1
				}
				if alive == 0 && neighbors == 3 {
					born = 1
				}
				next[y*n+x] = born
			}
		}
		current, next = next, current
	}
	checksum := 0
	for index, value := range current {
		checksum += value * (index + 1)
	}
	return float64(checksum)
}

func histogram(sampleCount int) float64 {
	bins := make([]int64, 1024)
	state := int64(1)
	for sample := 0; sample < sampleCount; sample++ {
		state = (state * 48271) % 2147483647
		bins[state%1024]++
	}
	checksum := int64(0)
	for index, count := range bins {
		checksum += int64(index+1) * count
	}
	return float64(checksum)
}

func main() {
	workload := os.Args[1]
	size, _ := strconv.Atoi(os.Args[2])
	iterations, _ := strconv.Atoi(os.Args[3])
	functions := map[string]func(int) float64{
		"nqueens": nqueens, "mandelbrot": mandelbrot, "matmul": matmul,
		"lcs": lcs, "sieve": sieve, "nbody": nbody, "binarytrees": binarytrees,
		"bfs": bfs, "sort": sortChecksum, "stencil": stencil, "histogram": histogram,
		"dijkstra": dijkstra, "floyd": floyd, "knapsack": knapsack, "editdist": editdist, "lis": lis, "life": life,
	}
	total := 0.0
	started := time.Now()
	for i := 0; i < iterations; i++ { total += functions[workload](size) }
	elapsedMs := float64(time.Since(started).Nanoseconds()) / 1_000_000.0
	fmt.Printf("CHECKSUM:%.9f\n", total)
	fmt.Printf("ELAPSED_MS:%.9f\n", elapsedMs)
}
