package main

import (
	"context"
	"fmt"
	"io/ioutil"
	"os"
	"strings"
	"text/template"
	"time"

	influxdb2 "github.com/influxdata/influxdb-client-go/v2"
	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

type ErrorType int

const (
	BadQuery ErrorType = iota
	BadDataType
	NoResults
	NoData
	Stuck
	UnexpectedNilValue
	BadFilter
)

type CliParams struct {
	influxDbServer *string
	influxDbToken  *string
	organisationId *string
	dryRun         bool
	bucketName     *string
	measurement    *string
	filters        *[]string
}

var Params CliParams

func getKafkaLagQuery(bucketName string, measurement string, filters []string) string {
	// Prepare filters
	formatted_entries := []string{}
	for _, filter := range filters {
		elements := strings.Split(filter, "=")
		if len(elements) != 2 {
			ExitWithError(BadFilter, filter)
		}
		name := elements[0]
		value := elements[1]
		formatted_entries = append(formatted_entries, fmt.Sprintf("  |> filter(fn: (r) => r[\"%s\"] == \"%s\")", name, value))
	}
	filtering_entries := strings.Join(formatted_entries, "\n")
	if len(filtering_entries) > 0 {
		filtering_entries = "\n" + filtering_entries
	}

	// Prepare the query
	query := fmt.Sprintf(`
from(bucket: "%s")
  |> range(start: -1m)
  |> filter(fn: (r) => r["_measurement"] == "%s")%s
  |> last()`,
		bucketName, measurement, filtering_entries)

	return query
}

func QueryInfluxDb() {
	fmt.Printf("Using InfluxDB URL: %s\n", *Params.influxDbServer)

	// Create a new client using an InfluxDB server base URL and an authentication token
	client := influxdb2.NewClient(*Params.influxDbServer, *Params.influxDbToken)
	// Ensures background processes finishes
	defer client.Close()
	// Get query client
	queryAPI := client.QueryAPI(*Params.organisationId)
	// get QueryTableResult
	query := getKafkaLagQuery(*Params.bucketName, *Params.measurement, *Params.filters)
	fmt.Printf("InfluxDB query:\n%s\n\n", query)

	fmt.Printf("Waiting for measurement '%s' to drop to 0...\n", *Params.measurement)
	const waitTime = 30 * time.Second
	var dataValue, previousDataValue float64
	var sameQueueSizeCounter int
	for count := 0; ; count++ {
		// loop until data value drops to 0 or we get stuck
		ctx, cancel := context.WithTimeout(context.Background(), waitTime)
		result, err := queryAPI.Query(ctx, query)
		cancel()
		if err != nil {
			ExitWithError(BadQuery, err)
		}
		hasResults := result.Next()
		if !hasResults {
			fmt.Printf("No results found at iteration: %d, waiting...\n", count)
			// FIXME(anton): make the max count configurable
			if count > 5 {
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
				// queue size hasn't changed in the last few iterations, time to stop
				ExitWithError(Stuck, dataValue)
			}

			if dataValue == 0.0 {
				return // we have caught up, we are done
			}
			// if  we are here we have activity wait till cancellation or till time
			// for another try
			fmt.Printf("Current metric value: %v, continue waiting...\n", dataValue)
		}
		time.Sleep(30 * time.Second)
	}
}

func ExitWithError(errorCode ErrorType, aux interface{}) {

	var msg string
	switch errorCode {
	case BadQuery:
		msg = "Query failed:\n%s\n"
	case BadDataType:
		msg = "Data is not of the expected 'float64' type but '%T'\n"
	case Stuck:
		msg = "\nData stuck at %v"
	case NoResults:
		msg = "\nNo results found at iteration: %d"
	case NoData:
		msg = "\nNo data found at iteration: %d"
	case UnexpectedNilValue:
		msg = "\nNil data found at iteration: %d"
	case BadFilter:
		msg = "\nInvalid filter specified: %s\n"
	}
	_, _ = fmt.Fprintf(os.Stderr, msg, aux)
	os.Exit(int(errorCode))
}

func ShowParams() {

	fmt.Printf(`
Cli parameters:
    dbServer: %s
    dbToken: %v
    orgId: %v
    bucketName: %s
    measurement: %s
    filters: %v
    dryRun: %t`,
		*Params.influxDbServer, *Params.influxDbToken, *Params.organisationId, *Params.bucketName, *Params.measurement, *Params.filters, Params.dryRun)

	fmt.Printf(`

Viper variables:
	influxdb-token: %s
	influxdb-url: %s`,
		viper.GetString("influxdb-token"), viper.GetString("influxdb-url"))

	fmt.Printf(`

Env variables:
	INFLUX_TOKEN: %s
	INFLUX_URL: %s
`,
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
			// Horrible hack (probably I'm missing something on how cobra/viper integration is supposed to work)
			// I would expect to have viper populate params automatically (somehow that's not happening)
			*Params.influxDbToken = viper.GetString("influxdb-token")
			*Params.influxDbServer = viper.GetString("influxdb-url")
		},
	}

	viper.BindEnv("influxdb-token", "INFLUX_TOKEN")
	viper.BindEnv("influxdb-url", "INFLUX_URL")

	Params.influxDbServer = rootCmd.Flags().StringP("influxdb-url", "u", "http://localhost:8086", "InfluxDB URL")
	Params.influxDbToken = rootCmd.Flags().StringP("influxdb-token", "x", "", "InfluxDB access token")
	Params.organisationId = rootCmd.Flags().StringP("organisation", "o", "", "InfluxDB organisation id")
	Params.bucketName = rootCmd.Flags().StringP("bucket-name", "b", "statsd", "Bucket where the metric is stored")
	Params.measurement = rootCmd.Flags().StringP("measurement", "m", "kafka_consumer_lag", "Name of the measurement (metric)")
	Params.filters = rootCmd.Flags().StringSliceP("filter", "f", []string{}, "Measurement filters (0 or more) in the format: filter-name=filter-value")
	rootCmd.Flags().BoolVarP(&Params.dryRun, "dry-run", "", false, "dry-run mode")

	flags := rootCmd.Flags()

	viper.BindPFlag("influxdb-token", flags.Lookup("influxdb-token"))
	viper.BindPFlag("influxdb-url", flags.Lookup("influxdb-url"))

	update_doc_cmd := &cobra.Command{
		Use: "update-docs",
        Short: "Update the documentation",
        Long: "generates README.md file from README-template.md and progam usage.",
		Run: func(cmd *cobra.Command, args []string) { updateDocs(rootCmd) },
	}
	rootCmd.AddCommand(update_doc_cmd)

	return rootCmd
}

func updateDocs(cmd *cobra.Command) {
	fmt.Println("Updating documentation...")

	templateRaw, err := ioutil.ReadFile("README-template.md")
	if err != nil {
		fmt.Printf("Could not generate documentation, error reading README-template.md: %s\n", err)
		return
	}
	parsedTemplate, err := template.New("template").Parse(string(templateRaw))
	usage := cmd.UsageString()


	readmeFile, err := os.Create("README.md")

	params := struct{
	    Usage string
	    }{
		Usage: usage,
	}

	parsedTemplate.Execute(readmeFile, params)
	if err != nil {
		fmt.Printf("Could not generate documentation, error creating README.md file: %s\n",err)
		return
	}

	defer func() { _ = readmeFile.Close() }()
}


func main() {
	var rootCmd = cliSetup()
	rootCmd.Execute()
}
