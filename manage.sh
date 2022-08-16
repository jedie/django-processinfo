#!/bin/bash

export DJANGO_SETTINGS_MODULE=django_processinfo_tests.django_project.settings

exec poetry run python3 ./manage.py "$@"
