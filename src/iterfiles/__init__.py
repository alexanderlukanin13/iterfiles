from __future__ import annotations

import operator
import os
import os.path
from collections.abc import Iterator, Generator
from dataclasses import dataclass, field
from datetime import date, datetime
from functools import reduce
from pathlib import Path
from typing import Callable, Iterable, Any, TypeVar, Sequence
from typing_extensions import Self

from . import stat as _s
from .stat import Path as IPath, PathSym, StatExpr
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


def _ensure_dir(dir_path: str | Path, must_exist: bool = True) -> IPath:
    """
    Convert str to Path. Check if directory exists and contains no invalid symbols.
    """
    dir_path = IPath(dir_path)  # use IPath here for easier testing (it doesn't affect performance)
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
    dir_path: str | Path
    pattern: str
    sort_key: Callable[[Path], Any] | None = None
    predicates: list[Callable[[Path], bool]] = field(default_factory=list)
    filter_stat: bool = False
    in_encoding: str | None = None
    in_errors: str | None = None
    in_newline: str | None = None
    target_dir: str | Path | None = None
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


class _iterfiles_base:  # noqa

    _config: _iterfiles_config

    def __init__(self, other: _iterfiles_base):
        super().__init__()  # do not remove: necessary to initialize @dataclass mixins in subclasses
        self._config = other._config

    def _iter_paths(self) -> Iterator[Path]:
        dir_path = _ensure_dir(self._config.dir_path)
        # Use glob, and return only files
        files: Iterator[IPath] = (IPath(x) for x in dir_path.glob(self._config.pattern) if x.is_file())
        # Any filtering?
        if self._config.predicates:
            predicates = self._config.predicates
            if len(predicates) == 1:
                p = predicates[0]
                files = (x for x in files if p(x))
            else:
                files = (x for x in files if all(f(x) for f in predicates))
        # If sorting, we need to read everything at once
        if self._config.sort_key:
            files = iter(sorted(files, key=self._config.sort_key))
        return files


TimeT = int | datetime | date | str
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

    def __iter__(self) -> Iterator[Path]:
        return self._iter_paths()

    def sorted(self, key: Callable[[Path], Any] | None = None) -> iterfiles:
        self._config.sort_key = key or _default_sort_key
        return self

    def filter(self, predicate: Callable[[Path], bool]) -> iterfiles:
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
                    st_gid: int | None = None,
                    st_gid__in: Sequence[int] | None = None,
                    st_size: int | None = None,
                    st_size__lt: int | None = None,
                    st_size__le: int | None = None,
                    st_size__gt: int | None = None,
                    st_size__ge: int | None = None,
                    st_size__range: tuple[int, int] | None = None,
                    st_atime: TimeT | None = None,
                    st_atime__ne: TimeT | None = None,
                    st_atime__lt: TimeT | None = None,
                    st_atime__le: TimeT | None = None,
                    st_atime__gt: TimeT | None = None,
                    st_atime__ge: TimeT | None = None,
                    st_atime__range: TimeTupleT | None = None,
                    st_mtime: TimeT | None = None,
                    st_mtime__ne: TimeT | None = None,
                    st_mtime__lt: TimeT | None = None,
                    st_mtime__le: TimeT | None = None,
                    st_mtime__gt: TimeT | None = None,
                    st_mtime__ge: TimeT | None = None,
                    st_mtime__range: TimeTupleT | None = None,
                    st_ctime: TimeT | None = None,
                    st_ctime__ne: TimeT | None = None,
                    st_ctime__lt: TimeT | None = None,
                    st_ctime__le: TimeT | None = None,
                    st_ctime__gt: TimeT | None = None,
                    st_ctime__ge: TimeT | None = None,
                    st_ctime__range: TimeTupleT | None = None,
                    ) -> iterfiles:
        exs: list[StatExpr] = list(expressions)
        if st_mode is not None:
            exs.append(_s.st_mode == st_mode)
        if st_mode__in is not None:
            exs.append(_s.st_mode.in_(st_mode__in))
        if st_mode__match is not None:
            exs.append(_s.st_mode.match(st_mode__match))

        if st_uid is not None:
            exs.append(_s.st_uid == st_uid)
        if st_uid__in is not None:
            exs.append(_s.st_uid.in_(st_uid__in))

        if st_gid is not None:
            exs.append(_s.st_uid == st_gid)
        if st_gid__in is not None:
            exs.append(_s.st_uid.in_(st_gid__in))

        if st_size is not None:
            exs.append(_s.st_size == st_size)
        if st_size__lt is not None:
            exs.append(_s.st_size < st_size__lt)
        if st_size__le is not None:
            exs.append(_s.st_size <= st_size__le)
        if st_size__gt is not None:
            exs.append(_s.st_size > st_size__gt)
        if st_size__ge is not None:
            exs.append(_s.st_size >= st_size__ge)
        if st_size__range is not None:
            exs.append(_s.st_size >= st_size__range[0])
            exs.append(_s.st_size <= st_size__range[1])

        if st_atime is not None:
            exs.append(_s.st_atime == st_atime)
        if st_atime__ne is not None:
            exs.append(_s.st_atime != st_atime__ne)
        if st_atime__lt is not None:
            exs.append(_s.st_atime < st_atime__lt)
        if st_atime__le is not None:
            exs.append(_s.st_atime <= st_atime__le)
        if st_atime__gt is not None:
            exs.append(_s.st_atime > st_atime__gt)
        if st_atime__ge is not None:
            exs.append(_s.st_atime >= st_atime__ge)
        if st_atime__range is not None:
            exs.append(_s.st_atime >= st_atime__range[0])
            exs.append(_s.st_atime <= st_atime__range[1])

        if st_mtime is not None:
            exs.append(_s.st_mtime == st_mtime)
        if st_mtime__ne is not None:
            exs.append(_s.st_mtime != st_mtime__ne)
        if st_mtime__lt is not None:
            exs.append(_s.st_mtime < st_mtime__lt)
        if st_mtime__le is not None:
            exs.append(_s.st_mtime <= st_mtime__le)
        if st_mtime__gt is not None:
            exs.append(_s.st_mtime > st_mtime__gt)
        if st_mtime__ge is not None:
            exs.append(_s.st_mtime >= st_mtime__ge)
        if st_mtime__range is not None:
            exs.append(_s.st_mtime >= st_mtime__range[0])
            exs.append(_s.st_mtime <= st_mtime__range[1])

        if st_ctime is not None:
            exs.append(_s.st_ctime == st_ctime)
        if st_ctime__ne is not None:
            exs.append(_s.st_ctime != st_ctime__ne)
        if st_ctime__lt is not None:
            exs.append(_s.st_ctime < st_ctime__lt)
        if st_ctime__le is not None:
            exs.append(_s.st_ctime <= st_ctime__le)
        if st_ctime__gt is not None:
            exs.append(_s.st_ctime > st_ctime__gt)
        if st_ctime__ge is not None:
            exs.append(_s.st_ctime >= st_ctime__ge)
        if st_ctime__range is not None:
            exs.append(_s.st_ctime >= st_ctime__range[0])
            exs.append(_s.st_ctime <= st_ctime__range[1])

        if op == 'and':
            op_callable = operator.and_
        elif op == 'or':
            op_callable = operator.or_
        else:
            raise ValueError(f"op argument has invalid value {op!r}, expected: 'and', 'or'")
        expr = reduce(op_callable, exs)
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
                     st_size__le: int | None = None,
                     st_size__gt: int | None = None,
                     st_size__ge: int | None = None,
                     st_size__range: tuple[int, int] | None = None,
                     st_atime: TimeT | None = None,
                     st_atime__lt: TimeT | None = None,
                     st_atime__le: TimeT | None = None,
                     st_atime__gt: TimeT | None = None,
                     st_atime__ge: TimeT | None = None,
                     st_atime__range: TimeTupleT | None = None,
                     st_mtime: TimeT | None = None,
                     st_mtime__lt: TimeT | None = None,
                     st_mtime__le: TimeT | None = None,
                     st_mtime__gt: TimeT | None = None,
                     st_mtime__ge: TimeT | None = None,
                     st_mtime__range: TimeTupleT | None = None,
                     st_ctime: TimeT | None = None,
                     st_ctime__lt: TimeT | None = None,
                     st_ctime__le: TimeT | None = None,
                     st_ctime__gt: TimeT | None = None,
                     st_ctime__ge: TimeT | None = None,
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
                                st_gid=st_gid__eq,
                                st_gid__in=st_gid__in,
                                st_size=st_size,
                                st_size__lt=st_size__lt,
                                st_size__le=st_size__le,
                                st_size__gt=st_size__gt,
                                st_size__ge=st_size__ge,
                                st_size__range=st_size__range,
                                st_atime=st_atime,
                                st_atime__lt=st_atime__lt,
                                st_atime__le=st_atime__le,
                                st_atime__gt=st_atime__gt,
                                st_atime__ge=st_atime__ge,
                                st_atime__range=st_atime__range,
                                st_mtime=st_mtime,
                                st_mtime__lt=st_mtime__lt,
                                st_mtime__le=st_mtime__le,
                                st_mtime__gt=st_mtime__gt,
                                st_mtime__ge=st_mtime__ge,
                                st_mtime__range=st_mtime__range,
                                st_ctime=st_ctime,
                                st_ctime__lt=st_ctime__lt,
                                st_ctime__le=st_ctime__le,
                                st_ctime__gt=st_ctime__gt,
                                st_ctime__ge=st_ctime__ge,
                                st_ctime__range=st_ctime__range)

    def text(self, encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None) -> _iterfiles_text:
        self._config.in_encoding = encoding
        self._config.in_errors = errors
        self._config.in_newline = newline
        return _iterfiles_text(self)

    def binary(self) -> _iterfiles_binary:
        return _iterfiles_binary(self)

    def foreach(self, function: Callable[[Path], Any]) -> None:
        for path in self:
            function(path)

    def set_output(self, target_dir: str | Path, rename: TRenameFunc | None = None) -> _iterfiles_map:
        self._config.target_dir = target_dir
        self._config.rename = rename
        return _iterfiles_map(self)

    def list(self) -> list[Path]:
        return list(self)

    def set(self) -> set[Path]:
        return set(self)


@dataclass
class _text_mixin:  # noqa

    _map_functions: list[Callable[[str], str]] = field(default_factory=list)

    def map(self, *functions: Callable[[str], str]) -> Self:
        self._map_functions.extend(functions)
        return self


class _iterfiles_text(_iterfiles_base, _text_mixin):  # noqa

    def __iter__(self) -> Generator[str]:
        encoding = self._config.in_encoding
        errors = self._config.in_errors
        newline = self._config.in_newline
        map_function = self._config.map_function
        for in_path in self._iter_paths():
            with open(in_path, encoding=encoding, errors=errors, newline=newline) as file:
                text = file.read()
                if map_function is not None:
                    text = map_function(text)
                yield text

    def set_output(self, target_dir: str | Path, rename: TRenameFunc | None = None) -> _iterfiles_text_map:
        self._config.target_dir = target_dir
        self._config.rename = rename
        return _iterfiles_text_map(self)

    def foreach(self, function: Callable[[str], Any]) -> None:
        for text in self:
            function(text)


@dataclass
class _binary_mixin:  # noqa

    _map_functions: list[Callable[[bytes], bytes]] = field(default_factory=list)

    def map(self, *functions: Callable[[bytes], bytes]) -> Self:
        self._map_functions.extend(functions)
        return self


class _iterfiles_binary(_iterfiles_base, _binary_mixin):  # noqa

    def __iter__(self) -> Generator[bytes]:
        map_function = self._config.map_function
        for in_path in self._iter_paths():
            with open(in_path, mode='rb') as file:
                binary = file.read()
                if map_function is not None:
                    binary = map_function(binary)
                yield binary

    def set_output(self, target_dir: str | Path, rename: TRenameFunc | None = None) -> _iterfiles_binary_map:
        self._config.target_dir = target_dir
        self._config.rename = rename
        return _iterfiles_binary_map(self)

    def foreach(self, function: Callable[[bytes], Any]) -> None:
        for binary in self:
            function(binary)


class _iterfiles_map_base(_iterfiles_base):  # noqa

    def _iter_tuples(self) -> Generator[tuple[Path, Path]]:
        source_dir = _ensure_dir(self._config.dir_path)
        if self._config.target_dir is None:
            raise Exception('iterfiles: internal error: target_dir not set, please contact the maintainer')
        target_dir = _ensure_dir(self._config.target_dir, must_exist=False)
        # Make sure caller is not messing up the directory structure.
        if target_dir in source_dir.parents or source_dir in target_dir.parents:
            raise InvalidPathError('Source must not be a parent of Target (and vice versa)')

        parents = set()  # optimize os.makedirs for "thousands of files in a folder" scenario

        rename = self._config.rename
        for source_file_path in self._iter_paths():
            target_file_path = target_dir / source_file_path.relative_to(source_dir)
            if rename:
                new_name = rename(target_file_path)
                target_file_path = target_file_path.parent / (new_name.name if type(new_name) is Path else new_name)
            if target_file_path.parent not in parents:
                os.makedirs(target_file_path.parent, exist_ok=True)
                parents.add(target_file_path.parent)
            yield source_file_path, target_file_path


class _iterfiles_map(_iterfiles_map_base, Iterable[tuple[Path, Path]]):  # noqa

    def __iter__(self) -> Generator[tuple[Path, Path]]:
        return self._iter_tuples()

    def foreach(self, function: Callable[[Path, Path], Any]) -> None:
        for in_path, out_path in self._iter_tuples():
            function(in_path, out_path)

    def text(self) -> _iterfiles_text_map:
        return _iterfiles_text_map(self)

    def binary(self) -> _iterfiles_binary_map:
        return _iterfiles_binary_map(self)

    def write_text(self, function: Callable[[Path], str], *, encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None) -> None:
        for in_path, out_path in self:
            with open(out_path, 'w', encoding=encoding, errors=errors, newline=newline) as out_file:
                out_file.write(function(in_path))

    def write_binary(self, function: Callable[[Path], bytes]) -> None:
        for in_path, out_path in self:
            with open(out_path, 'wb') as out_file:
                out_file.write(function(in_path))

    def list(self) -> list[tuple[Path, Path]]:
        return list(self)


def _encode_utf8(s: str) -> bytes:
    return s.encode('utf8')


class _iterfiles_text_map(_iterfiles_map_base, _text_mixin, Iterable[tuple[str, Path]]):  # noqa

    def __iter__(self) -> Generator[tuple[str, Path]]:
        encoding = self._config.in_encoding
        errors = self._config.in_errors
        newline = self._config.in_newline
        for in_path, out_path in self._iter_tuples():
            with open(in_path, encoding=encoding, errors=errors, newline=newline) as file:
                yield file.read(), out_path

    def foreach(self, function: Callable[[str, Path], Any]) -> None:
        for text_in, path_out in self:
            function(text_in, path_out)

    def write_text(self, function: Callable[[str], str] | None = None, *, encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None) -> None:
        for in_text, out_path in self:
            for f in self._map_functions:
                in_text = f(in_text)
            with open(out_path, 'w', encoding=encoding, errors=errors, newline=newline) as out_file:
                if function is not None:
                    in_text = function(in_text)
                out_file.write(in_text)

    def write_binary(self, function: Callable[[str], bytes] = _encode_utf8) -> None:
        for in_text, out_path in self:
            for f in self._map_functions:
                in_text = f(in_text)
            with open(out_path, 'wb') as out_file:
                out_file.write(function(in_text))


def _decode_utf8(b: bytes) -> str:
    return b.decode('utf8')


class _iterfiles_binary_map(_iterfiles_map_base, _binary_mixin, Iterable[tuple[bytes, Path]]):  # noqa

    def __iter__(self) -> Generator[tuple[bytes, Path]]:
        for in_path, out_path in self._iter_tuples():
            with open(in_path, 'rb') as file:
                yield file.read(), out_path

    def foreach(self, function: Callable[[bytes, Path], Any]) -> None:
        for bytes_in, path_out in self:
            function(bytes_in, path_out)

    def write_text(self, function: Callable[[bytes], str] = _decode_utf8, *, encoding: str | None = 'utf-8', errors: str | None = None, newline: str | None = None) -> None:
        for in_bytes, out_path in self:
            for f in self._map_functions:
                in_bytes = f(in_bytes)
            with open(out_path, 'w', encoding=encoding, errors=errors, newline=newline) as out_file:
                out_file.write(function(in_bytes))

    def write_binary(self, function: Callable[[bytes], bytes] | None = None) -> None:
        for in_bytes, out_path in self:
            for f in self._map_functions:
                in_bytes = f(in_bytes)
            with open(out_path, 'wb') as out_file:
                if function is not None:
                    in_bytes = function(in_bytes)
                out_file.write(in_bytes)
