FROM bitnamilegacy/nginx-ingress-controller:1.12.1 AS ingress
FROM quay-its.epfl.ch/svc0041/wp-base:rc
FROM openresty/openresty:1.27.1.1-3-alpine-fat

RUN ln /usr/local/openresty/nginx/sbin/nginx /usr/bin/

# Remove the "Welcome to OpenResty!" page
RUN rm /usr/local/openresty/nginx/html/index.html
COPY --from=ingress /nginx-ingress-controller /nginx-ingress-controller
# https://github.com/kubernetes/ingress-nginx/issues/3668
RUN set -e -x; apk add libcap-setcap; \
  setcap -r /nginx-ingress-controller; \
  rm -rf /var/cache/apk/*

ENTRYPOINT /nginx-ingress-controller

COPY --from=ingress /etc/nginx/nginx.conf /etc/nginx/nginx.conf
RUN chown root:root /etc/nginx/nginx.conf
RUN chmod 666 /etc/nginx/nginx.conf

COPY --from=ingress /etc/nginx/lua /etc/nginx/lua

RUN mkdir /tmp/nginx /etc/ingress-controller /etc/ingress-controller/telemetry
RUN cp /usr/local/openresty/nginx/conf/mime.types /etc/nginx/
# In OpenShift, getting permissions is hard mmkay.
# 💡 Permission to write into /etc/nginx/lua/ is required for /etc/nginx/lua/cfg.json
RUN chmod 1777 /tmp/nginx/ \
    /etc/nginx/ \
    /etc/nginx/lua/ \
    /etc/ingress-controller/ \
    /etc/ingress-controller/telemetry/ \
    /var/run/openresty/

## Uncomment the following line if you want to test out your RBAC live:
# COPY --from=bitnamilegacy/kubectl:latest /opt/bitnamilegacy/kubectl/bin/kubectl /usr/local/bin/kubectl

COPY ./prometheus/prometheus.lua /etc/nginx/lua/prometheus.lua
COPY ./prometheus/prometheus_keys.lua /etc/nginx/lua/prometheus_keys.lua
COPY ./prometheus/prometheus_resty_counter.lua /etc/nginx/lua/prometheus_resty_counter.lua
COPY --from=quay-its.epfl.ch/svc0041/wp-base:rc /wp /wp
COPY nginx.tmpl /etc/nginx/template/
COPY wordpress_fastcgi.conf /etc/nginx/template/

# Do this last if you don't want your apk to use OpenResty's own libssl etc. (Hint: it won't work)
ENV LD_LIBRARY_PATH=/usr/local/openresty/luajit/lib:/usr/local/openresty/pcre2/lib:/usr/local/openresty/openssl3/lib
