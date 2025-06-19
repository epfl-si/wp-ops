FROM ubuntu:noble

RUN set -e -x; export DEBIAN_FRONTEND=noninteractive; \
    apt -qy update; \
    apt -qy install apt-transport-https ca-certificates gnupg curl wget \
            git jq pwgen ; \
    apt-get clean

# https://kubernetes.io/docs/tasks/tools/install-kubectl-linux/
RUN set -e -x; \
    curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.33/deb/Release.key |   \
      gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg ;      \
    chmod 644 /etc/apt/keyrings/kubernetes-apt-keyring.gpg;                \
     echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.33/deb/ /' > /etc/apt/sources.list.d/kubernetes.list; \
    chmod 644 /etc/apt/sources.list.d/kubernetes.list

RUN set -e -x; export DEBIAN_FRONTEND=noninteractive; \
    apt -qy update;                                   \
    apt -qy install kubectl;                          \
    apt-get clean

ADD https://raw.githubusercontent.com/cptmorgan-rh/install-oc-tools/refs/heads/master/install-oc-tools.sh /usr/local/libexec/install-oc-tools.sh
RUN chmod 755 /usr/local/libexec/install-oc-tools.sh
RUN /usr/local/libexec/install-oc-tools.sh --latest
