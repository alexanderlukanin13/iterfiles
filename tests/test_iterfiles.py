import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest

from src.iterfiles import (
    iter_files, iter_texts,
    for_each_file, for_each_text,
    convert_files, convert_texts,
    InvalidDirectoryError
)

DATA_DIR = Path(__file__).absolute().parent / 'data'


def test_for_each_file():
    path = DATA_DIR / 'example1'

    results = []
    function = Mock(return_value=None, side_effect=lambda x: results.append(x))
    for_each_file(path, function)  # all files
    assert set(results) == {
        path / 'shapes.txt',
        path / 'aa' / 'colors.dat',  # including this
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt',
    }

    results = []
    function = Mock(return_value=None, side_effect=lambda x: results.append(x))
    for_each_file(path, function, pattern='**/*.txt')  # only *.txt
    assert set(results) == {
        path / 'shapes.txt',
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt',
    }

    results = []
    function = Mock(return_value=None, side_effect=lambda x: results.append(x))
    for_each_file(path, function, pattern='*/*.txt')  # only *.txt in first level folders
    assert set(results) == {
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
    }


def test_for_each_file_directory_error():
    with pytest.raises(InvalidDirectoryError, match=r'Path contains invalid symbols'):
        for_each_text('*', Mock())  # all files
    with pytest.raises(NotADirectoryError, match=r'Not a directory'):
        for_each_text(DATA_DIR / 'example1' / 'shapes.txt', Mock())  # all files
    with pytest.raises(FileNotFoundError, match=r'Directory not found'):
        for_each_text(DATA_DIR / 'not_found', Mock())  # all files


def test_for_each_text():
    path = DATA_DIR / 'example1'

    results = []
    function = Mock(return_value=None, side_effect=lambda x: results.append(x))
    for_each_text(path, function)  # all files
    assert set(results) == {
        'Square Circle\nHexagon\n',
        'Red Green\nBlue\n',  # including this
        'One Two\nThree\n',
        'Cat Dog\nParrot\n',
        'Alice Bob\nCarol\n',
        'Toyota Honda\nFord\n',
    }


def test_convert_files_directory_error():
    source_dir = DATA_DIR / 'example1'
    target_dir = source_dir / 'aa'
    function = Mock(return_value=None)
    with pytest.raises(InvalidDirectoryError, match=r'Source must not be a parent of Target \(and vice versa\)'):
        convert_files(source_dir, target_dir, function)
    with pytest.raises(InvalidDirectoryError, match=r'Source must not be a parent of Target \(and vice versa\)'):
        convert_files(target_dir, source_dir, function)


def test_convert_files(tmpdir):
    source_dir = DATA_DIR / 'example1'
    target_dir = Path(tmpdir)
    convert_files(source_dir, tmpdir, shutil.copy)
    assert set(iter_files(tmpdir)) == {
        target_dir / 'shapes.txt',
        target_dir / 'aa' / 'colors.dat',  # including this
        target_dir / 'aa' / 'numbers.txt',
        target_dir / 'aa' / 'pets.txt',
        target_dir / 'bb' / 'names.txt',
        target_dir / 'bb' / 'cc' / 'cars.txt',
    }
    assert set(iter_texts(tmpdir)) == {
        'Square Circle\nHexagon\n',
        'Red Green\nBlue\n',  # including this
        'One Two\nThree\n',
        'Cat Dog\nParrot\n',
        'Alice Bob\nCarol\n',
        'Toyota Honda\nFord\n',
    }


def test_convert_files_txt_only(tmpdir):
    source_dir = DATA_DIR / 'example1'
    target_dir = Path(tmpdir)
    convert_files(source_dir, tmpdir, shutil.copy, pattern='**/*.txt')
    assert set(iter_files(tmpdir)) == {
        target_dir / 'shapes.txt',
        target_dir / 'aa' / 'numbers.txt',
        target_dir / 'aa' / 'pets.txt',
        target_dir / 'bb' / 'names.txt',
        target_dir / 'bb' / 'cc' / 'cars.txt',
    }
    assert not (target_dir / 'aa' / 'colors.dat').exists()
    assert set(iter_texts(tmpdir)) == {
        'Square Circle\nHexagon\n',
        'One Two\nThree\n',
        'Cat Dog\nParrot\n',
        'Alice Bob\nCarol\n',
        'Toyota Honda\nFord\n',
    }


def test_convert_rename(tmpdir):
    source_dir = DATA_DIR / 'example1'
    target_dir = Path(tmpdir)
    convert_files(source_dir, tmpdir, shutil.copy, pattern='**/*.dat', rename=lambda p: p.with_suffix('.foo'))
    assert set(iter_files(tmpdir, pattern='**/*.foo')) == {
        target_dir / 'aa' / 'colors.foo',
    }


def test_convert_rename_str(tmpdir):
    source_dir = DATA_DIR / 'example1'
    target_dir = Path(tmpdir)
    convert_files(source_dir, tmpdir, shutil.copy, pattern='**/*.dat', rename=lambda p: p.with_suffix('.foo').name)
    assert set(iter_files(tmpdir, pattern='**/*.foo')) == {
        target_dir / 'aa' / 'colors.foo',
    }


def test_convert_text(tmpdir):
    source_dir = DATA_DIR / 'example1'

    def convert(source_text):
        return source_text.split(' ')[0]

    convert_texts(source_dir, tmpdir, convert, pattern='**/*.txt', encoding='utf8')
    assert set(iter_texts(tmpdir)) == {
        'Square',
        'One',
        'Cat',
        'Alice',
        'Toyota',
    }
