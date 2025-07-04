#!/usr/bin/env bash

date=$(date '+%Y-%m-%dT%H:%M:%S')
file_name="/tmp/backup.$date.yml"
kubectl get wordpresssite -o yaml > $file_name

export AWS_SECRET_ACCESS_KEY=$accessSecret
export AWS_ACCESS_KEY_ID=$keyId

aws --endpoint-url=https://s3.epfl.ch s3 cp $file_name s3://$bucket_name/WordpressSites/
