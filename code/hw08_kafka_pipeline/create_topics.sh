#!/bin/sh
KAFKA_CONTAINER="s4544-kafka"
BOOTSTRAP_SERVER="kafka:29092"

docker exec "$KAFKA_CONTAINER" /opt/kafka/bin/kafka-topics.sh \
  --create \
  --if-not-exists \
  --topic s4544_inbox \
  --partitions 1 \
  --replication-factor 1 \
  --bootstrap-server "$BOOTSTRAP_SERVER"

docker exec "$KAFKA_CONTAINER" /opt/kafka/bin/kafka-topics.sh \
  --create \
  --if-not-exists \
  --topic s4544_dead_letter \
  --partitions 1 \
  --replication-factor 1 \
  --bootstrap-server "$BOOTSTRAP_SERVER"

docker exec "$KAFKA_CONTAINER" /opt/kafka/bin/kafka-topics.sh \
  --create \
  --if-not-exists \
  --topic s4544_tasks \
  --partitions 2 \
  --replication-factor 1 \
  --bootstrap-server "$BOOTSTRAP_SERVER"

docker exec "$KAFKA_CONTAINER" /opt/kafka/bin/kafka-topics.sh \
  --create \
  --if-not-exists \
  --topic s4544_drafts \
  --partitions 1 \
  --replication-factor 1 \
  --bootstrap-server "$BOOTSTRAP_SERVER"

docker exec "$KAFKA_CONTAINER" /opt/kafka/bin/kafka-topics.sh \
  --create \
  --if-not-exists \
  --topic s4544_final \
  --partitions 1 \
  --replication-factor 1 \
  --bootstrap-server "$BOOTSTRAP_SERVER"

docker exec "$KAFKA_CONTAINER" /opt/kafka/bin/kafka-topics.sh \
  --list \
  --bootstrap-server "$BOOTSTRAP_SERVER"
