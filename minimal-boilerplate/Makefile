PKGDIR = foo


# Linting

.PHONY: vulture
vulture:
	-vulture vulture_whitelist.py ${PKGDIR}

.PHONY: flake8
flake8:
	-flake8 --statistics ${PKGDIR}

.PHONY: mypy
mypy:
	-mypy --strict --pretty -p ${PKGDIR}

.PHONY: check
check: mypy flake8 vulture


# Formatting

.PHONY: isort
isort:
	isort ${PKGDIR}

.PHONY: format-code
format-code: isort


# Testing

.PHONY: test
test:
	@pytest

.PHONY: test-coverage
test-coverage:
	@pytest --cov=${PKGDIR}

.PHONY: test-coverage-report
test-coverage-report:
	@pytest --cov=${PKGDIR} --cov-report=html


# Building

.PHONY: build
build:
	python -m build .

.PHONY: install-dev
install-dev:
	pip install --user -e .[dev]
