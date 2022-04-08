// Implements the Locust load tester integration.
// Note: there some Locust specific code in addLocustTestBuiltin starlark builtin.
// It needs to be there since it has more to do with starlark than Locust

package main

import (
	"fmt"
	"net/url"
	"strconv"
	"strings"
	"time"

	"github.com/rs/zerolog/log"
)

const (
	StartLocustUrl = "/swarm"
	StopLocustUrl  = "/stop"
	ResetLocustUrl = "/stats/reset"
)

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
		RunInfo: RunInfo{
			Duration:    duration,
			Name:        name,
			Description: description,
			Runner:      "locust",
			Spec: map[string]interface{}{
				"userCount": users,
				"spawnRate": spawnRate,
			},
		},
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
