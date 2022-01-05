package main

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

type Config struct {
	Stages []TestStage
}

func (c Config) getTotalDuration() time.Duration {
	var duration time.Duration
	for _, stage := range c.Stages {
		duration += stage.getTotalDuration()
	}
	return duration
}

func parseConfigFile(configPath string) Config {
	data, err := os.ReadFile(configPath)
	check(err)
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
