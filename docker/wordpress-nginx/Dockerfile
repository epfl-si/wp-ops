FROM openresty/openresty:1.27.1.1-0-alpine-fat AS openresty
FROM wp-base
FROM rancher/nginx-ingress-controller:nginx-1.11.3-rancher1
COPY --from=openresty /usr/local/openresty/nginx/sbin/nginx /usr/bin/nginx
COPY --from=openresty /usr/local/openresty /usr/local/openresty
COPY --from=wp-base /wp /wp
COPY nginx.tmpl /etc/nginx/template/
COPY wordpress_fastcgi.conf /etc/nginx/template/
ENV LD_LIBRARY_PATH=/usr/local/openresty/luajit/lib:/usr/local/openresty/pcre2/lib:/usr/local/openresty/openssl3/lib
