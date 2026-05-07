# Lab 15 — StatefulSets & Persistent Storage

## 1. StatefulSet Overview

StatefulSet was used for `devops-info` because the application stores state in `/data/visits`.

Deployment is suitable for stateless applications where pods are interchangeable. Deployment pods have random names, can be created or deleted in any order, and usually do not have stable per-pod storage.

StatefulSet is suitable for stateful applications because it provides:

- stable pod names;
- stable network identities;
- stable per-pod PersistentVolumeClaims;
- ordered deployment, scaling, and updates.

Examples of stateful workloads:

- PostgreSQL
- MySQL
- MongoDB
- Kafka
- RabbitMQ
- Elasticsearch
- Cassandra

## 2. Resource Verification

Command:

```bash
kubectl get po,sts,svc,pvc -n lab15
```

Output:

```text
NAME                                       READY   STATUS      RESTARTS   AGE
pod/lab15-devops-info-0                    1/1     Running     0          43s
pod/lab15-devops-info-1                    1/1     Running     0          35s
pod/lab15-devops-info-2                    1/1     Running     0          27s
pod/lab15-devops-info-post-install-k4jxq   0/1     Completed   0          43s
pod/lab15-devops-info-pre-install-527m4    0/1     Completed   0          53s

NAME                                 READY   AGE
statefulset.apps/lab15-devops-info   3/3     43s

NAME                                 TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)    AGE
service/lab15-devops-info            ClusterIP   10.96.14.47   <none>        80/TCP     43s
service/lab15-devops-info-headless   ClusterIP   None          <none>        5000/TCP   43s

NAME                                             STATUS   VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   AGE
persistentvolumeclaim/data-lab15-devops-info-0   Bound    pvc-7f54f509-8747-43cf-9987-3aeb5a383284   100Mi      RWO            standard       43s
persistentvolumeclaim/data-lab15-devops-info-1   Bound    pvc-b60b3eff-6440-4db5-b70e-1c9cf15b6a1d   100Mi      RWO            standard       35s
persistentvolumeclaim/data-lab15-devops-info-2   Bound    pvc-2198436d-b667-4a7e-ba94-ebcde833a870   100Mi      RWO            standard       27s
persistentvolumeclaim/lab15-devops-info-data     Bound    pvc-4817edb9-9589-42c8-b5de-2ed0872c7a6b   100Mi      RWO            standard       43s
```

The important StatefulSet PVCs are:

```text
data-lab15-devops-info-0
data-lab15-devops-info-1
data-lab15-devops-info-2
```

These PVCs were created automatically from `volumeClaimTemplates`.

## 3. Network Identity

`nslookup` was not installed inside the container, so DNS resolution was tested with `getent hosts`.

Command:

```bash
kubectl exec -it lab15-devops-info-0 -n lab15 -- /bin/sh
getent hosts lab15-devops-info-1.lab15-devops-info-headless
```

Output:

```text
10.244.0.38     lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local
```

StatefulSet DNS pattern:

```text
<pod-name>.<headless-service-name>.<namespace>.svc.cluster.local
```

Example:

```text
lab15-devops-info-1.lab15-devops-info-headless.lab15.svc.cluster.local
```

## 4. Per-Pod Storage Evidence

Port-forwarding was used to access each StatefulSet pod directly:

```bash
kubectl port-forward pod/lab15-devops-info-0 18080:5000 -n lab15
kubectl port-forward pod/lab15-devops-info-1 18081:5000 -n lab15
kubectl port-forward pod/lab15-devops-info-2 18082:5000 -n lab15
```

Requests to `/` increment the visit counter stored in `/data/visits`.

Commands:

```bash
curl localhost:18080
curl localhost:18080
curl localhost:18080/visits

curl localhost:18081
curl localhost:18081/visits

curl localhost:18082
curl localhost:18082/visits
```

Results:

```text
lab15-devops-info-0: visits = 5
lab15-devops-info-1: visits = 1
lab15-devops-info-2: visits = 1
```

The responses showed different pod hostnames:

```text
hostname: lab15-devops-info-0
hostname: lab15-devops-info-1
hostname: lab15-devops-info-2
```

This proves that each StatefulSet pod has isolated persistent storage.

## 5. Persistence Test

Commands:

```bash
kubectl exec lab15-devops-info-0 -n lab15 -- cat /data/visits
kubectl delete pod lab15-devops-info-0 -n lab15
kubectl wait --for=condition=Ready pod/lab15-devops-info-0 -n lab15 --timeout=120s
kubectl exec lab15-devops-info-0 -n lab15 -- cat /data/visits
```

Output after pod recreation:

```text
5
```

The visit counter value was preserved after deleting and recreating the pod. This confirms that `lab15-devops-info-0` reattached to the same PVC:

```text
data-lab15-devops-info-0
```

## 6. Conclusion

The StatefulSet implementation successfully provides:

- stable pod names;
- stable DNS identities through a headless Service;
- per-pod PVCs through `volumeClaimTemplates`;
- isolated visit counters per pod;
- persistent data after pod deletion.
