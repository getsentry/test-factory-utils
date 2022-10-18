package main

import (
	"fmt"
	"os"
	"testing"
	"time"
)

func loadTestStarlarkConfig(content string) (*Config, error) {
	f, err := os.CreateTemp("", "*.py")
	configPath := f.Name()

	if err != nil {
		return nil, err
	}
	defer func() { _ = os.Remove(f.Name()) }()

	_, err = f.WriteString(content)
	if err != nil {
		return nil, err
	}
	_ = f.Close()

	config, err := LoadStarlarkConfig(configPath, nil, nil)
	return &config, err

}

const loadTestUrlScript = `
set_load_tester_url("some_url")
# need to also add a vegeta action to use the url
add_vegeta_test(duration="30s", test_type="x", name="n", description="d", freq=1, per="1s", config={})
`

func TestSetLoadTesterUrl(t *testing.T) {
	config, err := loadTestStarlarkConfig(loadTestUrlScript)

	if err != nil {
		t.Fatalf("failed to load config.\n%s", err)
	}

	if config == nil || config.RunActionList == nil || len(config.RunActionList) != 1 {
		t.Fatalf("invalid config returned")
	}

	action, ok := (config.RunActionList[0]).(VegetaTestAction)

	if !ok {
		t.Fatalf("expected a VegetaTestAction but got %T", config.RunActionList[0])
	}

	if action.LoadTesterUrl != "some_url" {
		t.Fatalf("expecte 'some_url' got '%s'", action.LoadTesterUrl)
	}
}

const vegetaTestsScript = `
add_vegeta_test(duration="1s", test_type="t1", freq=1, per="10s", config={"a":1}, name="n1")
add_vegeta_test(duration="2s", test_type="t2", freq=2, per="20s", config={"a":2}, description="d2")
add_vegeta_test(duration="3s", test_type="t3", freq=3, per="30s", config={"a":3}, url="u3")
add_vegeta_test(duration="4s", test_type="t4", freq=4, per="40s", config={"a":4}, produce_report=False)
add_vegeta_test(duration="5s", test_type="t5", freq=5, per="50s", config={"a":5}, produce_report=True)
`

func TestAddVegetaTest(t *testing.T) {
	config, err := loadTestStarlarkConfig(vegetaTestsScript)

	if err != nil {
		t.Fatalf("failed to load config.\n%s", err)
	}

	if config == nil || config.RunActionList == nil || len(config.RunActionList) != 5 {
		t.Fatalf("invalid config returned")
	}
	actions := config.RunActionList

	for idx := 0; idx < len(actions); idx++ {
		action, ok := (config.RunActionList[idx]).(VegetaTestAction)

		if !ok {
			t.Fatalf("expected a VegetaTestAction but got %T", config.RunActionList[0])
		}

		// number used in the test values
		num := idx + 1

		expectedDuration, _ := time.ParseDuration(fmt.Sprintf("%ds", num))
		if action.Duration != expectedDuration {
			t.Errorf("invalid duration expected: %s got %s", expectedDuration, action.Duration)
		}

		actualTestType := action.Spec["testType"]
		expectedTestType := fmt.Sprintf("t%d", num)
		if actualTestType != expectedTestType {
			t.Errorf("invalid test type actual:'%s' expected:'%s'", actualTestType, expectedTestType)
		}
		numMessages := action.Spec["numMessages"]
		expectedMessages := int64(num)
		if numMessages != expectedMessages {
			t.Errorf("invalid number of messages actual:'%d' expected:'%d'", numMessages, expectedMessages)
		}

		params := action.Spec["params"].(map[string]any)
		param := params["a"]
		expectedParam := int64(num)
		if param != expectedParam {
			t.Errorf("invalid freq expected: %d got %d", expectedParam, param)
		}

		switch idx {
		case 0:
			// name
			if action.Name != "n1" {
				t.Errorf("bad name expected n1 got '%s'", action.Name)
			}
		case 1:
			// description
			if action.Description != "d2" {
				t.Errorf("bad description expected d2 got '%s'", action.Description)
			}
		case 2:
			// url
			if action.LoadTesterUrl != "u3" {
				t.Errorf("bad url expected u3 got '%s'", action.LoadTesterUrl)
			}
			// also test default produce_report ( it should be true)
			if action.disableReport != false {
				t.Errorf("bad flag produce_report expected true got %t", !action.disableReport)
			}
		case 3:
			// produce_report = False
			if action.disableReport != true {
				t.Errorf("bad flag produce_report expected false got %t", !action.disableReport)
			}
		case 4:
			// produce_report = true
			if action.disableReport != false {
				t.Errorf("bad flag produce_report expected true got %t", !action.disableReport)
			}
		}
	}
}
