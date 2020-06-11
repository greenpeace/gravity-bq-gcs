ifndef SENTRY_DSN
$(error SENTRY_DSN not set)
endif

.EXPORT_ALL_VARIABLES:

TF_VAR_sentry_dsn := $(SENTRY_DSN)

all: clean init plan apply show

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
