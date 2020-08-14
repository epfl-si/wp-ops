FROM epflsi/os-wp-base

RUN apt-get -qy update && apt-get -qy install --no-install-recommends \
    bash-completion \
    htop \
    inotify-tools \
    less \
    lnav \
    make \
    mysql-client \
    openssh-server \
    tree \
    pwgen \
    python3 \
    python3-pip \
    python3-virtualenv \
    python3-setuptools \
    virtualenv \
    screen \
    tmux \
    software-properties-common \
    restic \
  && \
    apt-get -qy autoremove && \
    apt-get clean

RUN mkdir /var/run/sshd && \
    sed -ri 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config && \
    sed -ri 's/AcceptEnv LANG LC_\*/AcceptEnv LANG LC_\* WP_ENV/g' /etc/ssh/sshd_config && \
    sed -ri 's/#UsePrivilegeSeparation sandbox/UsePrivilegeSeparation no/g'  /etc/ssh/sshd_config && \
    sed -ri 's/#?X11Forwarding\s+.*/X11Forwarding no/g' /etc/ssh/sshd_config && \
    mkdir /tmp/openshift && \
    cd /tmp/openshift && \
    curl -L -O https://github.com/openshift/origin/releases/download/v3.10.0/openshift-origin-client-tools-v3.10.0-dd10d17-linux-64bit.tar.gz && \
    tar -xf openshift-origin-client-tools-v3.10.0-dd10d17-linux-64bit.tar.gz && \
    mv */oc /usr/local/bin && \
    cd / && \
    rm -rf /tmp/openshift && \
    mkdir /root/.ssh

COPY nfs-bashrc.sh jahia2wp.sh /etc/profile.d/
COPY new-wp-site.sh /usr/local/bin/new-wp-site
RUN chmod a+x /usr/local/bin/new-wp-site
COPY ./docker-entrypoint.sh /

# lnav custom file formats
COPY lnav /var/www/.lnav/formats/epfl

ARG WP_OPS_BRANCH=master
RUN set -e -x; cd /wp; git clone https://github.com/epfl-si/wp-ops; \
    cd wp-ops; git checkout ${WP_OPS_BRANCH}

# setup access rights
RUN sed -ir 's#www-data.*:/usr/sbin/nologin#www-data:x:33:33:www-data:/var/www:/bin/bash#' /etc/passwd && \
    mkdir -p /var/www/.ssh && \
    chown -R www-data: /var/www && \
    chmod 700 /var/www/.ssh

# Install jahia2wp and its dependencies
RUN set -e -x; cd /; git clone --single-branch --branch release2018 https://github.com/epfl-si/jahia2wp
RUN set -e -x; \
    apt -qy install build-essential libxml2-dev python3-dev ; \
    pip3 install -r /jahia2wp/requirements/local.txt; \
    apt -qy remove --purge build-essential libxml2-dev python3-dev ; \
    apt -qy autoremove --purge

EXPOSE 22
ENTRYPOINT ["/docker-entrypoint.sh"]
