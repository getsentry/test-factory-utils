package main

import (
	"os/exec"
	"time"

	"github.com/rs/zerolog/log"
)

// RunExternalAction that allows to run external commands
type RunExternalAction struct {
	cmd []string
}

func (action RunExternalAction) GetDuration() time.Duration {
	// We do not know how long the execution will be, so just a half-educated guess
	return 10 * time.Second
}

func (action RunExternalAction) GetName() string {
	return "external command"
}

func (action RunExternalAction) GetTestInfo() *TestInfo {
	return nil
}

func (action RunExternalAction) Run() error {
	var err error

	command := exec.Command(action.cmd[0], action.cmd[1:]...)

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Not running the external command: `%v`", command)
	} else {
		log.Info().Msgf("Running external command: `%v`", command)
		err = command.Run()
	}

	return err
}
