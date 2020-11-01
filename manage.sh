#!/bin/bash

export DJANGO_SETTINGS_MODULE=django_processinfo.tests.django_project.settings

exec poetry run python3 django_processinfo/tests/django_project/manage.py "$@"
