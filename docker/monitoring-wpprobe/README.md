# monitoring-wpprobe

This docker allow to fetch data from wordpresses and push metrics to prometheus.


## Build

In order to test new version of the prober, follow these steps:

1. Be sure to have the modifications pushed on github (branch doesn't matter)
2. Deploy the new version with Ansible (the current branch will be used):  
   `./ansible/wpsible -t monitoring --prod`  
   Note: you can check the active branch on openshift (Builds > Build > monitoring-wpprobe > Edit YAML: git/ref)
3. Follow the logs  
   `oc logs -f build.build.openshift.io/monitoring-wpprobe-71`
4. Kick the pod that includes this container (tells openshift to use the latest ImageStream of the container):  
   `oc delete pod prometheus-0`
5. To see live logs of the wpprober:
   1. In openshift: Applications > Pods > prometheus-0 > Logs > Container: prober.
   2. `oc -n wwp logs -f prometheus-0 -c prober`
6. If needed, you can enter the container with:  
   `oc -n wwp exec prometheus-0 -it -c prober bash` 


## ToDos

- [x] Ansible: trigger start-build and redeploy when changed
- [x] Rename `epflWPSiteLangs` and homogenize metrics names
- [x] Plugin: add plugin status as label ?
- [ ] Lang: only one request ?
- [x] Comfort: add version to console when starting
