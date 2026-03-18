from __future__ import annotations

import operator
import os
import os.path
import collections.abc
import typing
from argparse import ArgumentError
from dataclasses import dataclass
from datetime import date, datetime
from functools import reduce
from pathlib import Path
from typing import Callable, Iterable, Union, Any, TypeVar, Sequence

from . import stat as _s
from .stat import Path as _Path
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


_T = TypeVar('_T')

@dataclass
class _iterfiles_config:  # noqa
    dir_path: Path
    pattern: str
    sort_key: Callable[[Path], Any] | None = None
    predicates: list[Callable[[Path], bool]] | None = None
    filter_stat: bool = False
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
        # Use glob, and return only files
        files = (x for x in dir_path.glob(self._config.pattern) if x.is_file())
        if not self._config.predicates:
            files = list(files)
        else:
            # If filter_stat was called, convert to custom _Path with stat caching
            if self._config.filter_stat:
                files = (_Path(x) for x in files)
            predicates = self._config.predicates
            if len(predicates) == 1:
                p = predicates[0]
                files = (x for x in files if p(x))
            else:
                files = (x for x in files if all(f(x) for f in predicates))
        # If sorting, we need to read everything at once
        if self._config.sort_key:
            files = list(files)
            files.sort(key=self._config.sort_key)
            files = iter(files)
        return files


class StatExpr:

    def __and__(self, other):
        raise NotImplementedError


TimeT = int | datetime | date | str | None
TimeTupleT = tuple[TimeT, TimeT]


class iterfiles(_iterfiles_base):  # noqa
    """
    Iterates over file names in dir_path.

    Use glob pattern to filter; by default, all files in all subdirectories are included.
    """

    def __init__(self, dir_path: Path | str, pattern: str = '**/*'):  # noqa
        if not isinstance(pattern, str):
            raise TypeError(f'pattern: expected glob string, got {pattern!r}')
        self._config = _iterfiles_config(dir_path=dir_path, pattern=pattern)

    def sorted(self, key: Callable[[Path], Any] | None = None) -> iterfiles:
        self._config.sort_key = key or _default_sort_key
        return self

    def filter(self, predicate: Callable[[Path], bool]) -> iterfiles:
        if self._config.predicates is None:
            self._config.predicates = []
        self._config.predicates.append(predicate)
        return self

    def filter_stat(self, *expressions: StatExpr,
                    op: str = 'and',
                    exclude: bool = False,
                    st_mode: int | str | None = None,
                    st_mode__in: int | str | None = None,
                    st_mode__match: str | None = None,
                    st_uid: int | None = None,
                    st_uid__in: Sequence[int] | None = None,
                    st_gid__eq: int | None = None,
                    st_gid__in: Sequence[int] | None = None,
                    st_size: int | None = None,
                    st_size__lt: int | None = None,
                    st_size__lte: int | None = None,
                    st_size__gt: int | None = None,
                    st_size__gte: int | None = None,
                    st_size__range: tuple[int, int] | None = None,
                    st_atime: TimeT | None = None,
                    st_atime__lt: TimeT | None = None,
                    st_atime__lte: TimeT | None = None,
                    st_atime__gt: TimeT | None = None,
                    st_atime__gte: TimeT | None = None,
                    st_atime__range: TimeTupleT | None = None,
                    st_mtime: TimeT | None = None,
                    st_mtime__lt: TimeT | None = None,
                    st_mtime__lte: TimeT | None = None,
                    st_mtime__gt: TimeT | None = None,
                    st_mtime__gte: TimeT | None = None,
                    st_mtime__range: TimeTupleT | None = None,
                    st_ctime: TimeT | None = None,
                    st_ctime__lt: TimeT | None = None,
                    st_ctime__lte: TimeT | None = None,
                    st_ctime__gt: TimeT | None = None,
                    st_ctime__gte: TimeT | None = None,
                    st_ctime__range: TimeTupleT | None = None,
                    ) -> iterfiles:
        exs = list(expressions)
        if st_mode is not None:
            exs.append(_s.st_mode == st_mode)
        if st_mode__in is not None:
            exs.append(_s.st_mode in st_mode__in)
        if st_mode__match is not None:
            exs.append(_s.st_mode / st_mode__match)

        if st_uid is not None:
            exs.append(_s.st_uid == st_uid)
        if st_uid__in is not None:
            exs.append(_s.st_uid in st_uid__in)

        if st_gid__eq is not None:
            exs.append(_s.st_uid == st_gid__eq)
        if st_gid__in is not None:
            exs.append(_s.st_uid in st_gid__in)

        if st_size is not None:
            exs.append(_s.st_size == st_size)
        if st_size__lt is not None:
            exs.append(_s.st_size < st_size__lt)
        if st_size__lte is not None:
            exs.append(_s.st_size <= st_size__lte)
        if st_size__gt is not None:
            exs.append(_s.st_size > st_size__gt)
        if st_size__gte is not None:
            exs.append(_s.st_size >= st_size__gte)
        if st_size__range is not None:
            exs.append(_s.st_size >= st_size__range[0])
            exs.append(_s.st_size <= st_size__range[1])

        if st_atime is not None:
            exs.append(_s.st_atime == st_atime)
        if st_atime__lt is not None:
            exs.append(_s.st_atime < st_atime__lt)
        if st_atime__lte is not None:
            exs.append(_s.st_atime <= st_atime__lte)
        if st_atime__gt is not None:
            exs.append(_s.st_atime > st_atime__gt)
        if st_atime__gte is not None:
            exs.append(_s.st_atime >= st_atime__gte)
        if st_atime__range is not None:
            exs.append(_s.st_atime >= st_atime__range[0])
            exs.append(_s.st_atime <= st_atime__range[1])

        if st_mtime is not None:
            exs.append(_s.st_mtime == st_mtime)
        if st_mtime__lt is not None:
            exs.append(_s.st_mtime < st_mtime__lt)
        if st_mtime__lte is not None:
            exs.append(_s.st_mtime <= st_mtime__lte)
        if st_mtime__gt is not None:
            exs.append(_s.st_mtime > st_mtime__gt)
        if st_mtime__gte is not None:
            exs.append(_s.st_mtime >= st_mtime__gte)
        if st_mtime__range is not None:
            exs.append(_s.st_mtime >= st_mtime__range[0])
            exs.append(_s.st_mtime <= st_mtime__range[1])

        if st_ctime is not None:
            exs.append(_s.st_ctime == st_ctime)
        if st_ctime__lt is not None:
            exs.append(_s.st_ctime < st_ctime__lt)
        if st_ctime__lte is not None:
            exs.append(_s.st_ctime <= st_ctime__lte)
        if st_ctime__gt is not None:
            exs.append(_s.st_ctime > st_ctime__gt)
        if st_ctime__gte is not None:
            exs.append(_s.st_ctime >= st_ctime__gte)
        if st_ctime__range is not None:
            exs.append(_s.st_ctime >= st_ctime__range[0])
            exs.append(_s.st_ctime <= st_ctime__range[1])

        if op == 'and':
            op = operator.and_
        elif op == 'or':
            op = operator.or_
        else:
            raise ValueError(f"op argument has invalid value {op!r}, expected: 'and', 'or'")
        expr = reduce(op, exs)
        if exclude:
            expr = ~expr
        self._config.predicates.append(expr.compile_function())
        self._config.filter_stat = True
        return self

    def exclude_stat(self, *expressions: StatExpr,
                    op: str = 'and',
                    st_mode: int | str | None = None,
                    st_mode__in: int | str | None = None,
                    st_mode__match: str | None = None,
                    st_uid: int | None = None,
                    st_uid__in: Sequence[int] | None = None,
                    st_gid__eq: int | None = None,
                    st_gid__in: Sequence[int] | None = None,
                    st_size: int | None = None,
                    st_size__lt: int | None = None,
                    st_size__lte: int | None = None,
                    st_size__gt: int | None = None,
                    st_size__gte: int | None = None,
                    st_size__range: tuple[int, int] | None = None,
                    st_atime: TimeT | None = None,
                    st_atime__lt: TimeT | None = None,
                    st_atime__lte: TimeT | None = None,
                    st_atime__gt: TimeT | None = None,
                    st_atime__gte: TimeT | None = None,
                    st_atime__range: TimeTupleT | None = None,
                    st_mtime: TimeT | None = None,
                    st_mtime__lt: TimeT | None = None,
                    st_mtime__lte: TimeT | None = None,
                    st_mtime__gt: TimeT | None = None,
                    st_mtime__gte: TimeT | None = None,
                    st_mtime__range: TimeTupleT | None = None,
                    st_ctime: TimeT | None = None,
                    st_ctime__lt: TimeT | None = None,
                    st_ctime__lte: TimeT | None = None,
                    st_ctime__gt: TimeT | None = None,
                    st_ctime__gte: TimeT | None = None,
                    st_ctime__range: TimeTupleT | None = None,
                    ) -> iterfiles:
        return self.filter_stat(*expressions,
                                op=op,
                                exclude=True,
                                st_mode=st_mode,
                                st_mode__in=st_mode__in,
                                st_mode__match=st_mode__match,
                                st_uid=st_uid,
                                st_uid__in=st_uid__in,
                                st_gid__eq=st_gid__eq,
                                st_gid__in=st_gid__in,
                                st_size=st_size,
                                st_size__lt=st_size__lt,
                                st_size__lte=st_size__lte,
                                st_size__gt=st_size__gt,
                                st_size__gte=st_size__gte,
                                st_size__range=st_size__range,
                                st_atime=st_atime,
                                st_atime__lt=st_atime__lt,
                                st_atime__lte=st_atime__lte,
                                st_atime__gt=st_atime__gt,
                                st_atime__gte=st_atime__gte,
                                st_atime__range=st_atime__range,
                                st_mtime=st_mtime,
                                st_mtime__lt=st_mtime__lt,
                                st_mtime__lte=st_mtime__lte,
                                st_mtime__gt=st_mtime__gt,
                                st_mtime__gte=st_mtime__gte,
                                st_mtime__range=st_mtime__range,
                                st_ctime=st_ctime,
                                st_ctime__lt=st_ctime__lt,
                                st_ctime__lte=st_ctime__lte,
                                st_ctime__gt=st_ctime__gt,
                                st_ctime__gte=st_ctime__gte,
                                st_ctime__range=st_ctime__range)

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


class _iterfiles_binary_map(_iterfiles_map):  # noqa

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
