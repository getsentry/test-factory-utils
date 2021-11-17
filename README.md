# test-factory

Configuration and tooling for the Sentry testbed environment.

## Setup

1. [Install `gcloud`](https://cloud.google.com/sdk/docs/install)


1. Prepare a Python virtual environment with Python 3.7+ and activate it.

   For example:

   ```
   python3 -m venv .venv

   source .venv/bin/activate
   ```

1. Install [`sentry-kube`](https://github.com/getsentry/ops/tree/master/k8s/cli) **into the newly created virtual environment**.

   `sentry-kube` is currently hosted in https://github.com/getsentry/ops/ repository.

   ```
   # Clone the ops repository somewhere else
   cd ../
   
   git clone https://github.com/getsentry/ops/

   ./ops/k8s/cli/install.sh
   ```
   
1. Pull the Kubernetes cluster credentials from Google. It'll fetch the authentication credentials from GCP and write to a local configuration file.

   ```
   gcloud container clusters get-credentials cluster-1 --region europe-west3-b --project sentry-st-testing
   ```

### Testing the installation

Run the following commands to check your setup:

```
# Should list all running pods in the cluster
sentry-kube kubectl get pod -A

# Should exit without error (output may be empty)
sentry-kube diff relay
```

## Google Cloud UI

The GCP project we currently operate in is called [`sentry-st-testing`](https://console.cloud.google.com/home/dashboard?project=sentry-st-testing).

## FAQ

### Can this repo be made public?

Potentially, but currently it contains some data that we don't want to make public (e.g., license key in "geoipupdate" service). Those values have to be cleaned up and rotated before we make the repo public.
