package main

import (
	"fmt"
	"math"
	"os"
	"strconv"
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

func main() {
	workload := os.Args[1]
	size, _ := strconv.Atoi(os.Args[2])
	iterations, _ := strconv.Atoi(os.Args[3])
	functions := map[string]func(int) float64{
		"nqueens": nqueens, "mandelbrot": mandelbrot, "matmul": matmul,
		"lcs": lcs, "sieve": sieve, "nbody": nbody, "binarytrees": binarytrees,
	}
	total := 0.0
	for i := 0; i < iterations; i++ { total += functions[workload](size) }
	fmt.Printf("CHECKSUM:%.9f\n", total)
}
