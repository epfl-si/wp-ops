FROM epflidevelop/os-wp-base

RUN apt-get -qy update && apt-get -qy install --no-install-recommends \
    bash-completion \
    htop \
    less \
    make \
    mysql-client \
    openssh-server \
    tree \
    python3 \
    python3-pip \
    python3-virtualenv \
    python3-setuptools \
    virtualenv \
    screen \
    software-properties-common \
    unzip \
    vim \
  && \
    apt-get -qy autoremove && \
    apt-get clean


RUN mkdir /var/run/sshd && \
    sed -ri 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config && \
    sed -ri 's/AcceptEnv LANG LC_\*/AcceptEnv LANG LC_\* WP_ENV/g' /etc/ssh/sshd_config && \
    sed -ri 's/#UsePrivilegeSeparation sandbox/UsePrivilegeSeparation no/g'  /etc/ssh/sshd_config && \
    sed -ri 's/#?PermitRootLogin\s+.*/PermitRootLogin yes/g' /etc/ssh/sshd_config && \
    mkdir /tmp/openshift && \
    cd /tmp/openshift && \
    curl -L -O https://github.com/openshift/origin/releases/download/v3.10.0/openshift-origin-client-tools-v3.10.0-dd10d17-linux-64bit.tar.gz && \
    tar -xf openshift-origin-client-tools-v3.10.0-dd10d17-linux-64bit.tar.gz && \
    mv */oc /usr/local/bin && \
    cd / && \
    rm -rf /tmp/openshift && \
    mkdir /root/.ssh

COPY jahia2wp.sh /etc/profile.d/
COPY ./docker-entrypoint.sh /

# setup access rights
RUN sed -ir 's#www-data.*:/usr/sbin/nologin#www-data:x:33:33:www-data:/var/www:/bin/bash#' /etc/passwd && \
    mkdir -p /var/www/.ssh && \
    chown -R www-data: /var/www && \
    chmod 700 /var/www/.ssh

RUN ln -s /srv/bin/vjahia2wp /usr/local/bin/

EXPOSE 22
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D"]
