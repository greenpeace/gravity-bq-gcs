SHELL := /bin/bash

TF_TEST_DIR := tf/test

.EXPORT_ALL_VARIABLES:

# Local function runtime bucket
BUCKET ?= cosmos-bq-gcs-data

# Bucket to store generated source files
# See: tf/artifacts/source.tf
RELEASE_SOURCE_BUCKET ?= cosmos-bq-gcs-source

# Match any semver tag beginning with 'v', eg v1.2.33
SEMVER_REGEX := ^v[0-9]+\.[0-9]+\.[0-9]+

TAGGED_RELEASE := $(shell [[ "$(CI_COMMIT_TAG)" =~ $(SEMVER_REGEX) ]] && echo true)

ifdef TAGGED_RELEASE
ENVIRONMENT := prod
else
ENVIRONMENT := dev
endif

ifndef CI_COMMIT_REF_NAME
CI_COMMIT_REF_NAME := $(shell git rev-parse --abbrev-ref HEAD)
endif

ifndef CI_COMMIT_TAG
CI_COMMIT_TAG := $(shell git describe --abbrev=0 --tags)
endif

ifndef CI_COMMIT_SHORT_SHA
CI_COMMIT_SHORT_SHA := $(shell git rev-parse --short HEAD)
endif

all: install tf

install:
	$(MAKE) -C src install

dev:
	$(MAKE) -C src dev

# =============================================================================

clean:
	rm -f $(TF_TEST_DIR)/build/bq-gcs.zip

lint:
	pylint src

dev-version-string:
	if [[ "$(CI_COMMIT_REF_NAME)" != "master" ]] && [[ -z "$(TAGGED_RELEASE)" ]]; then \
		sed -i -e 's#APP_VERSION = .*$$#APP_VERSION = "$(shell echo $(CI_COMMIT_TAG) | cut -dv -f2)-$(CI_COMMIT_REF_NAME)-$(CI_COMMIT_SHORT_SHA).$(shell head /dev/urandom | tr -dc 0-9 | head -c 8)"#g' src/main.py; fi

# =============================================================================

.PHONY: tf
tf: lint tf-app
#
# tf-fixtures:
# 	$(MAKE) -C tf/deployments/test/fixtures

tf-app $(TF_TEST_DIR)/build/bq-gcs.zip: dev-version-string
	$(MAKE) -sC $(TF_TEST_DIR)

tf-plan:
	$(MAKE) -sC $(TF_TEST_DIR) plan

tf-apply:
	$(MAKE) -sC  $(TF_TEST_DIR) apply

tf-output:
	@echo "Fixtures:"
	@echo "---"
	@$(MAKE) -sC $(TF_TEST_DIR) output
	@echo
	@echo "App:"
	@echo "---"
	@$(MAKE) -sC $(TF_TEST_DIR) output

tf-show:
	@$(MAKE) -sC $(TF_TEST_DIR) show

tf-destroy:
	@$(MAKE) -sC $(TF_TEST_DIR) destroy

tf-test test:
	@$(MAKE) -sC $(TF_TEST_DIR) test

# =============================================================================

# git-flow-release
# ---
# Performs the full git flow release process
git-flow-release: git-flow-release-start git-flow-release-version git-flow-release-finish

git-flow-release-start:
ifeq ($(strip $(NEW_RELEASE)),)
	$(error NEW_RELEASE is not set)
endif
	git flow release start $(NEW_RELEASE)

git-flow-release-version:
ifeq ($(strip $(NEW_RELEASE)),)
	$(error NEW_RELEASE is not set)
endif
	sed -i -e 's#APP_VERSION = .*$$#APP_VERSION = "$(shell echo $(NEW_RELEASE) | cut -dv -f2)"#g' src/main.py

git-flow-release-finish:
ifeq ($(strip $(NEW_RELEASE)),)
	$(error NEW_RELEASE is not set)
endif
	sleep 1
	git add .
	git commit -m "Release $(NEW_RELEASE)"
	sleep 1
	git flow release finish "$(NEW_RELEASE)" -m "Release $(NEW_RELEASE)" -T "$(NEW_RELEASE)"

# =============================================================================

set:
	gcloud config set auth/impersonate_service_account $(TF_EMAIL_PROD)

unset:
	gcloud config unset auth/impersonate_service_account

release-unauth: $(TF_TEST_DIR)/build/bq-gcs.zip dev-version-string
ifndef CI_COMMIT_REF_NAME
	$(error Intended to be run in GitLab CI only)
endif
	gsutil cp $(TF_TEST_DIR)/build/bq-gcs.zip gs://$(RELEASE_SOURCE_BUCKET)/bq-gcs-$(CI_COMMIT_REF_NAME).zip
	gsutil cp $(TF_TEST_DIR)/build/bq-gcs.zip gs://$(RELEASE_SOURCE_BUCKET)/bq-gcs-latest.zip

	if [[ "$(CI_COMMIT_REF_NAME)" = "develop" ]]; then { \
		gsutil cp $(TF_TEST_DIR)/build/bq-gcs.zip gs://$(RELEASE_SOURCE_BUCKET)/bq-gcs-$(CI_COMMIT_REF_NAME)-$(CI_COMMIT_SHORT_SHA).zip; \
		set_group_variable.sh $(GITLAB_DEPLOYMENTS_GROUP_ID) BQ_GCS_LOAD_DEVSHA $(CI_COMMIT_SHORT_SHA); \
	} fi

	if [[ "$(TAGGED_RELEASE)" = "true" ]]; then { \
		set_group_variable.sh $(GITLAB_DEPLOYMENTS_GROUP_ID) BQ_GCS_LOAD_VERSION $(CI_COMMIT_REF_NAME); \
	} fi

release: set release-unauth unset
