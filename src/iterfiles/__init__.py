from __future__ import annotations
import os
import os.path
import collections.abc
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Tuple, Union, Any, TypeVar

from ._version import __version__, __version_tuple__


# Function to change name (or extension) of a target file
TRenameFunc = Callable[[Path], Path]
TRenameFuncOrNone = TRenameFunc | None
# Function to change order of glob traverse
TKeyFuncOrNone = Callable[[Path], Any] | None
TPath = str | Path


class InvalidPathError(Exception):
    """Source or target directory argument is not acceptable."""
    pass


def _ensure_dir(dir_path: Union[str, Path], must_exist=True) -> Path:
    """
    Convert str to Path. Check if directory exists and contains no invalid symbols.
    """
    dir_path = Path(dir_path)
    s = str(dir_path)
    if '*' in s or '?' in s:
        raise InvalidPathError(f'Path contains invalid symbols (did you mean to use "pattern" argument instead?): {dir_path}')
    if dir_path.exists():
        if not dir_path.is_dir():
            raise NotADirectoryError(f'Not a directory: {dir_path}')
    elif must_exist:
        raise FileNotFoundError(f'Directory not found: {dir_path}')
    return dir_path


def iter_files(dir_path: Union[str, Path], pattern: str = '**/*', key: TKeyFuncOrNone = None) -> Iterable[Path]:
    """
    Iterates over file names in dir_path.

    Use glob pattern to filter; by default, all files in all subdirectories are included.
    """
    dir_path = _ensure_dir(dir_path)
    # NOTE: we must do list() to take a "snapshot" of all files at a given moment.
    # This is to ensure predictable behavior.
    files = [x for x in dir_path.glob(pattern) if x.is_file()]
    if key:
        files.sort(key=key)
    return iter(files)


def iter_texts(dir_path: Union[str, Path], pattern: str = '**/*', key: TKeyFuncOrNone = None, encoding=None, errors=None, newline=None) -> Iterable[str]:
    """
    Iterates over text file contents (as str) in dir_path.

    Use glob pattern to filter; by default, all files in all subdirectories are included.

    If necessary, specify encoding, errors and newline to pass to :py:func:`open`.
    """
    for file_path in iter_files(dir_path, pattern, key):
        with open(file_path, encoding=encoding, errors=errors, newline=newline) as file:
            yield file.read()


def for_each_file(dir_path: Union[str, Path], function: Callable[[Path], Any], pattern: str = '**/*', key: TKeyFuncOrNone = None) -> None:
    """
    Calls function for each file in dir_path.

    Use glob pattern to filter; by default, all files in all subdirectories are included.
    """
    for file_path in iter_files(dir_path, pattern, key):
        function(file_path)


def for_each_text(dir_path: Union[str, Path], function: Callable[[str], Any], pattern: str = '**/*', key: TKeyFuncOrNone = None,
                  encoding=None, errors=None, newline=None) -> None:
    """
    Calls function for each file contents (as str) in dir_path.

    Use glob pattern to filter; by default, all files in all subdirectories are included.

    If necessary, specify encoding, errors and newline to pass to :py:func:`open`.
    """
    for file_path in iter_texts(dir_path, pattern, key, encoding, errors, newline):
        function(file_path)


def iter_source_target_files(source_dir: Union[str, Path], target_dir: Union[str, Path], pattern: str = '**/*', key: TKeyFuncOrNone = None, rename: TRenameFuncOrNone = None) -> Iterable[Tuple[Path, Path]]:
    """
    Creates the same hierarchy of subdirectories in target_dir as in source_dir.
    Iterates over pairs: each file in source_dir, and corresponding file in target_dir.
    """
    source_dir = _ensure_dir(source_dir)
    target_dir = _ensure_dir(target_dir, must_exist=False)
    # Make sure caller is not messing up the directory structure.
    if target_dir in source_dir.parents or source_dir in target_dir.parents:
        raise InvalidPathError('Source must not be a parent of Target (and vice versa)')

    parents = set()  # optimize os.makedirs for "thousands of files in a folder" scenario

    for source_file_path in iter_files(source_dir, pattern, key):
        target_file_path = target_dir / source_file_path.relative_to(source_dir)
        if rename:
            new_name = rename(target_file_path)
            target_file_path = target_file_path.parent / (new_name.name if type(new_name) is Path else new_name)
        if target_file_path.parent not in parents:
            os.makedirs(target_file_path.parent, exist_ok=True)
            parents.add(target_file_path.parent)
        yield source_file_path, target_file_path


def convert_files(source_dir: Union[str, Path], target_dir: Union[str, Path], function: Callable[[Path, Path], Any], pattern: str = '**/*', key: TKeyFuncOrNone = None, rename: TRenameFuncOrNone = None) -> None:
    """
    Creates the same hierarchy of subdirectories in target_dir as in source_dir.
    Calls function for each pair of files (in source_dir and a corresponding file in target_dir).

    By default, target file has the same name and extension; specify ``rename`` callable to change target file name.
    """
    for source_file_path, target_file_path in iter_source_target_files(source_dir, target_dir, pattern, key, rename):
        function(source_file_path, target_file_path)


def convert_texts(source_dir: Union[str, Path], target_dir: Union[str, Path], function: Callable[[str], str], pattern: str = '**/*', key: TKeyFuncOrNone = None, rename: TRenameFuncOrNone = None,
                  encoding=None, errors=None, newline=None,
                  output_encoding=None, output_errors=None, output_newline=None) -> None:
    """
    Creates the same hierarchy of subdirectories in target_dir as in source_dir.
    Calls function for each file content (as str) in source_dir,
    and writes result (as str) into corresponding file in target_dir.

    By default, target file has the same name and extension; specify ``rename`` callable to change target file name.

    If necessary, specify encoding, errors and newline to pass to :py:func:`open`.
    """
    for source_file_path, target_file_path in iter_source_target_files(source_dir, target_dir, pattern, key, rename):
        with open(source_file_path, 'r', encoding=encoding, errors=errors, newline=newline) as file:
            target_file_path.write_text(function(file.read()), encoding=output_encoding, errors=output_errors, newline=output_newline)

_T = TypeVar('_T')

@dataclass
class _iterfiles_config:
    dir_path: Path
    pattern: str
    sort_key: Callable[[Path], Any] | None = None
    predicate: Callable[[Path], bool] | None = None
    in_encoding: str | None = None
    in_errors: str | None = None
    in_newline: str | None = None
    target_dir: str | None = None
    rename: TRenameFuncOrNone = None
    map_function: Callable[[_T], _T] | None = None


def _default_sort_key(p: Path) -> str:
    return str(p.absolute())


def dirs_first(p: Path) -> str:
    """Sort in alphabetic order, but directories always come first."""
    # To avoid expensive actual checking whether every parent is a directory,
    # we use a dirty hack: replace every '/' with '/\x00', EXCEPT the last one,
    # which is followed by file name. We only work with files here so this is OK.
    s = str(p.absolute())
    count = s.count(os.sep)
    if count < 2:
        return s
    return s.replace(os.sep, os.sep + '\x00', count - 1)


class _iterfiles_base(collections.abc.Iterable):  # noqa

    _config: _iterfiles_config

    def __init__(self, other: _iterfiles_base):
        self._config = other._config

    def __iter__(self) -> Iterable[Path]:
        dir_path = _ensure_dir(self._config.dir_path)
        # NOTE: we must do list() to take a "snapshot" of all files at a given moment.
        # This is to ensure predictable behavior.
        p = self._config.predicate
        files = [x for x in dir_path.glob(self._config.pattern) if x.is_file() and (not p or p(x))]
        if self._config.sort_key:
            files.sort(key=self._config.sort_key)
        return iter(files)


class iterfiles(_iterfiles_base):  # noqa

    def __init__(self, dir_path: Path | str, pattern: str = '**/*'):  # noqa
        if not isinstance(pattern, str):
            raise TypeError(f'pattern: expected glob string, got {pattern!r}')
        self._config = _iterfiles_config(dir_path=dir_path, pattern=pattern)

    def sorted(self, key: Callable[[Path], Any] | None = None) -> iterfiles:
        self._config.sort_key = key or _default_sort_key
        return self

    def filter(self, predicate: Callable[[Path], bool]) -> iterfiles:
        self._config.predicate = predicate
        return self

    def text(self, encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None) -> _iterfiles_text:
        self._config._in_encoding = encoding
        self._config._in_errors = errors
        self._config._in_newline = newline
        return _iterfiles_text(self)

    def binary(self):
        return _iterfiles_binary(self)

    def foreach(self, function: Callable[[Path], Any]) -> iterfiles:
        for path in self:
            function(path)
        return self

    def set_output(self, target_dir: Union[str, Path], rename: TRenameFunc | None = None) -> _iterfiles_map:
        self._config.target_dir = target_dir
        self._config.rename = rename
        return _iterfiles_map(self)


class _iterfiles_text(_iterfiles_base):  # noqa

    def __iter__(self) -> Iterable[str]:
        encoding = self._config.in_encoding
        errors = self._config.in_errors
        newline = self._config.in_newline
        map_function = self._config.map_function
        for in_path in super().__iter__():
            with open(in_path, encoding=encoding, errors=errors, newline=newline) as file:
                text = file.read()
                if map_function is not None:
                    text = map_function(text)
                yield text

    def map(self, function: Callable[[str], str]) -> _iterfiles_text:
        self._config.map_function = function
        return self

    def set_output(self, target_dir: Union[str, Path], rename: TRenameFunc | None = None) -> _iterfiles_text_map:
        self._config.target_dir = target_dir
        self._config.rename = rename
        return _iterfiles_text_map(self)

    def foreach(self, function: Callable[[str], Any]) -> _iterfiles_text:
        for text in self:
            function(text)
        return self


class _iterfiles_binary(_iterfiles_base):  # noqa

    def __iter__(self) -> Iterable[bytes]:
        map_function = self._config.map_function
        for in_path in super().__iter__():
            with open(in_path, mode='rb') as file:
                binary = file.read()
                if map_function is not None:
                    binary = map_function(binary)
                yield binary

    def map(self, function: Callable[[bytes], bytes]) -> _iterfiles_binary:
        self._config.map_function = function
        return self

    def set_output(self, target_dir: Union[str, Path], rename: TRenameFunc | None = None) -> _iterfiles_binary_map:
        self._config.target_dir = target_dir
        self._config.rename = rename
        return _iterfiles_binary_map(self)

    def foreach(self, function: Callable[[str], Any]) -> _iterfiles_binary:
        for binary in self:
            function(binary)
        return self


class _iterfiles_map(_iterfiles_base):  # noqa

    def __iter__(self) -> Iterable[tuple[Path, Path]]:
        source_dir = _ensure_dir(self._config.dir_path)
        target_dir = _ensure_dir(self._config.target_dir, must_exist=False)
        # Make sure caller is not messing up the directory structure.
        if target_dir in source_dir.parents or source_dir in target_dir.parents:
            raise InvalidPathError('Source must not be a parent of Target (and vice versa)')

        parents = set()  # optimize os.makedirs for "thousands of files in a folder" scenario

        rename = self._config.rename
        for source_file_path in super().__iter__():
            target_file_path = target_dir / source_file_path.relative_to(source_dir)
            if rename:
                new_name = rename(target_file_path)
                target_file_path = target_file_path.parent / (new_name.name if type(new_name) is Path else new_name)
            if target_file_path.parent not in parents:
                os.makedirs(target_file_path.parent, exist_ok=True)
                parents.add(target_file_path.parent)
            yield source_file_path, target_file_path

    def foreach(self, function: Callable[[Path, Path], Any]) -> _iterfiles_map:
        for in_path, out_path in self:
            function(in_path, out_path)
        return self

    def text(self) -> _iterfiles_text_map:
        return _iterfiles_text_map(self)

    def binary(self) -> _iterfiles_binary_map:
        return _iterfiles_binary_map(self)

    def write_text(self, function: Callable[[Path], str], encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None):
        for in_path, out_path in self:
            with open(out_path, 'w', encoding=encoding, errors=errors, newline=newline) as out_file:
                out_file.write(function(in_path))

    def write_binary(self, function: Callable[[Path], bytes]):
        for in_path, out_path in self:
            with open(out_path, 'wb') as out_file:
                out_file.write(function(in_path))


class _iterfiles_text_map(_iterfiles_map):  # noqa

    def __iter__(self) -> Iterable[tuple[str, Path]]:
        encoding = self._config.in_encoding
        errors = self._config.in_errors
        newline = self._config.in_newline
        for in_path, out_path in super().__iter__():
            with open(in_path, encoding=encoding, errors=errors, newline=newline) as file:
                yield file.read(), out_path

    def map(self, function: Callable[[str], str]) -> _iterfiles_text_map:
        self._config.map_function = function
        return self

    def foreach(self, function: Callable[[str, Path], Any]) -> Iterable[Any]:
        for text_in, path_out in self:
            yield function(text_in, path_out)

    def write_text(self, function: Callable[[str], str], encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None) -> None:
        for in_text, out_path in self:
            with open(out_path, 'w', encoding=encoding, errors=errors, newline=newline) as out_file:
                out_file.write(function(in_text))

    def write_binary(self, function: Callable[[str], bytes]) -> None:
        for in_text, out_path in self:
            with open(out_path, 'wb') as out_file:
                out_file.write(function(in_text))


class _iterfiles_binary_map(_iterfiles_map, _iterfiles_binary):  # noqa

    def __iter__(self) -> Iterable[tuple[bytes, Path]]:
        for in_path, out_path in super().__iter__():
            with open(in_path, 'rb') as file:
                yield file.read(), out_path

    def map(self, function: Callable[[bytes], bytes]) -> _iterfiles_binary_map:
        self._config.map_function = function
        return self

    def foreach(self, function: Callable[[bytes, Path], Any]) -> Iterable[Any]:
        for bytes_in, path_out in self:
            yield function(bytes_in, path_out)

    def write_text(self, function: Callable[[bytes], str], encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None) -> None:
        for in_bytes, out_path in self:
            with open(out_path, 'w', encoding=encoding, errors=errors, newline=newline) as out_file:
                out_file.write(function(in_bytes))

    def write_binary(self, function: Callable[[bytes], bytes]) -> None:
        for in_bytes, out_path in self:
            with open(out_path, 'wb') as out_file:
                out_file.write(function(in_bytes))
