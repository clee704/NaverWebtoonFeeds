.PHONY: init lint test docs dist clean

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

clean:
	rm -rf naverwebtoonfeeds.egg-info
	rm -rf dist
	rm -rf docs/_build
	rm -rf naverwebtoonfeeds/static/gen
	rm -rf naverwebtoonfeeds/static/.webassets-cache
	find . -type f -name *.pyc -exec rm {} \;
	find . -type d -name __pycache__ -depth -exec rm -rf {} \;
