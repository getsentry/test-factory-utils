DEBUG = True

# Project: https://sentry.io/organizations/sentry-test/issues/?project=6181827
SENTRY_DSN = 'https://da216dc5fe724c5c96adb09fa2274760@o19635.ingest.sentry.io/6181827'

DOGSTATSD_HOST = '127.0.0.1'
DOGSTATSD_PORT = 8125

CLUSTERS = [
  {
    'host': 'clickhouse-sentry.default.svc.cluster.local',
    'port': 9000,
    'http_port': 8123,
    'storage_sets': {
      "metrics",
      "events",
      "events_ro",
      "transactions",
      "cdc",
      "migrations",
      "discover",
      "outcomes",
      "sessions",
    },
    'single_node': True,
  },
]

### Kafka clusters
BROKER_CONFIG = {
  'bootstrap.servers': 'ingest-kafka.default.svc.cluster.local:9092',
}
