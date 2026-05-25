import pytest


def test_yield_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("def f(): yield x")


def test_lambda_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("f = lambda x: x")


def test_global_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("global a")


def test_nonlocal_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("nonlocal b")


def test_async_def_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("async def f(): pass")


def test_await_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("await something")


def test_slice_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("x[1:2]")


def test_walrus_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("(a := 1)")


def test_star_unpack_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("[*a]")


def test_import_star_forbidden(parse_code):
    with pytest.raises((SyntaxError, RuntimeError)):
        parse_code("from module import *")
