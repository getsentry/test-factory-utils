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
	Name        string
	Description string
	Duration    time.Duration

	StartUrl     string
	StartMethod  string // GET,POST...
	StartBody    string
	StartHeaders map[string]string

	StopUrl     string // if empty no stop request will be issued
	StopMethod  string // GET, POST...
	StopBody    string
	StopHeaders map[string]string
}

// TestRun represents the result of running a TestConfig
type TestRun struct {
	TestConfig
	StartTime time.Time
}

type RunReport struct {
	TestRuns  []TestRun
	StartTime time.Time
	EndTime   time.Time
}

type Config struct {
	TestConfigs []TestConfig
}

func (cfg Config) GetDuration() time.Duration {
	var retVal time.Duration
	for _, testRun := range cfg.TestConfigs {
		retVal += testRun.Duration
	}
	return retVal
}

func (cfg RunReport) GetDuration() time.Duration {
	var retVal time.Duration
	for _, testRun := range cfg.TestRuns {
		retVal += testRun.Duration
	}
	return retVal
}
