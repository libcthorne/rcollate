init:
	pip install -r requirements.txt

run:
	FLASK_APP=rcollate flask run

test:
	CONFIG_DIR=config/tests_config nosetests --with-coverage --cover-package=rcollate

.PHONY: init
