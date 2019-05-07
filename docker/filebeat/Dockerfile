FROM docker.elastic.co/beats/filebeat:7.0.0

COPY docker-entrypoint.sh /
USER root
RUN chmod a+x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
