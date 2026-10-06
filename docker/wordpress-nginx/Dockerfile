# The `wp-nginx` image is now wp-controller (https://github.com/epfl-si/wp-controller):
# a kopf controller that watches the WordpressSite resources, renders the
# nginx configuration and reloads nginx, instead of ingress-nginx.
FROM python:3.13-trixie
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    python3-dev \
    nginx \
    libnginx-mod-http-lua \
    && rm -f /etc/nginx/sites-enabled/default \
    && rm -rf /var/lib/apt/lists/*

# The build context is this directory, which doesn't hold the controller's
# source: fetch it. Set to a branch, tag or commit.
ARG WP_CONTROLLER_REF=main
RUN set -ex; \
    git clone https://github.com/epfl-si/wp-controller.git /tmp/wp-controller; \
    git -C /tmp/wp-controller checkout "$WP_CONTROLLER_REF"; \
    cp -a /tmp/wp-controller/. /app/; \
    rm -rf /tmp/wp-controller /app/.git

RUN pip install --no-cache-dir -r requirements.txt
RUN set -ex; mkdir -p /etc/nginx/snippets /etc/nginx/lua; \
    cp src/templates/fastcgi.conf /etc/nginx/snippets/fastcgi.conf; \
    cp src/templates/generic.conf /etc/nginx/conf.d/generic.conf; \
    cp src/templates/lua/*.lua /etc/nginx/lua/; \
    sed -i 's|^pid .*;|pid /tmp/nginx/nginx.pid;|; /^user /d' /etc/nginx/nginx.conf

# The WordPress codebase: served directly for static assets
# (wp-includes/wp-admin/wp-content plugins/themes) and PHP error pages.
COPY --from=quay-its.epfl.ch/svc0041/wp-base:rc /wp /wp

# Group is set to root (GID 0) to match OpenShift doctrine of not granting “true”
# root.
RUN groupadd -r wp-controller && useradd -r -m -g wp-controller wp-controller \
    && mkdir -p /etc/nginx/errors /tmp/nginx/client_body /tmp/nginx/proxy /tmp/nginx/fastcgi /tmp/nginx/uwsgi /tmp/nginx/scgi \
    && chown -R wp-controller:0 /etc/nginx/conf.d /etc/nginx/snippets /etc/nginx/errors /tmp/nginx /var/log/nginx /run \
    && chmod -R g+rwX /etc/nginx/conf.d /etc/nginx/snippets /etc/nginx/errors /tmp/nginx /var/log/nginx /run
# So `pip install --user` has a real home to write to, and its console
# scripts are on PATH.
ENV PATH="/home/wp-controller/.local/bin:${PATH}"
USER wp-controller

CMD ["sh", "-c", "kopf run main.py --namespace=${WATCH_NAMESPACE}"]
