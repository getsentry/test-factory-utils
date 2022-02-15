package main

import (
	"fmt"
	"net/url"
	"os"
	"time"

	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
)

const (
	DefaultLocustServer   = "http://ingest-load-tester.default.svc.cluster.local"
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
        *Total duration:*
        %s
`

// Command line arguments
type CliParams struct {
	duration             *time.Duration
	organisationId       *string
	boardId              *string
	numUsers             int64
	locustServerName     *string
	influxServerName     *string
	dryRun               bool
	configFilePath       *string
	reportFilePath       *string
	slackMessageFilePath *string
}

var Params CliParams

func cliSetup() *cobra.Command {
	var rootCmd = &cobra.Command{
		Use: "app",
		Run: func(cmd *cobra.Command, args []string) { runLoadStarter() },
	}
	rootCmd.Flags()

	Params.duration = rootCmd.Flags().DurationP("duration", "d", time.Millisecond*10000, "the duration to run the program")

	Params.locustServerName = rootCmd.Flags().StringP("locust", "l", DefaultLocustServer, "Locust server endpoint")

	Params.influxServerName = rootCmd.Flags().StringP("influx", "i", DefaultInfluxDbServer, "InfluxDB dashboard base URL")

	rootCmd.Flags().Int64VarP(&Params.numUsers, "users", "u", 5, "number of simulated users")

	Params.organisationId = rootCmd.Flags().StringP("organisation", "o", "", "the InfluxDb organisation id")

	Params.boardId = rootCmd.Flags().StringP("board", "b", "", "the InfluxDb board id")

	rootCmd.Flags().BoolVarP(&Params.dryRun, "dry-run", "", false, "dry-run mode")

	Params.configFilePath = rootCmd.Flags().StringP("config", "f", "", "Path to configuration file")

	Params.reportFilePath = rootCmd.Flags().StringP("report", "r", "", "If provided: report will be written here")

	Params.slackMessageFilePath = rootCmd.Flags().StringP("slack-message", "s", "", "If provided: notification report (simply put, a formatted Slack message) will be written here")

	return rootCmd
}

func executeConfig(config Config) RunReport {
	runReport := RunReport{}

	runReport.StartTime = time.Now().UTC()
	for i, stage := range config.Stages {
		stageNum := i + 1
		fmt.Printf("\n--- Stage %d ---\n", stageNum)
		fmt.Printf("Stage config: %#v\n", stage)
		fmt.Printf("Planned stage duration: %v\n", stage.getTotalDuration())
		report, err := stage.execute()
		check(err)
		fmt.Printf("Stage report: %#v\n", report)
		runReport.StageReports = append(runReport.StageReports, report)
	}
	runReport.EndTime = time.Now().UTC()
	runReport.DashboardURL = buildDashboardLink(runReport.StartTime, runReport.EndTime, 30)
	return runReport
}

func writeReportToFile(report RunReport) {
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
		fmt.Println("NOTE: Dry-run mode is ON")
	}

	var config Config

	fmt.Printf("\n--- Prepare ---\nInitializing the run...\n")

	// Here we decide: do we use the config file or command line args?
	if *Params.configFilePath == "" {
		// Use the CLI args
		stages := []TestStage{StageStatic{Users: Params.numUsers, Duration: *Params.duration}}
		config = Config{Stages: stages}
	} else {
		// Use the config file
		config = parseConfigFile(*Params.configFilePath)
	}

	fmt.Printf("Configuration: %#v\n", config)

	totalDuration := config.getTotalDuration()
	fmt.Printf("Total estimated running time: %s\n", totalDuration)
	fmt.Printf("Esimated completion time: %s\n", time.Now().UTC().Add(totalDuration))

	runReport := executeConfig(config)

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
func writeSlackMessage(startTime time.Time, endTime time.Time, config Config) {
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
