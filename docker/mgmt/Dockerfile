FROM debian:stretch

RUN apt-get -y update && apt-get install -y --no-install-recommends \
    apt-transport-https \
    bash-completion \
    curl \
    composer \
    git \
    gnupg \
    htop \
    jq \
    less \
    lsb-release \
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
    apt-get -y autoremove && \
    apt-get clean

RUN curl -sL https://deb.nodesource.com/setup_10.x | bash -
RUN curl -sL https://packages.sury.org/php/apt.gpg > /etc/apt/trusted.gpg.d/php.gpg
RUN echo "deb https://packages.sury.org/php/ $(lsb_release -sc) main" > /etc/apt/sources.list.d/php.list
RUN apt-get -y update
# The following goodies have dependencies above this line, and
# thus must be installed in another round of apt-get
RUN apt-get -y install nodejs \
    php7.1 \
    php7.1-gd \
    php7.1-cli \
    php7.1-curl \
    php7.1-ldap \
    php7.1-mysql \
    php7.1-xml \
    php7.1-zip \
  && \
    apt-get -y autoremove && \
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

# Download latest WP-CLI in the 1.5.x branch (otherwise diggy/polylang-cli
# won't install):
RUN curl -o /usr/local/bin/wp -L `curl https://api.github.com/repos/wp-cli/wp-cli/releases | jq -r '[.[] | select (.tag_name | startswith("v1.5"))][0] | .assets[0].browser_download_url'`
RUN chmod a+x /usr/local/bin/wp

RUN ln -s /srv/bin/vjahia2wp /usr/local/bin/

COPY ./config.yml /var/www/.wp-cli/config.yml
RUN chown -R www-data:www-data /var/www/.wp-cli
RUN su -s /bin/sh www-data -c "wp package install https://github.com/diggy/polylang-cli.git"
RUN su -s /bin/sh www-data -c "wp package install https://github.com/cortneyray/wp-cli-polylang.git"

EXPOSE 22
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D"]
