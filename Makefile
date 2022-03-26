
test:
	pytest --cov=notion_params --cov-report term-missing --cov-report= tests/ -vv

watch:
	ptw

build-dist:
	rm -rf build/ dist/ *.egg-info/
	python setup.py sdist bdist_wheel

publish-test:
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

publish:
	python3 -m twine upload dist/*

sample:
	PYTHONPATH=. python samples/sample.py
