package main

import (
	"context"
	"fmt"
	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
	"os"
	"time"
)

func getKafkaLagQuery(bucketName string, measurement string) string {
	return fmt.Sprintf(`from(bucket: "%s")
  |> range(start: -1m)
  |> filter(fn: (r) => r["_measurement"] == "%s")
  |> group(columns:[], mode:"by")
  |> aggregateWindow(every: 2m, fn: max, createEmpty: false)`, bucketName, measurement)
}

type ErrorType int

const (
	BadQuery ErrorType = iota
	BadDataType
	NoResults
	NoData
	Stuck
	UnexpectedNilValue
)

func QueryInfluxDb() {

	// Create a new client using an InfluxDB server base URL and an authentication token
	client := influxdb2.NewClient(*Params.influxDbServer, *Params.influxDbToken)
	// Ensures background processes finishes
	defer client.Close()
	// Get query client
	queryAPI := client.QueryAPI(*Params.organisationId)
	// get QueryTableResult
	query := getKafkaLagQuery(*Params.bucketName, *Params.measurement)
	var dataValue, previousDataValue float64
	var sameQueueSizeCounter int
	for count := 0; ; count++ {
		// loop until data value drops to 0 or we get stuck
		ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
		result, err := queryAPI.Query(ctx, query)
		cancel()
		if err != nil {
			ExitWithError(BadQuery, err)
		}
		hasResults := result.Next()
		if !hasResults {
			fmt.Printf("No results found iteration:%d\n", count)
			if count > 2 {
				ExitWithError(NoResults, count)
			}

		} else {
			// Access data (first record)
			record := result.Record()
			if record == nil {
				ExitWithError(NoData, count)
			}
			data := record.Value()
			if data == nil {
				ExitWithError(UnexpectedNilValue, count)
			}
			var ok bool
			previousDataValue = dataValue
			dataValue, ok = data.(float64)
			if !ok {
				ExitWithError(BadDataType, data)
			}
			if dataValue == previousDataValue {
				sameQueueSizeCounter++
			} else {
				sameQueueSizeCounter = 0
			}
			if sameQueueSizeCounter > 2 {
				// queue size hasn't changed in the last few iteration time to stop
				ExitWithError(Stuck, dataValue)
			}

			if dataValue == 0.0 {
				return // we have caught up, we are done
			}
			// if  we are here we have activity wait till cancellation or till time
			// for another try
			fmt.Printf("Metric value: %v, continue waiting...\n", dataValue)
		}
		time.Sleep(30 * time.Second)
	}
}

func ExitWithError(errorCode ErrorType, aux interface{}) {

	var msg string
	switch errorCode {
	case BadQuery:
		msg = "Query failed:\n%s"
	case BadDataType:
		msg = "Data is not of the expected float64 type but %T"
	case Stuck:
		msg = "\nData stuck at %v"
	case NoResults:
		msg = "\nNo results found iteration:%d"
	case NoData:
		msg = "\nNo data found iteration:%d "
	case UnexpectedNilValue:
		msg = "\nNil data found in iteration:%d "
	}
	_, _ = fmt.Fprintf(os.Stderr, msg, aux)
	os.Exit(int(errorCode))
}

type CliParams struct {
	influxDbServer *string
	influxDbToken  *string
	organisationId *string
	dryRun         bool
	bucketName     *string
	measurement    *string
}

var Params CliParams

func ShowParams() {

	fmt.Printf(`
Cli parameters:
    dbServer: %s
    dbToken: %v
    orgId: %v
    bucketName: %s
    measurement: %s
    dryRun: %t`,
		*Params.influxDbServer, *Params.influxDbToken, *Params.organisationId, *Params.bucketName, *Params.measurement, Params.dryRun)

	fmt.Printf(`

Viper variables:
	influxdb-token: %s
	influxdb-url: %s`,
		viper.GetString("influxdb-token"), viper.GetString("influxdb-url"))

	fmt.Printf(`

Env variables:
	INFLUX_TOKEN: %s
	INFLUX_URL: %s`,
		os.Getenv("INFLUX_TOKEN"), os.Getenv("INFLUX_URL"))
}

func cliSetup() *cobra.Command {
	var rootCmd = &cobra.Command{
		Use:   "influxdb-monitor",
		Short: "Waits for a condition in InfluxDB to become True or an expiration time ",
		Run: func(cmd *cobra.Command, args []string) {
			if Params.dryRun {
				ShowParams()
			} else {
				QueryInfluxDb()
			}
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

	Params.influxDbServer = rootCmd.Flags().StringP("influxdb-url", "u", "", "InfluxDb url (e.g. http://localhost:8086)")
	Params.influxDbToken = rootCmd.Flags().StringP("influxdb-token", "x", "", "InfluxDb access token")
	Params.organisationId = rootCmd.Flags().StringP("organisation", "o", "", "the InfluxDb organisation id")
	Params.bucketName = rootCmd.Flags().StringP("bucket-name", "b", "statsd", "the bucket where the metric is stored")
	Params.measurement = rootCmd.Flags().StringP("measurement", "m", "kafka_consumer_lag", "the name of the measurement")
	rootCmd.Flags().BoolVarP(&Params.dryRun, "dry-run", "", false, "dry-run mode")

	flags := rootCmd.Flags()

	viper.BindPFlag("influxdb-token", flags.Lookup("influxdb-token"))
	viper.BindPFlag("influxdb-url", flags.Lookup("influxdb-url"))

	return rootCmd

}

func main() {
	var rootCmd = cliSetup()
	rootCmd.Execute()
}
