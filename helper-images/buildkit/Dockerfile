FROM moby/buildkit:v0.10.3

# For testing and troubleshooting
RUN apk add --no-cache podman curl bash

ENV DOCKER_CRED_VERSION="2.1.0"
ENV DOCKER_CRED_SHA="91cca7b5ca33133bcd217982be31d670efe7f1a33eb5be72e014f74feecac00f"

RUN mkdir /tmp/docker-cred-gcr \
    && cd /tmp/docker-cred-gcr \
    && DOCKER_CRED_TMP=docker-cred-gcr.tar.gz \
    && wget "https://github.com/GoogleCloudPlatform/docker-credential-gcr/releases/download/v${DOCKER_CRED_VERSION}/docker-credential-gcr_linux_amd64-${DOCKER_CRED_VERSION}.tar.gz" -O ${DOCKER_CRED_TMP} \
    && echo "$DOCKER_CRED_SHA  $DOCKER_CRED_TMP" > docker_cred.sha256 \
    && sha256sum -c docker_cred.sha256 \
    && tar xvf docker-cred-gcr.tar.gz \
    && mv docker-credential-gcr /usr/bin/docker-credential-gcr \
    && chmod +x /usr/bin/docker-credential-gcr \
    && cd / \
    && rm -rf /tmp/docker-cred-gcr

RUN docker-credential-gcr configure-docker \
    --registries=europe-west3-docker.pkg.dev,us-central1-docker.pkg.dev,asia-northeast1-docker.pkg.dev

ENTRYPOINT [ "/bin/bash" ]
