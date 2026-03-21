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


class Path(pathlib.Path):
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
        print(ast.dump(module, indent=4))
        exec(compile(module, '<ast>', 'exec'))
        return f  # type: ignore  # noqa


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

    def _check_type(self, value):
        if not isinstance(value, self._TYPES):
            raise TypeError(f'Unexpected type for {self.attr}: {type(value)} (expected {"/".join(x.__qualname__ for x in self._TYPES)})')

    def _check_types(self, values):
        for value in values:
            if not isinstance(value, self._TYPES):
                raise TypeError(f'Unexpected type in {self.attr}: {type(value)} (expected collection of {"/".join(x.__qualname__ for x in self._TYPES)})')

    def __eq__(self, value) -> StatExpr:  # type: ignore
        self._check_type(value)
        return self._compare(Eq, value)

    def __ne__(self, value) -> StatExpr:  # type: ignore
        self._check_type(value)
        return self._compare(NotEq, value)

    def __lt__(self, value) -> StatExpr:
        self._check_type(value)
        return self._compare(Lt, value)

    def __le__(self, value) -> StatExpr:
        self._check_type(value)
        return self._compare(LtE, value)

    def __gt__(self, value) -> StatExpr:
        self._check_type(value)
        return self._compare(Gt, value)

    def __ge__(self, value) -> StatExpr:
        self._check_type(value)
        return self._compare(Gt, value)

    def in_(self, values):
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

    def __lt__(self, value: int | float | datetime | date | str):
        if isinstance(value, datetime):
            raise NotImplementedError
        elif isinstance(value, date):
            raise NotImplementedError
        elif not isinstance(value, int):
            raise TypeError(f'Cannot compare {self.attr} to {type(value)}, expecting int/date/datetime')
        return self._compare(Lt, value)


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
