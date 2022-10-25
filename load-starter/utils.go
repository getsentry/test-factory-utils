package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/rs/zerolog/log"
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

func SendHttpRequest(method string, url string, body string, headers map[string]string) error {
	var bodyData io.Reader
	if len(body) > 0 {
		bodyData = bytes.NewReader([]byte(body))
	}
	req, err := http.NewRequest(method, url, bodyData)
	if err != nil {
		return err
	}
	for key, val := range headers {
		req.Header.Add(key, val)
	}
	if err != nil {
		return err
	}

	var client = GetDefaultHttpClient()
	resp, err := client.Do(req)
	if err != nil {
		log.Error().Err(err).Msgf("Error sending command to client '%s': ", url)
		return err
	}
	if resp != nil {
		err = resp.Body.Close()
		if err != nil {
			log.Error().Err(err).Msg("Could not close response body")
		}
	}
	return nil
}

// DeepCopyPublicFields deep-copies a to b using json marshaling
// Note: Does not copy unexported fields
func DeepCopyPublicFields(a, b interface{}) {
	byt, _ := json.Marshal(a)
	json.Unmarshal(byt, b)
}
