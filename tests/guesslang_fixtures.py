from pathlib import Path
from uuid import uuid4


FIXTURES_PATH = Path(__file__).parent.joinpath('fixtures')


def copy_fixtures(destination_dir, nb_times=1):
    for _ in range(nb_times):
        for path in FIXTURES_PATH.glob('*'):
            dest_path = Path(destination_dir, uuid4().hex + path.suffix)
            dest_path.write_bytes(path.read_bytes())
