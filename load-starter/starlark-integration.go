package main

import (
	"fmt"
	"go.starlark.net/starlark"
	"go.starlark.net/syntax"
	"time"
)

type LoadTestEnv struct {
	LoadTesterUrl string
	LoadTests     []TestConfig
}

func LoadStarlarkConfig(configPath string) (Config, error) {
	//	config, registerTest := registerTestGenerator()
	thread := &starlark.Thread{Name: "Starlark execution"}
	var env = starlark.StringDict{
		"duration": starlark.NewBuiltin("duration", newDuration),
		//		"register_test": starlark.NewBuiltin("register_test", registerTest),
		"Nanosecond":  StarlarkDuration{val: time.Nanosecond, frozen: true},
		"Microsecond": StarlarkDuration{val: time.Microsecond, frozen: true},
		"Millisecond": StarlarkDuration{val: time.Millisecond, frozen: true},
		"Second":      StarlarkDuration{val: time.Second, frozen: true},
		"Minute":      StarlarkDuration{val: time.Minute, frozen: true},
		"Hour":        StarlarkDuration{val: time.Hour, frozen: true},
		"Day":         StarlarkDuration{val: time.Hour * 24, frozen: true},
	}
	_, err := starlark.ExecFile(thread, configPath, nil, env)
	if err != nil {
		fmt.Printf("exec file error\n%s", err)
		return Config{}, err
	}
	// TODO fix this
	return Config{}, nil
}

/*
func registerTestGenerator() (*Config, func(thread *starlark.Thread, b *starlark.Builtin, args starlark.Tuple, kwargs []starlark.Tuple) (starlark.Value, error)) {
	var config Config
	// registerTest adds a test spec to the list of tests that will be run, it is added as the `register_test(time,freq,per,params)` builtin
	var registerTest = func(thread *starlark.Thread, b *starlark.Builtin, args starlark.Tuple, kwargs []starlark.Tuple) (starlark.Value, error) {
		var name starlark.String
		var description starlark.String
		var id starlark.String
		var duration starlark.Value

		var startUrl starlark.String
		var startMethod starlark.String
		var startBody starlark.String
		var startHeaders starlark.Dict

		var endUrl starlark.String
		var endMethod starlark.String
		var endBody starlark.String
		var endHeaders starlark.Dict

		if err := starlark.UnpackArgs(b.Name(), args, kwargs, "time", &time, "freq", &freq, "per", &per, "params", &params); err != nil {
			return nil, err
		}

		var time starlark.Value
		var freq starlark.Int
		var per starlark.Value
		//var params starlark.Dict
		var params starlark.Value
		if err := starlark.UnpackArgs(b.Name(), args, kwargs, "time", &time, "freq", &freq, "per", &per, "params", &params); err != nil {
			return nil, err
		}

		fmt.Println("register_test called")
		fmt.Printf("time=%v\n", time)
		fmt.Printf("freq=%v\n", freq)
		fmt.Printf("per=%v\n", per)
		fmt.Printf("params=%v\n", params)

		//if err != nil {
		//	return nil, err
		//}
		return starlark.None, nil

	}
	return &config, registerTest
}
*/
// StarlarkDuration type for working with Durations in Starlark
type StarlarkDuration struct {
	val    time.Duration
	frozen bool
}

// String implement Value for StarlarkDuration
func (d StarlarkDuration) String() string {
	return fmt.Sprintf("%v", d.val)
}

// Type implement Value for StarlarkDuration
func (d StarlarkDuration) Type() string {
	return "duration"
}

// Freeze implement Value for StarlarkDuration
func (d StarlarkDuration) Freeze() {
	d.frozen = true
}

// Truth implement Value for StarlarkDuration
func (d StarlarkDuration) Truth() starlark.Bool {
	if d.val == 0 {
		return starlark.False
	}
	return starlark.True
}

// Hash implement Value for StarlarkDuration
func (d StarlarkDuration) Hash() (uint32, error) {
	return uint32(d.val), nil
}

// Binary implement HasBinary in order to enable arithmetic operations on StarlarkDuration
func (d StarlarkDuration) Binary(op syntax.Token, y starlark.Value, side starlark.Side) (starlark.Value, error) {
	switch op {
	case syntax.PLUS:
		val, ok := y.(StarlarkDuration)
		if !ok {
			return nil, fmt.Errorf("invalid type:%t used for duration addition, only duration supported.",
				y)
		}
		return StarlarkDuration{d.val + val.val, false}, nil

	case syntax.MINUS:
		val, ok := y.(StarlarkDuration)
		if !ok {
			return nil, fmt.Errorf("invalid type:%t used for duration substraction, only duration supported.", y)
		}
		if side == starlark.Left {
			return StarlarkDuration{d.val - val.val, false}, nil
		} else {
			return StarlarkDuration{val.val - d.val, false}, nil
		}

	case syntax.SLASH:
		if side == starlark.Right {
			return nil, fmt.Errorf("a duration cannot appear to the right of a / operator")
		}
		intVal, ok := y.(starlark.Int)
		if ok {
			int64Val, ok := intVal.Int64()
			if !ok {
				return nil, fmt.Errorf("could not convert int to int64 %v, intVal")
			}
			return StarlarkDuration{time.Duration(int64(d.val) / int64Val), false}, nil
		}
		floatVal, ok := y.(starlark.Float)
		if ok {
			f := float64(floatVal)
			return StarlarkDuration{time.Duration(int64(float64(d.val) / f)), false}, nil
		}

		return nil, fmt.Errorf("unsupported type=%t for op /", y)

	case syntax.STAR:
		intVal, ok := y.(starlark.Int)
		if ok {
			int64Val, ok := intVal.Int64()
			if !ok {
				return nil, fmt.Errorf("could not convert int to int64 %v, intVal")
			}
			return StarlarkDuration{time.Duration(int64(d.val) * int64Val), false}, nil
		}
		floatVal, ok := y.(starlark.Float)
		if ok {
			f := float64(floatVal)
			return StarlarkDuration{time.Duration(int64(float64(d.val) * f)), false}, nil
		}

		return nil, fmt.Errorf("unsupported type=%t for op *", y)
	default:
		return nil, nil // op not handled
	}
}

// Unary implement HasUnary in order to enable -/+ unary operations on StarlarkDuration
func (d StarlarkDuration) Unary(op syntax.Token) (starlark.Value, error) {
	switch op {
	case syntax.MINUS:
		return StarlarkDuration{-d.val, false}, nil
	case syntax.PLUS:
		return d, nil // nothing to do, support the + duration syntax
	default:
		return nil, nil
	}
}

// newDuration creates a starlark duration from a string, it is added as the `duration(s)` builtin
func newDuration(thread *starlark.Thread, b *starlark.Builtin, args starlark.Tuple, kwargs []starlark.Tuple) (starlark.Value, error) {
	var s string
	if err := starlark.UnpackPositionalArgs(b.Name(), args, kwargs, 1, &s); err != nil {
		return nil, err
	}
	duration, err := time.ParseDuration(s)
	if err != nil {
		return nil, err
	}
	return StarlarkDuration{duration, false}, nil

}
