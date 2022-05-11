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

type LocustTestAction struct {
	TestInfo

	LoadTesterUrl string
}

// CreateLocustTestAction creates a TestConfig for a Locust attack
func CreateLocustTestAction(duration time.Duration, name string, description string, loadTesterUrl string, users int64, spawnRate int64) LocustTestAction {
	loadTesterUrl = strings.TrimSuffix(loadTesterUrl, "/")

	log.Trace().Msgf("duration=%v\nname=%v\ndescription=%v\nloadTesterUrl=%v\nusers=%v\nspawnRate=%v",
		duration, name, description, loadTesterUrl, users, spawnRate)

	if spawnRate <= 0 {
		spawnRate = users / 4
	}

	var specParams = map[string]interface{}{
		"users":     users,
		"spawnRate": spawnRate,
	}

	return LocustTestAction{
		TestInfo: TestInfo{
			Duration:    duration,
			Name:        name,
			Description: description,
			Runner:      "locust",
			Spec:        specParams,
		}, LoadTesterUrl: loadTesterUrl}
}

func (action LocustTestAction) GetDuration() time.Duration {
	return action.Duration
}

func (action LocustTestAction) GetName() string {
	return action.Name
}

func (action LocustTestAction) GetTestInfo() *TestInfo {
	return &action.TestInfo
}

func (action LocustTestAction) Run() error {
	err := resetLocustStats(action.LoadTesterUrl)
	if err != nil {
		log.Error().Msgf("Failed to reset locust stats in '%s'", action.Name)
		return err
	}

	err = startLocust(action.LoadTesterUrl, action.Spec)
	if err != nil {
		log.Error().Msgf("Failed to start run in '%s'", action.Name)
		return err
	}

	if Params.dryRun {
		log.Debug().Msgf("[dry-run] Skipping wait for %s", action.Duration)
	} else {
		log.Debug().Msgf("Waiting for %s...", action.Duration)
		time.Sleep(action.Duration)
	}

	err = stopLocust(action.LoadTesterUrl)
	if err != nil {
		log.Error().Msgf("Failed to stop run in '%s'", action.Name)
		return err
	}

	return nil
}

func startLocust(locustUrl string, specParams map[string]interface{}) error {
	startUrl := fmt.Sprintf("%s%s", locustUrl, StartLocustUrl)

	startRequest := url.Values{}
	var users string = strconv.FormatInt(specParams["users"].(int64), 10)
	startRequest.Add("user_count", users)
	var spawnRate string = strconv.FormatInt(specParams["spawnRate"].(int64), 10)
	startRequest.Add("spawn_rate", spawnRate)
	startBody := startRequest.Encode()

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Sending start request to %s: %s", startUrl, startBody)
		return nil
	}

	headers := map[string]string{
		"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
	}

	err := SendHttpRequest(
		"POST", startUrl, startBody, headers,
	)
	return err
}

func stopLocust(locustUrl string) error {
	stopUrl := fmt.Sprintf("%s%s", locustUrl, StopLocustUrl)

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Sending stop request to %s", stopUrl)
		return nil
	}

	err := SendHttpRequest("GET", stopUrl, "", map[string]string{})
	return err
}

func resetLocustStats(locustUrl string) error {
	resetUrl := fmt.Sprintf("%s%s", locustUrl, ResetLocustUrl)

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Sending stats reset request to %s", resetUrl)
		return nil
	}

	err := SendHttpRequest("GET", resetUrl, "", map[string]string{})

	if err != nil {
		return fmt.Errorf("failed to reset the stats: %v", err)
	}
	return nil
}
