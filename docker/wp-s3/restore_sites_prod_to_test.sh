#!/bin/bash

# To run:
# default (5 sites below): no params
# other sites: url of sites

echo "Start of db restore"

# if no url(s) given then takes default urls
if [ $# -eq 0 ]; then
    readarray -t urls < "/restore/urls.txt"
    urls=("https://www.epfl.ch/" "https://www.epfl.ch/campus/" "https://www.epfl.ch/campus/services/" "https://www.epfl.ch/campus/services/website/" "https://www.epfl.ch/campus/services/website/canari/")
else
    urls=("$@")
fi
date="$(date +%Y%m%d%H%m%S)"

# restore each db from prod to test
for url in "${urls[@]}"; do
    echo "Url : $url"

    site_id=$(curl https://wp-veritas.epfl.ch/api/v2/sites\?siteUrl=$url | jq -r '.[0] | .id')
    echo "Site id : $site_id"

    readarray -t k8s_info < <(curl https://wp-veritas.epfl.ch/api/v2/sites/$site_id | jq -r '.kubernetesExtraInfo.ingressName, .kubernetesExtraInfo.databaseRef')
    ingress="${k8s_info[0]}"
    echo "Ingress : $ingress"
    mariadb_prod_host="${k8s_info[1]}"
    echo "MariaDB prod host : $mariadb_prod_host"

    mariadb_test_host=$(kubectl get ingress/$ingress -o yaml | grep WP_DB_HOST | tr -s ' ' | cut -d ' ' -f 4 | tr -d ';')
    echo "MariaDB test host : $mariadb_test_host"

    echo "Applying restore ..."
    kind_restore=$(mktemp)
    cat <<EOF > "$kind_restore"
apiVersion: k8s.mariadb.com/v1alpha1
kind: Restore
metadata:
  name: "restore-db-$ingress-$date"
  namespace: svc0041t-wordpress
spec:
  mariaDbRef:
    name: "$mariadb_test_host"
  resources:
    requests:
      cpu: "100m"
      memory: "256Mi"
    limits:
      memory: "256Mi"
  s3:
    bucket: svc0041-f09a145f151acfe768583301e0389e65
    prefix: "MariaDB-$mariadb_prod_host"
    endpoint: s3.epfl.ch
    accessKeyIdSecretKeyRef:
      name: s3-prod-ro-credentials
      key: keyId
    secretAccessKeySecretKeyRef:
      name: s3-prod-ro-credentials
      key: accessSecret
    tls:
      enabled: true
  database: "wp-db-$ingress"
  targetRecoveryTime: # if empty then takes last restore
  args:
    - --verbose
EOF

    pod=$(kubectl apply -f "$kind_restore" -o name)
    kubectl wait --for=condition=complete "$pod" --timeout=10m

    # delete resources
    kubectl delete -f "$kind_restore"
    rm "$kind_restore"

    echo "Replace 'www.epfl.ch' by 'wpn-test.epfl.ch'"
    wp --ingress=$ingress search-replace "https://www.epfl.ch" "https://wpn-test.epfl.ch"
done

# update menu
kubectl rollout restart deployment menu-api
echo "End of db restore"
