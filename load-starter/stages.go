package main

import (
	"fmt"
	"time"
)

const (
	StageStaticName  = "static"
	StageGradualName = "gradual"
)

type TestStage interface {
	getType() string
	validate() error
	getTotalDuration() time.Duration
	execute() (StageReport, error)
}

// Report structs
type StepReport struct {
	Users     int64
	StartTime time.Time `yaml:"startTime"`
	EndTime   time.Time `yaml:"endTime"`
}

// Report per stage
type StageReport struct {
	StepReports []StepReport `yaml:"steps"`
	StageName   string       `yaml:"name"`
	StageType   string       `yaml:"stageType"`
}

// Top level report for the entire run
type RunReport struct {
	StageReports []StageReport `yaml:"stageReports"`
	StartTime    time.Time     `yaml:"startTime"`
	EndTime      time.Time     `yaml:"endTime"`
}

// Stage structs

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

func (t StageStatic) execute() (StageReport, error) {
	stageReport := StageReport{StageType: t.getType()}
	stepReport := StepReport{Users: t.Users}

	stepReport.StartTime = time.Now().UTC()
	err := startLocust(t.Users, t.Users/4)
	if err != nil {
		return stageReport, err
	}

	// Wait for the test to run
	if Params.dryRun {
		fmt.Printf("[dry-run] Skipping wait for %s\n", t.Duration)
	} else {
		fmt.Printf("Waiting for %s...\n", t.Duration)
		time.Sleep(t.Duration)
	}

	err = stopLocust()
	if err != nil {
		return stageReport, err
	}

	stepReport.EndTime = time.Now().UTC()
	stageReport.StepReports = append(stageReport.StepReports, stepReport)
	return stageReport, nil
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

func (t StageGradual) execute() (StageReport, error) {
	stageReport := StageReport{StageType: t.getType()}
	usersPerStep := t._getUsersByStep()

	for _, users := range usersPerStep {
		stepReport := StepReport{Users: users}

		stepReport.StartTime = time.Now().UTC()
		err := startLocust(users, users/4)
		if err != nil {
			return stageReport, err
		}

		// Wait for the step to run
		if Params.dryRun {
			fmt.Printf("[dry-run] Skipping wait for %s\n", t.StepDuration)
		} else {
			fmt.Printf("Waiting for %s...\n", t.StepDuration)
			time.Sleep(t.StepDuration)
		}

		stepReport.EndTime = time.Now().UTC()
		stageReport.StepReports = append(stageReport.StepReports, stepReport)

		// TODO: reset stats?
	}

	err := stopLocust()
	if err != nil {
		return stageReport, err
	}

	return stageReport, nil
}
