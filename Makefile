.PHONY: all
all: gitbackup

# Change this if you lack access to either of these Keybase repositories:
BACKUP_NAMESPACES = wwp wwp-test

.PHONY: checkout
checkout:
	$(MAKE) k8s-backup/wwp-test || true
	$(MAKE) k8s-backup/wwp || true

k8s-backup/wwp-test:
	mkdir k8s-backup || true
	cd k8s-backup && git clone keybase://team/epfl_wp_test/k8s-backup wwp-test

k8s-backup/wwp:
	mkdir k8s-backup || true
	cd k8s-backup && git clone keybase://team/epfl_wp_prod/k8s-backup wwp

_BACKUP_REPOS = $(patsubst %, k8s-backup/%, $(BACKUP_NAMESPACES))
_BACKUP_YAMLS = $(patsubst %, %/configmaps.yaml, $(_BACKUP_REPOS))

COMMIT_MSG = "Automatic commit"

.PHONY: gitbackup
gitbackup: $(_BACKUP_YAMLS)
	set -e -x;                                                                         \
        for keybase_repo in $(_BACKUP_REPOS); do                                           \
	  (cd $$keybase_repo;                                                              \
	   git fetch; git reset --hard origin/master;                                      \
	   oc get -o yaml -n "`basename "$$keybase_repo"`" configmaps > configmaps.yaml;   \
	   oc get -o yaml -n "`basename "$$keybase_repo"`" routes > routes.yaml;           \
	   git add *.yaml;                                                                 \
	   git commit -m "`echo "$(COMMIT_MSG)\n\nmade with $(MAKE)"`" *.yaml || true;     \
	   git push);                                                                      \
	done

S3_ENDPOINT_URL=https://s3.epfl.ch/
S3_ASSETS_BUCKET=svc0041-c1561ba80625465c2a53f01693922e7c

define source_assets_secrets
	. /keybase/team/epfl_wp_test/s3-assets-credentials.sh; \
	export AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_DEFAULT_REGION
endef

.PHONY: assets
assets:
	@-mkdir assets 2>/dev/null || true
	$(source_assets_secrets); \
	aws --endpoint-url=$(S3_ENDPOINT_URL) s3 sync s3://$(S3_ASSETS_BUCKET) assets/

.PHONY: push-assets
push-assets:
	$(source_assets_secrets); \
	aws --endpoint-url=$(S3_ENDPOINT_URL) s3 sync assets/ s3://$(S3_ASSETS_BUCKET)
