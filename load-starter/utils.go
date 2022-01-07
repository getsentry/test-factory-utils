package main

import (
	"fmt"
	"os"
)

func check(e error) {
	if e != nil {
		fmt.Println(e)
		os.Exit(1)
	}
}
func intAbs(v int64) int64 {
	if v < 0 {
		return -v
	}
	return v
}
