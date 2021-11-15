# Zookafka

Zookafka is our deployment of both a zookeeper instance and a kafka instance. Both of these services are run with a single replica in a non highly-available fashion.

## Operations

### Adding Topic Partitions

As topics grow in message volume it is sometimes necessary to scale the number of partitions we have on that topic to allow more concurrent consumers per group. While some topics may require special consideration we generally follow the second method ("existing topic") described in the [Adding more partitions to Kafka topic](https://www.notion.so/sentry/Adding-more-partitions-to-Kafka-topic-108182e92973417c9f01a34279c6fc84) notion document.

## Alerts

### Kafka - Backlogged Consumer Group

This alert triggers when a specific kafka consumer group falls behind in its consumption of messages from the specified topic. Our consumer groups map directly to deployments so the first place to look is the corresponding deployments status.

Generally if this alert is not firing due to a one-off incident with a consumergroup or zookafka it will be due to an imbalance in message production vs consumption.
