package main

import (
	"fmt"
	"io/ioutil"
	"net/url"
	"os"
	"strconv"
	"strings"
	"text/template"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
)

const (
	DefaultLocustServer = "http://ingest-load-tester.default.svc.cluster.local"
	DefaultLoadServer   = "http://go-load-tester.default.svc.cluster.local"
	InfluxDateFormat    = "2006-01-02T15:04:05Z"
	SlackDateFormat     = "Mon 02 Jan 06 15:04:05 MST"
)

const slackTemplate = `---
# These blocks will be placed in the beginning of the message
header_blocks:
- type: header
  text:
    type: plain_text
    text: Test report

# These blocks will be rendered as attachments
attachment_blocks:
- type: section
  text:
    type: mrkdwn
    text: "%s"
- type: section
  fields:
    - type: mrkdwn
      text: |-
        *Test start:*
        %s
- type: section
  fields:
    - type: mrkdwn
      text: |-
        *Test end:*
        %s
    - type: mrkdwn
      text: |-
        *Total Duration:*
        %s
`

// Command line arguments
type CliParams struct {
	// InfluxDB-specific params
	influxServerName     *string
	influxOrganisationId *string
	influxBoardId        *string

	// Grafana-specific params
	grafanaServerName     *string
	grafanaBoardId        *string
	grafanaOrganisationId *string

	locustServerUrl      *string
	loadServerUrl        *string
	dryRun               bool
	configFilePath       *string
	reportFilePath       *string
	slackMessageFilePath *string
	logLevel             string
	useColor             bool
}

type DashboardLink struct {
	name string
	url  string
}

var Params CliParams

func cliSetup() *cobra.Command {
	var rootCmd = &cobra.Command{
		Short: "Drives load tests by sending commands to a load tester",
		Long: `The sequence of load tests are specified in a starlark script.
ingest-load-tester (a Locust based tool) and go-load-tester (a Vegeta based tool) are supported.`,
		Use: "load-starter --config config.py --report report.yaml ",
		Run: func(cmd *cobra.Command, args []string) { runLoadStarter() },
	}
	rootCmd.Flags()

	Params.locustServerUrl = rootCmd.Flags().StringP("locust", "l", DefaultLocustServer, "Locust server endpoint (deprecated)")

	Params.loadServerUrl = rootCmd.Flags().String("load-server", DefaultLoadServer, "Load server endpoint")

	Params.influxServerName = rootCmd.Flags().String("influx-base", "", "InfluxDB dashboard base URL")

	Params.influxOrganisationId = rootCmd.Flags().String("influx-organisation", "", "InfluxDb organisation id")

	Params.influxBoardId = rootCmd.Flags().String("influx-board", "", "InfluxDb board id")

	Params.grafanaServerName = rootCmd.Flags().String("grafana-base", "", "Grafana base URL")

	Params.grafanaBoardId = rootCmd.Flags().String("grafana-board", "", "Grafana board id")

	Params.grafanaOrganisationId = rootCmd.Flags().String("grafana-organisation", "", "Grafana board id")

	rootCmd.Flags().BoolVarP(&Params.dryRun, "dry-run", "", false, "dry-run mode")

	Params.configFilePath = rootCmd.Flags().StringP("config", "f", "", "Path to a skylark configuration file")

	Params.reportFilePath = rootCmd.Flags().StringP("report", "r", "", "If provided: report will be written here")

	Params.slackMessageFilePath = rootCmd.Flags().StringP("slack-message", "s", "", "If provided: notification report (simply put, a formatted Slack message) will be written here")

	rootCmd.PersistentFlags().StringVar(&Params.logLevel, "log", "info", "Log level: trace, debug, (info), warn, error, fatal, panic")
	rootCmd.PersistentFlags().BoolVar(&Params.useColor, "color", false, "Use color (only for console output).")

	_ = rootCmd.Flags().MarkDeprecated("locust", "locust flag is deprecated, please use load-tester instead")

	update_doc_cmd := &cobra.Command{
		Use: "update-docs",
        Short: "Update the documentation",
        Long: "generates README.md file from README-template.md and progam usage.",
		Run: func(cmd *cobra.Command, args []string) { updateDocs(rootCmd) },
	}
	rootCmd.AddCommand(update_doc_cmd)

	cobra.OnInitialize(initConfig)
	return rootCmd
}

// initConfig call after Cobra has read the configuration, all the settings should be ready in Params
func initConfig() {
	// setup logging
	var consoleWriter = zerolog.ConsoleWriter{Out: os.Stdout, NoColor: Params.useColor,
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

func executeConfig(config Config) CombinedReport {
	var retVal = CombinedReport{
		StartTime: time.Now().UTC(),
		TestRuns:  make([]RunReport, 0, len(config.RunActionList)),
	}

	for _, action := range config.RunActionList {
		testInfo := action.GetTestInfo()

		if testInfo == nil {
			// Non-test action
			log.Info().Msg("")
			log.Info().Msgf("--- Action '%s' ---", action.GetName())
			log.Info().Msgf("Planned duration: %s", action.GetDuration())
			var err = action.Run()
			if err != nil {
				log.Error().Err(err).Msgf("Failed to run a non-test action: %s", action.GetName())
			}
		} else {
			// Test action
			var run = RunReport{
				TestInfo:  *testInfo,
				StartTime: time.Now().UTC(),
			}
			log.Info().Msg("")
			log.Info().Msgf("--- Test '%s' ---", run.Name)
			log.Info().Msgf("Planned duration: %s", run.Duration)

			var err = action.Run()
			run.EndTime = time.Now().UTC()
			if err != nil {
				log.Error().Err(err).Msgf("Failed to run a test action: %s", action.GetName())
			}
			retVal.TestRuns = append(retVal.TestRuns, run)
		}

	}
	retVal.EndTime = time.Now().UTC()
	return retVal
}

func writeReportToFile(report CombinedReport) {
	if *Params.reportFilePath == "" {
		log.Info().Msg("No report file path provided, not writing the report to file.\n")
		return
	}

	reportData, err := yaml.Marshal(report)
	check(err)

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Would write the following report to %s:\n~~~\n%s~~~\n", *Params.reportFilePath, reportData)
	} else {
		err = os.WriteFile(*Params.reportFilePath, reportData, 0644)
		check(err)
	}
	log.Info().Msgf("Wrote run report to: %s", *Params.reportFilePath)
}

func runLoadStarter() {
	if Params.dryRun {
		log.Info().Msg("NOTE: Dry-run mode is ON")
	}

	var config Config
	var err error

	log.Info().Msg("")
	log.Info().Msg("--- Prepare ---")
	log.Info().Msg("Initializing the run...")

	var configPath = *Params.configFilePath
	if configPath != "" {
		if IsStarlarkConfig(configPath) {
			config, err = LoadStarlarkConfig(configPath, Params.loadServerUrl, Params.locustServerUrl)
		}
		if err != nil {
			log.Error().Err(err).Msgf("Failed to load config file from: %s", configPath)
			return
		}

	}
	var totalDuration = config.GetDuration()
	log.Info().Msgf("Total estimated running time: %s", totalDuration)
	log.Info().Msgf("Estimated completion time: %s", time.Now().UTC().Add(totalDuration))
	var report = executeConfig(config)

	log.Info().Msg("")
	log.Info().Msg("--- Report ---")
	log.Info().Msg("Finished all test steps, preparing the report...")
	writeReportToFile(report)
	writeSlackMessage(report.StartTime, report.EndTime, config)
}

func buildDashboardLinks(startTime time.Time, endTime time.Time, buffer time.Duration) []DashboardLink {
	dashboardLinks := make([]DashboardLink, 0)

	// Some buffer time to make sure we capture a little before and after the test
	startTimeStamp := startTime.Add(-buffer)
	endTimeStamp := endTime.Add(buffer)

	if *Params.influxServerName != "" {
		queryString := url.Values{}

		queryString.Add("lower", startTimeStamp.Format(InfluxDateFormat))
		queryString.Add("upper", endTimeStamp.Format(InfluxDateFormat))

		reportUrl := fmt.Sprintf("%s/orgs/%s/dashboards/%s?%s",
			*Params.influxServerName, *Params.influxOrganisationId, *Params.influxBoardId, queryString.Encode(),
		)

		dashboardLinks = append(dashboardLinks, DashboardLink{url: reportUrl, name: "InfluxDB"})
	}

	if *Params.grafanaServerName != "" {
		queryString := url.Values{}

		queryString.Add("orgId", *Params.grafanaOrganisationId)
		queryString.Add("from", strconv.FormatInt(startTimeStamp.UnixMilli(), 10))
		queryString.Add("to", strconv.FormatInt(endTimeStamp.UnixMilli(), 10))

		reportUrl := fmt.Sprintf("%s/d/%s/?%s",
			*Params.grafanaServerName, *Params.grafanaBoardId, queryString.Encode(),
		)

		dashboardLinks = append(dashboardLinks, DashboardLink{url: reportUrl, name: "Grafana"})
	}

	return dashboardLinks
}

// Constructs a Slack Notification with the URL of the influx db dashboard for the test
func writeSlackMessage(startTime time.Time, endTime time.Time, config Config) {
	if *Params.slackMessageFilePath == "" {
		log.Info().Msg("No Slack message path provided, not writing it.")
		return
	}

	reportUrls := buildDashboardLinks(startTime, endTime, 30*time.Second)

	var reportText string
	if len(reportUrls) == 0 {
		reportText = "(no links to report)"
	} else {
		reportText = ""
		for _, dashboardLink := range reportUrls {
			reportText += fmt.Sprintf("<%s|View data (%s)>\\n", dashboardLink.url, dashboardLink.name)
		}
	}

	// Only print number of users when the only testing stage is "static"
	runDuration := config.GetDuration()

	rawMessage := fmt.Sprintf(slackTemplate,
		reportText,
		startTime.Local().Format(SlackDateFormat),
		endTime.Local().Format(SlackDateFormat),
		runDuration,
	)

	var testObj map[string]interface{}

	log.Info().Msg("Validating the message...")
	log.Debug().Msgf("Raw message:\n%s", rawMessage)
	// This will check that the rendered message is actually a valid YAML, and e.g. that there are no tabs in it, among other things

	err := yaml.Unmarshal([]byte(rawMessage), &testObj)
	check(err)

	if Params.dryRun {
		log.Info().Msgf("[dry-run] Would write the following Slack yaml to %s:\n~~~\n%s~~~\n", *Params.slackMessageFilePath, rawMessage)
	} else {
		err = os.WriteFile(*Params.slackMessageFilePath, []byte(rawMessage), 0644)
		check(err)
	}
	fmt.Printf("Wrote Slack message to: %s\n", *Params.slackMessageFilePath)

	return
}

func main() {
	var rootCmd = cliSetup()
	err := rootCmd.Execute()
	if err != nil {
		// fall back on printf (not sure if log is initialized)
		fmt.Printf("Could not execute command %s", err)
	}
}

func updateDocs(cmd *cobra.Command) {
	fmt.Println("Updating documentation...")

	templateRaw, err := ioutil.ReadFile("README-template.md")
	if err != nil {
		log.Fatal().Err(err).Msg("Could not generate documentation, error reading README-template.md: %s\n")
		return
	}
	parsedTemplate, err := template.New("template").Parse(string(templateRaw))
	usage := cmd.UsageString()

    var example_report_file_name = "example-report.yaml"
    exampleReport, err := ioutil.ReadFile(example_report_file_name)
	if err != nil {
		log.Fatal().Err(err).Msgf("Could not generate documentation, error reading file:%s\n", example_report_file_name)
		return
	}

	readmeFile, err := os.Create("README.md")


	params := struct{
	    Usage string
	    ExampleReport string
	    }{
		Usage: usage,
		ExampleReport: string(exampleReport),
	}

	parsedTemplate.Execute(readmeFile, params)
	if err != nil {
		log.Fatal().Err(err).Msg("Could not generate documentation, error creating README.md file: %s\n")
		return
	}

	defer func() { _ = readmeFile.Close() }()
}
