#!/usr/bin/env bash
#Petit script pour effeacer tous les hosts plus utilisé dans Telegraf/InfuxDB/Grafana

echo -e "
telegraf_remove_host.sh  zf201023.1736

Utilisation:

./telegraf_remove_host.sh list_file_host.txt
"

source /keybase/team/epfl_wwp_blue/influxdb_secrets.sh
dbflux_db=telegraf

while read -r telegraf_host
do 
  echo -e "Le host: $telegraf_host"
  
  curl -i -XPOST "$dbflux_srv_host:$dbflux_srv_port/query?u=$dbflux_u_admin&p=$dbflux_p_admin&db=$dbflux_db"  --data-urlencode "q=show series where host='$telegraf_host'"
  curl -i -XPOST "$dbflux_srv_host:$dbflux_srv_port/query?u=$dbflux_u_admin&p=$dbflux_p_admin&db=$dbflux_db"  --data-urlencode "q=drop series where host='$telegraf_host'"

done < $1
