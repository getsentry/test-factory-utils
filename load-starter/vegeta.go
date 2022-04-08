// Implements the Vegeta load tester integration.
// Note: there some Vegeta specific code in addVegetaTestBuiltin starlark builtin.
// It needs to be there since it has more to do with starlark than Vegeta

package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/rs/zerolog/log"
)

const (
	StartVegetaUrl = "/command/"
	StopVegetaUrl  = "/stop/"
)

// CreateVegetaTestConfig creates a TestConfig for a Vegeta attack
func CreateVegetaTestConfig(duration time.Duration, testType string, freq int64, per string, config map[string]interface{}, name string, description string, loadTesterUrl string) (TestConfig, error) {

	loadTesterUrl = strings.TrimSuffix(loadTesterUrl, "/")

	log.Trace().Msgf("duration=%v\n freq=%v\n per=%v\n name=%v\n description=%v\n url=%v\n config:\n%v\n",
		duration, freq, per, name, description, loadTesterUrl, config)

	var startRequest = map[string]interface{}{
		"attackDuration": duration.String(),
		"numMessages":    freq,
		"per":            per,
		"params":         config,
		"testType":       testType,
	}
	if len(name) > 0 {
		startRequest["name"] = name
	}
	if len(description) > 0 {
		startRequest["description"] = description
	}

	var startBody, err = json.Marshal(startRequest)

	if err != nil {
		return TestConfig{}, err
	}

	// put the startRequest also in the spec (for reporting), remove duplicate info
	// tracked in the RunInfo
	delete(startRequest, "attackDuration")
	delete(startRequest, "name")
	delete(startRequest, "description")

	return TestConfig{
		RunInfo: RunInfo{
			Name:        name,
			Description: description,
			Duration:    duration,
			Spec:        startRequest,
			Runner:      "vegeta",
		},

		StartUrl:    fmt.Sprintf("%s%s", loadTesterUrl, StartVegetaUrl),
		StartMethod: "POST",
		StartHeaders: map[string]string{
			"Content-Type": "application/json",
		},
		StartBody: string(startBody),

		StopUrl:    fmt.Sprintf("%s%s", loadTesterUrl, StopVegetaUrl),
		StopMethod: "GET",
	}, nil
}
