package main

import (
	"bytes"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
)

const (
	DefaultLocustServer   = "http://ingest-load-tester.default.svc.cluster.local"
	DefaultLoadServer     = "http://ingest-load-tester.default.svc.cluster.local" // TODO set to Vegeta server
	DefaultInfluxDbServer = "http://localhost:8086"
	InfluxDateFormat      = "2006-01-02T15:04:05Z"
	SlackDateFormat       = "Mon 02 Jan 06 15:04:05 MST"
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
    text: %s
- type: section
  fields:
    - type: mrkdwn
      text: |-
        *Test start:*
        %s
    - type: mrkdwn
      text: |-
        *Number of users:*
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
	duration             *time.Duration
	organisationId       *string
	boardId              *string
	numUsers             int64
	locustServerName     *string
	loadServerName       *string
	influxServerName     *string
	dryRun               bool
	configFilePath       *string
	reportFilePath       *string
	slackMessageFilePath *string
	logLevel             string
	useColor             bool
}

var Params CliParams

func cliSetup() *cobra.Command {
	var rootCmd = &cobra.Command{
		Use: "app",
		Run: func(cmd *cobra.Command, args []string) { runLoadStarterLegacy() },
	}
	rootCmd.Flags()

	Params.duration = rootCmd.Flags().DurationP("Duration", "d", time.Millisecond*10000, "the Duration to run the program")

	Params.locustServerName = rootCmd.Flags().StringP("locust", "l", DefaultLocustServer, "Locust server endpoint (deprecated)")

	Params.loadServerName = rootCmd.Flags().String("load-server", DefaultLoadServer, "Load server endpoint")

	Params.influxServerName = rootCmd.Flags().StringP("influx", "i", DefaultInfluxDbServer, "InfluxDB dashboard base URL")

	rootCmd.Flags().Int64VarP(&Params.numUsers, "users", "u", 5, "number of simulated users")

	Params.organisationId = rootCmd.Flags().StringP("organisation", "o", "", "the InfluxDb organisation id")

	Params.boardId = rootCmd.Flags().StringP("board", "b", "", "the InfluxDb board id")

	rootCmd.Flags().BoolVarP(&Params.dryRun, "dry-run", "", false, "dry-run mode")

	Params.configFilePath = rootCmd.Flags().StringP("config", "f", "", "Path to configuration file")

	Params.reportFilePath = rootCmd.Flags().StringP("report", "r", "", "If provided: report will be written here")

	Params.slackMessageFilePath = rootCmd.Flags().StringP("slack-message", "s", "", "If provided: notification report (simply put, a formatted Slack message) will be written here")

	rootCmd.PersistentFlags().StringVar(&Params.logLevel, "log", "error", "Log level: trace, info, warn, (error), fatal, panic")
	rootCmd.PersistentFlags().BoolVar(&Params.useColor, "color", false, "Use color (only for console output).")

	_ = rootCmd.Flags().MarkDeprecated("locust", "locust flag is deprecated, please use load-tester instead")
	_ = rootCmd.Flags().MarkDeprecated("users", "users flag is deprecated, please use config file to specify options instead")

	cobra.OnInitialize(initConfig)
	return rootCmd
}

// initConfig call after Cobra has read the configuration, all the settings should be ready in Params
func initConfig() {
	//setup logging
	var consoleWriter = zerolog.ConsoleWriter{Out: os.Stdout, NoColor: Params.useColor,
		TimeFormat: "15:04:05"}
	log.Logger = zerolog.New(consoleWriter).With().Timestamp().Logger()

	var logLevel zerolog.Level

	switch strings.ToLower(Params.logLevel) {
	case "t", "trc", "trace":
		logLevel = zerolog.TraceLevel
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
	case "d", "dis", "disable", "disabled":
		logLevel = zerolog.Disabled
	default:
		logLevel = zerolog.ErrorLevel
	}

	zerolog.SetGlobalLevel(logLevel)
}

func executeConfig(config Config) RunReport {
	var retVal = RunReport{
		TestRuns: make([]TestRun, 0, len(config.TestConfigs)),
	}

	for _, config := range config.TestConfigs {
		var run = TestRun{
			TestConfig: config,
			StartTime:  time.Now().UTC(),
		}
		retVal.TestRuns = append(retVal.TestRuns, run)
		logTestDetails(run)
		var err = runTest(config)
		if err != nil {
			log.Error().Msgf("Failed to run test:%s\n%v", config.Name, err)
		}
	}

	return retVal
}

func logTestDetails(run TestRun) {
	log.Info().Msgf("\n--- Test %s ---", run.Name)
	log.Info().Msgf("\n-- duration: %#v\n", run.Duration)
}

func runTest(config TestConfig) error {
	if Params.dryRun {
		log.Info().Msgf("[dry-run] Sending start request to %s: %s\n", config.StartUrl, config.StartBody)
		return nil
	}

	var err = sendHttpRequest(config.StartMethod, config.StartUrl, config.StartBody, config.StartHeaders)
	if err != nil {
		log.Error().Msgf("Failed to start run %s", config.Name)
		return err
	}

	time.Sleep(config.Duration)

	if len(config.StartUrl) == 0 {
		return nil // nothing more to do
	}

	err = sendHttpRequest(config.StopMethod, config.StopUrl, config.StopBody, config.StopHeaders)
	if err != nil {
		log.Error().Msgf("Failed to stop run %s", config.Name)
		return err
	}

	return nil
}

func sendHttpRequest(method string, url string, body string, headers map[string]string) error {
	var bodyData io.Reader
	if len(body) > 0 {
		bodyData = bytes.NewReader([]byte(body))
	}
	req, err := http.NewRequest(method, url, bodyData)
	if err != nil {
		return err
	}
	for key, val := range headers {
		req.Header.Add(key, val)
	}
	if err != nil {
		return err
	}

	var client = GetDefaultHttpClient()
	resp, err := client.Do(req)
	if err != nil {
		log.Error().Msgf(" error sending command to client '%s': \n%s", url, err)
		return err
	}
	if resp != nil {
		_ = resp.Body.Close()
	}
	return nil
}

func executeConfigLegacy(config LegacyConfig) LegacyRunReport {
	runReport := LegacyRunReport{}

	runReport.StartTime = time.Now().UTC()
	for i, stage := range config.Stages {
		stageNum := i + 1
		fmt.Printf("\n--- Stage %d ---\n", stageNum)
		fmt.Printf("Stage config: %#v\n", stage)
		fmt.Printf("Planned stage Duration: %v\n", stage.getTotalDuration())
		report, err := stage.execute()
		check(err)
		fmt.Printf("Stage report: %#v\n", report)
		runReport.StageReports = append(runReport.StageReports, report)
	}
	runReport.EndTime = time.Now().UTC()
	runReport.DashboardURL = buildDashboardLink(runReport.StartTime, runReport.EndTime, 30)
	return runReport
}

func writeReportToFile(report LegacyRunReport) {
	if *Params.reportFilePath == "" {
		fmt.Printf("No report file path provided, not writing the report to file.\n")
		return
	}

	reportData, err := yaml.Marshal(report)
	check(err)

	if Params.dryRun {
		fmt.Printf("[dry-run] Would write the following report to %s:\n~~~\n%s~~~\n", *Params.reportFilePath, reportData)
	} else {
		err = os.WriteFile(*Params.reportFilePath, reportData, 0644)
		check(err)
	}
	fmt.Printf("Wrote run report to: %s\n", *Params.reportFilePath)
}

func runLoadStarter() {
	if Params.dryRun {
		log.Info().Msg("NOTE: Dry-run mode is ON")
	}

	var config Config
	var err error

	log.Info().Msg("\n--- Prepare ---\nInitializing the run...\n")

	//TODO add legacy support
	var configPath = *Params.configFilePath
	if configPath != "" {
		if IsStarlarkConfig(configPath) {
			config, err = LoadStarlarkConfig(configPath)
		}
		if err != nil {
			log.Error().Msgf("Failed to load config file from: %s \n%s\n", configPath, err)
			return
		}

	}

	var report = executeConfig(config)
	//TODO finish this fix this
	log.Info().Msgf("Data:\n%v", report)

	//// Here we decide: do we use the config file or command line args?
	//if *Params.configFilePath == "" {
	//	// Use the CLI args
	//	stages := []LegacyTestStage{StageStatic{Users: Params.numUsers, Duration: *Params.duration}}
	//	config = LegacyConfig{Stages: stages}
	//} else {
	//	// Use the config file
	//	config = parseConfigFile(*Params.configFilePath)
	//}
	//
	//fmt.Printf("Configuration: %#v\n", config)
	//
	//totalDuration := config.getTotalDuration()
	//fmt.Printf("Total estimated running time: %s\n", totalDuration)
	//fmt.Printf("Esimated completion time: %s\n", time.Now().UTC().Add(totalDuration))
	//
	//runReport := executeConfigLegacy(config)
	//
	//fmt.Printf("\n--- Report ---\nFinished the run, preparing the report...\n")
	//writeReportToFile(runReport)
	//writeSlackMessage(runReport.StartTime, runReport.EndTime, config)
}

func runLoadStarterLegacy() {
	if Params.dryRun {
		fmt.Println("NOTE: Dry-run mode is ON")
	}

	var config LegacyConfig

	fmt.Printf("\n--- Prepare ---\nInitializing the run...\n")

	// Here we decide: do we use the config file or command line args?
	if *Params.configFilePath == "" {
		// Use the CLI args
		stages := []LegacyTestStage{StageStatic{Users: Params.numUsers, Duration: *Params.duration}}
		config = LegacyConfig{Stages: stages}
	} else {
		// Use the config file
		config = parseConfigFile(*Params.configFilePath)
	}

	fmt.Printf("Configuration: %#v\n", config)

	totalDuration := config.getTotalDuration()
	fmt.Printf("Total estimated running time: %s\n", totalDuration)
	fmt.Printf("Esimated completion time: %s\n", time.Now().UTC().Add(totalDuration))

	runReport := executeConfigLegacy(config)

	fmt.Printf("\n--- Report ---\nFinished the run, preparing the report...\n")
	writeReportToFile(runReport)
	writeSlackMessage(runReport.StartTime, runReport.EndTime, config)
}

func buildDashboardLink(startTime time.Time, endTime time.Time, buffer time.Duration) string {
	queryString := url.Values{}

	// Some buffer time to make sure we capture a little before and after the test
	startTimeStamp := startTime.Add(-buffer).Format(InfluxDateFormat)
	queryString.Add("lower", startTimeStamp)

	endTimeStamp := endTime.Add(buffer).Format(InfluxDateFormat)
	queryString.Add("upper", endTimeStamp)

	reportUrl := fmt.Sprintf("%s/orgs/%s/dashboards/%s?%s",
		*Params.influxServerName, *Params.organisationId, *Params.boardId, queryString.Encode(),
	)
	return reportUrl
}

// Constructs a Slack Notification with the URL of the influx db dashboard for the test
func writeSlackMessage(startTime time.Time, endTime time.Time, config LegacyConfig) {
	if *Params.slackMessageFilePath == "" {
		fmt.Printf("No Slack message path provided, not writing it.\n")
		return
	}

	reportUrl := buildDashboardLink(startTime, endTime, 30*time.Second)
	reportText := fmt.Sprintf("<%s|View data (InfluxDB)>", reportUrl)

	// Only print number of users when the only testing stage is "static"
	usersString := "varying"
	if len(config.Stages) == 1 && config.Stages[0].getType() == StageStaticName {
		users := config.Stages[0].(StageStatic).Users
		usersString = fmt.Sprintf("%d", users)
	}
	runDuration := config.getTotalDuration()

	rawMessage := fmt.Sprintf(slackTemplate,
		reportText,
		startTime.Local().Format(SlackDateFormat),
		usersString,
		endTime.Local().Format(SlackDateFormat),
		runDuration,
	)

	var testObj map[string]interface{}

	fmt.Println("Validating the message...")
	// This will check that the rendered message is actually a valid YAML, and e.g. that there are no tabs in it, among other things
	err := yaml.Unmarshal([]byte(rawMessage), &testObj)
	check(err)

	if Params.dryRun {
		fmt.Printf("[dry-run] Would write the following Slack yaml to %s:\n~~~\n%s~~~\n", *Params.slackMessageFilePath, rawMessage)
	} else {
		err = os.WriteFile(*Params.slackMessageFilePath, []byte(rawMessage), 0644)
		check(err)
	}
	fmt.Printf("Wrote Slack message to: %s\n", *Params.slackMessageFilePath)

	return
}

func main() {
	var rootCmd = cliSetup()
	rootCmd.Execute()
}
