package main

import (
	"fmt"
	"net/http"
	"os"
	"time"
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

// getDefaultHttpClient returns a correctly configured HTTP Client for passing
// requests to workers (a common point to configure options for worker requests)
func GetDefaultHttpClient() http.Client {
	return http.Client{Timeout: time.Duration(1) * time.Second}
}
