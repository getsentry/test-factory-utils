package main

import (
	"fmt"
	"net/url"
	"os"
	"time"

	"github.com/slack-go/slack"
	"github.com/spf13/cobra"
	"gopkg.in/yaml.v2"
)

const (
	DefaultLocustServer   = "http://ingest-load-tester.default.svc.cluster.local"
	DefaultInfluxDbServer = "http://localhost:8086"
	InfluxDateFormat      = "2006-01-02T15:04:05Z"
	SlackDateFormat       = "Mon 02 Jan 06\n15:04:05 MST"
)

// Command line arguments
type CliParams struct {
	duration         *time.Duration
	organisationId   *string
	boardId          *string
	numUsers         int64
	locustServerName *string
	influxServerName *string
	dryRun           bool
	configFilePath   *string
	reportFilePath   *string
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
	fmt.Printf("Total planned running time: %s\n", config.getTotalDuration())

	runReport := executeConfig(config)

	fmt.Printf("\n--- Report ---\nFinished the run, preparing the report...\n")
	writeReportToFile(runReport)
	err := sendSlackNotification(runReport.StartTime, runReport.EndTime, config)
	if err != nil {
		fmt.Printf("Failed to send Slack notification:\n%s", err)
	}
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
func sendSlackNotification(startTime time.Time, endTime time.Time, config Config) error {
	token := os.Getenv("SLACK_AUTH_TOKEN")
	channelID := os.Getenv("SLACK_CHANNEL_ID")
	workflowUrl := os.Getenv("WORKFLOW_URL")
	workflowId := os.Getenv("WORKFLOW_ID")

	reportUrl := buildDashboardLink(startTime, endTime, 30*time.Second)
	fmt.Printf("Dashboard link: %s\n", reportUrl)

	reportText := fmt.Sprintf("<%s|View data (InfluxDB)>", reportUrl)
	if workflowUrl != "" {
		reportText += fmt.Sprintf("\n<%s|View workflow details (Argo)>", workflowUrl)
	}
	if workflowId != "" {
		reportText += fmt.Sprintf("\nWorkflow ID: %s", workflowId)
	}

	// Create a new client to slack by giving token
	// Set debug to true while developing
	client := slack.New(token)

	// Only print number of users when the only testing stage is "static"
	usersString := "varying"
	if len(config.Stages) == 1 && config.Stages[0].getType() == StageStaticName {
		users := config.Stages[0].(StageStatic).Users
		usersString = fmt.Sprintf("%d", users)
	}
	runDuration := config.getTotalDuration()

	attachment := slack.Attachment{
		Pretext: "Here's your test report",
		Text:    reportText,
		// Color Styles the Text, making it possible to have like Warnings etc.
		Color: "#36a64f",
		Fields: []slack.AttachmentField{
			{
				Title: "Test start",
				Value: startTime.Local().Format(SlackDateFormat),
				Short: true,
			},
			{
				Title: "Number of users",
				Value: usersString,
				Short: true,
			},
			{
				Title: "Test end",
				Value: endTime.Local().Format(SlackDateFormat),
				Short: true,
			},
			{
				Title: "Total duration",
				Value: fmt.Sprintf("%s", runDuration),
				Short: true,
			},
		},
		Actions: []slack.AttachmentAction{{URL: reportUrl}},
	}

	message := slack.MsgOptionAttachments(attachment)

	fmt.Println("Sending the report to Slack...")

	if Params.dryRun {
		fmt.Printf("[dry-run] Message: %#v\n", attachment)
	} else {
		_, _, err := client.PostMessage(
			channelID,
			message,
		)

		if err != nil {
			fmt.Printf("Failed to send to Slack: %s\n", err)
			return err
		}
	}

	fmt.Println("\nDone!")
	return nil
}

func main() {
	var rootCmd = cliSetup()
	rootCmd.Execute()
}
