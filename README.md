# proactive-cluster-autoscaler

Example proactive cluster autoscaler that uses the [proactive node scaling operator](https://github.com/redhat-cop/proactive-node-scaling-operator).

Tested on OCP 4.7.2

## Create Cluster Autoscaler

> Note: verify the [RHCOS AMI](https://access.redhat.com/documentation/en-us/openshift_container_platform/4.7/html/installing/installing-on-aws#installation-aws-user-infra-rhcos-ami_installing-restricted-networks-aws) is correct in values.yaml.

```sh
helm upgrade -i autoscaler helm/autoscaler --set machineset.infrastructure_id=$(oc get -o jsonpath='{.status.infrastructureName}{"\n"}' infrastructure cluster) -n openshift-machine-api
```

## Install Proactive Node Scaling Operator

```sh
helm upgrade -i proactive-node-scaling-operator helm/proactive-node-scaling-operator -n openshift-operators
```
