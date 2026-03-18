import ast
from ast import (Attribute, Compare, Name, Load, Lt, LtE, Gt, GtE, Eq, NotEq, Constant, And, Or, Not, BoolOp, UnaryOp,
                 FunctionDef, Return, Module)
from datetime import datetime, date
import pathlib
from functools import cached_property
from typing import TypeVar, Callable


class Path(pathlib.Path):
    """Custom Path subclass with stat caching."""

    @cached_property
    def _stat(self):
        return super().stat()


StatExprT = TypeVar('StatExpr')


class StatExpr:

    def __init__(self, ast_expr: ast.expr):
        self.ast_expr = ast_expr

    def __and__(self, other: StatExprT) -> StatExprT:
        return StatExpr(
            BoolOp(
                op=And(),
                values=[self.ast_expr, other.ast_expr]
            )
        )

    def __or__(self, other: StatExprT) -> StatExprT:
        return StatExpr(
            BoolOp(
                op=Or(),
                values=[self.ast_expr, other.ast_expr]
            )
        )

    def __not__(self) -> StatExprT:
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
        exec(compile(module, '<string>', 'exec'))
        return f  # noqa


class _StatParam:

    _TYPES = (int,)

    def __init__(self, attr: str):
        self.attr = attr

    def _compare(self, cmp: type[ast.cmpop], other) -> StatExpr:
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
                comparators=[Constant(value=other)])
        )

    def _check_type(self, other):
        if not isinstance(other, self._TYPES):
            raise TypeError(f'Unexpected type for {self.attr}: {type(other)} (expected {"/".join(x.__qualname__ for x in self._TYPES)})')

    def _check_types(self, others):
        for other in others:
            if not isinstance(other, self._TYPES):
                raise TypeError(f'Unexpected type in {self.attr}: {type(other)} (expected collection of {"/".join(x.__qualname__ for x in self._TYPES)})')

    def __eq__(self, other) -> StatExpr:
        self._check_type(other)
        return self._compare(Eq, other)

    def __ne__(self, other) -> StatExpr:
        self._check_type(other)
        return self._compare(NotEq, other)

    def __lt__(self, other) -> StatExpr:
        self._check_type(other)
        return self._compare(Lt, other)

    def __lte__(self, other) -> StatExpr:
        self._check_type(other)
        return self._compare(LtE, other)

    def __gt__(self, other) -> StatExpr:
        self._check_type(other)
        return self._compare(Gt, other)

    def __gte__(self, other) -> StatExpr:
        self._check_type(other)
        return self._compare(Gt, other)

    def in_(self, others):
        if not hasattr(others, '__contains__'):
            raise TypeError(f'Unexpected type for {self.attr}: {type(others)} (expected collection of {"/".join(x.__qualname__ for x in self._TYPES)})')
        self._check_types(others)
        raise NotImplementedError


class _StatParamID(_StatParam):
    pass


class _StatParamSize(_StatParam):
    pass


class _StatParamTime(_StatParam):



    def _time_as_int_lower(self, arg: int | datetime | date) -> int:
        if isinstance(arg, date):
            return datetime.combine(arg, datetime.min.time())

    def __lt__(self, other: int | datetime | date):
        if isinstance(other, datetime):
            raise NotImplementedError
        elif isinstance(other, date):
            raise NotImplementedError
        elif not isinstance(other, int):
            raise TypeError(f'Cannot compare {self.attr} to {type(other)}, expecting int/date/datetime')
        return StatExpr(self._ast_compare(Lt, other))





st_uid = _StatParamID('st_uid')
st_gid = _StatParamID('st_gid')
st_size = _StatParamSize('st_size')
st_atime = _StatParamTime('st_atime')
st_mtime = _StatParamTime('st_mtime')
st_ctime = _StatParamTime('st_ctime')
