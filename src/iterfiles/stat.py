import ast
import os
import re
from ast import (Attribute, Compare, Name, Load, Lt, LtE, Gt, GtE, Eq, NotEq, Constant, And, Or, Not, BoolOp, UnaryOp,
                 FunctionDef, Return, Module)
from _ast import expr, cmpop
from datetime import datetime, date
import pathlib
from functools import cached_property
from typing import Callable

__all__ = ['st_mode', 'st_uid', 'st_gid', 'st_size', 'st_atime', 'st_mtime', 'st_ctime']

import pendulum
from pendulum import Interval, DateTime

from iterfiles.pendulum import DateWithUnit, DateDay, parse_humanized


class IterfilesPath(pathlib.Path):
    """Custom Path subclass with stat caching."""

    @cached_property
    def _stat(self) -> os.stat_result:
        return super().stat()

    @property
    def st_mode(self) -> int:
        return self._stat.st_mode

    @property
    def st_uid(self) -> int:
        return self._stat.st_uid

    @property
    def st_gid(self) -> int:
        return self._stat.st_gid

    @property
    def st_size(self) -> int:
        return self._stat.st_size

    @property
    def st_atime(self) -> float:
        return self._stat.st_atime

    @property
    def st_mtime(self) -> float:
        return self._stat.st_mtime

    @property
    def st_ctime(self) -> float:
        return self._stat.st_ctime


class IterfilesPathSym(IterfilesPath):

    @cached_property
    def _stat(self) -> os.stat_result:
        return super().stat(follow_symlinks=True)


class StatExpr:

    def __init__(self, ast_expr: expr):
        self.ast_expr = ast_expr

    def __and__(self, other: 'StatExpr') -> 'StatExpr':
        return StatExpr(
            BoolOp(
                op=And(),
                values=[self.ast_expr, other.ast_expr]
            )
        )

    def __or__(self, other: 'StatExpr') -> 'StatExpr':
        return StatExpr(
            BoolOp(
                op=Or(),
                values=[self.ast_expr, other.ast_expr]
            )
        )

    def __invert__(self) -> 'StatExpr':
        return StatExpr(
            UnaryOp(
                op=Not(),
                operand=self.ast_expr
            )
        )

    def compile_function(self) -> Callable[[pathlib.Path], bool]:
        module =  Module(body=[FunctionDef(
            name='f',
            args=ast.arguments(args=[ast.arg(arg='x')]),
            body=[
                Return(value=self.ast_expr)
            ]
        )])
        ast.fix_missing_locations(module)
        d = {}
        exec(compile(module, '<filter-stat>', 'exec'), d)
        return d['f']  # type: ignore  # noqa


class _StatParam:

    _TYPES: tuple = (int,)

    def __init__(self, attr: str):
        self.attr = attr

    def _compare(self, cmp: type[cmpop], value) -> StatExpr:
        return StatExpr(
            Compare(
                left=Attribute(
                    value=Attribute(
                        value=Name(id='x', ctx=Load()),
                        attr='_stat',
                        ctx=Load()),
                    attr=self.attr,
                    ctx=Load()),
                ops=[cmp()],
                comparators=[Constant(value=value)])
        )

    def _in_range(self, start: int | float, end: int | float) -> StatExpr:
        assert start < end, "INTERNAL ERROR: Invalid range: {value!r}, you shouldn't see this, please contact the maintainer"
        return StatExpr(
            Compare(
                left=Constant(value=start),
                ops=[LtE(), LtE()],
                comparators=[
                    Attribute(
                        value=Attribute(
                            value=Name(id='x', ctx=Load()),
                            attr='_stat',
                            ctx=Load()),
                        attr=self.attr,
                        ctx=Load()),
                    Constant(value=end)])
        )

    def _not_in_range(self, start: int | float, end: int | float) -> StatExpr:
        assert start < end, "INTERNAL ERROR: Invalid range: {value!r}, you shouldn't see this, please contact the maintainer"
        return StatExpr(
            UnaryOp(
                op=Not(),
                operand=Compare(
                    left=Constant(value=start),
                    ops=[LtE(), LtE()],
                    comparators=[
                        Attribute(
                            value=Attribute(
                                value=Name(id='x', ctx=Load()),
                                attr='_stat',
                                ctx=Load()),
                            attr=self.attr,
                            ctx=Load()),
                        Constant(value=end)]))
        )

    def _check_type(self, value):
        if not isinstance(value, self._TYPES):
            raise TypeError(f'Unexpected type for {self.attr}: {type(value)} (expected {"/".join(x.__qualname__ for x in self._TYPES)})')

    def _check_types(self, values):
        for value in values:
            if not isinstance(value, self._TYPES):
                raise TypeError(f'Unexpected type in {self.attr}: {type(value)} (expected collection of {"/".join(x.__qualname__ for x in self._TYPES)})')

    def __eq__(self, value: int) -> StatExpr:  # type: ignore
        self._check_type(value)
        return self._compare(Eq, value)

    def __ne__(self, value: int) -> StatExpr:  # type: ignore
        self._check_type(value)
        return self._compare(NotEq, value)

    def __lt__(self, value: int) -> StatExpr:
        self._check_type(value)
        return self._compare(Lt, value)

    def __le__(self, value: int) -> StatExpr:
        self._check_type(value)
        return self._compare(LtE, value)

    def __gt__(self, value: int) -> StatExpr:
        self._check_type(value)
        return self._compare(Gt, value)

    def __ge__(self, value: int) -> StatExpr:
        self._check_type(value)
        return self._compare(GtE, value)

    def in_(self, values: list[int]):
        if not hasattr(values, '__contains__'):
            raise TypeError(f'Unexpected type for {self.attr}: {type(values)} (expected collection of {"/".join(x.__qualname__ for x in self._TYPES)})')
        self._check_types(values)
        raise NotImplementedError


class _StatParamID(_StatParam):
    pass


class _StatParamSize(_StatParam):
    _TYPES = (int, str)


class _StatParamTime(_StatParam):
    _TYPES = (int, float, datetime, date, str)

    def __eq__(self, value: int | float | datetime | date | str) -> StatExpr:
        self._check_type(value)
        value = _process_value(value)
        if isinstance(value, tuple):
            return self._in_range(value[0], value[1])
        else:
            return self._compare(Eq, value)

    def __ne__(self, value: int | float | datetime | date | str) -> StatExpr:
        self._check_type(value)
        value = _process_value(value)
        if isinstance(value, tuple):
            return self._not_in_range(value[0], value[1])
        else:
            return self._compare(NotEq, value)

    def __lt__(self, value: int | float | datetime | date | str) -> StatExpr:
        self._check_type(value)
        return self._compare(Lt, _lower_bound(value))

    def __le__(self, value: int | float | datetime | date | str) -> StatExpr:
        self._check_type(value)
        return self._compare(LtE, _upper_bound(value))

    def __gt__(self, value: int | float | datetime | date | str) -> StatExpr:
        self._check_type(value)
        return self._compare(Gt, _upper_bound(value))

    def __ge__(self, value: int | float | datetime | date | str) -> StatExpr:
        self._check_type(value)
        return self._compare(GtE, _lower_bound(value))


def _process_value(value: int | float | datetime | date | str
                   ) -> int | float | tuple[float, float] | DateWithUnit:
    """
    Process user-defined value given to StatExpr (e.g. st_mtime < '2026-03-25'),
    parse if str, and normalize to timestamp/DateWithUnit, or interval of those.
    """
    # 1.a. int/float timestamp: return as is
    if isinstance(value, (int, float)):
        return value
    # 1.b. str: parse and continue to other data types
    elif isinstance(value, str):
        value = parse_humanized(value)
        # NOTE: no return, fall through to next if block

    # 2.a. datetime: add local timezone if naive, and return as timestamp
    if isinstance(value, datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=pendulum.local_timezone())
        return value.timestamp()
    # 2.b. DateWithUnit: - return as a pair of timestamps
    elif isinstance(value, DateWithUnit):
        value = value.as_interval()
        return value.start.timestamp(), value.end.timestamp()
    # 2.c. naive date (user-supplied): add local timezone and return as timestamp
    elif isinstance(value, date):
        value = DateDay(value.year, value.month, value.day, tzinfo=pendulum.local_timezone()).as_interval()
        return value.start.timestamp(), value.end.timestamp()
    # 2.d. Interval: return as a pair of timestamps
    elif isinstance(value, Interval):
        if isinstance(value.start, DateTime):
            return value.start.timestamp(), value.end.timestamp()
        else:
            return value.start.as_interval().start.timestamp(), value.end.as_interval().end.timestamp()
    raise TypeError(f'Unexpected type for timestamp: {value!r} (must be int/float/str/date/datetime)')


def _lower_bound(value: int | float | datetime | date | str) -> int | float:
    value = _process_value(value)
    if isinstance(value, tuple):
        value = value[0]
    assert isinstance(value, (int, float))
    return value


def _upper_bound(value: int | float | datetime | date | str) -> int | float:
    value = _process_value(value)
    if isinstance(value, tuple):
        value = value[1]
    assert isinstance(value, (int, float))
    return value


class _StatParamMode(_StatParam):
    _TYPES = (int, str, re.Pattern)

    def match(self, pattern: int | str | re.Pattern) -> StatExpr:
        raise NotImplementedError



st_uid = _StatParamID('st_uid')
st_gid = _StatParamID('st_gid')
st_size = _StatParamSize('st_size')
st_atime = _StatParamTime('st_atime')
st_mtime = _StatParamTime('st_mtime')
st_ctime = _StatParamTime('st_ctime')
st_mode = _StatParamMode('st_mode')
