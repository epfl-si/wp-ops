# This container won't work in a development environment: it needs to be
# deployed in the Kubernetes cluster and have to access this node's path
# `/var/run/secrets/kubernetes.io/serviceaccount/token` in order to access the
# Kubernetes's API.
# See https://kubernetes.io/docs/tasks/configure-pod-container/configure-service-account/

FROM ubuntu:noble AS base

ENV DEBIAN_FRONTEND=noninteractive

RUN set -e -x; apt-get -qy update; \
    apt-get --no-install-recommends -qy install \
        python3 \
        mariadb-client \
     && rm -rf /var/lib/apt/lists/*; # from 1.12GB to 869MB

FROM base AS build

RUN set -e -x; apt-get -qy update; \
    apt-get --no-install-recommends -qy install \
        curl \
        git \
        less \
        libmariadb-dev \
        python3-pip \
        python3-dev \
        build-essential \
     && rm -rf /var/lib/apt/lists/*; # from 1.12GB to 869MB

RUN set -e -x; cd /usr/local/bin/ ; \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" ; \
    chmod +x kubectl

COPY ./requirements.txt .
RUN pip3 install -r ./requirements.txt --break-system-packages


FROM base AS run

COPY --from=build /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=build /usr/local/bin/kubectl /usr/local/bin/kubectl

ADD wp-fleet.py wordpresssites.py database.py /
