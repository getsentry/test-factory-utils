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
    send_message(channel, text, token, level, message_file)


def send_message(channel, text, token, level, message_file):
    if message_file:
        # Send from file
        with open(message_file) as f:
            raw = f.read()
            # Replace environment variables
            rendered = string.Template(raw).substitute(os.environ)
            message = yaml.safe_load(rendered)

        if 'level' in message:
            level = message['level']
            if level not in COLORS:
                raise ValueError(f'Invalid "level" value: {level}')
        color = COLORS[level]

        header_blocks = message['header_blocks']

        attachments = [
            {
                "color": color,
                "blocks": message['attachment_blocks'],
            }
        ]

        post_message_kwargs = {
            'blocks': header_blocks,
            'attachments': attachments,
        }
    else:
        # Send from CLI
        if not text:
            raise ValueError("No text specified!")
        post_message_kwargs = {
            'text': text,
        }

    client = WebClient(token=token)
    try:
        client.chat_postMessage(
            channel=channel, **post_message_kwargs
        )
    except SlackApiError as e:
        print(f"Got an error: {e.response}")


if __name__ == "__main__":
    main()
