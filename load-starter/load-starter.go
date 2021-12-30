package main

import (
	"fmt"
	"net/url"
	"os"
	"time"

	"github.com/slack-go/slack"
	"github.com/spf13/cobra"
)

const (
	defaultLocustServer   = "http://ingest-load-tester.default.svc.cluster.local"
	defaultInfluxDbServer = "http://localhost:8086"
	slackDateFormat       = "2006-01-02T15:04:05Z"
	testDateFormat        = "Mon 02 Jan 06\n15:04:05 MST"
)

var (
	duration         *time.Duration
	organisationId   *string
	boardId          *string
	numUsers         int64
	locustServerName *string
	influxServerName *string
	dryRun           bool
	configFilePath   *string
)

func main() {
	var rootCmd = cliSetup()
	rootCmd.Execute()
}

func cliSetup() *cobra.Command {
	var rootCmd = &cobra.Command{
		Use: "app",
		Run: func(cmd *cobra.Command, args []string) { RunLoadStarter() },
	}
	rootCmd.Flags()

	duration = rootCmd.Flags().DurationP("duration", "d", time.Millisecond*10000, "the duration to run the program")

	locustServerName = rootCmd.Flags().StringP("locust", "l", defaultLocustServer, "Locust server endpoint")

	influxServerName = rootCmd.Flags().StringP("influx", "i", defaultInfluxDbServer, "InfluxDB dashboard base URL")

	rootCmd.Flags().Int64VarP(&numUsers, "users", "u", 5, "number of simulated users")

	organisationId = rootCmd.Flags().StringP("organisation", "o", "", "the InfluxDb organisation id")

	boardId = rootCmd.Flags().StringP("board", "b", "", "the InfluxDb board id")

	rootCmd.Flags().BoolVarP(&dryRun, "dry-run", "", false, "dry-run mode")

	configFilePath = rootCmd.Flags().StringP("config", "f", "", "Path to configuration file")

	return rootCmd
}

func executeConfig(config Config) {
	for i, stage := range config.Stages {
		fmt.Printf("\n--- Stage %d ---\n", i)
		fmt.Printf("Stage config: %#v\n", stage)
		fmt.Printf("Planned stage duration: %v\n", stage.getTotalDuration())
		stage.execute()
	}
}

func RunLoadStarter() {
	if dryRun {
		fmt.Println("Dry-run mode is ON")
	}

	var config Config

	// Here we decide: do we use the config file or command line args?
	if *configFilePath == "" {
		// Use the CLI args
		stages := []TestStage{StageStatic{Users: numUsers, Duration: *duration}}
		config = Config{Stages: stages}
	} else {
		// Use the config file
		config = parseConfigFile(*configFilePath)
	}

	fmt.Printf("Configuration: %#v\n", config)

	fmt.Println("Initializing the run...")

	startTime := time.Now().UTC()
	executeConfig(config)
	endTime := time.Now().UTC()

	fmt.Printf("\nFinished the run, sending the report...\n")
	sendSlackNotification(startTime, endTime, config)
}

// Constructs a Slack Notification with the URL of the influx db dashboard for the test
func sendSlackNotification(startTime time.Time, endTime time.Time, config Config) error {
	// Some buffer time to make sure we capture a little before and after the test
	buffer := time.Second * 30

	queryString := url.Values{}

	startTimeStamp := startTime.Add(-buffer).Format(slackDateFormat)
	queryString.Add("lower", startTimeStamp)

	endTimeStamp := endTime.Add(buffer).Format(slackDateFormat)
	queryString.Add("upper", endTimeStamp)

	reportUrl := fmt.Sprintf("%s/orgs/%s/dashboards/%s?%s",
		*influxServerName, *organisationId, *boardId, queryString.Encode(),
	)
	fmt.Printf("The dashboard link: %s\n", reportUrl)

	token := os.Getenv("SLACK_AUTH_TOKEN")
	channelID := os.Getenv("SLACK_CHANNEL_ID")
	workflowUrl := os.Getenv("WORKFLOW_URL")
	workflowId := os.Getenv("WORKFLOW_ID")

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

	usersString := "varying"
	if len(config.Stages) == 1 && config.Stages[0].getType() == STAGE_STATIC_NAME {
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
				Value: startTime.Local().Format(testDateFormat),
				Short: true,
			},
			{
				Title: "Number of users",
				Value: usersString,
				Short: true,
			},
			{
				Title: "Test end",
				Value: endTime.Local().Format(testDateFormat),
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

	if dryRun {
		fmt.Printf("[dry-run] Message: %#v\n", attachment)
	} else {
		_, _, err := client.PostMessage(
			channelID,
			message,
		)

		if err != nil {
			fmt.Printf("Failed to send to slack: %s\n", err)
			return err
		}
	}

	fmt.Println("Done!")
	return nil
}
