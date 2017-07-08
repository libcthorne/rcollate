init:
	pip install -r requirements.txt

run:
	FLASK_APP=rcollate flask run

test:
	CONFIG_DIR=config/tests_config python tests/test_rcollate.py

.PHONY: init
