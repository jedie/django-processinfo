import shutil
import subprocess
from pathlib import Path


PACKAGE_ROOT = Path(__file__).parent.parent


def test_lint():
    assert Path(PACKAGE_ROOT, 'Makefile').is_file()
    make_bin = shutil.which('make')
    assert make_bin is not None
    subprocess.check_call([make_bin, 'lint'], cwd=PACKAGE_ROOT)
