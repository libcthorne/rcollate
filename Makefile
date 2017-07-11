run: init
	FLASK_APP=rcollate flask run

init:
	pip install -e .

test:
	CONFIG_DIR=config/tests_config coverage run -m unittest discover tests
	coverage report --include=rcollate/*

.PHONY: init
