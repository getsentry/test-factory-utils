package main

import (
	"fmt"
	"log"
	"os"
	"time"

	"gopkg.in/yaml.v2"
)

const (
	StageStaticName  = "static"
	StageGradualName = "gradual"
)

//// Stage structs

type StageStatic struct {
	Name     string
	Users    int64
	Duration time.Duration
}

type StageGradual struct {
	Name         string
	StartUsers   int64 `yaml:"startUsers"`
	EndUsers     int64 `yaml:"endUsers"`
	Step         int64
	StepDuration time.Duration `yaml:"stepDuration"`
}

// Used only when parsing the configuration
type RawConfig struct {
	Stages []interface{}
}

type TestStage interface {
	getType() string
	validate() error
	getTotalDuration() time.Duration
	execute() error
}

type Config struct {
	Stages []TestStage
}

//// Interface implementations

// StageStatic

func (t StageStatic) getType() string {
	return StageStaticName
}

func (t StageStatic) validate() error {
	if t.Users < 0 {
		return fmt.Errorf("Invalid number of users for stage: %#v", t)
	}
	if t.Duration.Seconds() == 0.0 {
		return fmt.Errorf("Duration cannot be zero/empty for stage: %#v", t)
	}
	return nil
}

func (t StageStatic) getTotalDuration() time.Duration {
	return t.Duration
}

func (t StageStatic) execute() error {
	err := startLocust(t.Users, t.Users/4)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	// Wait for the test to run
	if Params.dryRun {
		fmt.Printf("[dry-run] Skipping wait for %s\n", t.Duration)
	} else {
		fmt.Printf("Will be waiting for %s...\n", t.Duration)
		time.Sleep(t.Duration)
	}

	err = stopLocust()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	return nil
}

// StageGradual

func (t StageGradual) getType() string {
	return StageGradualName
}

func (t StageGradual) validate() error {
	if t.StartUsers < 0 {
		return fmt.Errorf("Invalid starting number of users: %d", t.StartUsers)
	}
	if t.EndUsers < 0 {
		return fmt.Errorf("Invalid target number of users: %d", t.EndUsers)
	}
	if t.StepDuration.Seconds() == 0.0 {
		return fmt.Errorf("Step duration cannot be zero/empty for stage: %#v", t)
	}
	if (t.StartUsers < t.EndUsers && t.Step <= 0) || (t.StartUsers > t.EndUsers && t.Step >= 0) {
		return fmt.Errorf("Invalid combination of step and start/end users: %#v", t)
	}
	return nil
}

func (t StageGradual) _getUsersByStep() []int64 {
	users := []int64{t.StartUsers}
	if t.Step == 0 {
		return users
	}

	lastUsers := t.StartUsers

	for {
		lastUsers = lastUsers + t.Step
		if (t.Step > 0 && lastUsers >= t.EndUsers) || (t.Step < 0 && lastUsers <= t.EndUsers) {
			users = append(users, t.EndUsers)
			break
		}

		users = append(users, lastUsers)
	}

	return users
}

func (t StageGradual) getTotalDuration() time.Duration {
	totalSteps := len(t._getUsersByStep())
	return time.Duration(int(t.StepDuration) * totalSteps)
}

func (t StageGradual) execute() error {
	usersPerStep := t._getUsersByStep()

	for _, users := range usersPerStep {

		err := startLocust(users, users/4)
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}

		// Wait for the step to run
		if Params.dryRun {
			fmt.Printf("[dry-run] Skipping wait for %s\n", t.StepDuration)
		} else {
			fmt.Printf("Will be waiting for %s...\n", t.StepDuration)
			time.Sleep(t.StepDuration)
		}

		// TODO: reset stats?
	}

	err := stopLocust()
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	return nil
}

//// Misc functions

func (c Config) getTotalDuration() time.Duration {
	var duration time.Duration
	for _, stage := range c.Stages {
		duration += stage.getTotalDuration()
	}
	return duration
}

// Parsing function

func parseConfigFile(configPath string) Config {
	data, err := os.ReadFile(configPath)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}
	return parseConfig(data)
}

func parseConfig(data []byte) Config {
	rawConfig := RawConfig{}

	err := yaml.Unmarshal(data, &rawConfig)
	if err != nil {
		log.Fatalf("error: %v", err)
	}
	// fmt.Printf("--- raw config:\n%v\n\n", rawConfig)

	config := Config{}
	config.Stages = make([]TestStage, 0)

	for _, s := range rawConfig.Stages {
		stageType := s.(map[interface{}]interface{})["type"]

		switch stageType {
		case StageStaticName:
			{
				// TODO: can this be deduped or rewritten?
				stage := StageStatic{}
				str, err := yaml.Marshal(&s)
				if err != nil {
					fmt.Println(err)
					os.Exit(1)
				}
				yaml.Unmarshal(str, &stage)

				config.Stages = append(config.Stages, stage)
			}
		case StageGradualName:
			{
				// TODO: can this be deduped or rewritten?
				stage := StageGradual{}
				str, err := yaml.Marshal(&s)
				if err != nil {
					fmt.Println(err)
					os.Exit(1)
				}
				yaml.Unmarshal(str, &stage)

				config.Stages = append(config.Stages, stage)
			}
		default:
			{
				log.Fatalf("Configuration: cannot parse one or more testing stages! Stage: '%v'", s)
			}
		}

		// Validate the newly added stage
		err = config.Stages[len(config.Stages)-1].validate()
		if err != nil {
			fmt.Println(err)
			os.Exit(1)
		}
	}

	return config
}
