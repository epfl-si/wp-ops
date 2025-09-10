SHELL := /bin/bash

WP_FLEET_IMAGE_NAME = quay-its.epfl.ch/svc0041/wp-fleet
WP_FLEET_IMAGE_TAG ?= latest

.PHONY: build
## Build the image as `WP_FLEET_IMAGE_NAME`
build:
	docker build -t $(WP_FLEET_IMAGE_NAME):$(WP_FLEET_IMAGE_TAG) .

.PHONY: push
## Push the image using `REGISTRY` and `WP_FLEET_IMAGE_TAG`
push:
	docker push $(WP_FLEET_IMAGE_NAME):$(WP_FLEET_IMAGE_TAG)
