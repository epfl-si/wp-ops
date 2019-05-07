#!/bin/sh

set -e

cat > /usr/share/filebeat/filebeat.yml <<EOF
filebeat.inputs:
- type: log
  enabled: true
  paths:
  - "/webservices/logs/*"
  fields_under_root: true

output.kafka:
  hosts: ["kafka-exopge-1.epfl.ch:9092","kafka-exopge-2.epfl.ch:9092","kafka-exopge-3.epfl.ch:9092"]
  topic: "wwp-${LINE}-webservice-access"
EOF

/usr/share/filebeat/filebeat -e -c /usr/share/filebeat/filebeat.yml
