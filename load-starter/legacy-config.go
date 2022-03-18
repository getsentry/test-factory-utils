package main

// This file contains the parsing of legacy configuration files

import (
	"log"
	"os"
	"time"

	"gopkg.in/yaml.v2"
)

// Used only when parsing the configuration
type RawConfig struct {
	Stages []interface{}
}

type LegacyConfig struct {
	Stages []LegacyTestStage
}

func (c LegacyConfig) getTotalDuration() time.Duration {
	var duration time.Duration
	for _, stage := range c.Stages {
		duration += stage.getTotalDuration()
	}
	return duration
}

func parseConfigFile(configPath string) LegacyConfig {
	data, err := os.ReadFile(configPath)
	check(err)
	return parseConfig(data)
}

func parseLegacyConfigFile(configPath string) ([]TestConfig, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return nil, err
	}
	return parseLegacyConfig(data)
}

func parseLegacyConfig(data []byte) ([]TestConfig, error) {
	return nil, nil
}

func parseConfig(data []byte) LegacyConfig {
	rawConfig := RawConfig{}

	err := yaml.Unmarshal(data, &rawConfig)
	if err != nil {
		log.Fatalf("error: %v", err)
	}
	// fmt.Printf("--- raw config:\n%v\n\n", rawConfig)

	config := LegacyConfig{}
	config.Stages = make([]LegacyTestStage, 0)

	for _, s := range rawConfig.Stages {
		stageType := s.(map[interface{}]interface{})["type"]

		switch stageType {
		case StageStaticName:
			{
				// TODO: can this be deduped or rewritten?
				stage := StageStatic{}
				str, err := yaml.Marshal(&s)
				check(err)
				yaml.Unmarshal(str, &stage)

				config.Stages = append(config.Stages, stage)
			}
		case StageGradualName:
			{
				// TODO: can this be deduped or rewritten?
				stage := StageGradual{}
				str, err := yaml.Marshal(&s)
				check(err)
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
		check(err)
	}

	return config
}
