FROM nginx:alpine

RUN apk add --no-cache bash inotify-tools

COPY generate-nginx-config.sh /usr/local/bin/
COPY entrypoint.sh /usr/local/bin/

RUN chmod +x /usr/local/bin/*.sh

EXPOSE 80

CMD ["/usr/local/bin/entrypoint.sh"]
