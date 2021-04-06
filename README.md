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

## Install the GPU and NFD operators from OLM in the openshift-operators namespace

```sh
helm upgrade -i gpu-nfd-operators helm/operators -n openshift-operators
```

Create the gpu-operator-resources namespace...

```sh
oc new-project gpu-operator-resources
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

## Try gpu

Get entitlement...

1. Navigate to <https://access.redhat.com/management/systems>
2. Create a new system, call it whatever you like
3. Select the newly created system
4. Select Subscriptions tab
5. Select Attach Subscription
6. Search and add the "Red Hat Developer Subscription for Individuals" Subscription
7. In the same window select the Download Certificates button
8. Unzip the consumer_export within the zipped file
9. Grab the location of consumer_export/export/entitlement_certificates/*.pem file

Follow the Instructions from <https://docs.nvidia.com/datacenter/kubernetes/openshift-on-gpu-install-guide/index.html#openshift-gpu-install-gpu-operator-via-helmv3> to test the entitlement...

```sh
cp <path/to/pem/file>/<certificate-file-name>.pem nvidia.pem
curl -O  https://raw.githubusercontent.com/openshift-psap/blog-artifacts/master/how-to-use-entitled-builds-with-ubi/0003-cluster-wide-machineconfigs.yaml.template
# if > OCP 4.6 modify the spec.config.ignition.version to 3.2.0 for all MachineConfigs
sed  "s/BASE64_ENCODED_PEM_FILE/$(base64 -w0 nvidia.pem)/g" 0003-cluster-wide-machineconfigs.yaml.template > 0003-cluster-wide-machineconfigs.yaml
oc create -f 0003-cluster-wide-machineconfigs.yaml
oc get machineconfig | grep entitlement
cat << EOF >> mypod.yaml 
apiVersion: v1
kind: Pod
metadata:
 name: cluster-entitled-build-pod
spec:
 containers:
   - name: cluster-entitled-build
     image: registry.access.redhat.com/ubi8:latest
     command: [ "/bin/sh", "-c", "dnf search kernel-devel --showduplicates" ]
 restartPolicy: Never
EOF
oc create -f mypod.yaml
oc logs cluster-entitled-build-pod -n default
```

Should see something similar to the following...

```sh
Updating Subscription Management repositories.
Unable to read consumer identity
Subscription Manager is operating in container mode.
Red Hat Enterprise Linux 8 for x86_64 - AppStre  15 MB/s |  14 MB     00:00    
Red Hat Enterprise Linux 8 for x86_64 - BaseOS   15 MB/s |  13 MB     00:00    
Red Hat Universal Base Image 8 (RPMs) - BaseOS  493 kB/s | 760 kB     00:01    
Red Hat Universal Base Image 8 (RPMs) - AppStre 2.0 MB/s | 3.1 MB     00:01    
Red Hat Universal Base Image 8 (RPMs) - CodeRea  12 kB/s | 9.1 kB     00:00    
====================== Name Exactly Matched: kernel-devel ======================
kernel-devel-4.18.0-80.1.2.el8_0.x86_64 : Development package for building
                                        : kernel modules to match the kernel
kernel-devel-4.18.0-80.el8.x86_64 : Development package for building kernel
                                  : modules to match the kernel
kernel-devel-4.18.0-80.4.2.el8_0.x86_64 : Development package for building
                                        : kernel modules to match the kernel
kernel-devel-4.18.0-80.7.1.el8_0.x86_64 : Development package for building
                                        : kernel modules to match the kernel
kernel-devel-4.18.0-80.11.1.el8_0.x86_64 : Development package for building
                                         : kernel modules to match the kernel
kernel-devel-4.18.0-147.el8.x86_64 : Development package for building kernel
                                   : modules to match the kernel
kernel-devel-4.18.0-80.11.2.el8_0.x86_64 : Development package for building
                                         : kernel modules to match the kernel
kernel-devel-4.18.0-80.7.2.el8_0.x86_64 : Development package for building
                                        : kernel modules to match the kernel
kernel-devel-4.18.0-147.0.3.el8_1.x86_64 : Development package for building
                                         : kernel modules to match the kernel
kernel-devel-4.18.0-147.0.2.el8_1.x86_64 : Development package for building
                                         : kernel modules to match the kernel
kernel-devel-4.18.0-147.3.1.el8_1.x86_64 : Development package for building
                                         : kernel modules to match the kernel
```

Deploy the pytorch-app (which also builds the app)...

```sh
helm upgrade -i pytorch-app helm/pytorch-app -n proactive-node-scaling-test2 --set image.repository=image-registry.openshift-image-registry.svc:5000/proactive-node-scaling-test2/pytorch-app --set replicaCount=1
```

Alternatively, generate the Dockerfile and scripts from s2i for building the image locally...

```sh
s2i build pytorch-app/ registry.access.redhat.com/ubi8/python-38:latest --as-dockerfile=Dockerfile
```
