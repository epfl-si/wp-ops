FROM quay-its.epfl.ch/svc0041/wp-cron:latest

RUN apt-get -qy update
RUN apt-get -qy install unzip jq

RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" ; \
    unzip awscliv2.zip ; \
    ./aws/install

COPY wordpresssites-backup.sh /
COPY restore_sites_prod_to_test.sh /

RUN chmod +x /wordpresssites-backup.sh
RUN chmod +x /restore_sites_prod_to_test.sh
