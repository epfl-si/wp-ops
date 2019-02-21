# A Makefile that mostly works around
# https://github.com/openshift/origin/issues/8971

.PHONY: usage
usage:
	@echo >&2 "Usage: $(MAKE) pushtotest"
	@echo >&2 "       $(MAKE) pushtoprod"


.PHONY: pushtotest
pushtotest:
	-oc delete -n wwp-test -f disk-usage-report.yaml
	 oc create -n wwp-test -f disk-usage-report.yaml

.PHONY: pushtoprod
pushtoprod:
	-$(test2prod) < disk-usage-report.yaml | oc delete -n wwp -f -
	 $(test2prod) < disk-usage-report.yaml | oc create -n wwp -f -


test2prod := perl -pe 's|docker-registry.default.svc:5000/wwp-test|docker-registry.default.svc:5000/wwp|g'
