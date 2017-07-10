run: init
	FLASK_APP=rcollate flask run

init:
	pip install -e .

test:
	CONFIG_DIR=config/tests_config nosetests --with-coverage --cover-package=rcollate

.PHONY: init
