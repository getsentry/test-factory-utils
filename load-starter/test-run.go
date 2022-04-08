package main

import (
	"time"
)

// Rerpresents one action that can be run as part of the test
type RunAction interface {
	Run() error
	GetDuration() time.Duration
	GetName() string
	GetTestInfo() *TestInfo
}

type TestInfo struct {
	Name        string
	Description string
	Duration    time.Duration
	Runner      string
	Spec        map[string]any
}

// Represents a list of actions that are executed in one execution
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
