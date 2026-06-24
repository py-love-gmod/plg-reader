from plg_reader import IRFunctionDef, IRName


def test_star_args_with_annotation(parse_code):
    ir = parse_code("def f(*args: int): pass")
    func = ir.body[0]
    assert isinstance(func, IRFunctionDef)
    p = func.params[0]
    assert p.name == "args"
    assert p.kind == "star_arg"
    assert p.annotation is not None
    assert isinstance(p.annotation, IRName)
    assert p.annotation.name == "int"
    assert p.default is None


def test_kw_args_with_annotation(parse_code):
    ir = parse_code("def f(**kwargs: str): pass")
    func = ir.body[0]
    p = func.params[0]
    assert p.name == "kwargs"
    assert p.kind == "kw_arg"
    assert p.annotation is not None
    assert isinstance(p.annotation, IRName)
    assert p.annotation.name == "str"


def test_star_no_annotation(parse_code):
    ir = parse_code("def f(*args): pass")
    func = ir.body[0]
    p = func.params[0]
    assert p.name == "args"
    assert p.kind == "star_arg"
    assert p.annotation is None


def test_star_and_kw_combined(parse_code):
    ir = parse_code("def f(a, *args: list, **kwargs: dict): pass")
    func = ir.body[0]
    assert len(func.params) == 3
    star = func.params[1]
    assert star.name == "args"
    assert star.kind == "star_arg"
    assert isinstance(star.annotation, IRName)
    assert star.annotation.name == "list"
    kw = func.params[2]
    assert kw.name == "kwargs"
    assert kw.kind == "kw_arg"
    assert isinstance(kw.annotation, IRName)
    assert kw.annotation.name == "dict"
