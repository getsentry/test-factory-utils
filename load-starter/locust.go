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

// TODO: we can probably reuse TestInfo here
type LocustTestAction struct {
	Name        string
	Description string
	Duration    time.Duration

	LoadTesterUrl string
	UserCount     int64
	SpawnRate     int64
}

func CreateLocustTestConfig(duration time.Duration, name string, description string, loadTesterUrl string, users int64, spawnRate int64) LocustTestAction {
	loadTesterUrl = strings.TrimSuffix(loadTesterUrl, "/")

	log.Trace().Msgf("duration=%v\nname=%v\ndescription=%v\nloadTesterUrl=%v\nusers=%v\nspawnRate=%v",
		duration, name, description, loadTesterUrl, users, spawnRate)

	if spawnRate <= 0 {
		spawnRate = users / 4
	}

	return LocustTestAction{
		Duration:      duration,
		Name:          name,
		Description:   description,
		UserCount:     users,
		SpawnRate:     spawnRate,
		LoadTesterUrl: loadTesterUrl,
	}
}

func (action LocustTestAction) GetDuration() time.Duration {
	return action.Duration
}

func (action LocustTestAction) GetName() string {
	return action.Name
}

func (action LocustTestAction) GetTestInfo() *TestInfo {
	return &TestInfo{
		Duration:    action.Duration,
		Name:        action.Name,
		Description: action.Description,
		Runner:      "locust",
		Spec: map[string]interface{}{
			"userCount": action.UserCount,
			"spawnRate": action.SpawnRate,
		},
	}
}

func (action LocustTestAction) Run() error {
	err := resetLocustStats(action.LoadTesterUrl)
	if err != nil {
		log.Error().Err(err).Msgf("Failed to reset locust stats in '%s'", action.Name)
		return err
	}

	err = startLocust(action.LoadTesterUrl, action.UserCount, action.SpawnRate)
	if err != nil {
		log.Error().Err(err).Msgf("Failed to start run in '%s'", action.Name)
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
		log.Error().Err(err).Msgf("Failed to stop run in '%s'", action.Name)
		return err
	}

	return nil
}

func startLocust(locustUrl string, users int64, spawnRate int64) error {
	startUrl := fmt.Sprintf("%s%s", locustUrl, StartLocustUrl)

	startRequest := url.Values{}
	startRequest.Add("user_count", strconv.FormatInt(users, 10))
	startRequest.Add("spawn_rate", strconv.FormatInt(spawnRate, 10))
	startBody := startRequest.Encode()

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Sending start request to %s: %s", startUrl, startBody)
		return nil
	}

	err := SendHttpRequest(
		"POST", startUrl, startBody, map[string]string{
			"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
		},
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
		return fmt.Errorf("Failed to reset the stats: %v", err)
	}
	return nil
}
