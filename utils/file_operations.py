import os
import shutil
import tempfile
from pathlib import Path

def create_file(file_name):
    temppath = tempfile.mkdtemp(prefix='plotly_')
    print(temppath)
    return temppath, (Path(temppath) / f'{file_name}.html').absolute()


def remove_dir(path):
    shutil.rmtree(path=os.path.abspath(path))