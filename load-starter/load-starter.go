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
	defaultLocustServer   = "ingest-load-tester.default.svc.cluster.local"
	defaultInfluxDbServer = "localhost:8086"
	startLocustUrl        = "http://%s/swarm"
	stopLocustUrl         = "http://%s/stop"
	testDateFormat        = "Mon 02 Jan 06\n15:04:05 MST"
	slackAuthToken        = "xoxb-2757754192454-2766782134324-oK6ewxLGOlElIk4UE9nYTTpY"
	slackChannelId        = "#slack-notif-test"
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
	locustServerName = rootCmd.Flags().StringP("locust", "l", defaultLocustServer, "locust server DNS")
	influxServerName = rootCmd.Flags().StringP("influx", "i", defaultInfluxDbServer, "influxDb server DNS")
	rootCmd.Flags().Int64VarP(&numUsers, "users", "u", 5, "number of simulated users")
	rootCmd.MarkFlagRequired("numUsers")
	organisationId = rootCmd.Flags().StringP("organisation", "o", "", "the InfluxDb organisation id")
	rootCmd.MarkFlagRequired("organisation")
	boardId = rootCmd.Flags().StringP("board", "b", "", "the InfluxDb board id")
	rootCmd.MarkFlagRequired("board")

	return rootCmd
}

func RunLoadStarter() {

	fmt.Printf("\nWill be waiting for %s ....", duration)

	//some buffer time to make sure we capture a little before and after the test
	buffer := time.Second * 30

	startTime := time.Now().UTC().Add(-buffer)

	err := startLocust(numUsers, numUsers)
	if err != nil {
		fmt.Println(err)
		os.Exit(1)
	}

	//wait for the test to run
	time.Sleep(*duration)

	err = stopLocust()
	if err != nil {
		fmt.Println(err)
		os.Exit(2)
	}
	endTime := time.Now().UTC().Add(buffer)
	sendSlackNotification(startTime, endTime, numUsers)
}

// Starts a locust load task by calling the spawn endpoint
func startLocust(numUsers int64, spawnRate int64) error {
	startUrl := fmt.Sprintf(startLocustUrl, *locustServerName)
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
	stopUrl := fmt.Sprintf(stopLocustUrl, *locustServerName)

	response, err := http.Get(stopUrl)
	if err != nil {
		return fmt.Errorf("Failed to stop the test: %v", err)
	}
	defer response.Body.Close()
	return nil
}

// Constructs a Slack Notification with the URL of the influx db dashboard for the test
func sendSlackNotification(startTime time.Time, endTime time.Time, numUsers int64) error {
	queryString := url.Values{}

	startTimeStamp := startTime.Format("2006-01-02T15:04:05Z")
	queryString.Add("lower", startTimeStamp)

	endTimeStamp := endTime.Format("2006-01-02T15:04:05Z")
	queryString.Add("upper", endTimeStamp)

	reportUrl := fmt.Sprintf("http://%s/orgs/%s/dashboards/%s?%s",
		*influxServerName, *organisationId, *boardId, queryString.Encode(),
	)
	fmt.Println("Dashboard is: \n%s", reportUrl)

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
				Title: "Test Start",
				Value: startTime.Local().Format(testDateFormat),
				Short: false,
			},
			{
				Title: "Test End",
				Value: endTime.Local().Format(testDateFormat),
				Short: false,
			},

			{
				Title: "Number of users",
				Value: fmt.Sprintf("%d", numUsers),
				Short: false,
			},
		},
		Actions: []slack.AttachmentAction{slack.AttachmentAction{URL: reportUrl}},
	}

	_, _, err := client.PostMessage(
		channelID,
		slack.MsgOptionAttachments(attachment),
	)

	if err != nil {
		err = fmt.Errorf("failed to send message to slack: %s", err)
		fmt.Printf("Failed to send to slack: %s", err)
		return err
	}
	return nil
}
