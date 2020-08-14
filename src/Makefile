.EXPORT_ALL_VARIABLES:

ENTITY ?= dev
ENVIRONMENT ?= test

install:
	pip install -U -r requirements.txt

dev:
	functions-framework --target main --debug --signature-type event
