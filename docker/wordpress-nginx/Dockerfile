FROM openresty/openresty:1.27.1.1-0-alpine-fat AS openresty
FROM wp-base
FROM rancher/nginx-ingress-controller:nginx-1.11.3-rancher1

USER 0

# https://github.com/kubernetes/ingress-nginx/issues/3668
RUN apk add --no-cache libcap && \
    setcap -r /nginx-ingress-controller && \
    apk del libcap

# In OpenShift, getting permissions is hard mmkay
RUN mkdir /var/run/openresty/
RUN chmod 1777 /etc/ingress-controller/ssl/ /tmp/nginx/ \
    /etc/ingress-controller/telemetry/ /etc/nginx/ \
    /var/run/openresty/
RUN chmod 666 /etc/nginx/nginx.conf

## Uncomment the following line if you want to test out your RBAC live:
# COPY --from=bitnami/kubectl:latest /opt/bitnami/kubectl/bin/kubectl /usr/local/bin/kubectl

COPY ./prometheus/prometheus.lua /etc/nginx/lua/prometheus.lua
COPY ./prometheus/prometheus_keys.lua /etc/nginx/lua/prometheus_keys.lua
COPY ./prometheus/prometheus_resty_counter.lua /etc/nginx/lua/prometheus_resty_counter.lua
RUN chown www-data:www-data /etc/nginx/lua/prometheus.lua /etc/nginx/lua/prometheus_keys.lua /etc/nginx/lua/prometheus_resty_counter.lua

USER 101

COPY --from=openresty /usr/local/openresty/nginx/sbin/nginx /usr/bin/nginx
COPY --from=openresty /usr/local/openresty /usr/local/openresty
COPY --from=wp-base /wp /wp
COPY nginx.tmpl /etc/nginx/template/
COPY wordpress_fastcgi.conf /etc/nginx/template/
ENV LD_LIBRARY_PATH=/usr/local/openresty/luajit/lib:/usr/local/openresty/pcre2/lib:/usr/local/openresty/openssl3/lib
