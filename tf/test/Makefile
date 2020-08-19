
all: clean init plan apply show test

clean:
	rm -fr tf.plan build

init:
	@terraform init
	cat .terraform/terraform.tfstate

validate:
	@terraform validate

refresh: validate
	@terraform refresh

plan: validate
	@terraform plan -out tf.plan

apply:
	terraform apply --auto-approve tf.plan

output:
	@terraform output

show:
	@terraform show

destroy: init
	terraform destroy

publish test:
	gcloud pubsub topics publish $(shell terraform output input_topic) --message '$(shell jq -c . fixtures/test.table.json)'
