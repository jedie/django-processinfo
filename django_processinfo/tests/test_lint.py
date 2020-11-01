import shutil
import subprocess
from pathlib import Path

from django_processinfo.publish import PACKAGE_ROOT


def test_lint():
    assert Path(PACKAGE_ROOT, 'Makefile').is_file()
    make_bin = shutil.which('make')
    assert make_bin is not None
    subprocess.check_call([make_bin, 'lint'], cwd=PACKAGE_ROOT)
