# workflow-notifier

This is a script that sends notifications about finished workflows. At the moment it sends updates to Slack only. Message format can be provided as a YAML file or from command line. The sent messages will be enriched with additional values (link to workflow, workflow name), if they are found in the environment.

When provided as YAML, Slack Block Kit Builder is a helpful sandbox to figure out the format of the message: [https://app.slack.com/block-kit-builder/](https://app.slack.com/block-kit-builder/)
