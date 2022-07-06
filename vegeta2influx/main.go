/*
Copyright © 2022 Sentry

This utility gets as input Vegeta response logs (in json format) and converts them into calls to InfluxDb.

It is meant to be used directly with the `vegeta` executable in this manner:

```
> vegeta attack --duration=1m --targets=targets.txt ... | vegeta encode | vegeta2influx --bucketName=myBucket ...
```

Another typical use is to first capture the attack in a file and then push the result to influx like so:

```
> vegeta attack --duration=1m --targets=targets.txt ... | vegeta encode > results.txt
> vegeta2influx --input=results.txt --bucketName=myBucket --influxdb-url=http://localhost:8086 ...
```

*/

package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/influxdata/influxdb-client-go/v2/api"
	"github.com/influxdata/influxdb-client-go/v2/api/write"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

type CliParams struct {
	influxDbServer string
	influxDbToken  string
	organisationId string
	dryRun         bool
	bucketName     string
	measurement    string
	input          string
	useColor       bool
	logLevel       string
	tagsRaw        []string
	//loaded from the result of parsing tagsRaw
	tags map[string]string
}

var Params CliParams

type VegetaResult struct {
	Attack    string      `json:"attack"`
	Seq       int64       `json:"seq"`
	Code      int         `json:"code"`
	Timestamp time.Time   `json:"timestamp"`
	Latency   int64       `json:"latency"`
	BytesOut  int64       `json:"bytes_out"`
	BytesIn   int64       `json:"bytes_in"`
	Error     string      `json:"error"`
	Body      interface{} `json:"body"`
}

// a WriteAPIBlocking that only writes to stdout (instead of sending to an influx backend)
type dryRunWriteAPIBlocking struct {
	precision time.Duration
}

func (api dryRunWriteAPIBlocking) WriteRecord(_ context.Context, lines ...string) error {
	for _, line := range lines {
		log.Info().Msg(line)
	}
	return nil
}

func (api dryRunWriteAPIBlocking) WritePoint(_ context.Context, points ...*write.Point) error {
	for _, point := range points {
		log.Info().Msg(write.PointToLineProtocol(point, api.precision))
	}
	return nil
}

func pushData() {
	ctx := context.Background()

	if Params.dryRun {
		log.Info().Msg("Dry Run, pretending to send messages:")
	} else {
		log.Info().Msgf("Writing to:\n"+
			"Server=%s\n"+
			"Organisation=%s\n"+
			"Bucket=%s\n"+
			"Measurement=%s\n",
			Params.influxDbServer, Params.organisationId, Params.bucketName, Params.measurement)
	}
	inputFile := os.Stdin
	if len(Params.input) > 0 {
		var err error
		inputFile, err = os.Open(Params.input)
		if err != nil {
			log.Error().Err(err).Msgf("Could not open inputFile: %s", Params.input)
			return
		}
		defer func() { _ = inputFile.Close() }()
	}

	var writeApi api.WriteAPIBlocking
	if Params.dryRun {
		precision, _ := time.ParseDuration("1ms")
		writeApi = &dryRunWriteAPIBlocking{precision: precision}
	} else {
		client := influxdb2.NewClient(Params.influxDbServer, Params.influxDbToken)

		_, err := client.Health(context.Background())

		if err != nil {
			log.Error().Err(err).Msg("Could not build client")
			return
		}

		writeApi = client.WriteAPIBlocking(Params.organisationId, Params.bucketName)
		// Ensures background processes finishes
		defer client.Close()
	}
	pushDataInternal(ctx, writeApi, inputFile, Params.measurement, Params.tags)
}

func pushDataInternal(ctx context.Context, writeApi api.WriteAPIBlocking, input io.Reader, measurement string, tags map[string]string) {
	scanner := bufio.NewScanner(input)
	for scanner.Scan() {
		var pointData VegetaResult
		text := scanner.Text()
		rawData := []byte(text)
		err := json.Unmarshal(rawData, &pointData)
		if err != nil {
			log.Error().Err(err).Msgf("Could not unmarshal response object into JSON, moving to the next one:\n %s", text)
			continue
		}
		writePoint(ctx, writeApi, pointData, measurement, tags)
		log.Trace().Msgf("Wrote point captured at:%s", pointData.Timestamp)
	}
}

func writePoint(ctx context.Context, api api.WriteAPIBlocking, pointData VegetaResult, measureName string, extraTags map[string]string) {

	var tags map[string]string
	if extraTags != nil {
		tags = make(map[string]string, len(extraTags)+2)
		for k, v := range extraTags {
			tags[k] = v
		}
	} else {
		tags = make(map[string]string, 2)
	}

	tags["attack"] = pointData.Attack
	tags["status"] = fmt.Sprintf("%d", pointData.Code)

	fields := map[string]any{
		"value":    pointData.Latency,
		"bytesIn":  pointData.BytesIn,
		"bytesOut": pointData.BytesOut,
	}

	point := influxdb2.NewPoint(measureName, tags, fields, pointData.Timestamp)
	err := api.WritePoint(ctx, point)

	if err != nil {
		log.Error().Err(err).Msgf("Failed to WritePoint to influx db")
	}
}

func cliSetup() *cobra.Command {

	var rootCmd = &cobra.Command{
		Use:   "vegeta2influx",
		Short: "Converts vegeta json report outputs to influxdb metric insert requests",
		Long: `Converts the output from a vegeta report into calls to insert metrics in InfluxDb

The input should be a sequence of Json documents, one per line.
This is what you get after a call to:  "vegeta attack --duration=1m | vegeta report".
Each line which is a JSON document of the form:
{"attack":"at1","seq":19,"code":200,"timestamp":"2022-07-04T17:52:06.096582044+02:00","latency":306656,"bytes_out":0,"bytes_in":0,"error":"","body":"..."}
Will be converted into a call to insert a point into influxDb.
The point inserted will have the name specified with the measurement CLI parameter
The date specified by the timestamp, the value will be latency field and attack and status fields will be saved as tags. 
`,
		Run: func(cmd *cobra.Command, args []string) {
			pushData()
		},
		PreRun: func(cmd *cobra.Command, args []string) {
			// viper variables come from environment and are overridden by cli params (exactly what we need)
			// override the fields in Params with them
			Params.influxDbToken = viper.GetString("token")
			Params.influxDbServer = viper.GetString("url")
			Params.organisationId = viper.GetString("org")
			Params.bucketName = viper.GetString("bucket")
			Params.measurement = viper.GetString("measurement")
			Params.tags = parseTags(Params.tagsRaw)
		},
	}

	rootCmd.PersistentFlags().StringVarP(&Params.influxDbServer, "influxdb-url", "u", "http://localhost:8086", "InfluxDB URL")
	rootCmd.PersistentFlags().StringVarP(&Params.influxDbToken, "influxdb-token", "x", "", "InfluxDB access token")
	rootCmd.PersistentFlags().StringVarP(&Params.organisationId, "organisation", "o", "", "InfluxDB organisation id")
	rootCmd.PersistentFlags().StringVarP(&Params.bucketName, "bucket-name", "b", "vegeta", "Bucket where the metric is stored")
	rootCmd.PersistentFlags().StringVarP(&Params.measurement, "measurement", "m", "request", "Name of the measurement (metric)")
	rootCmd.PersistentFlags().BoolVarP(&Params.dryRun, "dry-run", "d", false, "dry-run mode")
	rootCmd.PersistentFlags().StringVarP(&Params.input, "input", "i", "", "File name to use for input, default <stdin>")
	rootCmd.PersistentFlags().StringVarP(&Params.logLevel, "log", "l", "info", "Log level: trace, info, warn, (error), fatal, panic")
	rootCmd.PersistentFlags().BoolVarP(&Params.useColor, "color", "c", false, "Use color (only for console output).")
	rootCmd.PersistentFlags().StringArrayVarP(&Params.tagsRaw, "tags", "t", []string{}, "Additional tags -t name=value -t n2=v2")

	// bind env vars to viper vars
	_ = viper.BindEnv("token", "VE2IN_TOKEN")
	_ = viper.BindEnv("url", "VE2IN_URL")
	_ = viper.BindEnv("org", "VE2IN_ORG")
	_ = viper.BindEnv("bucket", "VE2IN_BUCKET")
	_ = viper.BindEnv("measurement", "VE2IN_MEASUREMENT")

	// bind flags to viper vars (will override environment variables)
	_ = viper.BindPFlag("token", rootCmd.PersistentFlags().Lookup("influxdb-token"))
	_ = viper.BindPFlag("url", rootCmd.PersistentFlags().Lookup("influxdb-url"))
	_ = viper.BindPFlag("org", rootCmd.PersistentFlags().Lookup("organisation"))
	_ = viper.BindPFlag("bucket", rootCmd.PersistentFlags().Lookup("bucket-name"))
	_ = viper.BindPFlag("measurement", rootCmd.PersistentFlags().Lookup("measurement"))

	return rootCmd
}

func main() {
	var rootCmd = cliSetup()
	initLogging()
	log.Info().Msg("vegeta2influx started, parsing input...")
	_ = rootCmd.Execute()
}

func initLogging() {
	var consoleWriter = zerolog.ConsoleWriter{Out: os.Stdout, NoColor: !Params.useColor,
		TimeFormat: "15:04:05"}
	log.Logger = zerolog.New(consoleWriter).With().Timestamp().Caller().Logger()

	var logLevel zerolog.Level

	switch strings.ToLower(Params.logLevel) {
	case "t", "trc", "trace":
		logLevel = zerolog.TraceLevel
	case "d", "dbg", "debug":
		logLevel = zerolog.DebugLevel
	case "i", "inf", "info":
		logLevel = zerolog.InfoLevel
	case "w", "warn", "warning":
		logLevel = zerolog.WarnLevel
	case "e", "err", "error":
		logLevel = zerolog.ErrorLevel
	case "f", "fatal":
		logLevel = zerolog.FatalLevel
	case "p", "panic":
		logLevel = zerolog.PanicLevel
	case "dis", "disable", "disabled":
		logLevel = zerolog.Disabled
	default:
		logLevel = zerolog.ErrorLevel
	}

	zerolog.SetGlobalLevel(logLevel)
}

func parseTags(tagsRaw []string) map[string]string {
	retVal := make(map[string]string)

	for _, tagRaw := range tagsRaw {
		ss := strings.Split(tagRaw, "=")
		if len(ss) != 2 {
			log.Warn().Msgf("Could not parse tag %s it must be in the format: -t key=value", ss)
			continue
		} else {
			retVal[ss[0]] = ss[1]
		}
	}
	return retVal
}
