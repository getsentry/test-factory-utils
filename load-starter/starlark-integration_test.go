package main

import (
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
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
add_vegeta_test(duration="6s", test_type="t6", freq=6, per="60s", config={"a":6}, labels=[('l1','v1'),['l2','v2']])
add_vegeta_test(duration="7s", test_type="t7", freq=7, per="70s", config={"a":7}, labels=(('l1','v1'),['l2','v2']))
add_vegeta_test(duration="8s", test_type="t8", freq=8, per="80s", config={"a":8}, labels={'l1':'v1','l2':'v2'})
add_vegeta_test(duration="9s", test_type="t9", freq=9, per="90s", config={"a":9}, labels=[['l1','v1','v2']])
`

func TestAddVegetaTest(t *testing.T) {
	config, err := loadTestStarlarkConfig(vegetaTestsScript)

	if err != nil {
		t.Fatalf("failed to load config.\n%s", err)
	}

	if config == nil || config.RunActionList == nil || len(config.RunActionList) != 9 {
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
		case 5, 6, 7, 8:
			// labels (l1,v1), (l2,v2)
			params := action.Spec
			labels, ok := (params["labels"]).([][]string)

			if !ok {
				t.Errorf("could not get labels")
			}
			switch idx {
			case 5, 6:
				expectedLabels := [][]string{{"l1", "v1"}, {"l2", "v2"}}
				if diff := cmp.Diff(expectedLabels, labels); diff != "" {
					t.Errorf("expected label error (-want +got):\n%s", diff)
				}
			case 7:
				// labels come from a dict so they may be reversed:
				expectedLabels1 := [][]string{{"l1", "v1"}, {"l2", "v2"}}
				expectedLabels2 := [][]string{{"l2", "v2"}, {"l1", "v1"}}
				diff1 := cmp.Diff(expectedLabels1, labels)
				diff2 := cmp.Diff(expectedLabels2, labels)
				if diff1 != "" && diff2 != "" {
					// any of the two errors would do
					t.Errorf("expected label error (-want +got):\n%s", diff1)
				}
			}
			if idx == 8 {
				expectedLabels := [][]string{{"l1", "v1", "v2"}}
				if diff := cmp.Diff(expectedLabels, labels); diff != "" {
					t.Errorf("expected label error (-want +got):\n%s", diff)
				}
			}
		}
	}
}

const locustTestsScript = `
add_locust_test(duration="1s", users=100, spawn_rate=10, name="n1", description="d1", url="some_url", produce_report=True)
add_locust_test(duration="2s", users=200, produce_report=False)
add_locust_test(duration="3s", users=300)
`

func TestAddLocustTest(t *testing.T) {
	config, err := loadTestStarlarkConfig(locustTestsScript)

	if err != nil {
		t.Fatalf("failed to load config.\n%s", err)
	}

	if config == nil || config.RunActionList == nil || len(config.RunActionList) != 3 {
		t.Fatalf("invalid config returned")
	}
	actions := config.RunActionList

	for idx := 0; idx < len(actions); idx++ {
		action, ok := (config.RunActionList[idx]).(LocustTestAction)

		if !ok {
			t.Fatalf("expected a LocustTestAction but got %T", config.RunActionList[0])
		}

		// number used in the test values
		num := idx + 1

		expectedDuration, _ := time.ParseDuration(fmt.Sprintf("%ds", num))
		if action.Duration != expectedDuration {
			t.Errorf("invalid duration expected: %s got %s", expectedDuration, action.Duration)
		}

		spec := action.Spec
		users := spec["users"].(int64)
		spawnRate := spec["spawnRate"]
		expectedParam := int64(num)

		if users != expectedParam*100 {
			t.Errorf("unexpected number of users expected:%d got:%d", users, expectedParam*100)
		}

		switch idx {
		case 0:
			if spawnRate != expectedParam*10 {
				t.Errorf("unexpected spwan rates expected:%d got:%d", expectedParam*10, spawnRate)
			}
			if action.Name != "n1" {
				t.Errorf("bad name expected n1 got '%s'", action.Name)
			}
			if action.Description != "d1" {
				t.Errorf("bad description expected d2 got '%s'", action.Description)
			}
			if action.Runner != "locust" {
				t.Errorf("bad runner expected 'locust' got '%s'", action.Runner)
			}
			if action.LoadTesterUrl != "some_url" {
				t.Errorf("bad url expected 'some_url' got '%s'", action.LoadTesterUrl)
			}
			if action.disableReport != false {
				t.Errorf("unexpected produce report state for test 0 expected True got False")
			}
		case 1:
			if action.disableReport != true {
				t.Errorf("unexpected produce report state for test 1 expected False got True")
			}
			// if not explicitly provided spawnRate is numUsers/4
			if spawnRate != users/4 {
				t.Errorf("unexpected spwan rates expected:%d got:%d", expectedParam*10, spawnRate)
			}

		case 2:
			if action.disableReport != false {
				t.Errorf("unexpected produce report state for test 2 expected True got False")
			}
			// if not explicitly provided spawnRate is numUsers/4
			if spawnRate != users/4 {
				t.Errorf("unexpected spwan rates expected:%d got:%d", expectedParam*10, spawnRate)
			}
		}
	}
}

const addRunExternal = `
add_run_external(["ls","-al"])
`

func TestAddRunExternalTest(t *testing.T) {
	config, err := loadTestStarlarkConfig(addRunExternal)

	if err != nil {
		t.Fatalf("failed to load config.\n%s", err)
	}

	if config == nil || config.RunActionList == nil || len(config.RunActionList) != 1 {
		t.Fatalf("invalid config returned")
	}

	action, ok := (config.RunActionList[0]).(RunExternalAction)

	if !ok {
		t.Fatalf("expected a LocustTestAction but got %T", config.RunActionList[0])
	}

	cmd := action.cmd

	if len(cmd) != 2 {
		t.Fatalf("Expected 2 commands got %d", len(cmd))
	}

	if cmd[0] != "ls" || cmd[1] != "-al" {
		t.Errorf("wrong values expected 'ls','-al' got '%s','%s'", cmd[0], cmd[1])
	}

}

const addSleep = `
add_sleep("20s")
`

func TestAddSleepTest(t *testing.T) {
	config, err := loadTestStarlarkConfig(addSleep)

	if err != nil {
		t.Fatalf("failed to load config.\n%s", err)
	}

	if config == nil || config.RunActionList == nil || len(config.RunActionList) != 1 {
		t.Fatalf("invalid config returned")
	}

	action, ok := (config.RunActionList[0]).(SleepAction)

	if !ok {
		t.Fatalf("expected a LocustTestAction but got %T", config.RunActionList[0])
	}

	if action.duration != time.Second*20 {
		t.Errorf("sleep expected 20s got %s", action.duration.String())
	}

}
