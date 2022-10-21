package main

import (
	"time"
)

// Rerpresents one action that can be run as part of the test
type RunAction interface {
	// Runs the action logic
	Run() error
	GetDuration() time.Duration
	GetName() string
	// For test actions returns all test attributes
	// For non-test actions returns "nil"
	GetTestInfo() *TestInfo
}

// TestInfo represents a test configuration
type TestInfo struct {
	Name        string
	Description string
	// Duration represents the duration of the test
	Duration time.Duration
	// Runner the runner used for this test ( vegeta or locust)
	Runner string
	// Parameters passed to the test runner (passed as is and interpreted directly by the runner)
	Spec map[string]any
	// DisableReport if true will disable report generation for this test (used for warm-up or cool-down
	// stages that do not generate useful measurements and would just produce noise)
	// field should **NOT** be serialised
	disableReport bool
}

// Config Represents a list of actions that are executed in one execution
type Config struct {
	RunActionList []RunAction
}

// RunReport represents the result of running one test step/run (one TestConfig)
type RunReport struct {
	TestInfo  `yaml:"runInfo" json:"runInfo"`
	StartTime time.Time `yaml:"startTime" json:"startTime"`
	EndTime   time.Time `yaml:"endTime" json:"endTime"`
}

// CombinedReport represents the aggregated results of all test runs
type CombinedReport struct {
	TestRuns  []RunReport `yaml:"testRuns" json:"testRuns"`
	StartTime time.Time   `yaml:"startTime" json:"startTime"`
	EndTime   time.Time   `yaml:"endTime" json:"endTime"`
}

func (cfg Config) GetDuration() time.Duration {
	var retVal time.Duration
	for _, testRun := range cfg.RunActionList {
		retVal += testRun.GetDuration()
	}
	return retVal
}
