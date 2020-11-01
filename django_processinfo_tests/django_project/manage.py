import os
import sys


if __name__ == '__main__':
    assert 'DJANGO_SETTINGS_MODULE' in os.environ, 'No "DJANGO_SETTINGS_MODULE" in environment!'
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv)
