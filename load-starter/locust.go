// Implements the Locust load tester integration.
// Note: there some Locust specific code in addLocustTestBuiltin starlark builtin.
// It needs to be there since it has more to do with starlark than Locust

package main

import (
	"fmt"
	"github.com/rs/zerolog/log"
	"net/http"
	"net/url"
	"strconv"
	"strings"
	"time"
)

const (
	StartLocustUrl = "/swarm"
	StopLocustUrl  = "/stop"
	ResetLocustUrl = "/stats/reset"
)

// Starts a locust load task by calling the spawn endpoint
// TODO remove, it is obsolete
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
// TODO remove, it is obsolete
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

func CreateLocustTestConfig(duration time.Duration, name string, description string, loadTesterUrl string, users int64, spawnRate int64) TestConfig {

	log.Trace().Msgf(`duration=%v
name=%v
description=%v
loadTesterUrl=%v
users=%v
spawnRate=%v`,
		duration, name, description, loadTesterUrl, users, spawnRate)

	loadTesterUrl = strings.TrimSuffix(loadTesterUrl, "/")

	startRequest := url.Values{}
	startRequest.Add("user_count", strconv.FormatInt(users, 10))
	startRequest.Add("spawn_rate", strconv.FormatInt(spawnRate, 10))
	startBody := startRequest.Encode()

	return TestConfig{
		Duration:    duration,
		Name:        name,
		Description: description,

		StartUrl:    fmt.Sprintf("%s%s", loadTesterUrl, StartLocustUrl),
		StartMethod: "POST",
		StartBody:   startBody,
		StartHeaders: map[string]string{
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
		},

		StopUrl:    fmt.Sprintf("%s%s", loadTesterUrl, StopLocustUrl),
		StopMethod: "GET",
	}
}
