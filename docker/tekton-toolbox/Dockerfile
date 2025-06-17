FROM ubuntu:noble

RUN set -e -x; export DEBIAN_FRONTEND=noninteractive; \
    apt -qy update; \
    apt -qy install git jq pwgen ; \
    apt-get clean
