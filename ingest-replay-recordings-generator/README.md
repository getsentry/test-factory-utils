---
layout: page
title: ingest-replay-recordings-generator
permalink: /ingest-replay-recordings-generator/
---
<!-- README.md is auto generated from README-template.md by calling ingest-replay-recordings-generator with the `--update-docs` argument -->

ingest-replay-recordings-generator is a tool that generates Sentry metrics messages and writes them to a kafka topic.

ingest-replay-recordings-generator can be configured using a settings file (json or yaml) via the `-f` or `--settings-file` argument or directly through command
line arguments.

The following arguments are available in the settings file:

```yaml
kafka:
  bootstrap.servers: "127.0.0.1:9092"
org_id: 1
project_id: 10
message: '[{"hello":"world"}]'
compressed: false

```

The following arguments are available in the command line:

```
Usage: main.py [OPTIONS]

  Populates the ingest-replay-recordings kafka topic with messages

Options:
  -n, --num-messages TEXT   The number of messages to send to the kafka queue
  -f, --settings-file TEXT  The settings file name (json or yaml)
  -t, --topic-name TEXT     The name of the ingest replay recordings topic
  -b, --broker TEXT         Kafka broker address and port (e.g. localhost:9092)
  -r, --repeatable          Should it generate a repeatable load or use a random
                            generator (default: random)
  -o, --org INTEGER         organisation id
  -p, --project INTEGER     project id
  --dry-run                 if set only prints the settings
  --update-docs             creates a README.md  documentation file
  --help                    Show this message and exit.
```
