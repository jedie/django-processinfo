
import os
import django_processinfo

TEMPLATE_DIRS = (
    os.path.join(os.path.abspath(os.path.dirname(django_processinfo.__file__)), "templates/"),
)
