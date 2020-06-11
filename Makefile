TF_TEST_DIR := tf/test

dev:
	$(MAKE) -C src dev

send:
	curl -d "@mock.json" \
		-X POST \
		-H "Ce-Type: true" \
		-H "Ce-Specversion: true" \
		-H "Ce-Source: true" \
		-H "Ce-Id: true" \
		-H "Content-Type: application/json" \
		http://localhost:8080

publish:
	gcloud pubsub topics publish gravity-bq-gcs-test-input --message '$(shell cat tf/test/fixtures/payload.json)'

# =============================================================================

clean:
	rm -f $(TF_TEST_DIR)/build/bq-gcs.zip

# =============================================================================

terraform: terraform-app
#
# terraform-fixtures:
# 	$(MAKE) -C terraform/deployments/test/fixtures

terraform-app $(TF_TEST_DIR)/build/bq-gcs.zip:
	$(MAKE) -sC $(TF_TEST_DIR)

terraform-plan:
	$(MAKE) -sC $(TF_TEST_DIR) plan

terraform-apply:
	$(MAKE) -sC  $(TF_TEST_DIR) apply

output: terraform-output
terraform-output:
	@echo "Fixtures:"
	@echo "---"
	@$(MAKE) -sC $(TF_TEST_DIR) output
	@echo
	@echo "App:"
	@echo "---"
	@$(MAKE) -sC $(TF_TEST_DIR) output

terraform-show:
	@$(MAKE) -sC $(TF_TEST_DIR) show

terraform-destroy:
	@$(MAKE) -sC $(TF_TEST_DIR) destroy

terraform-test:
	@$(MAKE) -sC $(TF_TEST_DIR) test
