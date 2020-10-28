#!/usr/bin/env bash
#Petit script pour lancer le post traitement des logs pour une batterie de tests

echo -e "
all_run.sh  zf200917.1604

Utilisation:

./all_run.sh > toto.txt
"

./parse-ansible-out4.py awx_logs_align_10_sites_1_forks_1_pods.txt
./parse-ansible-out4.py awx_logs_align_10_sites_5_forks_1_pods.txt
./parse-ansible-out4.py awx_logs_align_10_sites_5_forks_2_pods.txt
./parse-ansible-out4.py awx_logs_align_10_sites_5_forks_2_pods_parll.txt
./parse-ansible-out4.py awx_logs_align_10_sites_5_forks_2_pods_cache.txt
./parse-ansible-out4.py awx_logs_align_10_sites_10_forks_1_pods.txt
./parse-ansible-out4.py awx_logs_align_10_sites_10_forks_1_pods_pipe.txt
./parse-ansible-out4.py awx_logs_align_10_sites_10_forks_1_pods_debug4.txt
./parse-ansible-out4.py awx_logs_align_10_sites_2_forks_5_pods.txt
./parse-ansible-out4.py awx_logs_align_100_sites_30_forks_1_pods.txt
./parse-ansible-out4.py awx_logs_align_100_sites_17_forks_3_pods.txt



