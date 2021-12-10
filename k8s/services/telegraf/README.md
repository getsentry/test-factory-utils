# telegraf

Repo: https://github.com/influxdata/telegraf/

Telegraf is an aggregation and forwarding agent, part of the TICK stack.

We run two flavours of Telegraf:

1. DaemonSet (`daemonset.yaml`). Runs on every node in the cluster. Exposes statsd UDP port, so apps can send their metrics there.

2. Cluster-agent(`deployment.yaml`). Only one instance of it should be running at a given time. It's used to collect some metrics that should be fetched only once, e.g. Prometheus metrics.


The configuration is inspired by https://github.com/influxdata/helm-charts/tree/master/charts/telegraf-ds
