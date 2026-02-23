import operator
import os
from pathlib import Path
from typing import Callable, Iterable, Tuple, Union, Any


# Function to change name (or extension) of a target file
_RenameFunc = Union[None, Callable[[Path], Path]]
_Rename = Union[_RenameFunc, str]
# Function to change order of glob traverse
_KeyFunc = Union[None, Callable[[Path], Any]]


class InvalidDirectoryError(Exception):
    """Source or target directory argument is not acceptable."""
    pass


def _ensure_dir(dir_path: Union[str, Path], must_exist=True) -> Path:
    """
    Convert str to Path. Check if directory exists and contains no invalid symbols.
    """
    dir_path = Path(dir_path)
    s = str(dir_path)
    if '*' in s or '?' in s:
        raise InvalidDirectoryError(f'Path contains invalid symbols (did you mean to use "pattern" argument instead?): {dir_path}')
    if dir_path.exists():
        if not dir_path.is_dir():
            raise NotADirectoryError(f'Not a directory: {dir_path}')
    elif must_exist:
        raise FileNotFoundError(f'Directory not found: {dir_path}')
    return dir_path


class iterfiles:  # noqa

    def __init__(self, dir_path: Union[str, Path], pattern: str = '**/*', is_file=True) -> Iterable[Path]:
        """
        Iterates over file names in dir_path.

        Use glob pattern to filter; by default, all files in all subdirectories are included.
        """
        self._dir_path = _ensure_dir(dir_path)
        self._file_paths = self._dir_path.glob(pattern)
        if is_file:
            self.filter(lambda x: x.is_file())

    def sort(self, key: Callable[[Path], Any], desc: bool = False):
        if type(self._file_paths) is not list:
            self._file_paths = list(self._file_paths)
        self._file_paths.sort(key, desc)
        return self

    def filter(self, predicate: Callable[[Path], bool]):
        self._file_paths = filter(predicate, self._file_paths)
        return self

    def filter_stat(self, predicate: Callable[[os.stat_result], bool], **kw):
        if kw:
            ltgt = ltgt_predicate(kw)
            predicate = lambda x: predicate(x) and ltgt(x)
        self._file_paths = filter(lambda x: predicate(x.stat()), self._file_paths)
        return self

    def __iter__(self):
        yield from self._file_paths

    def texts(self, encoding='utf-8', errors=None, newline=None):
        for file_path in self:
            with open(file_path, encoding=encoding, errors=errors, newline=newline) as file:
                yield file.read()

    def _target(self, target_dir: Union[str, Path], rename: _Rename = None) -> Iterable[Tuple[Path, Path]]:
        """
        Creates the same hierarchy of subdirectories in target_dir as in source_dir.
        Iterates over pairs: each Path in source_dir, and corresponding Path in target_dir.
        """
        target_dir = _ensure_dir(target_dir, must_exist=False)
        # Make sure caller is not messing up the directory structure.
        if target_dir in self._dir_path.parents or self._dir_path in target_dir.parents:
            raise InvalidDirectoryError('Source must not be a parent of Target (and vice versa)')

        # If rename is a string, it's a new file extension
        if isinstance(rename, str):
            suffix = rename
            if not suffix.startswith('.'):
                suffix = '.' + suffix
            rename = lambda x: x.with_suffix(suffix)

        parents = set()  # optimize os.makedirs for "thousands of files in a folder" scenario

        for source_file_path in self:
            target_file_path = target_dir / source_file_path.relative_to(source_dir)
            if rename:
                new_name = rename(target_file_path)
                target_file_path = target_file_path.parent / (new_name.name if type(new_name) is Path else new_name)
            if target_file_path.parent not in parents:
                os.makedirs(target_file_path.parent, exist_ok=True)
                parents.add(target_file_path.parent)
            yield source_file_path, target_file_path

    def convert(self, target_dir: Union[str, Path], function: Callable[[Path, Path], Any], rename: _Rename = None) -> None:
        for source_file_path, target_file_path in self._target(target_dir, rename):
            function(source_file_path, target_file_path)

    def convert_text(self, target_dir: Union[str, Path], function: Callable[[str], str],
                      rename: _Rename = None
                      encoding='utf-8', errors=None, newline=None,
                      output_encoding='utf-8', output_errors=None, output_newline=None):
        for source_file_path, target_file_path in self._target(target_dir, rename):
            with open(source_file_path, encoding=encoding, errors=errors, newline=newline) as source_file:
                with open(target_file_path, 'w', encoding=output_encoding, errors=output_errors, newline=output_newline) as target_file:
                    target_file.write(function(source_file.read()))


# def iter_texts(dir_path: Union[str, Path], pattern: str = '**/*', key: _KeyFunc = None, encoding=None, errors=None, newline=None) -> Iterable[str]:
# iter_texts(source, pattern)
# iterfiles(source, pattern).text()

# def for_each_file(dir_path: Union[str, Path], function: Callable[[Path], Any], pattern: str = '**/*', key: _KeyFunc = None) -> None:
# for_each_file(source, function, pattern)
# iterfiles(source, pattern).foreach(function)
# for file in iterfiles

# def for_each_text(dir_path: Union[str, Path], function: Callable[[str], Any], pattern: str = '**/*', key: _KeyFunc = None,
#                   encoding=None, errors=None, newline=None) -> None:
# for_each_text(source, function, pattern)
# for text in iterfiles(source, pattern).text():
#     function(text)
# iterfiles(source, pattern).foreach_text(function)


# def iter_source_target_files(source_dir: Union[str, Path], target_dir: Union[str, Path], pattern: str = '**/*', key: _KeyFunc = None, rename: _RenameFunc = None) -> Iterable[Tuple[Path, Path]]:
# iter_source_target_files(source, target, pattern, rename)
# iterfiles(source, pattern).target(target, rename)

# def convert_files(source_dir: Union[str, Path], target_dir: Union[str, Path], function: Callable[[Path, Path], Any], pattern: str = '**/*', key: _KeyFunc = None, rename: _RenameFunc = None) -> None:
# convert_files(source, target, function, pattern, rename)
# iterfiles(source, pattern).convert(target, function, rename)

# def convert_texts(source_dir: Union[str, Path], target_dir: Union[str, Path], function: Callable[[str], str], pattern: str = '**/*', key: _KeyFunc = None, rename: _RenameFunc = None,
#                   encoding=None, errors=None, newline=None,
#                   output_encoding=None, output_errors=None, output_newline=None) -> None:
# convert_texts(source, target, function, pattern, rename, encoding='utf-8')
# iterfiles(source, pattern).convert_text(target, function, rename, encoding='utf-8')
# from iterfiles.stat import st_size
# iterfiles(source, pattern).filter(st_size < 1024).convert_text(target, function, rename, encoding='utf-8')
iterfiles(source, pattern).filter_st(lambda x: x.st_size<1024).convert_text(target, function, rename='jpg')
iterfiles(source, pattern).filter_st(st_size<1024).convert_text(target, function, rename='jpg')

# iterfiles(path, pattern='').filter(lambda whatever).to_target(target_path).foreach(func)
# iterfiles(path, pattern='').filter(lambda whatever).to_target(target_path).foreach_text(func2
# for_each_text()


class OperatorPredicate:
    def __init__(self, namespace, params, default_op=None):
        self.combine = all
        self._ops = []
        for x in params:
            x = x.split('__', 1)
            value = x[0]
            op = getattr(namespace, default_op if len(x) == 1 else x[1])
            self._ops.append((op, value))

    def __call__(self, x):
        return self.combine(op(x, value) for op, value in self._ops)


def ltgt_predicate(**kw):
    return OperatorPredicate(operator, kw, default_op='eq')


class StatLambda:
    def __init__(self, st_field):
        self.st = st_field

    def __lt__(self, other):
        st = self.st
        return lambda x: getattr(x.stat(), st) < other
    
    def __lte__(self, other):
        st = self.st
        return lambda x: getattr(x.stat(), st) <= other
    
    def __gt__(self, other):
        st = self.st
        return lambda x: getattr(x.stat(), st) > other
    
    def __gte__(self, other):
        st = self.st
        return lambda x: getattr(x.stat(), st) >= other
    
    def __eq__(self, other):
        st = self.st
        return lambda x: getattr(x.stat(), st) == other
    
    def __neq__(self, other):
        st = self.st
        return lambda x: getattr(x.stat(), st) != other


st_size = StatLambda('st_size')

# !λ.stat().st_size > 16*1024*1024 and λ.contains('haha')
# 0 <= λ <= 100
 
λ.__inrange(0, 100)


iterfiles FileFilter()

(st_size__in=(1,100) and st_whatever > 100)
