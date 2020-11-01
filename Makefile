SHELL := /bin/bash
MAX_LINE_LENGTH := 119

help: ## List all commands
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9 -]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

check-poetry:
	@if [[ "$(shell poetry --version 2>/dev/null)" == *"Poetry"* ]] ; \
	then \
		echo "Poetry found, ok." ; \
	else \
		echo 'Please install poetry first, with e.g.:' ; \
		echo 'make install-poetry' ; \
		exit 1 ; \
	fi

install-poetry: ## install or update poetry
	@if [[ "$(shell poetry --version 2>/dev/null)" == *"Poetry"* ]] ; \
	then \
		echo 'Update poetry' ; \
		poetry self update ; \
	else \
		echo 'Install poetry' ; \
		curl -sSL "https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py" | python3 ; \
	fi

install: check-poetry ## install PyInventory via poetry
	poetry install

update: check-poetry ## update the sources and installation
	git fetch --all
	git pull origin master
	poetry update

lint: ## Run code formatters and linter
	poetry run flynt -e "volumes" --fail-on-change --line_length=${MAX_LINE_LENGTH} .
	poetry run isort --check-only .
	poetry run flake8 .

fix-code-style: ## Fix code formatting
	poetry run flynt -e "volumes" --line_length=${MAX_LINE_LENGTH} .
	poetry run pyupgrade --exit-zero-even-if-changed --py3-plus --py36-plus --py37-plus `find . -name "*.py" -type f ! -path "./.tox/*" ! -path "./volumes/*" 2>/dev/null`
	poetry run isort .
	poetry run autopep8 --exclude="volumes,migrations" --aggressive --aggressive --in-place --recursive .

tox-listenvs: check-poetry ## List all tox test environments
	poetry run tox --listenvs

tox: check-poetry ## Run pytest via tox with all environments
	poetry run tox

tox-py36: check-poetry ## Run pytest via tox with *python v3.6*
	poetry run tox -e py36

tox-py37: check-poetry ## Run pytest via tox with *python v3.7*
	poetry run tox -e py37

tox-py38: check-poetry ## Run pytest via tox with *python v3.8*
	poetry run tox -e py38

pytest: check-poetry ## Run pytest
	poetry run pytest

update-rst-readme: ## update README.rst from README.creole
	poetry run update_rst_readme

publish: ## Release new version to PyPi
	poetry run publish

run-dev-server:  ## Run the django dev server in endless loop.
	./manage.sh collectstatic --noinput --link
	./manage.sh migrate
	./manage.sh runserver