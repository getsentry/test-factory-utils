package main

import (
	"fmt"
	"net/http"
	"net/url"
	"strconv"
	"strings"
)

const (
	StartLocustUrl = "/swarm"
	StopLocustUrl  = "/stop"
	ResetLocustUrl = "/stats/reset"
)

// Starts a locust load task by calling the spawn endpoint
func startLocust(users int64, spawnRate int64) error {
	fmt.Printf("Preparing to start Locust; users: %d: spawnRate: %d\n", users, spawnRate)

	startUrl := fmt.Sprintf("%s%s", *Params.locustServerName, StartLocustUrl)
	contentType := "application/x-www-form-urlencoded; charset=UTF-8"
	requestBody := url.Values{}

	requestBody.Add("user_count", strconv.FormatInt(users, 10))
	requestBody.Add("spawn_rate", strconv.FormatInt(spawnRate, 10))
	body := requestBody.Encode()

	if Params.dryRun {
		fmt.Printf("[dry-run] Sending start request to %s: %s\n", startUrl, body)
		return nil
	}

	response, err := http.Post(startUrl, contentType, strings.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to start the test:%v", err)
	}
	defer response.Body.Close()
	statusOK := response.StatusCode >= 200 && response.StatusCode < 300
	if !statusOK {
		return fmt.Errorf("failed to start test, server responded with %s", response.Status)
	}
	return nil
}

// Starts a locust load testing by calling the stop endpoint
func stopLocust() error {
	stopUrl := fmt.Sprintf("%s%s", *Params.locustServerName, StopLocustUrl)

	if Params.dryRun {
		fmt.Printf("[dry-run] Sending stop request to %s\n", stopUrl)
		return nil
	}

	response, err := http.Get(stopUrl)
	if err != nil {
		return fmt.Errorf("Failed to stop the test: %v", err)
	}
	defer response.Body.Close()
	return nil
}

// Reset locust stats
func resetLocustStats() error {
	resetUrl := fmt.Sprintf("%s%s", *Params.locustServerName, ResetLocustUrl)

	if Params.dryRun {
		fmt.Printf("[dry-run] Sending stats reset request to %s\n", resetUrl)
		return nil
	}

	response, err := http.Get(resetUrl)
	if err != nil {
		return fmt.Errorf("Failed to reset the stats: %v", err)
	}
	defer response.Body.Close()
	return nil
}
