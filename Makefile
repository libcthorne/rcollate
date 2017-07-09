init:
	pip install -r requirements.txt

run:
	FLASK_APP=rcollate flask run

test:
	CONFIG_DIR=config/tests_config coverage run -m unittest discover tests
	coverage report --include=rcollate/*

.PHONY: init
