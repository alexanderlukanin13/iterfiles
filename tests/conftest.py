import functools
import os
from pathlib import Path

import pendulum
import pytest

from iterfiles.stat import Path as IPath


@pytest.fixture
def cache_glob(monkeypatch):
    """Optimization: cache Path.glob results."""
    @functools.cache
    def cached_glob(path: IPath, pattern: str):
        return list(Path.glob(path, pattern))

    with monkeypatch.context() as m:
        m.setattr(IPath, "glob", cached_glob)
        yield


@pytest.fixture
def cache_stat(monkeypatch):
    """Optimization: cache Path.stat results."""
    path_stat = Path.stat
    os_stat = os.stat

    @functools.cache
    def cached_path_stat(path, *, follow_symlinks = True) -> os.stat_result:
        return path_stat(path, follow_symlinks=follow_symlinks)

    @functools.cache
    def cached_os_stat(path, *, dir_fd=None, follow_symlinks = True) -> os.stat_result:
        return os_stat(path, dir_fd=dir_fd, follow_symlinks=follow_symlinks)

    with monkeypatch.context() as m:
        m.setattr(IPath, "stat", cached_path_stat)
        m.setattr(os, "stat", cached_os_stat)
        yield


@pytest.fixture
def cache_fs_read(cache_glob, cache_stat):
    """Optimization: cache relevant filesystem reading operations."""
    return


def patch_local_timezone(monkeypatch, tz):
    def local_timezone():
        return pendulum.timezone(tz)

    with monkeypatch.context() as m:
        m.setattr(pendulum, 'local_timezone', local_timezone)
        yield

@pytest.fixture
def local_timezone_alaska(monkeypatch):
    yield from patch_local_timezone(monkeypatch, 'US/Alaska')

@pytest.fixture
def local_timezone_paris(monkeypatch):
    yield from patch_local_timezone(monkeypatch, 'Europe/Paris')

@pytest.fixture
def local_timezone_bishkek(monkeypatch):
    yield from patch_local_timezone(monkeypatch, 'Asia/Bishkek')
