import os
import sysconfig
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from functools import cache

import clii

from .bynary_rw import BinaryRW


@cache
def get_cpus_and_executor() -> tuple[
    int,
    type[ThreadPoolExecutor] | type[ProcessPoolExecutor],
]:
    cpus = os.cpu_count() or 1
    if bool(sysconfig.get_config_var("Py_GIL_DISABLED")):
        return cpus, ThreadPoolExecutor

    else:
        return cpus, ProcessPoolExecutor


__all__ = [
    "clii",
    "BinaryRW",
    "get_cpus_and_executor",
]
