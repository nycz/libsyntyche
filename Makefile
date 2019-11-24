
.PHONY: test
test:
	@pytest


.PHONY: mypy
mypy:
	@mypy --strict --pretty -p libsyntyche


.PHONY: coverage
coverage:
	@pytest --cov=libsyntyche


.PHONY: coverage-report
coverage-report:
	@pytest --cov=libsyntyche --cov-report=html
