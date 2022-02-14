#!/usr/bin/env python3
import os
import string
from enum import Enum, unique
from multiprocessing.sharedctypes import Value

import click
import yaml
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


@unique
class MessageLevel(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"

    @staticmethod
    def values():
        return [profile.value for profile in MessageLevel]


COLORS = {
    # Green
    MessageLevel.SUCCESS.value: "#36a64f",
    # Yellow
    MessageLevel.WARNING.value: "#ECB22E",
    # Red
    MessageLevel.DANGER.value: "#E01E5A",
}


@click.command()
@click.option(
    "--text",
    "-t",
    envvar="NOTIFIER_TEXT",
    help="Text message to send",
)
@click.option(
    "--channel",
    "-c",
    envvar="NOTIFIER_SLACK_CHANNEL",
    help="Channel to send the message to",
)
@click.option(
    "--token",
    envvar="NOTIFIER_SLACK_TOKEN",
    help="Slack OAuth token",
    required=True,
)
@click.option(
    "--level",
    "-l",
    envvar="NOTIFIER_MESSAGE_LEVEL",
    help="Slack OAuth token",
    type=click.Choice(MessageLevel.values()),
    default=MessageLevel.SUCCESS.value,
)
@click.option(
    "--message-file",
    "-f",
    envvar="NOTIFIER_MESSAGE_FILE",
    help="Path to file with message in YAML format",
)
def main(text: str, channel: str, token: str, level: str, message_file: str):
    send_slack_message(channel, text, token, level, message_file)


def send_slack_message(channel, text, token, level, message_file):
    if message_file:
        print(f"Sending from file: {message_file}")
        with open(message_file) as f:
            raw = f.read()
            # Replace environment variables
            rendered = string.Template(raw).substitute(os.environ)
            message = yaml.safe_load(rendered)

        if not message:
            raise ValueError("Empty message file?")

        if "level" in message:
            level = message["level"]
            if level not in COLORS:
                raise ValueError(f'Invalid "level" value: {level}')
        color = COLORS[level]

        header_blocks = message["header_blocks"]

        attachments = [
            {
                "color": color,
                "blocks": message["attachment_blocks"],
            }
        ]

        post_message_kwargs = {
            "blocks": header_blocks,
            "attachments": attachments,
        }
    else:
        if not text:
            raise ValueError("No text specified!")
        print(f"Sending from command line: {text}")
        post_message_kwargs = {
            # "text" will be used as a fallback when rich content cannot be generated
            "text": text,
            "blocks": [{"type": "section", "text": {"type": "mrkdwn", "text": text}}],
        }

    # Prepend a divider
    post_message_kwargs["blocks"] = [{"type": "divider"}] + post_message_kwargs[
        "blocks"
    ]

    # Add additional values from the environment
    enhance_from_env(post_message_kwargs["blocks"])

    client = WebClient(token=token)
    try:
        client.chat_postMessage(channel=channel, **post_message_kwargs)
    except SlackApiError as e:
        print(f"Got an error: {e.response}")


def enhance_from_env(blocks):
    """
    Take a few predefined value from environment and add the corresponding blocks
    to the message.
    """
    workflow_name = os.environ.get("WORKFLOW_NAME", "").strip()
    workflow_id = os.environ.get("WORKFLOW_ID", "").strip()
    workflow_url = os.environ.get("WORKFLOW_URL", "").strip()
    text = ""
    if workflow_id:
        if workflow_url:
            text = f"*Workflow:* <{workflow_url}|{workflow_id}>"
        else:
            text = f"*Workflow:* {workflow_id}"
    else:
        if workflow_url:
            text = f"*Workflow:* {workflow_url}"
    if workflow_name:
        if text:
            text += f" ({workflow_name})"
    if text:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})

    workflow_comment = os.environ.get("WORKFLOW_COMMENT", "").strip()
    if workflow_comment:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Comment:* {workflow_comment}"},
            }
        )


if __name__ == "__main__":
    main()
