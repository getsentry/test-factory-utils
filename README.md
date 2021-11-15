# test-factory

Configuration and tooling for the Sentry testbed environment.

## Setup

1. Prepare a virtual environment with Python 3.7+ and activate it

   For example:
   
   ```
   python3 -m venv .venv
   
   source .venv/bin/activate
   ```
  

2. Install [`sentry-kube`](https://github.com/getsentry/ops/tree/master/k8s/cli) (into the new environment)

   `sentry-kube` is currently hosted in https://github.com/getsentry/ops/ repository.

   ```
   git clone https://github.com/getsentry/ops/
   
   ./ops/k8s/cli/install.sh
   ```
