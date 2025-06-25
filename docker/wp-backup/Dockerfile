FROM quay-its.epfl.ch/svc0041/wp-cron:2025-041

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" ; \
    unzip awscliv2.zip ; \
    sudo ./aws/install

COPY wordpresssites-backup.sh /

RUN chmod +x /wordpresssites-backup.sh
