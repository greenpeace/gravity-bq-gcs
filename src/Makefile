.EXPORT_ALL_VARIABLES:

ENVIRONMENT ?= dev

install:
	pip install -U -r requirements.txt

dev:
	functions-framework --target main --debug --signature-type event
