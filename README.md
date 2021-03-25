# proactive-cluster-autoscaler

Example proactive cluster autoscaler that uses the [proactive node scaling operator](https://github.com/redhat-cop/proactive-node-scaling-operator).

Tested on OCP 4.7.2

## Install Proactive Node Scaling Operator

```sh
helm upgrade -i proactive-node-scaling-operator helm/proactive-node-scaling-operator -n openshift-operators
```

## Create Cluster Autoscaler

> Note: verify the [RHCOS AMI](https://access.redhat.com/documentation/en-us/openshift_container_platform/4.7/html/installing/installing-on-aws#installation-aws-user-infra-rhcos-ami_installing-restricted-networks-aws) is correct in values.yaml.

```sh
oc new-project proactive-autoscaler-test
oc new-project proactive-autoscaler-test2
helm upgrade -i autoscaler helm/autoscaler --set machineset.infrastructure_id=$(oc get -o jsonpath='{.status.infrastructureName}{"\n"}' infrastructure cluster) -n proactive-autoscaler-test --create-namespace
```

## Deploy test application

```sh
helm upgrade -i test-app helm/test-app -n proactive-autoscaler-test --create-namespace --set replicaCount=10
```

You should see the following number of pause pods in each namespace for the different watermarks when 10 test-app pods are deployed...

| Watermark Name        | Namespace                  | # of Pause Pods |
| --------------------- | -------------------------- | --------------- |
| proactive-autoscaler  | proactive-autoscaler-test  | 2               |
| proactive-autoscaler2 | proactive-autoscaler-test  | 8               |
| proactive-autoscaler  | proactive-autoscaler-test2 | 1               |

## Scale the application up or down to test the pause pods

```sh
helm upgrade -i test-app helm/test-app -n proactive-autoscaler-test --set replicaCount=1
```
