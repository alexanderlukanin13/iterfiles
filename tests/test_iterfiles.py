import os
import shutil
from pathlib import Path
from unittest.mock import Mock

import pytest

from iterfiles import iterfiles, InvalidPathError

DATA_DIR = Path(__file__).absolute().parent / 'data'


def test_iteration():
    """
    Test simple iteration, sorting, filtering and set_output.
    No reading/writing here.
    """
    path = DATA_DIR / 'example1'

    # 1. Iterate all files
    assert list(iterfiles(path)) == [
        path / 'shapes.txt',
        path / 'aa' / 'colors.dat',  # including this non-txt file
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt',
    ]

    # 2.1. Iterate only txt files
    assert list(iterfiles(path, pattern='**/*.txt')) == [
        path / 'shapes.txt',
        path / 'aa' / 'numbers.txt',  # excluding colors.dat
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt',
    ]

    # 2.2. Iterate only txt files in first-level folders
    assert list(iterfiles(path, pattern='*/*.txt')) == [
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
    ]

    # 3.1. Iterate input + output, without rename
    # (note: we are not actually writing anything in this test function)
    output_path = DATA_DIR / 'output'
    assert list(iterfiles(path, pattern='**/*.txt').set_output(output_path)) == [
        (path / 'shapes.txt', output_path / 'shapes.txt'),
        (path / 'aa' / 'numbers.txt', output_path / 'aa' / 'numbers.txt'),  # excluding colors.dat
        (path / 'aa' / 'pets.txt', output_path / 'aa' / 'pets.txt'),
        (path / 'bb' / 'names.txt', output_path / 'bb' / 'names.txt'),
        (path / 'bb' / 'cc' / 'cars.txt', output_path / 'bb' / 'cc' / 'cars.txt'),
    ]

    # 3.2. Iterate input + output, with rename
    assert list(iterfiles(path, pattern='**/*.txt').set_output(output_path, lambda x: x.with_suffix('.changed'))) == [
        (path / 'shapes.txt', output_path / 'shapes.changed'),
        (path / 'aa' / 'numbers.txt', output_path / 'aa' / 'numbers.changed'),  # excluding colors.dat
        (path / 'aa' / 'pets.txt', output_path / 'aa' / 'pets.changed'),
        (path / 'bb' / 'names.txt', output_path / 'bb' / 'names.changed'),
        (path / 'bb' / 'cc' / 'cars.txt', output_path / 'bb' / 'cc' / 'cars.changed'),
    ]

    # 4.1. Filter and sort
    assert list(iterfiles(path).filter(lambda p: p.stem != 'pets').sorted()) == [
        path / 'aa' / 'colors.dat',  # including this non-txt file
        path / 'aa' / 'numbers.txt',
        path / 'bb' / 'cc' / 'cars.txt',
        path / 'bb' / 'names.txt',
        path / 'shapes.txt',
    ]

    # 4.2. Sort and filter (same result as above)
    assert list(iterfiles(path).sorted().filter(lambda p: p.stem != 'pets')) == [
        path / 'aa' / 'colors.dat',  # including this non-txt file
        path / 'aa' / 'numbers.txt',
        path / 'bb' / 'cc' / 'cars.txt',
        path / 'bb' / 'names.txt',
        path / 'shapes.txt',
    ]

    # 4.3. Double filter
    assert set(iterfiles(path).filter(lambda p: p.stem != 'pets').filter(lambda p: p.stem != 'numbers')) == {
        path / 'aa' / 'colors.dat',  # including this non-txt file
        path / 'bb' / 'cc' / 'cars.txt',
        path / 'bb' / 'names.txt',
        path / 'shapes.txt',
    }


def test_for_each_file_directory_error():
    with pytest.raises(InvalidPathError, match=r'Path contains invalid symbols'):
        list(iterfiles('*'))  # all files
    with pytest.raises(NotADirectoryError, match=r'Not a directory'):
        list(iterfiles(DATA_DIR / 'example1' / 'shapes.txt'))
    with pytest.raises(FileNotFoundError, match=r'Directory not found'):
        list(iterfiles(DATA_DIR / 'not_found'))


def test_foreach():
    path = DATA_DIR / 'example1'

    results = []
    function = Mock(return_value=None, side_effect=lambda x: results.append(x))
    iterfiles(path).foreach(function)  # all files

    assert results == [
        path / 'shapes.txt',
        path / 'aa' / 'colors.dat',  # including this non-txt file
        path / 'aa' / 'numbers.txt',
        path / 'aa' / 'pets.txt',
        path / 'bb' / 'names.txt',
        path / 'bb' / 'cc' / 'cars.txt',
    ]

def test_text_foreach():
    path = DATA_DIR / 'example1'

    results = []
    function = Mock(return_value=None, side_effect=lambda x: results.append(x))
    iterfiles(path).text().foreach(function)

    assert results == [
        'Square Circle\nHexagon\n',                     # shapes.txt
        'Red Green\nBlue\n',         # including this!  # aa/colors.dat
        'One Two\nThree\n',                             # aa/numbers.txt
        'Cat Dog\nParrot\n',                            # aa/pets.txt
        'Alice Bob\nCarol\n',                           # bb/names.txt
        'Toyota Honda\nFord\n',                         # bb/cc/cars.txt
    ]


def test_binary_foreach():
    path = DATA_DIR / 'example1'

    results = []
    function = Mock(return_value=None, side_effect=lambda x: results.append(x))
    iterfiles(path).binary().foreach(function)

    assert results == [
        b'Square Circle\nHexagon\n',                     # shapes.txt
        b'Red Green\nBlue\n',         # including this!  # aa/colors.dat
        b'One Two\nThree\n',                             # aa/numbers.txt
        b'Cat Dog\nParrot\n',                            # aa/pets.txt
        b'Alice Bob\nCarol\n',                           # bb/names.txt
        b'Toyota Honda\nFord\n',                         # bb/cc/cars.txt
    ]


def test_set_output_directory_error():
    """
    Test set_output() errors.
    set_output *does not* do any disk IO, but it checkes the sanity of output path.
    """
    source_dir = DATA_DIR / 'example1'
    target_dir = source_dir / 'aa'
    with pytest.raises(InvalidPathError, match=r'Source must not be a parent of Target \(and vice versa\)'):
        iterfiles(source_dir).set_output(target_dir).foreach(lambda x: None)
    with pytest.raises(InvalidPathError, match=r'Source must not be a parent of Target \(and vice versa\)'):
        iterfiles(target_dir).set_output(source_dir).foreach(lambda x: None)


def test_set_output_foreach_shutil_copy(tmp_path):
    path = DATA_DIR / 'example1'
    iterfiles(path).set_output(tmp_path).foreach(shutil.copy)
    assert set(iterfiles(tmp_path)) == {
        tmp_path / 'shapes.txt',
        tmp_path / 'aa' / 'colors.dat',  # including this
        tmp_path / 'aa' / 'numbers.txt',
        tmp_path / 'aa' / 'pets.txt',
        tmp_path / 'bb' / 'names.txt',
        tmp_path / 'bb' / 'cc' / 'cars.txt',
    }
    assert (tmp_path / 'shapes.txt').read_text() == 'Square Circle\nHexagon\n'
    assert (tmp_path / 'aa' / 'colors.dat').read_text() == 'Red Green\nBlue\n'
    assert (tmp_path / 'aa' / 'numbers.txt').read_text() == 'One Two\nThree\n'
    assert (tmp_path / 'aa' / 'pets.txt').read_text() == 'Cat Dog\nParrot\n'
    assert (tmp_path / 'bb' / 'names.txt').read_text() == 'Alice Bob\nCarol\n'
    assert (tmp_path / 'bb' / 'cc' / 'cars.txt').read_text() == 'Toyota Honda\nFord\n'



def test_set_output_foreach_shutil_copy_txt_only(tmp_path):
    source_dir = DATA_DIR / 'example1'
    iterfiles(source_dir, pattern='**/*.txt').set_output(tmp_path).foreach(shutil.copy)
    assert set(iterfiles(tmp_path)) == {
        tmp_path / 'shapes.txt',
        tmp_path / 'aa' / 'numbers.txt',
        tmp_path / 'aa' / 'pets.txt',
        tmp_path / 'bb' / 'names.txt',
        tmp_path / 'bb' / 'cc' / 'cars.txt',
    }
    assert (tmp_path / 'shapes.txt').read_text() == 'Square Circle\nHexagon\n'
    assert not (tmp_path / 'aa' / 'colors.dat').exists()
    assert (tmp_path / 'aa' / 'numbers.txt').read_text() == 'One Two\nThree\n'
    assert (tmp_path / 'aa' / 'pets.txt').read_text() == 'Cat Dog\nParrot\n'
    assert (tmp_path / 'bb' / 'names.txt').read_text() == 'Alice Bob\nCarol\n'
    assert (tmp_path / 'bb' / 'cc' / 'cars.txt').read_text() == 'Toyota Honda\nFord\n'


def test_set_output_foreach_shutil_copy_rename(tmp_path):
    source_dir = DATA_DIR / 'example1'
    iterfiles(source_dir, pattern='**/*.dat').set_output(tmp_path, lambda p: p.with_suffix('.foo')).foreach(shutil.copy)
    assert set(iterfiles(tmp_path, pattern='**/*.foo')) == {
        tmp_path / 'aa' / 'colors.foo',
    }
    assert (tmp_path / 'aa' / 'colors.foo').read_text() == 'Red Green\nBlue\n'


def test_set_output_write_text(tmp_path):
    path = DATA_DIR / 'example1'

    def get_first_line(text):
        return text.split(' ')[0]

    iterfiles(path, pattern='**/*.txt').text().set_output(tmp_path).write_text(get_first_line)
    assert set(iterfiles(tmp_path, pattern='**/*.txt').text()) == {
        'Square',
        'One',
        'Cat',
        'Alice',
        'Toyota',
    }


def test_set_output_write_text_2(tmp_path):
    """Same as above, just different order of text() and set_output()"""
    path = DATA_DIR / 'example1'

    def get_first_line(text):
        return text.split(' ')[0]

    iterfiles(path, pattern='**/*.txt').set_output(tmp_path).text().write_text(get_first_line)
    assert set(iterfiles(tmp_path, pattern='**/*.txt').text()) == {
        'Square',
        'One',
        'Cat',
        'Alice',
        'Toyota',
    }


def test_set_output_write_binary(tmp_path):
    path = DATA_DIR / 'example1'

    def first_six_bytes(binary: bytes):
        return binary[:6]

    iterfiles(path, pattern='**/*.txt').binary().set_output(tmp_path).write_binary(first_six_bytes)
    assert set(iterfiles(tmp_path, pattern='**/*.txt').binary()) == {
        b'Square',                     # shapes.txt
        b'One Tw',                    # aa/numbers.txt
        b'Cat Do',                    # aa/pets.txt
        b'Alice ',                     # bb/names.txt
        b'Toyota',                     # bb/cc/cars.txt
    }


def test_set_output_write_binary_2(tmp_path):
    path = DATA_DIR / 'example1'

    def first_six_bytes(binary: bytes):
        return binary[:6]

    iterfiles(path, pattern='**/*.txt').set_output(tmp_path).binary().write_binary(first_six_bytes)
    assert set(iterfiles(tmp_path, pattern='**/*.txt').binary()) == {
        b'Square',                     # shapes.txt
        b'One Tw',                    # aa/numbers.txt
        b'Cat Do',                    # aa/pets.txt
        b'Alice ',                     # bb/names.txt
        b'Toyota',                     # bb/cc/cars.txt
    }
