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
	   oc get -o yaml -n "`basename "$$keybase_repo"`" dc > deploymentconfigs.yaml;    \
	   git add *.yaml;                                                                 \
	   git commit -m "`echo "$(COMMIT_MSG)\n\nmade with $(MAKE)"`" *.yaml || true;     \
	   git push);                                                                      \
	done
