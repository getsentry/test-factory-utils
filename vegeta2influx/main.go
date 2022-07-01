package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"

	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/influxdata/influxdb-client-go/v2/api"
	"github.com/influxdata/influxdb-client-go/v2/api/write"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

type CliParams struct {
	influxDbServer *string
	influxDbToken  *string
	organisationId *string
	dryRun         bool
	bucketName     *string
	measurement    *string
	input          *string
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

func (api dryRunWriteAPIBlocking) WriteRecord(ctx context.Context, lines ...string) error {
	for _, line := range lines {
		fmt.Println(line)

	}
	return nil
}

func (api dryRunWriteAPIBlocking) WritePoint(ctx context.Context, points ...*write.Point) error {
	for _, point := range points {
		fmt.Print(write.PointToLineProtocol(point, api.precision))
	}
	return nil
}

func pushData() {

	file := os.Stdin
	ctx := context.Background()
	if Params.input != nil && len(*Params.input) > 0 {
		var err error
		file, err = os.Open(*Params.input)
		if err != nil {
			//TODO add logging
			fmt.Printf("Could not open file: %s\n%s\nQUITTING!", *Params.input, err)
			return
		}
		defer file.Close()
	}
	scanner := bufio.NewScanner(file)

	var writeApi api.WriteAPIBlocking
	if Params.dryRun {
		precision, _ := time.ParseDuration("1ms")
		writeApi = &dryRunWriteAPIBlocking{precision: precision}
	} else {
		client := influxdb2.NewClient(*Params.influxDbServer, *Params.influxDbToken)
		writeApi = client.WriteAPIBlocking(*Params.organisationId, *Params.bucketName)
		// Ensures background processes finishes
		defer client.Close()
	}
	for scanner.Scan() {
		var pointData VegetaResult
		rawData := []byte(scanner.Text())
		err := json.Unmarshal(rawData, &pointData)

		if err != nil {
			//TODO Log error
			continue
		}
		writePoint(ctx, writeApi, pointData, *Params.measurement)
	}
}

func writePoint(ctx context.Context, api api.WriteAPIBlocking, pointData VegetaResult, measureName string) {

	tags := map[string]string{
		"attack": pointData.Attack,
		"status": fmt.Sprintf("%d", pointData.Code),
	}
	fields := map[string]any{
		"value": pointData.Latency,
	}

	point := influxdb2.NewPoint(measureName, tags, fields, pointData.Timestamp)
	_ = api.WritePoint(ctx, point)
}

func cliSetup() *cobra.Command {
	var rootCmd = &cobra.Command{
		Use:   "influxdb-monitor",
		Short: "Waits for a condition in InfluxDB to become True or an expiration time ",
		Run: func(cmd *cobra.Command, args []string) {
			pushData()
		},
		PreRun: func(cmd *cobra.Command, args []string) {
			//Horrible hack (probably I'm missing something on how cobra/viper integration is supposed to work)
			//I would expect to have viper populate params automatically (somehow that's not happening)
			*Params.influxDbToken = viper.GetString("influxdb-token")
			*Params.influxDbServer = viper.GetString("influxdb-url")
		},
	}

	viper.BindEnv("influxdb-token", "INFLUX_TOKEN")
	viper.BindEnv("influxdb-url", "INFLUX_URL")

	Params.influxDbServer = rootCmd.Flags().StringP("influxdb-url", "u", "http://localhost:8086", "InfluxDB URL")
	Params.influxDbToken = rootCmd.Flags().StringP("influxdb-token", "x", "", "InfluxDB access token")
	Params.organisationId = rootCmd.Flags().StringP("organisation", "o", "", "InfluxDB organisation id")
	Params.bucketName = rootCmd.Flags().StringP("bucket-name", "b", "vegeta", "Bucket where the metric is stored")
	Params.measurement = rootCmd.Flags().StringP("measurement", "m", "request", "Name of the measurement (metric)")
	rootCmd.Flags().BoolVarP(&Params.dryRun, "dry-run", "", false, "dry-run mode")
	Params.input = rootCmd.Flags().StringP("input", "i", "", "Filname to use for input, default <stdin>")

	flags := rootCmd.Flags()

	viper.BindPFlag("influxdb-token", flags.Lookup("influxdb-token"))
	viper.BindPFlag("influxdb-url", flags.Lookup("influxdb-url"))

	return rootCmd
}

func main() {
	fmt.Println("Pushing data!!! ")
	var rootCmd = cliSetup()
	rootCmd.Execute()
}
