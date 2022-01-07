package main

import (
	"github.com/google/go-cmp/cmp"
	"testing"
)

// Tests _getU*serByStep functionality
func TestUsersByStep(t *testing.T) {
	tables := []struct {
		input    StageGradual
		expected []int64
	}{
		{
			input: StageGradual{
				Name:       "basic",
				StartUsers: 10,
				EndUsers:   20,
				Step:       5,
			},
			expected: []int64{10, 15, 20},
		},
		{
			input: StageGradual{
				Name:       "not exact",
				StartUsers: 10,
				EndUsers:   25,
				Step:       5,
			},
			expected: []int64{10, 15, 20, 25},
		},
		{
			input: StageGradual{
				Name:       "negative",
				StartUsers: 20,
				EndUsers:   10,
				Step:       -5,
			},
			expected: []int64{20, 15, 10},
		},
		{
			input: StageGradual{
				Name:       "negative not exact",
				StartUsers: 25,
				EndUsers:   10,
				Step:       -5,
			},
			expected: []int64{25, 20, 15, 10},
		},
	}

	for _, stageCase := range tables {
		actual := stageCase.input._getUsersByStep()

		if diff := cmp.Diff(stageCase.expected, actual); diff != "" {
			t.Errorf("Failed to calculate expected stages for '%s' (-expect +actual)\n %s",
				stageCase.input.Name, diff)
		}
	}
}
