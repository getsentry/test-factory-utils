---
layout: page
title: report-generator
permalink: /report-generator/
---

<!-- README.md is auto generated from README-template.md by calling ingest-metrics-generator with the `--update-docs` argument -->

`report-generator` generates html reports from test results stored in MongoDb.

The following arguments are available in the command line:

```
Usage:  [OPTIONS]

Options:
  -m, --mongo-db TEXT           url of mongo db (something like:
                                'mongodb://mongo-server/27017')  [required]
  -b, --gcs-bucket-name TEXT    GCS bucket name for saving the report
  -n, --report-name TEXT        path to the name of the report file
  -f, --filters <TEXT TEXT>...
  -s, --git-sha TEXT            the git sha of the version of interest
                                [required]
  --no-upload                   if passed will not upload the report to GCS
  -r, --report TEXT             report generator python file  [required]
  --help                        Show this message and exit.
```
