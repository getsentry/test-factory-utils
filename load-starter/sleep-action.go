package main

import (
	"fmt"
	"github.com/rs/zerolog/log"
	"time"
)

// SleepAction pauses the attack for the specified amount of time
type SleepAction struct {
	duration time.Duration
}

func (action SleepAction) GetDuration() time.Duration {
	return action.duration
}

func (action SleepAction) GetName() string {
	return fmt.Sprintf("sleep(%s)", action.duration)
}

func (action SleepAction) GetTestInfo() *TestInfo {
	return nil
}

func (action SleepAction) Run() error {
	var err error

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Not running would sleep for: `%s`", action.duration)
	} else {
		log.Info().Msgf("Sleeping for %s", action.duration)
		time.Sleep(action.duration)
	}

	return err
}
