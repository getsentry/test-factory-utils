package main

import (
	"time"
)

// TestConfig definitions
// A TestConfig is a distinct experiment that the load starter performs
// A TestConfig has a Duration and configuration parameters
// The configuration parameters are opaque they are sent as JSON to the runner
// A TestConfig has a start command and an optional stop command, if the stop command
// is the empty string it will not be sent
type TestConfig struct {
	TestInfo

	StartUrl     string
	StartMethod  string // GET,POST...
	StartBody    string
	StartHeaders map[string]string

	StopUrl     string // if empty no stop request will be issued
	StopMethod  string // GET, POST...
	StopBody    string
	StopHeaders map[string]string
}

type TestInfo struct {
	Name        string
	Description string
	Duration    time.Duration
	Runner      string
	Spec        map[string]any
}
type Config struct {
	TestConfigs []TestConfig
}

// RunReport represents the result of running one test step/run (one TestConfig)
type RunReport struct {
	TestInfo  `yaml:"testInfo" json:"testInfo"`
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
	for _, testRun := range cfg.TestConfigs {
		retVal += testRun.Duration
	}
	return retVal
}
