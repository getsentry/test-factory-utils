# buildkit

Wrapper around moby/buildkit that adds `docker-credential-gcr` and a few packages to facilitate troubleshooting.

`docker-credential-gcr` is needed mostly to authenticate with Artifact Registry: https://cloud.google.com/artifact-registry/docs/docker/authentication#standalone-helper
