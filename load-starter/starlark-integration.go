package main

import (
	"errors"
	"fmt"
	"os/exec"
	"reflect"

	// "os/exec"
	"time"

	"github.com/rs/zerolog/log"
	"go.starlark.net/starlark"
	"go.starlark.net/syntax"
)

type LoadTestEnv struct {
	LoadTesterUrl string
	LoadTests     []TestConfig
}

func LoadStarlarkConfig(configPath string) (Config, error) {
	thread := &starlark.Thread{Name: "Starlark execution"}
	var tests LoadTestEnv

	var env = starlark.StringDict{
		"duration":            starlark.NewBuiltin("duration", newDuration),
		"set_load_tester_url": starlark.NewBuiltin("set_load_tester_url", tests.setLoadTesterUrl),
		"add_locust_test":     starlark.NewBuiltin("add_locust_test", tests.addLocustTestBuiltin),
		"add_vegeta_test":     starlark.NewBuiltin("add_vegeta_test", tests.addVegetaTestBuiltin),
		"run_external":        starlark.NewBuiltin("run_external", tests.runExternalBuiltin),
		"Nanosecond":          StarlarkDuration{val: time.Nanosecond, frozen: true},
		"Microsecond":         StarlarkDuration{val: time.Microsecond, frozen: true},
		"Millisecond":         StarlarkDuration{val: time.Millisecond, frozen: true},
		"Second":              StarlarkDuration{val: time.Second, frozen: true},
		"Minute":              StarlarkDuration{val: time.Minute, frozen: true},
		"Hour":                StarlarkDuration{val: time.Hour, frozen: true},
		"Day":                 StarlarkDuration{val: time.Hour * 24, frozen: true},
	}
	_, err := starlark.ExecFile(thread, configPath, nil, env)
	if err != nil {
		fmt.Printf("exec file error\n%s", err)
		return Config{}, err
	}
	return Config{TestConfigs: tests.LoadTests}, nil
}

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

// toDuration tries to convert a starlark Value to Duration, it supports strings ( which parses into a time.Duration) or
// StarlarkDuration which unwraps into a native time.Duration
func toDuration(val starlark.Value) (time.Duration, error) {
	switch val.(type) {
	case starlark.String:
		return time.ParseDuration(val.(starlark.String).GoString())
	case StarlarkDuration:
		return val.(StarlarkDuration).val, nil
	}
	return 0, fmt.Errorf("cannot convert %T to duration", val)
}

func toInt(val starlark.Value) (int64, error) {
	intVal, ok := val.(starlark.Int)
	if !ok {
		return 0, fmt.Errorf("could not convert %v to int", val)
	}
	retVal, ok := intVal.Int64()
	if !ok {
		return 0, fmt.Errorf("could not convert %v to int64", intVal)
	}
	return retVal, nil
}

func toFloat(val starlark.Value) (float64, error) {
	floatVal, ok := val.(starlark.Float)
	if !ok {
		return 0, fmt.Errorf("could not convert %v to float", val)
	}
	return float64(floatVal), nil
}

func toString(rawVal starlark.Value) string {
	if rawVal == nil || rawVal == starlark.None {
		return ""
	}
	stringVal, ok := rawVal.(starlark.String)
	if ok {
		// starlark strings convert to string by wrapping in "<val>" the value, we don't need this
		return stringVal.GoString()
	}
	// if it is not a starlark string just use the String() representation
	return rawVal.String()
}

func toDict(rawVal starlark.Value) (map[string]interface{}, error) {

	if rawVal == nil || rawVal == starlark.None {
		return nil, nil
	}

	dictVal, ok := rawVal.(*starlark.Dict)

	if !ok {
		return nil, fmt.Errorf("could not convert value of type %T to dictionary", rawVal)
	}
	var retVal = make(map[string]interface{})

	for _, item := range dictVal.Items() {
		key, val, err := convertItem(item)
		if err != nil {
			return nil, err
		} else {
			retVal[key] = val
		}
	}

	return retVal, nil
}

func toArray(rawVal starlark.Value) ([]interface{}, error) {
	if rawVal == nil || rawVal == starlark.None {
		return nil, nil
	}
	var length int
	var values starlark.Iterator
	switch rawVal.(type) {
	case *starlark.List:
		values = rawVal.(*starlark.List).Iterate()
		length = rawVal.(*starlark.List).Len()
	case starlark.Tuple:
		values = rawVal.(starlark.Tuple).Iterate()
		length = rawVal.(starlark.Tuple).Len()
	case *starlark.Set:
		values = rawVal.(*starlark.Set).Iterate()
		length = rawVal.(*starlark.Set).Len()
	default:
		return nil, fmt.Errorf("invalid array type %s", rawVal.Type())
	}
	var retVal = make([]interface{}, 0, length)
	defer values.Done()
	var rawChild starlark.Value
	for values.Next(&rawChild) {
		val, err := convertValue(rawChild)
		if err != nil {
			return nil, err
		}
		retVal = append(retVal, val)
	}
	return retVal, nil
}

func convertValue(rawVal starlark.Value) (interface{}, error) {
	if rawVal == nil {
		return nil, nil
	}
	switch rawVal.(type) {
	case starlark.NoneType:
		return nil, nil
	case starlark.Int:
		val, err := toInt(rawVal)
		if err == nil {
			return val, nil
		} else {
			return nil, fmt.Errorf("could not convert to int %v\n err:%v", rawVal, err)
		}
	case starlark.Float:
		val, err := toFloat(rawVal)
		if err == nil {
			return val, nil
		} else {
			return nil, fmt.Errorf("could not convert to float64 %v\n err:%v", rawVal, err)
		}
	case starlark.String:
		val := rawVal.(starlark.String)
		return val.GoString(), nil
	case *starlark.Dict:
		val, err := toDict(rawVal)
		if err != nil {
			return nil, err
		} else {
			return val, nil
		}
	case *starlark.List, starlark.Tuple, *starlark.Set:
		val, err := toArray(rawVal)
		if err != nil {
			return nil, err
		} else {
			return val, nil
		}
	case StarlarkDuration:
		val := rawVal.(StarlarkDuration).String() // convert duration to string (so we can serialize it easily)
		return val, nil
	default:
		return nil, fmt.Errorf("%s unsupported type in dict", rawVal.Type())
	}
}

// convertItem converts a dictionary item which is a Tuple of length 2 into a string->value go tuple
// that can be inserted into
// a map[string] interface{}, the basic types of values are:
// * int
// * float
// * string
// * nil
// * []Value
// * map[string]Value
func convertItem(item starlark.Tuple) (string, interface{}, error) {
	if item == nil {
		return "", nil, errors.New("invalid nil item")
	}
	if len(item) != 2 {
		return "", nil, fmt.Errorf("invalid item len=%d expected 2", len(item))
	}
	var rawKey = item.Index(0)
	var rawVal = item.Index(1)

	rawKeyVal, ok := rawKey.(starlark.String)
	if !ok {
		return "", nil, fmt.Errorf("invalid key type=%s expected string", rawKey.Type())
	}
	var key = rawKeyVal.GoString()

	val, err := convertValue(rawVal)

	if err != nil {
		return "", nil, err
	}

	return key, val, nil
}

// setLoadTesterUrl implements the builtin set_load_tester_url(url=None) which sets the default URL for any test.
// A test can override the default URL by specifying a different URL.
// If there is no default URL set at the time when a test is added and the test does not specify a URL the add
// test operation will fail.
//
// setLoadTesterUrl can be called multiple times, the URL used for a test is set when the test is added (the
// addXXXTest operation) either to the URL specified in the addXXXTest call or to the last setLoadTesterUrl call.
//
// To remove the default load test Url, call it without a parameter or with None ( set_load_tester_url() )
func (env *LoadTestEnv) setLoadTesterUrl(thread *starlark.Thread, b *starlark.Builtin, args starlark.Tuple, kwargs []starlark.Tuple) (retVal starlark.Value, err error) {

	var url starlark.Value
	retVal = starlark.None

	if err = starlark.UnpackArgs(b.Name(), args, kwargs, "url?", &url); err != nil {
		return // error
	}
	if url == starlark.None {
		env.LoadTesterUrl = ""
		return // ok
	}

	urlStr, ok := url.(starlark.String)

	if !ok {
		err = fmt.Errorf("set_load_tester_url called with invalid type: %s", url.Type())
		return // error
	}

	env.LoadTesterUrl = urlStr.GoString()

	log.Trace().Msgf("Load tester Url set to %s\n", env.LoadTesterUrl)

	return // ok
}

// addLocustTestBuiltin implements the builtin add_locust_test(duration:str|duration, users:int,  spawn_rate:int|None=None,
// name:str|None=None,description:str|None, url:str|None, id:str|None=None)
func (env *LoadTestEnv) addLocustTestBuiltin(thread *starlark.Thread, b *starlark.Builtin, args starlark.Tuple, kwargs []starlark.Tuple) (retVal starlark.Value, err error) {
	var duration starlark.Value
	var users starlark.Int
	var spawnRate starlark.Value
	var name starlark.Value
	var description starlark.Value
	var url starlark.Value

	retVal = starlark.None

	if err = starlark.UnpackArgs(b.Name(), args, kwargs, "duration", &duration, "users", &users,
		"spawn_rate?", &spawnRate, "name?", &name, "description?", &description, "url?", &url); err != nil {
		return
	}

	var usersVal int64
	usersVal, err = toInt(users)
	if err != nil {
		return
	}

	var durationVal time.Duration
	durationVal, err = toDuration(duration)
	if err != nil {
		return
	}

	var spawnRateVal int64
	spawnRateVal, err = toInt(spawnRate)
	if err != nil {
		//use default
		spawnRateVal = usersVal / 4
	}

	var nameVal = toString(name)
	var descriptionVal = toString(description)
	var urlVal = toString(url)

	if len(urlVal) == 0 {
		urlVal = env.LoadTesterUrl
	}

	var testConfig = CreateLocustTestConfig(durationVal, nameVal, descriptionVal, urlVal, usersVal, spawnRateVal)
	env.LoadTests = append(env.LoadTests, testConfig)

	err = nil
	return
}

// addVegetaTestBuiltin implements the builtin add_vegeta_test(duration:str|duration, freq:int, per:str|duration,
//        config:dict, name:str|None=None, description:str|None=None)
func (env *LoadTestEnv) addVegetaTestBuiltin(thread *starlark.Thread, b *starlark.Builtin, args starlark.Tuple, kwargs []starlark.Tuple) (retVal starlark.Value, err error) {
	var duration starlark.Value
	var freq starlark.Int
	var per starlark.Value
	var config *starlark.Dict
	var name starlark.Value
	var description starlark.Value
	var url starlark.Value
	var testType starlark.String

	retVal = starlark.None

	if err = starlark.UnpackArgs(b.Name(), args, kwargs, "duration", &duration, "test_type", &testType, "freq", &freq,
		"per", &per, "config", &config, "name?", &name, "description?", &description, "url?", &url); err != nil {
		return
	}

	var durationVal time.Duration
	durationVal, err = toDuration(duration)
	if err != nil {
		return
	}

	var freqVal int64
	freqVal, err = toInt(freq)
	if err != nil {
		return
	}

	var perVal time.Duration
	perVal, err = toDuration(per)
	if err != nil {
		return
	}

	var configVal map[string]interface{}

	configVal, err = toDict(config)
	if err != nil {
		return
	}

	var nameVal = toString(name)
	var descriptionVal = toString(description)
	var urlVal = toString(url)
	var testTypeVal = toString(testType)

	if len(urlVal) == 0 {
		urlVal = env.LoadTesterUrl
	}

	var testConfig TestConfig
	testConfig, err = CreateVegetaTestConfig(durationVal, testTypeVal, freqVal, perVal.String(), configVal, nameVal, descriptionVal, urlVal)

	if err != nil {
		return
	}

	env.LoadTests = append(env.LoadTests, testConfig)

	return
}

// runExternalBuiltin implements the builtin run_external(command:str, arg1:str, arg2:str,...)
func (env *LoadTestEnv) runExternalBuiltin(thread *starlark.Thread, b *starlark.Builtin, args starlark.Tuple, kwargs []starlark.Tuple) (retVal starlark.Value, err error) {
	retVal = starlark.None

	var starlarkCmd *starlark.List

	if err = starlark.UnpackArgs(b.Name(), args, kwargs, "cmd", &starlarkCmd); err != nil {
		return
	}

	if len(kwargs) > 0 {
		err = errors.New("run_external: redundant kwargs")
		return
	}

	rawCmd, err := toArray(starlarkCmd)
	processedCmd := make([]string, 0, len(rawCmd))

	for _, val := range rawCmd {
		if reflect.TypeOf(val).Kind() == reflect.String {
			processedCmd = append(processedCmd, val.(string))
		} else {
			err = fmt.Errorf("run_external: invalid argument: %v", val)
			return
		}
	}

	command := exec.Command(processedCmd[0], processedCmd[1:]...)

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Not running the external command: `%v`", command)
	} else {
		log.Info().Msgf("Running external command: `%v`", command)
		err = command.Run()
	}

	if err != nil {
		return
	}

	err = nil
	return

	// var duration starlark.Value
	// var freq starlark.Int
	// var per starlark.Value
	// var config *starlark.Dict
	// var name starlark.Value
	// var description starlark.Value
	// var url starlark.Value
	// var testType starlark.String

	// retVal = starlark.None

	// if err = starlark.UnpackArgs(b.Name(), args, kwargs, "duration", &duration, "test_type", &testType, "freq", &freq,
	// 	"per", &per, "config", &config, "name?", &name, "description?", &description, "url?", &url); err != nil {
	// 	return
	// }

	// var durationVal time.Duration
	// durationVal, err = toDuration(duration)
	// if err != nil {
	// 	return
	// }

	// var freqVal int64
	// freqVal, err = toInt(freq)
	// if err != nil {
	// 	return
	// }

	// var perVal time.Duration
	// perVal, err = toDuration(per)
	// if err != nil {
	// 	return
	// }

	// var configVal map[string]interface{}

	// configVal, err = toDict(config)
	// if err != nil {
	// 	return
	// }

	// var nameVal = toString(name)
	// var descriptionVal = toString(description)
	// var urlVal = toString(url)
	// var testTypeVal = toString(testType)

	// if len(urlVal) == 0 {
	// 	urlVal = env.LoadTesterUrl
	// }

	// var testConfig TestConfig
	// testConfig, err = CreateVegetaTestConfig(durationVal, testTypeVal, freqVal, perVal.String(), configVal, nameVal, descriptionVal, urlVal)

	// if err != nil {
	// 	return
	// }

	// env.LoadTests = append(env.LoadTests, testConfig)

	// return
}
