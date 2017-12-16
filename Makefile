
develop:
	virtualenv --no-site-packages --python /usr/bin/python2.7 virtualenv
	{ \
	    . ./virtualenv/bin/activate; \
	    curl https://bootstrap.pypa.io/get-pip.py | python; \
	    pip install pytest flake8; \
	}


clean:
	git clean -dfx


check:
	flake8 ./pybake --ignore E501


test:
	pytest ./tests/ -vvv --junitxml=./reports/unittest-results.xml


to_pypi_test:
	python setup.py register -r pypitest
	python setup.py sdist upload -r pypitest


to_pypi_live:
	python setup.py register -r pypi
	python setup.py sdist upload -r pypi
