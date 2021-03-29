# proactive-cluster-autoscaler

> Tested on OCP 4.7.2

Example proactive cluster autoscaler that uses the [proactive node scaling operator](https://github.com/redhat-cop/proactive-node-scaling-operator).

It also tests the `scheduler.alpha.kubernetes.io/tolerationsWhitelist` annotation to control pod scheduling at the namespace level in the scenario where only certain namespaces (and users) should be able to schedule pods using certain node types. It should be known that all user workload namespaces would require this annotation to protect special nodes.

## Create Namespaces with default pod tolerations and whitelist annotations

See [PodTolerationRestriction admission controller: add default cluster tolerations to the default whitelisted tolerations #64616](https://github.com/kubernetes/kubernetes/issues/64616)

```sh
helm upgrade -i proactive-node-scaling-test-namespaces helm/namespaces -n proactive-node-scaling-operator --create-namespace
```

## Install Proactive Node Scaling Operator

```sh
helm upgrade -i proactive-node-scaling-operator helm/proactive-node-scaling-operator -n proactive-node-scaling-operator
```

## Create Cluster Autoscaler

> Note: verify the [RHCOS AMI](https://access.redhat.com/documentation/en-us/openshift_container_platform/4.7/html/installing/installing-on-aws#installation-aws-user-infra-rhcos-ami_installing-restricted-networks-aws) is correct in values.yaml.

```sh
helm upgrade -i autoscaler helm/autoscaler --set machineset.infrastructure_id=$(oc get -o jsonpath='{.status.infrastructureName}{"\n"}' infrastructure cluster) -n proactive-node-scaling-test
```

## Deploy test application

See [podtolerationrestriction](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#podtolerationrestriction) and [configuration-annotation-format](https://kubernetes.io/docs/reference/access-authn-authz/admission-controllers/#configuration-annotation-format)

```sh
helm upgrade -i test-app helm/test-app -n proactive-node-scaling-test --set replicaCount=10
```

You should see the following number of pause pods in each namespace for the different watermarks when 10 test-app pods are deployed...

| Watermark Name        | Namespace                    | # of Pause Pods |
| --------------------- | ---------------------------- | --------------- |
| proactive-autoscaler  | proactive-node-scaling-test  | 2               |
| proactive-autoscaler2 | proactive-node-scaling-test  | 8               |
| proactive-autoscaler  | proactive-node-scaling-test2 | 1               |

The test app should be allowed to schedule on other nodes without taints...

```sh
helm upgrade -i test-app helm/test-app -n proactive-node-scaling-test --set replicaCount=1 --set nodeSelector.key="node-role.kubernetes.io/worker"
```

This will also cause the pause pods to unschedule.

## Negative test the whitelist on the proactive-node-scaling-negative-test namespace

```sh
helm upgrade -i test-app helm/test-app -n proactive-node-scaling-negative-test --set replicaCount=1
```

The Event on the pod should state `pod didn't trigger scale-up: 1 node(s) had taint {node-role.kubernetes.io/proactive-autoscaler: }, that the pod didn't tolerate` and remain in Pending status.

If a user tries to set the tolerations in the deployment, the whitelist from the namespace annotation should prevent it from scheduling...

```sh
helm upgrade -i test-app helm/test-app -n proactive-node-scaling-negative-test --set replicaCount=1 -f helm/test-app/values-negative-test.yaml
```

The ReplicaSet Event should state `Error creating: pod tolerations (possibly merged with namespace default tolerations) conflict with its namespace whitelist`

The test app should be allowed to schedule on other nodes without taints...

```sh
helm upgrade -i test-app helm/test-app -n proactive-node-scaling-negative-test --set replicaCount=1 --set nodeSelector=''
```

## Scale the application up or down to test the pause pods

```sh
helm upgrade -i test-app helm/test-app -n proactive-node-scaling-test --set replicaCount=1
```
