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

type VegetaTestAction struct {
	TestInfo

	LoadTesterUrl string
}

// CreateVegetaTestAction creates a TestConfig for a Vegeta attack
func CreateVegetaTestAction(duration time.Duration, testType string, freq int64, per string, config map[string]interface{},
	name string, description string, loadTesterUrl string, produceReport bool) (VegetaTestAction, error) {

	loadTesterUrl = strings.TrimSuffix(loadTesterUrl, "/")

	log.Trace().Msgf("duration=%v\n freq=%v\n per=%v\n name=%v\n description=%v\n url=%v\n config:\n%v\n",
		duration, freq, per, name, description, loadTesterUrl, config)

	var specParams = map[string]interface{}{
		"attackDuration": duration.String(),
		"numMessages":    freq,
		"per":            per,
		"params":         config,
		"testType":       testType,
	}

	if len(name) > 0 {
		specParams["name"] = name
	}
	if len(description) > 0 {
		specParams["description"] = description
	}

	// Make sure that everything is serializable
	var _, err = json.Marshal(specParams)
	if err != nil {
		return VegetaTestAction{}, err
	}

	return VegetaTestAction{
		TestInfo: TestInfo{
			Name:          name,
			Description:   description,
			Duration:      duration,
			Runner:        "vegeta",
			Spec:          specParams,
			disableReport: !produceReport,
		}, LoadTesterUrl: loadTesterUrl}, nil
}

func (action VegetaTestAction) GetDuration() time.Duration {
	return action.Duration
}

func (action VegetaTestAction) GetName() string {
	return action.Name
}

func (action VegetaTestAction) GetTestInfo() *TestInfo {
	testInfo := TestInfo{}
	DeepCopyPublicFields(action.TestInfo, &testInfo)
	// manually copy private fields (fields not marshaled in JSON)
	testInfo.disableReport = action.TestInfo.disableReport

	fmt.Printf("%v\n", action.TestInfo)
	fmt.Printf("%v\n", testInfo)

	specParams := testInfo.Spec

	// Remove duplicate info already tracked in the TestInfo
	delete(specParams, "attackDuration")
	delete(specParams, "name")
	delete(specParams, "description")

	return &testInfo
}

func (action VegetaTestAction) Run() error {
	err := startVegeta(action.LoadTesterUrl, action.Spec)
	if err != nil {
		log.Error().Msgf("Failed to start Vegeta run in '%s'", action.Name)
		return err
	}

	if Params.dryRun {
		log.Debug().Msgf("[dry-run] Skipping wait for %s", action.Duration)
	} else {
		log.Debug().Msgf("Waiting for %s...", action.Duration)
		time.Sleep(action.Duration)
	}

	err = stopVegeta(action.LoadTesterUrl)
	if err != nil {
		log.Error().Msgf("Failed to stop Vegeta run in '%s'", action.Name)
		return err
	}

	return nil
}

func startVegeta(vegetaUrl string, specParams map[string]interface{}) error {
	startUrl := fmt.Sprintf("%s%s", vegetaUrl, StartVegetaUrl)

	startBody, err := json.Marshal(specParams)
	if err != nil {
		return err
	}

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Sending start request to %s: %s", startUrl, startBody)
		return nil
	}

	headers := map[string]string{
		"Content-Type": "application/json",
	}

	err = SendHttpRequest(
		"POST", startUrl, string(startBody), headers,
	)
	return err
}

func stopVegeta(locustUrl string) error {
	stopUrl := fmt.Sprintf("%s%s", locustUrl, StopVegetaUrl)

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Sending stop request to %s", stopUrl)
		return nil
	}

	err := SendHttpRequest("GET", stopUrl, "", map[string]string{})
	return err
}
