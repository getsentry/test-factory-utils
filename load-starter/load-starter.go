package main

import (
	"fmt"
	"github.com/slack-go/slack"
	"net/http"
	"net/url"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

const (
	defaultLocustServer   = "http://ingest-load-tester.default.svc.cluster.local"
	defaultInfluxDbServer = "http://localhost:8086"
	startLocustUrl        = "/swarm"
	stopLocustUrl         = "/stop"
	testDateFormat        = "Mon 02 Jan 06\n15:04:05 MST"
)

var duration *time.Duration
var organisationId *string
var boardId *string
var numUsers int64
var locustServerName *string
var influxServerName *string

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
	duration = rootCmd.Flags().DurationP("duration", "d", time.Millisecond*10,
		"the duration to run the program")
	locustServerName = rootCmd.Flags().StringP("locust", "l", defaultLocustServer, "locust server endpoint")
	influxServerName = rootCmd.Flags().StringP("influx", "i", defaultInfluxDbServer, "influxDB dashboard base URL")
	rootCmd.Flags().Int64VarP(&numUsers, "users", "u", 5, "number of simulated users")
	rootCmd.MarkFlagRequired("numUsers")
	organisationId = rootCmd.Flags().StringP("organisation", "o", "", "the InfluxDb organisation id")
	rootCmd.MarkFlagRequired("organisation")
	boardId = rootCmd.Flags().StringP("board", "b", "", "the InfluxDb board id")
	rootCmd.MarkFlagRequired("board")

	return rootCmd
}

func RunLoadStarter() {
	fmt.Printf("\nWill be waiting for %s ....\n", duration)

	startTime := time.Now().UTC()
	err := startLocust(numUsers, numUsers/4)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	// Wait for the test to run
	time.Sleep(*duration)

	err = stopLocust()
	if err != nil {
		fmt.Println(err)
		os.Exit(2)
	}
	endTime := time.Now().UTC()
	sendSlackNotification(startTime, endTime, numUsers)
}

// Starts a locust load task by calling the spawn endpoint
func startLocust(numUsers int64, spawnRate int64) error {
	startUrl := fmt.Sprintf("%s%s", *locustServerName, startLocustUrl)
	contentType := "application/x-www-form-urlencoded; charset=UTF-8"
	requestBody := url.Values{}

	requestBody.Add("user_count", strconv.FormatInt(numUsers, 10))
	requestBody.Add("spawn_rate", strconv.FormatInt(spawnRate, 10))
	body := requestBody.Encode()
	response, err := http.Post(startUrl, contentType, strings.NewReader(body))
	if err != nil {
		return fmt.Errorf("failed to start the test:%v", err)
	}
	defer response.Body.Close()
	statusOK := response.StatusCode >= 200 && response.StatusCode < 300
	if !statusOK {
		return fmt.Errorf("failed to start test, server responded with %s", response.Status)
	}
	return nil
}

// Starts a locust load testing by calling the stop endpoint
func stopLocust() error {
	stopUrl := fmt.Sprintf("%s%s", *locustServerName, stopLocustUrl)

	response, err := http.Get(stopUrl)
	if err != nil {
		return fmt.Errorf("Failed to stop the test: %v", err)
	}
	defer response.Body.Close()
	return nil
}

// Constructs a Slack Notification with the URL of the influx db dashboard for the test
func sendSlackNotification(startTime time.Time, endTime time.Time, numUsers int64) error {
	// Some buffer time to make sure we capture a little before and after the test
	buffer := time.Second * 30

	queryString := url.Values{}

	urlDateFormat := "2006-01-02T15:04:05Z"

	startTimeStamp := startTime.Add(-buffer).Format(urlDateFormat)
	queryString.Add("lower", startTimeStamp)

	endTimeStamp := endTime.Add(buffer).Format(urlDateFormat)
	queryString.Add("upper", endTimeStamp)

	reportUrl := fmt.Sprintf("%s/orgs/%s/dashboards/%s?%s",
		*influxServerName, *organisationId, *boardId, queryString.Encode(),
	)
	fmt.Printf("The dashboard link: %s\n", reportUrl)

	token := os.Getenv("SLACK_AUTH_TOKEN")
	channelID := os.Getenv("SLACK_CHANNEL_ID")

	// Create a new client to slack by giving token
	// Set debug to true while developing
	client := slack.New(token)

	attachment := slack.Attachment{
		Pretext: "Here's your test report",
		Text:    reportUrl,
		// Color Styles the Text, making it possible to have like Warnings etc.
		Color: "#36a64f",
		Fields: []slack.AttachmentField{
			{
				Title: "Number of users",
				Value: fmt.Sprintf("%d", numUsers),
				Short: false,
			},
			{
				Title: "Test duration",
				Value: fmt.Sprintf("%s", duration),
				Short: false,
			},
			{
				Title: "Test start",
				Value: startTime.Local().Format(testDateFormat),
				Short: false,
			},
			{
				Title: "Test end",
				Value: endTime.Local().Format(testDateFormat),
				Short: false,
			},
		},
		Actions: []slack.AttachmentAction{slack.AttachmentAction{URL: reportUrl}},
	}

	fmt.Println("Sending the report to Slack...")
	_, _, err := client.PostMessage(
		channelID,
		slack.MsgOptionAttachments(attachment),
	)

	if err != nil {
		err = fmt.Errorf("failed to send message to slack: %s", err)
		fmt.Printf("Failed to send to slack: %s", err)
		return err
	}

	fmt.Println("Done!")
	return nil
}
