import sys
from pathlib import Path

from plg_reader import build_python_file

sys.stdout.reconfigure(encoding="utf-8")  # pyright: ignore[reportAttributeAccessIssue]


"""
Многострочный
docstring
"""

c = 10
d = 20


def func(a, y=0):
    pass


class obj:
    attr = type("attr", (), {"method": print})()


lst = [0]
dct = {"key": 0}

x = 42
y: int = 10
z: str
x += 1
a, b = 1, 2

func(x, y=5)
lst[0]
dct["key"]

neg = -x
result = a + b * c if c else d

my_list = [1, 2, 3]
my_tuple = (1, 2, 3)
my_set = {1, 2, 3}
my_dict = {"a": 1, "b": 2}

name = "World"
greeting = f"Hello {name}!"
debug_str = rf"Debug {name=}"


def foo(x):
    del x
    raise ValueError("an error")
    pass


# End of test
ir = build_python_file(Path(__file__))
print(ir.pretty())
