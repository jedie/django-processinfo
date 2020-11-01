from pathlib import Path


BASE_PATH = Path(__file__).resolve().parent.parent.parent
assert Path(BASE_PATH, 'django_processinfo').is_dir(), f'Wrong BASE_PATH={BASE_PATH!r}'
