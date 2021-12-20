

develop:
	python3 -m venv venv


clean:
	git clean -dfxn | grep 'Would remove' | awk '{print $3}' | grep -v -e '^.idea' -e '^.cache' | xargs rm -rf


check:
	flake8 ./pybake --ignore E501


test:
	pytest ./tests/ -vvv --junitxml=./reports/unittest-results.xml


to_pypi_test: test
	python -m build
	twine upload -r testpypi dist/*


to_pypi_live: test
	python -m build
	twine upload dist/*
