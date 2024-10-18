#!/bin/bash

CSVFILE=result.csv
site=`kubectl get wordpresssite -A | awk  '{print $3}'`

while IFS= read -r line; do
	t1=$(date)
	result=`curl -kLs https://wpn.fsd.team$line/ |grep -o Doohickey`
	t2=$(date)

	if [[ -z "$result" ]]; then
		echo "$line, $t1, $t2" >> $CSVFILE
	fi
    
done <<< "$site"

