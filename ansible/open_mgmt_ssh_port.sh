#!/bin/bash

echo "Current openshift context: " $(oc config current-context)
echo "Current openshift operator: " $(oc whoami)
echo "Current openshift project: " $(oc project)
echo "Current mgmt pod name: " $(oc get pods -o name | grep mgmt | head -1)
echo "Are you sure you want to forward the mgmt ssh port on this machine? (y/n)"
read answer

if [ "$answer" != "${answer#[Yy]}" ] ;then
    echo "What local port do you want to forward? (do not forget to specify the same port for ansible scripts)"
    read port
    oc port-forward $(oc get pods -o name | grep mgmt | head -1) "$port":22
else
    echo "exiting"
fi
