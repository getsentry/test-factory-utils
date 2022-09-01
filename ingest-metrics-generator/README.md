---
layout: page
title: ingest-metrics-generator
permalink: /ingest-metrics-generator/
---
<!-- README.md is auto generated from README-template.md by calling ingest-metrics-generator with the `--update-docs` argument -->

ingest-metrics-generator is a tool that generates metrics messages and writes them to a kafka topic.

ingest-metrics-generator can be configured using a settings file (json or yaml) via the `-f` or `--settings-file` argument or directly through command
line arguments.

The following arguments are available in the settings file:

```yaml
kafka:
  bootstrap.servers: "127.0.0.1:9092"
org: 1
projects: [ 5,6,7,8,9,10 ]
spread: 2h              # time spread of timestamp from now ( will generate messages with timestamp anywhere between `now` and `now - spread` )
releases: 20
environments: 10
repeatable: false       # if repeatable is true it will do a repeatable pseudo-random message generation (guarantees two runs with same settings will generate the same messages)
metric_types:
  session: 4,            # generate 4 times as many session metrics as 'session.error' or 'session.duration' metrics
  user: 2,               # generate 2 times as many user metrics as 'session.error' metrics
  "session.error": 1,
  "session.duration": 1
col_min: 3
col_max: 7

```

The following arguments are available in the command line:

```
Usage: main.py [OPTIONS]

  Populates the ingest-metrics kafka topic with messages

Options:
  -n, --num-messages TEXT         The number of messages to send to the kafka
                                  queue
  -f, --settings-file TEXT        The settings file name (json or yaml)
  -t, --topic-name TEXT           The name of the ingest metrics topic
  -b, --broker TEXT               Kafka broker address and port (e.g.
                                  localhost:9092)
  -r, --repeatable                Should it generate a repeatable load or use a
                                  random generator (default: random)
  --timestamp INTEGER             Timestamp reference to use. If exactly
                                  repeatable tests are desired then a timestamp
                                  ref can be used
  -s, --spread TEXT               Time spread from timestamp backward, (e.g.
                                  1w2d3h4m5s 1 week 2 days 3 hours 4 minutes 5
                                  seconds)
  -o, --org INTEGER               organisation id
  -p, --project INTEGER           project id
  --releases INTEGER              Number of releases to generate. If --releases-
                                  unique-rate is provided, this parameter
                                  defines the number of fallback (non-unique)
                                  releases.
  --releases-unique-rate FLOAT RANGE
                                  Ratio of unique releases to generate
                                  [0<=x<=1]
  --environments INTEGER          Number of environments to generate. If
                                  --environments-unique-rate is provided, this
                                  parameter defines the number of fallback (non-
                                  unique) environments.
  --environments-unique-rate FLOAT RANGE
                                  Ratio of unique environments to generate
                                  [0<=x<=1]
  --num-extra-tags INTEGER        Number of additional tags to generate.
  --extra-tags-values INTEGER     Number of additional tag values to generate.
                                  If --extra-tags-unique-rate is provided, this
                                  parameter defines the number of fallback (non-
                                  unique) tag values.
  --extra-tags-unique-rate FLOAT RANGE
                                  Ratio of unique tag values (for extra-tags) to
                                  generate  [0<=x<=1]
  --col-min INTEGER               min number of items in collections (sets &
                                  distributions)
  --col-max INTEGER               max number of items in collections (sets &
                                  distributions)
  --dry-run                       if set only prints the settings
  --update-docs                   creates a README.md  documentation file
  --help                          Show this message and exit.
```
