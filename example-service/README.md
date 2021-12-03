# About

## Configure Docker registry

Run the following command to configure Docker registry access for GCP:

```
gcloud auth configure-docker europe-west3-docker.pkg.dev
```

After that you can run `push-image.sh` script that builds and pushes the image to the registry.
