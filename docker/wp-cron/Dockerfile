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
        less \
        mariadb-client \
        php-cli \
        php-mysql \
        php-curl \
        python3 \
        python3-pip \
     && rm -rf /var/lib/apt/lists/*; # from 1.12GB to 869MB

RUN set -e -x; cd /usr/local/bin/ ; \
    curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" ; \
    chmod +x kubectl

COPY ./requirements.txt .
RUN pip3 install -r ./requirements.txt --break-system-packages

COPY --from=quay-its.epfl.ch/svc0041/wp-base:rc /wp /wp
COPY --from=quay-its.epfl.ch/svc0041/wp-base:rc /usr/local/bin/wp /usr/local/bin/wp

ADD wp-cron.py wordpresses.py pushgateway.py /
