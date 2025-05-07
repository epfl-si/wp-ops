# This container won't work in a development environment: it needs to be
# deployed in the Kubernetes cluster and have to access this node's path
# `/var/run/secrets/kubernetes.io/serviceaccount/token` in order to access the
# Kubernetes's API.
# See https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/

FROM ubuntu:noble

ENV DEBIAN_FRONTEND=noninteractive

RUN set -e -x; apt-get -qy update; \
    apt-get --no-install-recommends -qy install \
        curl \
        git \
        mariadb-client \
        php-cli \
        php-mysql \
        python3 \
        python3-pip \
     && rm -rf /var/lib/apt/lists/*; # from 1.12GB to 869MB

RUN set -e -x; cd /usr/local/bin/ ; \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" ; \
    chmod +x kubectl

# `wp-base` below means the image built from https://github.com/epfl-si/wp-ops/tree/WPN/docker/wp-base
COPY --from=wp-base /wp /wp
COPY --from=wp-base /usr/local/bin/wp /usr/local/bin/wp
