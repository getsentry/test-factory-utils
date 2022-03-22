package main

import (
	"fmt"
	"net/http"
	"os"
	"strings"
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

func minInt(nums ...int64) int64 {
	if len(nums) == 0 {
		return 0
	}
	var retVal = nums[0]

	for _, val := range nums {
		if val < retVal {
			retVal = val
		}
	}
	return retVal
}

// getDefaultHttpClient returns a correctly configured HTTP Client for passing
// requests to workers (a common point to configure options for worker requests)
func GetDefaultHttpClient() http.Client {
	return http.Client{Timeout: time.Duration(1) * time.Second}
}

// IsStarlarkConfig checks if the extension to see if the file looks like a starlark file
// accepted extensions are ".py" and ".star"
func IsStarlarkConfig(filePath string) bool {
	var starlarkSuffixes = []string{".py", ".star"}

	for _, suffix := range starlarkSuffixes {
		if strings.HasSuffix(filePath, suffix) {
			return true
		}
	}
	return false
}
