FROM moby/buildkit:v0.10.3

# Wrappers, troubleshotting
RUN apk add --no-cache podman podman-docker docker-compose curl bash jq gettext

# Install recent 'yq'
RUN YQ_SHA256="042f7462ec8378f8b0d3bac85d1b1a063b63beef5d8e3826bb2377294116ae90" \
    && YQ_TMP=/tmp/yq \
    && wget --quiet -O $YQ_TMP "https://github.com/mikefarah/yq/releases/download/v4.25.2/yq_linux_amd64" \
    && echo "$YQ_SHA256  $YQ_TMP" > yq.sha256 \
    && sha256sum -c yq.sha256 \
    && rm yq.sha256 \
    && mv $YQ_TMP /usr/local/bin/yq \
    && chmod +x /usr/local/bin/yq

# Install 'kompose'
RUN KOMPOSE_SHA256="cd85b8c205dc63985e9bde4911b15c8556029e09671599919ed81bff8453a36f" \
    && KOMPOSE_TMP=/tmp/kompose \
    && curl -L "https://github.com/kubernetes/kompose/releases/download/v1.26.1/kompose-linux-amd64" -o $KOMPOSE_TMP \
    && echo "$KOMPOSE_SHA256  $KOMPOSE_TMP" > kompose.sha256 \
    && sha256sum -c kompose.sha256 \
    && rm kompose.sha256 \
    && mv $KOMPOSE_TMP /usr/local/bin/kompose \
    && chmod +x /usr/local/bin/kompose

# Install 'docker-credential-gcr'
RUN DOCKER_CRED_SHA="91cca7b5ca33133bcd217982be31d670efe7f1a33eb5be72e014f74feecac00f" \
    && DOCKER_CRED_VERSION="2.1.0" \
    && mkdir /tmp/docker-cred-gcr \
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
