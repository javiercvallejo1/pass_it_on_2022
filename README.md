# pass_it_on_2022
This project describes a simple implementation of airflow on kubernetes, additionaly, provides a study case example using this architecture.

the repo has 2 branches: devops and airflow
    devops contains all necesary definitions to create infrastructure
    airflow contains some sample dags to test deployment

# terraform-gcp-gke-airflow

The current architecture was implemented following this guide [Provision a GKE Cluster guide](https://learn.hashicorp.com/tutorials/terraform/gke?in=terraform/kubernetes)

### Prerequisites

- GCP account configured. 
- Kubectl cli

#### Dependencies
- gcloud cli
- Cluster version: 1.20 
- Terraform >= 0.13

### Installing

To have K8s cluster running:

Execute Terraform commands:

```
terraform init
```
```
terraform apply --var-file=terraform.tfvars
```
Once that the cluster is created, set the kubectl context:

```
gcloud container clusters get-credentials $(terraform output -raw kubernetes_cluster_name) --region $(terraform output -raw location)
```

To destroy the GKE cluster, we run:

```
terraform destroy --var-file=terraform.tfvars
```
### Airflow
To work with Airflow we will use a NFS service, we will created on the cluster.

Create a namespace for the nsf service
```
kubectl create namespace nfs
```
Now is time to create the nfs server 
```
kubectl -n nfs apply -f nfs/nfs-server.yaml 
```
export the nfs server.
```
export NFS_SERVER=$(kubectl -n nfs get service/nfs-server -o jsonpath="{.spec.clusterIP}") 
```

To install airflow go to the directory `kubernetes/`. [Install Airflow](../kubernetes/README.md)

# airflow

### Prerequisites
- Helm 3

#### Dependencies
- Kubernetes cluster version: 1.20 

### Storage
Create a namespace for storage deployment:
```
kubectl create namespace storage
```
Add the chart for the nfs-provisioner
```
helm repo add nfs-subdir-external-provisioner https://kubernetes-sigs.github.io/nfs-subdir-external-provisioner/
```
Install nfs-external-provisioner
```
helm install nfs-subdir-external-provisioner nfs-subdir-external-provisioner/nfs-subdir-external-provisioner \
    --namespace storage \
    --set nfs.server=$NFS_SERVER \
    --set nfs.path=/
```
## For Airflow

Here we are using official Airflow helm chart as example, but, can also been installed any other Airflow distribution.

Create the namespace
```
kubectl create namespace airflow
```

Add the chart repository and confirm:
```
helm repo add apache-airflow https://airflow.apache.org
```

Update the file `airflow-values.yaml` attributes; repo, branch and subPath of your DAGs. 
```yaml
    gitSync:
    enabled: true

    # git repo clone url
    # ssh examples ssh://git@github.com/apache/airflow.git
    # git@github.com:apache/airflow.git
    # https example: https://github.com/apache/airflow.git
    repo: https://github.com/javiercvallejo1/pass_it_on_2022.git
    branch: airflow
    rev: HEAD
    depth: 1
    # the number of consecutive failures allowed before aborting
    maxFailures: 0
    # subpath within the repo where dags are located
    # should be "" if dags are at repo root
    subPath: ""
```

Install the airflow chart from the repository:
```
helm install airflow -f airflow-values.yaml apache-airflow/airflow --namespace airflow
```
We can verify that our pods are up and running by executing:
```
kubectl get pods -n airflow
```

### Accessing to Airflow dashboard

The Helm chart shows how to connect:
```
You can now access your dashboard(s) by executing the following command(s) and visiting the corresponding port at localhost in your browser:

Airflow Webserver:     kubectl port-forward svc/airflow-webserver 8080:8080 --namespace airflow
Flower dashboard:      kubectl port-forward svc/airflow-flower 5555:5555 --namespace airflow
Default Webserver (Airflow UI) Login credentials:
    username: admin
    password: admin
Default Postgres connection credentials:
    username: postgres
    password: postgres
    port: 5432

You can get Fernet Key value by running the following:

    echo Fernet Key: $(kubectl get secret --namespace airflow airflow-fernet-key -o jsonpath="{.data.fernet-key}" | base64 --decode)
```
