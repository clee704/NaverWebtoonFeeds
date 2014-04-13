init:
	pip install -r requirements.txt

test:
	py.test test

docs:
	SPHINX_RUNNING=1 $(MAKE) -C docs html

viewdocs:
	cd docs/_build/html; open http://127.0.0.1:8000/; python -m SimpleHTTPServer

dist: test clean
	python setup.py sdist

release: test clean
	python setup.py sdist upload

clean:
	rm -rf naverwebtoonfeeds.egg-info
	rm -rf build
	rm -rf dist
	rm -rf docs/_build
	rm -rf naverwebtoonfeeds/static/webassets
	rm -rf naverwebtoonfeeds/static/.webassets-cache
	find . -type f -name '.*.sw?' -exec rm -f {} \;
	find . -type f -name '*.py[co]' -exec rm -f {} \;
	find . -type d -name '__pycache__' -depth -exec rm -rf {} \;

lint:
	pylint naverwebtoonfeeds

.PHONY: init test docs viewdocs dist release clean lint
