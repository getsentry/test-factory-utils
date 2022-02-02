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

func QueryInfluxDb() {
	ctx, cancel := context.WithTimeout(context.Background(), *Params.timeout)
	defer cancel()

	// Create a new client using an InfluxDB server base URL and an authentication token
	client := influxdb2.NewClient(*Params.influxDbServer, *Params.influxDbToken)
	// Ensures background processes finishes
	defer client.Close()
	// Get query client
	queryAPI := client.QueryAPI(*Params.organisationId)
	// get QueryTableResult
	query := getKafkaLagQuery(*Params.bucketName, *Params.measurement)

	for {
		// loop until kafka_consumer_lag drops to 0 or we timeout
		result, err := queryAPI.Query(ctx, query)
		if err != nil {
			_, _ = fmt.Fprintf(os.Stderr, "Query failed:\n%s", err)
			os.Exit(2) // bad query
		}
		result.Next()
		// Access data (first row)
		data := result.Record().Value()
		if data == nil || data == 0.0 {
			return // if there is absolutely no data or we have caught up we are done
		}

		// if  we are here we have activity wait till cancellation or till time
		// for another try
		select {
		case <-time.After(30 * time.Second):
			continue // try again maybe the lag is at 0
		case <-ctx.Done():
			// request canceled exit with error
			_, _ = fmt.Fprintf(os.Stderr, "\nWaiting for kafka consumer lag timed out after %v  !!!", *Params.timeout)
			os.Exit(1)
		}
	}
}

type CliParams struct {
	timeout        *time.Duration
	influxDbServer *string
	influxDbToken  *string
	organisationId *string
	dryRun         bool
	bucketName     *string
	measurement    *string
}

var Params CliParams

func ShowParams() {

	fmt.Printf(`Cli parameters:
    timeout: %v
    dbServer: %s
    dbToken: %v
    orgId: %v
    bucketName: %s
    measurement: %s
    dryRun: %t`,
		Params.timeout, *Params.influxDbServer, *Params.influxDbToken, *Params.organisationId, *Params.bucketName, *Params.measurement, Params.dryRun)
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

	Params.timeout = rootCmd.Flags().DurationP("timeout", "t", time.Minute*2,
		"the maximum duration after which a timeout occurs")
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
