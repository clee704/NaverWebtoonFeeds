.PHONY: init lint test docs dist

init:
	pip install -r requirements.txt

lint:
	pylint naverwebtoonfeeds

test:
	NWF_ENV=test py.test tests

docs:
	$(MAKE) -C docs html

dist:
	python setup.py sdist
