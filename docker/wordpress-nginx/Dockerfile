FROM openresty/openresty:1.27.1.1-0-alpine-fat AS openresty
FROM wp-base
FROM rancher/nginx-ingress-controller:nginx-1.11.3-rancher1

USER 0

# https://github.com/kubernetes/ingress-nginx/issues/3668
RUN apk add --no-cache libcap && \
    setcap -r /nginx-ingress-controller && \
    apk del libcap

# In OpenShift, getting permissions is hard mmkay
RUN mkdir -p 1777 /var/run/openresty/
RUN chmod 1777 /etc/ingress-controller/ssl/ /tmp/nginx/ \
    /etc/ingress-controller/telemetry/ /etc/nginx/
RUN chmod 666 /etc/nginx/nginx.conf

USER 101

COPY --from=openresty /usr/local/openresty/nginx/sbin/nginx /usr/bin/nginx
COPY --from=openresty /usr/local/openresty /usr/local/openresty
COPY --from=wp-base /wp /wp
COPY nginx.tmpl /etc/nginx/template/
COPY wordpress_fastcgi.conf /etc/nginx/template/
ENV LD_LIBRARY_PATH=/usr/local/openresty/luajit/lib:/usr/local/openresty/pcre2/lib:/usr/local/openresty/openssl3/lib
