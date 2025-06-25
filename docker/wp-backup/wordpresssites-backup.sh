#!/bin/bash

date=$(date '+%Y-%m-%dT%H:%M:%S')
file_name="backup.$date.yml"
oc get wps -o yaml >> $file_name

credentials=$(oc extract secret/s3-backup-credentials --to=-)
AWS_SECRET_ACCESS_KEY=$(echo "$credentials" | sed -n '1p')
AWS_ACCESS_KEY_ID=$(echo "$credentials" | sed -n '2p')
aws configure set aws_access_key_id $AWS_ACCESS_KEY_ID
aws configure set aws_secret_access_key $AWS_SECRET_ACCESS_KEY

aws --endpoint-url=https://s3.epfl.ch s3 cp $file_name s3://svc0041-5da0d377aa221ddc24a6110fee695f69/WordpressSites/
